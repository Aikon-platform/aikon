import os
import time

from pathlib import Path
from typing import Tuple, List, Optional
from pymupdf_img import convert_pdf

from webapp.utils.constants import MAX_RES, MAX_SIZE, MAX_QUAL
from webapp.utils.logger import log
from webapp.utils.paths import IMG_PATH, MEDIA_PATH


def pdf_2_img(
    pdf_path: str,
    output_dir: Path = IMG_PATH,
    dpi: int = MAX_RES,
    ext: str = "jpg",
    max_size: int = MAX_SIZE,
    quality: int = MAX_QUAL,
    page_range: Optional[Tuple[int, int]] = None,
    batch_size: int = 50,
    auto_alpha_format: bool = False,
) -> List[str]:
    start_time = time.time()

    pdf_path = (MEDIA_PATH / pdf_path).resolve()
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
        img_prefix=f"{img_prefix}_",
        dpi=dpi,
        ext=ext,
        quality=quality,
        max_size=max_size,
        batch_size=batch_size,
        auto_alpha_format=auto_alpha_format,
    )

    if not result_files:
        log(f"[pdf2img] No images generated for {pdf_path}")
        return []

    elapsed_time = time.time() - start_time
    log(f"Conversion of {img_prefix} completed in {elapsed_time:.2f} seconds")

    return result_files
