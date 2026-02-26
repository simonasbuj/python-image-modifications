import random
from typing import Dict, Tuple

from PIL import Image


def apply_pixel_color_modifications(
    image: Image.Image,
    num_modifications: int,
    color: Tuple[int, int, int] = (0, 255, 0),
) -> Tuple[Image.Image, Dict[str, object]]:
    """
    Apply reversible pixel color modifications.
    Changes a large square region of pixels to a specified color (default: green)
    and stores original colors for reversal.

    Args:
        image: PIL Image object
        num_modifications: Number of pixels to modify
        color: RGB tuple for the color to apply (default: green)

    Returns:
        Tuple of (modified_image, modification_params_dict)
    """
    img = image.copy()
    width, height = img.size
    pixels = img.load()
    total_pixels = width * height

    num_modifications = min(num_modifications, total_pixels)

    side_length = int(num_modifications**0.5)

    side_length = min(side_length, width, height)

    rect_width = side_length
    rect_height = side_length

    max_x = width - rect_width
    max_y = height - rect_height

    if max_x < 0 or max_y < 0:
        start_x, start_y = 0, 0
        rect_width, rect_height = width, height
    else:
        start_x = random.randint(0, max_x)
        start_y = random.randint(0, max_y)

    original_pixels: list[tuple[int, int, int]] = []

    for x in range(start_x, start_x + rect_width):
        for y in range(start_y, start_y + rect_height):
            original_color = pixels[x, y]
            original_pixels.append((x, y, original_color))
            pixels[x, y] = color

    modification_params = {
        "algorithm": "pixel_color",
        "original_pixels": original_pixels,
        "modification_color": color,
        "num_modifications": len(original_pixels),
        "region": {
            "start_x": start_x,
            "start_y": start_y,
            "width": rect_width,
            "height": rect_height,
        },
    }

    return img, modification_params


def reverse_pixel_color_modifications(
    image: Image.Image, modification_params: Dict
) -> Image.Image:
    """
    Reverse pixel color modifications by restoring original pixel colors.

    Args:
        image: Modified PIL Image object
        modification_params: Dictionary containing original_pixels

    Returns:
        Reversed PIL Image object
    """
    img = image.copy()
    pixels = img.load()

    original_pixels = modification_params.get("original_pixels", [])

    for pixel_data in original_pixels:
        if isinstance(pixel_data, (list, tuple)):
            x, y = int(pixel_data[0]), int(pixel_data[1])
            original_color = pixel_data[2]

            if isinstance(original_color, list):
                original_color = tuple(int(c) for c in original_color)
            elif not isinstance(original_color, tuple):
                original_color = tuple(original_color)

            pixels[x, y] = original_color

    return img


def calculate_image_hash(image: Image.Image) -> str:
    """
    Calculate a simple hash of the image for comparison.
    Uses pixel values to create a hash.
    """
    import hashlib

    pixels = list(image.getdata())
    pixel_str = str(pixels)
    return hashlib.md5(pixel_str.encode()).hexdigest()


def compare_images_pixelwise(img1: Image.Image, img2: Image.Image) -> bool:
    """
    Compare two images pixel by pixel.

    Returns:
        True if images are identical, False otherwise
    """
    if img1.size != img2.size:
        return False

    pixels1 = img1.load()
    pixels2 = img2.load()

    for x in range(img1.width):
        for y in range(img1.height):
            if pixels1[x, y] != pixels2[x, y]:
                return False

    return True
