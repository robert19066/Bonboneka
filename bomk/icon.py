"""
bomk/icon.py – Generate and inject app icons at various Android densities.
"""

from pathlib import Path
from PIL import Image
from .lib import Logger


# Android icon sizes (in pixels) for different densities
ICON_SIZES = {
    "mdpi":    48,
    "hdpi":    72,
    "xhdpi":   96,
    "xxhdpi":  144,
    "xxxhdpi": 192,
}


def inject_icon(
    template_path: Path,
    icon_path: str,
    logger: Logger | None = None,
) -> None:
    """
    Take a single icon image and resize it to all required Android densities.
    Place resized icons in the template's mipmap directories.
    """
    icon_file = Path(icon_path)
    if not icon_file.exists():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    # Supported image formats
    if icon_file.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError(f"Unsupported icon format: {icon_file.suffix}\nSupported: PNG, JPG, WEBP")

    try:
        original_image = Image.open(icon_file)
        if original_image.mode in ("RGBA", "LA", "P"):
            # Keep transparency for PNG
            original_image = original_image.convert("RGBA")
        else:
            original_image = original_image.convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to open icon image: {e}")

    logger and logger.step(f"Resizing icon: {icon_file.name}")

    # Generate and place icons for each density
    for density, size in ICON_SIZES.items():
        mipmap_dir = template_path / "app" / "src" / "main" / "res" / f"mipmap-{density}"
        if not mipmap_dir.exists():
            logger and logger.verbose(f"  Creating: {mipmap_dir.relative_to(template_path)}")
            mipmap_dir.mkdir(parents=True, exist_ok=True)

        # Resize image
        resized = original_image.resize((size, size), Image.Resampling.LANCZOS)

        # Save as ic_launcher.png
        output_path = mipmap_dir / "ic_launcher.png"
        if original_image.mode == "RGBA":
            resized.save(output_path, "PNG")
        else:
            resized.save(output_path, "PNG")

        logger and logger.debug(f"  {density}: {size}×{size} → {output_path.name}")

    logger and logger.success(f"Icon injected into all densities (mipmap-*)")
