import random

import pytest
from PIL import Image

from app.services.image_processor import (
    compare_images_pixelwise,
    compute_modification_region,
    reverse_pixel_color_modifications,
)


def test_region_whole_image_when_num_mods_exceeds_total_pixels() -> None:
    width, height = 10, 5
    start_x, start_y, rect_w, rect_h = compute_modification_region(
        width, height, num_modifications=10000
    )
    assert (start_x, start_y) == (0, 0)
    assert (rect_w, rect_h) == (width, height)


def test_region_is_square_and_within_bounds_for_perfect_square() -> None:
    random.seed(1)

    width, height = 10, 10

    start_x, start_y, rect_w, rect_h = compute_modification_region(
        width, height, num_modifications=9
    )

    assert start_x == 2
    assert start_y == 1
    assert rect_w == 3
    assert rect_h == 3
    assert width >= start_x + rect_w
    assert height >= start_y + rect_h


@pytest.mark.parametrize(
    "size,color,modify_size,modify_pixel,expected",
    [
        ((10, 10), (255, 0, 0), False, False, True),
        ((10, 10), (255, 0, 0), True, False, False),
        ((10, 10), (255, 0, 0), False, True, False),
    ],
    ids=["identical", "different_size", "different_pixels"],
)
def test_compare_images_pixelwise(
    size: tuple[int, int],
    color: tuple[int, int, int],
    modify_size: bool,
    modify_pixel: bool,
    expected: bool,
) -> None:
    img1 = Image.new("RGB", size, color)

    img2_size = (5, 5) if modify_size else size
    img2 = Image.new("RGB", img2_size, color)

    if modify_pixel:
        img2.putpixel((5, 5), (0, 255, 0))

    assert compare_images_pixelwise(img1, img2) is expected


def test_reverse_pixel_color_modifications_single() -> None:
    img = Image.new("RGB", (10, 10), (255, 0, 0))
    img.putpixel((3, 4), (0, 255, 0))

    params = {
        "original_pixels": [
            (3, 4, (255, 0, 0)),
        ]
    }

    reversed_img = reverse_pixel_color_modifications(img, params)

    assert reversed_img.getpixel((3, 4)) == (255, 0, 0)
    assert reversed_img.getpixel((0, 0)) == (255, 0, 0)
