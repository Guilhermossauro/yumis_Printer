from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread

from app.printing import print_file
from app.state import AppState, PrintJob


@dataclass(frozen=True)
class QueuedPrintRequest:
    job: PrintJob
    file_path: Path
    print_options: dict[str, str]


class PrintQueueWorker:
    def __init__(self, state: AppState) -> None:
        self._state = state
        self._queue: Queue[QueuedPrintRequest] = Queue()
        self._stop_event = Event()
        self._thread = Thread(target=self._work_loop, daemon=True)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=3)

    def enqueue(
        self,
        file_path: Path,
        printer_name: str,
        copies: int,
        submitted_by: str,
        print_options: dict[str, str] | None = None,
    ) -> PrintJob:
        job = self._state.create_job(
            file_name=file_path.name,
            printer_name=printer_name,
            copies=copies,
            submitted_by=submitted_by,
        )
        self._queue.put(
            QueuedPrintRequest(
                job=job,
                file_path=file_path,
                print_options=print_options or {},
            )
        )
        self._state.add_log(
            f"Job {job.job_id} entrou na fila para {printer_name} com {copies} copia(s)."
        )
        return job

    def _work_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                request = self._queue.get(timeout=0.5)
            except Empty:
                continue

            self._state.update_job(
                request.job.job_id,
                status="Imprimindo",
                message="Documento enviado para o spooler local.",
            )
            self._state.add_log(
                f"Processando job {request.job.job_id} para {request.job.printer_name}."
            )

            try:
                for _ in range(request.job.copies):
                    print_file(
                        request.file_path,
                        request.job.printer_name,
                        **request.print_options,
                    )
            except Exception as exc:  # pragma: no cover - depende da impressora local
                self._state.update_job(
                    request.job.job_id,
                    status="Erro",
                    message=str(exc),
                    completed=True,
                )
                self._state.add_log(f"Job {request.job.job_id} falhou: {exc}")
            else:
                self._state.update_job(
                    request.job.job_id,
                    status="Concluido",
                    message="Documento enviado para a impressora com sucesso.",
                    completed=True,
                )
                self._state.add_log(
                    f"Job {request.job.job_id} concluido em {request.job.printer_name}."
                )
            finally:
                self._queue.task_done()