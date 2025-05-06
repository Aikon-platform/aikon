import concurrent.futures
import os
import time
import fitz
from pathlib import Path
from typing import Tuple, List, Optional

from webapp.utils.constants import MAX_RES, MAX_SIZE, MAX_QUAL
from webapp.utils.logger import log
from webapp.utils.paths import IMG_PATH, MEDIA_DIR, BASE_DIR


def calculate_matrix(page: fitz.Page, dpi: int, max_size: int) -> fitz.Matrix:
    zoom = dpi / 72.0

    rect = page.rect
    width, height = rect.width * zoom, rect.height * zoom

    if max(width, height) > max_size:
        scale = max_size / max(width, height)
        return fitz.Matrix(zoom * scale, zoom * scale)

    return fitz.Matrix(zoom, zoom)


def convert_batch(
    pdf_path: Path,
    start: int,
    end: int,
    output_dir: Path,
    img_prefix: str,
    dpi: int = MAX_RES,
    ext: str = "jpg",
    quality: int = MAX_QUAL,
    max_size: int = MAX_SIZE,
    timeout: int = 500,
) -> List[str]:
    result_files = []

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _process_batch,
                pdf_path,
                start,
                end,
                output_dir,
                img_prefix,
                dpi,
                ext,
                quality,
                max_size,
            )
            result_files = future.result(timeout=timeout)
    except Exception as e:
        log(f"Batch processing failed ({start}-{end})", exception=e)
        if dpi > 150:
            return _process_batch(
                pdf_path,
                start,
                end,
                output_dir,
                img_prefix,
                int(dpi * 0.6),
                ext,
                quality,
                max_size,
            )

    return result_files


def _process_batch(
    pdf_path: Path,
    start: int,
    end: int,
    output_dir: Path,
    img_prefix: str,
    dpi: int = MAX_RES,
    ext: str = "jpg",
    quality: int = MAX_QUAL,
    max_size: int = MAX_SIZE,
) -> List[str]:
    result_files = []

    with fitz.open(pdf_path) as doc:
        for page_idx in range(start - 1, end):
            if page_idx >= len(doc):
                break

            page = doc[page_idx]
            output_filename = f"{img_prefix}_{page_idx + 1:04d}.{ext}"
            output_path = output_dir / output_filename

            matrix = calculate_matrix(page, dpi, max_size)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            if ext.lower() in ["jpg", "jpeg"]:
                pixmap.save(str(output_path), output=ext.lower(), jpg_quality=quality)
            else:
                pixmap.save(str(output_path), output=ext.lower())

            result_files.append(str(output_path))

    return result_files


def convert_pdf(
    pdf_path: Path,
    page_range: Optional[Tuple[int, int]] = None,
    output_dir: Path = BASE_DIR / IMG_PATH,
    img_prefix: Optional[str] = None,
    dpi: int = MAX_RES,
    ext: str = "jpg",
    quality: int = MAX_QUAL,
    max_size: int = MAX_SIZE,
    batch_size: int = 25,
) -> List[str]:
    result_files = []

    try:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)

            if not page_range:
                page_range = (1, total_pages)

            start_page, end_page = page_range
            end_page = min(end_page, total_pages)

            batches = []
            current_start = start_page
            while current_start <= end_page:
                current_end = min(current_start + batch_size - 1, end_page)
                batches.append((current_start, current_end))
                current_start = current_end + 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    convert_batch,
                    pdf_path,
                    batch[0],
                    batch[1],
                    output_dir,
                    img_prefix,
                    dpi,
                    ext,
                    quality,
                    max_size,
                )
                for batch in batches
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    batch_results = future.result()
                    result_files.extend(batch_results)
                except Exception as e:
                    log(f"Batch future processing failed for {pdf_path}", exception=e)

        result_files.sort()
        return result_files

    except fitz.FileDataError as e:
        log(f"PDF file is corrupted or invalid", exception=e)
        return []
    except Exception as e:
        log(f"PyMuPDF conversion failed", exception=e)
        return []


def pdf_2_img(
    pdf_path: str,
    output_dir: str = BASE_DIR / IMG_PATH,
    dpi: int = MAX_RES,
    ext: str = "jpg",
    max_size: int = MAX_SIZE,
    quality: int = MAX_QUAL,
    page_range: Optional[Tuple[int, int]] = None,
    batch_size: int = 50,
) -> List[str]:
    start_time = time.time()

    pdf_path = (Path(MEDIA_DIR) / pdf_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        log(f"[pdf2img] PDF file not found: {pdf_path}")
        return []

    output_dir = Path(output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        log(f"[pdf2img] Output directory does not exist, creating: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    img_prefix = pdf_path.stem

    result_files = convert_pdf(
        pdf_path=pdf_path,
        page_range=page_range,
        output_dir=output_dir,
        img_prefix=img_prefix,
        dpi=dpi,
        ext=ext,
        quality=quality,
        max_size=max_size,
        batch_size=batch_size,
    )

    if not result_files:
        log(f"[pdf2img] No images generated for {pdf_path}")
        return []

    elapsed_time = time.time() - start_time
    log(f"Conversion of {img_prefix} completed in {elapsed_time:.2f} seconds")

    return result_files


def _pdf_to_img(pdf_name, dpi=MAX_RES, timeout=3600):
    """
    Convert the PDF file to JPEG images
    NOTE old function, not used anymore
    """
    import subprocess

    pdf_path = f"{MEDIA_DIR}/{pdf_name}"
    pdf_name = Path(pdf_name).stem
    try:
        if not os.path.exists(pdf_path):
            log(f"[_pdf_to_img] PDF file not found: {pdf_path}")
            return False

        cmd = f"pdftoppm -jpeg -r {dpi} -scale-to {MAX_SIZE} {pdf_path} {IMG_PATH}/{pdf_name} -sep _ "
        res = subprocess.run(
            cmd,
            shell=True,
            check=True,
            timeout=int(timeout * 0.8),
            capture_output=True,
            text=True,
        )

        if res.returncode != 0:
            dpi = int(dpi * 0.5)
            size = int(MAX_SIZE * 0.8)
            cmd = f"pdftoppm -jpeg -r {dpi} -scale-to {size} {pdf_path} {IMG_PATH}/{pdf_name} -sep _ "
            log(
                f"[_pdf_to_img] Failed to convert {pdf_name}.pdf: {res.stderr}\nUsing fallback command: {cmd}"
            )
            res = subprocess.run(cmd, shell=True, check=True, timeout=int(timeout))

        return res.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"[_pdf_to_img] Command timed out for {pdf_name}.pdf")
        return False
    except Exception as e:
        log(
            f"[_pdf_to_img] Failed to convert {pdf_name}.pdf to images:\n{e} ({e.__class__.__name__})"
        )
        return False
