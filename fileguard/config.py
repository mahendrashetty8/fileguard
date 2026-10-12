"""Configuration and file category mappings for FileGuard.

This module centralizes extension mappings and category definitions so that
extension logic is not scattered across multiple files.
"""

from pathlib import Path
from typing import Dict, List, Set, Union


# Canonical category order for display and organization
CATEGORY_ORDER: List[str] = [
    "Images",
    "Documents",
    "Videos",
    "Audio",
    "Archives",
    "Other",
]

DEFAULT_OTHER_CATEGORY: str = "Other"

# Standard extension mappings (lowercase, with leading dot)
FILE_CATEGORIES: Dict[str, Set[str]] = {
    "Images": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".bmp",
        ".tiff",
        ".ico",
    },
    "Documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".csv",
        ".xlsx",
        ".xls",
        ".ppt",
        ".pptx",
        ".rtf",
        ".odt",
        ".md",
    },
    "Videos": {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    },
    "Audio": {
        ".mp3",
        ".wav",
        ".aac",
        ".flac",
        ".ogg",
        ".m4a",
        ".wma",
    },
    "Archives": {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tgz",
    },
}


def get_category_for_extension(ext: str) -> str:
    """Return the category name for a given file extension.

    Args:
        ext: File extension (with or without leading dot).

    Returns:
        The matched category name, or DEFAULT_OTHER_CATEGORY if unmapped.
    """
    if not ext:
        return DEFAULT_OTHER_CATEGORY

    normalized = ext.strip().lower()
    if not normalized.startswith("."):
        normalized = f".{normalized}"

    for category, extensions in FILE_CATEGORIES.items():
        if normalized in extensions:
            return category

    return DEFAULT_OTHER_CATEGORY


def get_category_for_file(file_path: Union[Path, str]) -> str:
    """Return the category name for a file path based on its suffix.

    Args:
        file_path: Path to the file.

    Returns:
        The matched category name.
    """
    path = Path(file_path)
    suffix = path.suffix
    return get_category_for_extension(suffix)


def get_all_categories() -> List[str]:
    """Return a list of all configured categories in display order."""
    return list(CATEGORY_ORDER)
