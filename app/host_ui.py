from __future__ import annotations

import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import webview

from app import config
from app.print_queue import PrintQueueWorker
from app.printers import discover_printers
from app.server import LocalServerThread, _try_add_firewall_rule
from app.state import AppState, PrinterInfo
from app.utils import get_local_ip_address


class HostAPI:
    """API exposted to JavaScript via PyWebView."""

    def __init__(self, state: AppState, queue_worker: PrintQueueWorker) -> None:
        self.state = state
        self.queue_worker = queue_worker
        self.server_thread: LocalServerThread | None = None

    def get_state(self) -> dict:
        """Return current application state."""
        printers = self.state.get_printers()
        shared_printers = self.state.get_shared_printers()
        upload_stats = self.get_upload_stats()
        
        return {
            "printer_count": len(printers),
            "shared_printer_count": len(shared_printers),
            "is_server_running": self.state.is_server_running(),
            "server_url": self.state.get_server_url(),
            "job_counts": self.state.get_job_counts(),
            "upload_count": upload_stats["file_count"],
            "upload_total_mb": upload_stats["total_size_mb"],
            "jobs": [
                {
                    "job_id": job.job_id,
                    "file_name": job.file_name,
                    "printer_name": job.printer_name,
                    "status": job.status,
                }
                for job in self.state.get_jobs()[:20]
            ],
            "logs": self.state.get_logs(),
        }

    def get_upload_stats(self) -> dict[str, float | int]:
        """Return current upload folder stats."""
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        files = [entry for entry in config.UPLOAD_DIR.iterdir() if entry.is_file()]
        total_size = sum(file.stat().st_size for file in files)
        return {
            "file_count": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def cleanup_old_uploads(self, days: int = 7) -> dict[str, int | str]:
        """Delete uploaded files older than N days."""
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 7

        days = max(1, min(365, days))
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cutoff = datetime.now() - timedelta(days=days)

        removed = 0
        failed = 0
        for entry in config.UPLOAD_DIR.iterdir():
            if not entry.is_file():
                continue
            modified_at = datetime.fromtimestamp(entry.stat().st_mtime)
            if modified_at >= cutoff:
                continue
            try:
                entry.unlink(missing_ok=True)
                removed += 1
            except OSError:
                failed += 1

        self.state.add_log(
            f"Limpeza de uploads: removidos {removed} arquivo(s) com mais de {days} dia(s)."
        )
        if failed:
            self.state.add_log(f"Limpeza de uploads: {failed} arquivo(s) não puderam ser removidos.")

        return {
            "ok": True,
            "days": days,
            "removed": removed,
            "failed": failed,
        }

    def get_printers(self) -> list[dict]:
        """Return list of available printers with selection state."""
        printers = self.state.get_printers()
        selected_names = set(self.state.get_shared_printer_names())
        
        return [
            {
                "name": p.name,
                "source": p.source,
                "status": p.status,
                "is_default": p.is_default,
                "selected": p.name in selected_names,
            }
            for p in printers
        ]

    def refresh_printers(self) -> None:
        """Discover and refresh available printers."""
        printers = discover_printers()
        self.state.set_printers(printers)
        
        if printers:
            self.state.add_log(f"[{len(printers)}] impressora(s) encontrada(s).")
        else:
            self.state.add_log("Nenhuma impressora foi encontrada. Verifique as impressoras do Windows.")

    def set_printer_selected(self, printer_name: str, selected: bool) -> None:
        """Update printer selection state."""
        selected_names = set(self.state.get_shared_printer_names())
        
        if selected:
            selected_names.add(printer_name)
        else:
            selected_names.discard(printer_name)
        
        self.state.set_shared_printers(list(selected_names))
        self.state.add_log(f"Impressoras liberadas atualizadas: {len(selected_names)} selecionada(s).")

    def start_server(self) -> None:
        """Start the local HTTP server."""
        if self.state.is_server_running():
            self.state.add_log("Servidor local já está ativo.")
            return

        shared_printers = self.state.get_shared_printers()
        if not shared_printers:
            self.state.add_log("ERRO: Selecione ao menos uma impressora antes de iniciar o servidor.")
            return

        ip_address = get_local_ip_address()
        server_url = f"http://{ip_address}:{config.SERVER_PORT}"
        self.state.set_server_url(server_url)

        # Pre-create firewall rule by port so the rule is not tied to the EXE
        # extraction path (PyInstaller one-file changes path on each run).
        _try_add_firewall_rule(config.SERVER_PORT)

        try:
            self.server_thread = LocalServerThread(
                self.state,
                self.queue_worker,
                config.SERVER_HOST,
                config.SERVER_PORT,
            )
            self.server_thread.start()
        except Exception as exc:
            self.server_thread = None
            self.state.add_log(f"ERRO ao iniciar servidor: {exc}")
            return

        self.state.set_server_running(True)
        self.state.add_log(f"✓ Servidor iniciado em {server_url}")

    def stop_server(self) -> None:
        """Stop the local HTTP server."""
        if not self.state.is_server_running() or self.server_thread is None:
            return

        self.server_thread.shutdown()
        self.server_thread.join(timeout=2)
        self.server_thread = None
        self.state.set_server_running(False)
        self.state.add_log("⏸ Servidor pausado pelo host.")

    def open_site(self) -> None:
        """Open the server URL in the default browser."""
        server_url = self.state.get_server_url()
        if not server_url:
            self.state.add_log("ERRO: Inicie o servidor antes de abrir o site local.")
            return

        webbrowser.open(server_url)
        self.state.add_log(f"↗ Abrindo navegador para {server_url}")


def get_html_path() -> str:
    """Get the path to the host HTML file, compatible with both frozen EXE and dev mode."""
    html_path = config.BASE_DIR / "templates" / "host.html"
    if not html_path.exists():
        raise FileNotFoundError(f"Host HTML file not found at {html_path}")
    return html_path.as_uri()


class HostWindow:
    """PyWebView host window with integrated API."""

    def __init__(self) -> None:
        self.state = AppState()
        self.queue_worker = PrintQueueWorker(self.state)
        self.queue_worker.start()
        self.api = HostAPI(self.state, self.queue_worker)
        self.webview: webview.WebView | None = None
        
        # Discover printers on startup
        self.api.refresh_printers()

    def run(self) -> None:
        """Launch the PyWebView window."""
        html_path = get_html_path()
        
        self.webview = webview.create_window(
            title="Yumis' Printer - Painel do Host",
            url=html_path,
            js_api=self.api,
            width=1400,
            height=900,
            min_size=(1100, 720),
        )
        
        self.webview.events.closed += self.on_closed
        webview.start(debug=False)

    def on_closed(self) -> None:
        """Handle window close event."""
        self.api.stop_server()
        self.queue_worker.stop()


def main() -> None:
    """Entry point for the host UI."""
    host = HostWindow()
    host.run()