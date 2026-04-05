from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename

from app import config
from app.print_queue import PrintQueueWorker
from app.printing import get_pdf_page_count
from app.state import AppState


_FIREWALL_RULE_NAME = "Yumis Printer"


def _try_add_firewall_rule(port: int) -> None:
    """Best-effort: create a Windows Firewall inbound rule by port so the EXE
    is not blocked regardless of its extraction path (one-file PyInstaller)."""
    if sys.platform != "win32":
        return
    try:
        flags = 0x08000000  # CREATE_NO_WINDOW
        # Check if rule already exists
        check = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule",
             f"name={_FIREWALL_RULE_NAME}"],
            capture_output=True, timeout=5, creationflags=flags,
        )
        if check.returncode == 0:
            return  # already registered
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={_FIREWALL_RULE_NAME}",
             "dir=in", "action=allow", "protocol=tcp",
             f"localport={port}", "profile=private,domain"],
            capture_output=True, timeout=10, creationflags=flags,
        )
    except Exception:
        pass  # If it fails (e.g. not admin) the Windows dialog will appear instead


def create_app(state: AppState, queue_worker: PrintQueueWorker) -> Flask:
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / "templates"),
        static_folder=str(config.BASE_DIR / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

    @app.get("/")
    def home():
        message = request.args.get("message", "")
        message_type = request.args.get("type", "info")
        return render_template(
            "index.html",
            printers=state.get_shared_printers(),
            server_url=state.get_server_url(),
            allowed_extensions=sorted(config.ALLOWED_EXTENSIONS),
            max_upload_mb=config.MAX_UPLOAD_MB,
            job_counts=state.get_job_counts(),
            message=message,
            message_type=message_type,
        )

    @app.post("/upload")
    def upload_file():
        uploaded_file = request.files.get("document")
        if uploaded_file is None or not uploaded_file.filename:
            return _redirect_home("Selecione um arquivo para enviar.", "error")

        file_suffix = Path(uploaded_file.filename).suffix.lower()
        if file_suffix not in config.ALLOWED_EXTENSIONS:
            return _redirect_home("Formato nao suportado para impressao.", "error")

        if not state.get_shared_printers():
            return _redirect_home("Nenhuma impressora foi liberada pelo host.", "error")

        safe_name = secure_filename(uploaded_file.filename)
        target_name = f"{uuid4().hex}_{safe_name}"
        target_path = config.UPLOAD_DIR / target_name
        uploaded_file.save(target_path)

        state.add_log(f"Arquivo recebido de um cliente: {safe_name}")
        return redirect(url_for("preview_upload", upload_name=target_name))

    @app.get("/preview/<path:upload_name>")
    def preview_upload(upload_name: str):
        file_path = _resolve_upload(upload_name)
        if file_path is None:
            return _redirect_home("Arquivo nao encontrado.", "error")

        preview_kind = "image" if file_path.suffix.lower() != ".pdf" else "pdf"
        page_count = get_pdf_page_count(file_path) if preview_kind == "pdf" else 1
        return render_template(
            "preview.html",
            upload_name=file_path.name,
            preview_kind=preview_kind,
            page_count=page_count,
            printers=state.get_shared_printers(),
            filename=file_path.name,
            jobs=state.get_jobs()[:8],
        )

    @app.get("/uploads/<path:upload_name>")
    def uploaded_file(upload_name: str):
        file_path = _resolve_upload(upload_name)
        if file_path is None:
            return _redirect_home("Arquivo nao encontrado.", "error")
        return send_from_directory(config.UPLOAD_DIR, file_path.name)

    @app.post("/api/print")
    def print_uploaded_file():
        payload = request.get_json(silent=True) or request.form.to_dict()
        upload_name = (payload.get("upload_name") or "").strip()
        printer_name = (payload.get("printer_name") or "").strip()
        copies_raw = payload.get("copies") or 1
        orientation = (payload.get("orientation") or "auto").strip().lower()
        color_mode = (payload.get("color_mode") or "color").strip().lower()
        pages_mode = (payload.get("pages_mode") or "all").strip().lower()
        page_ranges = (payload.get("page_ranges") or "").strip()

        file_path = _resolve_upload(upload_name)
        if file_path is None:
            return jsonify({"ok": False, "message": "Arquivo nao encontrado."}), 404

        if not printer_name or not state.is_printer_shared(printer_name):
            return jsonify({"ok": False, "message": "A impressora selecionada nao esta liberada."}), 400

        try:
            copies = max(1, min(20, int(copies_raw)))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "message": "Quantidade de copias invalida."}), 400

        if orientation not in {"auto", "portrait", "landscape"}:
            return jsonify({"ok": False, "message": "Orientacao invalida."}), 400

        if color_mode not in {"color", "grayscale"}:
            return jsonify({"ok": False, "message": "Modo de cor invalido."}), 400

        if pages_mode not in {"all", "custom"}:
            return jsonify({"ok": False, "message": "Modo de paginas invalido."}), 400

        if file_path.suffix.lower() != ".pdf":
            pages_mode = "all"
            page_ranges = ""

        if pages_mode == "custom" and not page_ranges:
            return jsonify({"ok": False, "message": "Informe o intervalo de paginas."}), 400

        submitted_by = request.headers.get("X-Forwarded-For") or request.remote_addr or "Cliente local"
        job = queue_worker.enqueue(
            file_path,
            printer_name,
            copies,
            submitted_by,
            print_options={
                "orientation": orientation,
                "color_mode": color_mode,
                "pages_mode": pages_mode,
                "page_ranges": page_ranges,
            },
        )
        return jsonify(
            {
                "ok": True,
                "message": f"Documento colocado na fila com sucesso. Job {job.job_id}.",
                "job_id": job.job_id,
            }
        )

    @app.get("/api/jobs")
    def list_jobs():
        return jsonify(
            {
                "ok": True,
                "jobs": [job.__dict__ for job in state.get_jobs()[:30]],
            }
        )

    def _redirect_home(message: str, message_type: str):
        return redirect(url_for("home", message=message, type=message_type))

    def _resolve_upload(upload_name: str) -> Path | None:
        safe_name = Path(upload_name).name
        if safe_name != upload_name:
            return None
        candidate = config.UPLOAD_DIR / safe_name
        if not candidate.exists() or candidate.suffix.lower() not in config.ALLOWED_EXTENSIONS:
            return None
        return candidate

    return app


class LocalServerThread(threading.Thread):
    def __init__(self, state: AppState, queue_worker: PrintQueueWorker, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self._app = create_app(state, queue_worker)
        self._server = make_server(host, port, self._app, threaded=True)
        self._context = self._app.app_context()

    def run(self) -> None:
        self._context.push()
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()