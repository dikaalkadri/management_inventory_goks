"""
Shared file handling utilities for upload and download operations.
"""
import os
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename

import config


ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed.

    Args:
        filename: Original filename from upload.

    Returns:
        True if the file extension is in the allowed set.
    """
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_upload(file_storage, subfolder: str = '') -> tuple[str, str]:
    """Save an uploaded file to the uploads directory.

    Generates a unique filename to prevent collisions.

    Args:
        file_storage: Werkzeug FileStorage object from request.files.
        subfolder: Optional subfolder inside the upload directory.

    Returns:
        Tuple of (saved_filepath, original_filename).

    Raises:
        ValueError: If the file type is not allowed.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("Tidak ada file yang dipilih.")

    original_name = file_storage.filename

    if not allowed_file(original_name):
        raise ValueError(
            f"Tipe file tidak didukung: {original_name}. "
            f"Gunakan format: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    ext = original_name.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}_{secure_filename(original_name)}"

    # Build save path
    save_dir = config.UPLOAD_FOLDER
    if subfolder:
        save_dir = os.path.join(save_dir, subfolder)
    os.makedirs(save_dir, exist_ok=True)

    filepath = os.path.join(save_dir, unique_name)
    file_storage.save(filepath)

    return filepath, original_name


def generate_output_filename(
    original_name: str,
    month: int,
    year: int,
    outlet: str,
    tglperiode: str
) -> str:
    """Generate a descriptive output filename.

    Example: "32. Selayo_01-30-april-26_tahap1.xlsx"

    Args:
        original_name: Original uploaded filename for reference.
        month: Selected month number (1-12).
        year: Selected year.
        outlet: Selected outlet name dengan nomor (e.g. "32. Selayo").
        tglperiode: Date period string (e.g., "01-30").

    Returns:
        Generated output filename yang mempertahankan nomor outlet.
    """
    # PERBAIKAN: Jangan buang nomor di depan titik. Cukup bersihkan spasi di ujungnya.
    # Contoh: "32. Selayo" tetap menjadi "32. Selayo"
    outlet_clean = outlet.strip()

    # Indonesian month names in lowercase
    bulan_names = [
        '', 'januari', 'februari', 'maret', 'april', 'mei', 'juni',
        'juli', 'agustus', 'september', 'oktober', 'november', 'desember'
    ]

    bulan_str = bulan_names[month] if 1 <= month <= 12 else str(month)
    year_short = str(year)[-2:]

    # Menghasilkan format: "32. Selayo_01-30-april-26_tahap1.xlsx"
    return f"{outlet_clean}_{tglperiode}-{bulan_str}-{year_short}_tahap1.xlsx"


def cleanup_file(filepath: str) -> None:
    """Safely delete a file, ignoring errors.

    Args:
        filepath: Path to file to delete.
    """
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
