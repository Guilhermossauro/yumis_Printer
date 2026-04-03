from __future__ import annotations

import platform
from io import BytesIO
from pathlib import Path

try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32ui  # type: ignore
except ImportError:  # pragma: no cover - depends on Windows runtime
    win32api = None
    win32con = None
    win32ui = None

try:
    from PIL import Image, ImageWin
except ImportError:  # pragma: no cover - depends on runtime packages
    Image = None
    ImageWin = None

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - depends on runtime packages
    fitz = None


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def print_file(
    file_path: Path,
    printer_name: str,
    *,
    orientation: str = "auto",
    color_mode: str = "color",
    pages_mode: str = "all",
    page_ranges: str = "",
) -> str:
    if platform.system() != "Windows":
        raise RuntimeError("A impressao real esta disponivel apenas no Windows.")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _print_pdf(
            file_path,
            printer_name,
            orientation=orientation,
            color_mode=color_mode,
            pages_mode=pages_mode,
            page_ranges=page_ranges,
        )
    if suffix in IMAGE_EXTENSIONS:
        return _print_image(
            file_path,
            printer_name,
            orientation=orientation,
            color_mode=color_mode,
        )
    raise ValueError("Formato de arquivo nao suportado para impressao.")


def get_pdf_page_count(file_path: Path) -> int:
    if file_path.suffix.lower() != ".pdf" or fitz is None:
        return 1
    document = fitz.open(file_path)
    try:
        return max(1, document.page_count)
    finally:
        document.close()


def _print_pdf(
    file_path: Path,
    printer_name: str,
    *,
    orientation: str,
    color_mode: str,
    pages_mode: str,
    page_ranges: str,
) -> str:
    if fitz is None:
        raise RuntimeError("PyMuPDF e necessario para imprimir PDFs com consistencia.")
    if Image is None:
        raise RuntimeError("Pillow e necessario para renderizar PDFs para impressao.")

    document = fitz.open(file_path)
    if document.page_count == 0:
        raise RuntimeError("O PDF enviado nao possui paginas validas.")

    page_indexes = _resolve_page_indexes(document.page_count, pages_mode, page_ranges)
    if not page_indexes:
        raise RuntimeError("Nenhuma pagina valida foi selecionada para impressao.")

    device_context = _create_printer_device_context(printer_name)
    try:
        device_context.StartDoc(file_path.name)
        for page_index in page_indexes:
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            image = _apply_color_mode(image, color_mode)
            image = _apply_orientation(image, orientation)
            device_context.StartPage()
            _draw_image_on_context(device_context, image)
            device_context.EndPage()
        device_context.EndDoc()
    finally:
        document.close()
        device_context.DeleteDC()

    return f"PDF enviado para {printer_name} com {len(page_indexes)} pagina(s)."


def _print_image(file_path: Path, printer_name: str, *, orientation: str, color_mode: str) -> str:
    if Image is None:
        raise RuntimeError("Pillow e pywin32 sao necessarios para imprimir imagens.")

    image = Image.open(file_path)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image = _apply_color_mode(image, color_mode)
    image = _apply_orientation(image, orientation)

    device_context = _create_printer_device_context(printer_name)
    try:
        device_context.StartDoc(file_path.name)
        device_context.StartPage()
        _draw_image_on_context(device_context, image)
        device_context.EndPage()
        device_context.EndDoc()
    finally:
        device_context.DeleteDC()

    return f"Imagem enviada para {printer_name}."


def _create_printer_device_context(printer_name: str):
    if ImageWin is None or win32ui is None or win32con is None:
        raise RuntimeError("Pillow e pywin32 sao necessarios para enviar documentos a impressora.")

    device_context = win32ui.CreateDC()
    device_context.CreatePrinterDC(printer_name)
    return device_context


def _draw_image_on_context(device_context, image) -> None:
    printable_width = device_context.GetDeviceCaps(win32con.HORZRES)
    printable_height = device_context.GetDeviceCaps(win32con.VERTRES)
    margin_left = device_context.GetDeviceCaps(win32con.PHYSICALOFFSETX)
    margin_top = device_context.GetDeviceCaps(win32con.PHYSICALOFFSETY)

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    target_width, target_height = _fit_inside(
        image.size[0], image.size[1], printable_width, printable_height
    )
    start_x = margin_left + max(0, (printable_width - target_width) // 2)
    start_y = margin_top + max(0, (printable_height - target_height) // 2)

    dib = ImageWin.Dib(image)
    dib.draw(
        device_context.GetHandleOutput(),
        (start_x, start_y, start_x + target_width, start_y + target_height),
    )


def _fit_inside(width: int, height: int, max_width: int, max_height: int) -> tuple[int, int]:
    ratio = min(max_width / width, max_height / height)
    return max(1, int(width * ratio)), max(1, int(height * ratio))


def _resolve_page_indexes(page_count: int, pages_mode: str, page_ranges: str) -> list[int]:
    if pages_mode == "all":
        return list(range(page_count))
    if pages_mode != "custom":
        raise RuntimeError("Modo de paginas invalido.")

    normalized = page_ranges.strip()
    if not normalized:
        raise RuntimeError("Informe o intervalo de paginas.")

    indexes: set[int] = set()
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    for part in parts:
        if "-" in part:
            raw_start, raw_end = part.split("-", 1)
            try:
                start = int(raw_start)
                end = int(raw_end)
            except ValueError as exc:
                raise RuntimeError("Intervalo de paginas invalido.") from exc

            if start < 1 or end < 1 or start > end:
                raise RuntimeError("Intervalo de paginas invalido.")

            for page_number in range(start, end + 1):
                if page_number > page_count:
                    raise RuntimeError("Intervalo de paginas fora do total do documento.")
                indexes.add(page_number - 1)
        else:
            try:
                page_number = int(part)
            except ValueError as exc:
                raise RuntimeError("Numero de pagina invalido.") from exc

            if page_number < 1 or page_number > page_count:
                raise RuntimeError("Numero de pagina fora do total do documento.")
            indexes.add(page_number - 1)

    return sorted(indexes)


def _apply_orientation(image, orientation: str):
    if orientation not in {"auto", "portrait", "landscape"}:
        return image

    width, height = image.size
    if orientation == "portrait" and width > height:
        return image.rotate(90, expand=True)
    if orientation == "landscape" and height > width:
        return image.rotate(90, expand=True)
    return image


def _apply_color_mode(image, color_mode: str):
    if color_mode == "grayscale":
        return image.convert("L")
    return image