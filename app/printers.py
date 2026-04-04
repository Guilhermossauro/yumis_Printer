from __future__ import annotations

import platform

from app.state import PrinterInfo

try:
    import win32print  # type: ignore
except ImportError:  # pragma: no cover - depends on Windows runtime
    win32print = None


def discover_printers() -> list[PrinterInfo]:
    if platform.system() != "Windows" or win32print is None:
        return []

    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    raw_printers = win32print.EnumPrinters(flags, None, 2)
    default_printer = _get_default_printer_name()

    printers: list[PrinterInfo] = []
    seen_names: set[str] = set()

    for raw_printer in raw_printers:
        printer_name = raw_printer.get("pPrinterName")
        if not printer_name or printer_name in seen_names:
            continue

        seen_names.add(printer_name)
        attributes = int(raw_printer.get("Attributes", 0))
        source = _resolve_source(printer_name, attributes)
        status = _resolve_status(raw_printer.get("Status", 0))

        printers.append(
            PrinterInfo(
                name=printer_name,
                source=source,
                status=status,
                is_default=printer_name == default_printer,
            )
        )

    printers.sort(key=lambda printer: (not printer.is_default, printer.name.lower()))
    return printers


def _get_default_printer_name() -> str:
    if win32print is None:
        return ""
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return ""


def _resolve_source(printer_name: str, attributes: int) -> str:
    if printer_name.startswith("\\"):
        return "Rede"

    network_flag = getattr(win32print, "PRINTER_ATTRIBUTE_NETWORK", 0)
    shared_flag = getattr(win32print, "PRINTER_ATTRIBUTE_SHARED", 0)

    if attributes & network_flag:
        return "Rede"
    if attributes & shared_flag:
        return "Compartilhada"
    return "Local"


def _resolve_status(raw_status: int) -> str:
    if not raw_status:
        return "Pronta"

    status_map = [
        (getattr(win32print, "PRINTER_STATUS_PAUSED", 0), "Pausada"),
        (getattr(win32print, "PRINTER_STATUS_BUSY", 0), "Ocupada"),
        (getattr(win32print, "PRINTER_STATUS_PRINTING", 0), "Imprimindo"),
        (getattr(win32print, "PRINTER_STATUS_OFFLINE", 0), "Offline"),
        (getattr(win32print, "PRINTER_STATUS_PAPER_OUT", 0), "Sem papel"),
        (getattr(win32print, "PRINTER_STATUS_ERROR", 0), "Com erro"),
    ]

    for flag, label in status_map:
        if flag and raw_status & flag:
            return label

    return "Disponivel"