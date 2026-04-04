from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class PrinterInfo:
    name: str
    source: str = "Local"
    status: str = "Disponivel"
    is_default: bool = False


@dataclass(frozen=True)
class PrintJob:
    job_id: str
    file_name: str
    printer_name: str
    copies: int
    submitted_by: str
    submitted_at: str
    status: str
    message: str = ""
    completed_at: str = ""


class AppState:
    def __init__(self) -> None:
        self._lock = RLock()
        self._printers: list[PrinterInfo] = []
        self._shared_printer_names: set[str] = set()
        self._logs: list[str] = []
        self._jobs: list[PrintJob] = []
        self._server_running = False
        self._server_url = ""

    def set_printers(self, printers: list[PrinterInfo]) -> None:
        with self._lock:
            self._printers = list(printers)
            available_names = {printer.name for printer in printers}
            self._shared_printer_names &= available_names

    def get_printers(self) -> list[PrinterInfo]:
        with self._lock:
            return list(self._printers)

    def set_shared_printers(self, printer_names: list[str]) -> None:
        with self._lock:
            available_names = {printer.name for printer in self._printers}
            self._shared_printer_names = {
                printer_name for printer_name in printer_names if printer_name in available_names
            }

    def get_shared_printer_names(self) -> list[str]:
        with self._lock:
            return sorted(self._shared_printer_names)

    def get_shared_printers(self) -> list[PrinterInfo]:
        with self._lock:
            return [
                printer
                for printer in self._printers
                if printer.name in self._shared_printer_names
            ]

    def is_printer_shared(self, printer_name: str) -> bool:
        with self._lock:
            return printer_name in self._shared_printer_names

    def set_server_running(self, is_running: bool) -> None:
        with self._lock:
            self._server_running = is_running

    def is_server_running(self) -> bool:
        with self._lock:
            return self._server_running

    def set_server_url(self, server_url: str) -> None:
        with self._lock:
            self._server_url = server_url

    def get_server_url(self) -> str:
        with self._lock:
            return self._server_url

    def add_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self._logs.append(f"[{timestamp}] {message}")
            self._logs = self._logs[-300:]

    def get_logs(self) -> list[str]:
        with self._lock:
            return list(self._logs)

    def create_job(
        self,
        *,
        file_name: str,
        printer_name: str,
        copies: int,
        submitted_by: str,
    ) -> PrintJob:
        submitted_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        job = PrintJob(
            job_id=uuid4().hex[:8],
            file_name=file_name,
            printer_name=printer_name,
            copies=copies,
            submitted_by=submitted_by,
            submitted_at=submitted_at,
            status="Na fila",
            message="Aguardando processamento.",
        )
        with self._lock:
            self._jobs.insert(0, job)
            self._jobs = self._jobs[:200]
        return job

    def update_job(
        self,
        job_id: str,
        *,
        status: str,
        message: str,
        completed: bool = False,
    ) -> None:
        with self._lock:
            updated_jobs: list[PrintJob] = []
            for job in self._jobs:
                if job.job_id == job_id:
                    completed_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S") if completed else job.completed_at
                    updated_jobs.append(
                        replace(
                            job,
                            status=status,
                            message=message,
                            completed_at=completed_at,
                        )
                    )
                else:
                    updated_jobs.append(job)
            self._jobs = updated_jobs

    def get_jobs(self) -> list[PrintJob]:
        with self._lock:
            return list(self._jobs)

    def get_job_counts(self) -> dict[str, int]:
        with self._lock:
            counts = {"queued": 0, "printing": 0, "done": 0, "error": 0}
            for job in self._jobs:
                if job.status == "Na fila":
                    counts["queued"] += 1
                elif job.status == "Imprimindo":
                    counts["printing"] += 1
                elif job.status == "Concluido":
                    counts["done"] += 1
                elif job.status == "Erro":
                    counts["error"] += 1
            return counts