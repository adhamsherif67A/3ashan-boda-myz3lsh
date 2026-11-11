"""Unit tests for the bottom-camera transect detector (no ROS graph needed)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mako_vision.transect_detector import detect_transect  # noqa: E402

WIDTH, HEIGHT = 320, 240
TILE = (174, 221, 230)
BLUE = (6, 31, 204)
RED = (217, 6, 9)
BLACK = (6, 6, 6)


def image(draw, encoding='rgb8'):
    pixels = [[TILE for _ in range(WIDTH)] for _ in range(HEIGHT)]
    draw(pixels)
    data = bytearray()
    for row in pixels:
        for r, g, b in row:
            data += bytes((r, g, b) if encoding == 'rgb8' else (b, g, r))
    return SimpleNamespace(encoding=encoding, width=WIDTH, height=HEIGHT, step=WIDTH * 3, data=bytes(data))


def vertical(pixels, x, colour, width=8):
    for row in pixels:
        for dx in range(width):
            row[x + dx] = colour


def horizontal(pixels, y, x0, x1, colour, height=8):
    for dy in range(height):
        for x in range(x0, x1):
            pixels[y + dy][x] = colour


def corridor(pixels):
    vertical(pixels, 90, BLUE)
    vertical(pixels, 222, BLUE)


def test_two_blue_rails_form_a_centred_pair():
    result = detect_transect(image(corridor))
    assert result['blue_pair'] is True
    assert result['blue_count'] == 2
    assert result['red_seen'] is False
    assert abs(result['blue_midpoint'][0] - WIDTH / 2) < 12


@pytest.mark.parametrize('encoding', ['rgb8', 'bgr8'])
def test_colour_order_is_respected(encoding):
    assert detect_transect(image(corridor, encoding))['blue_pair'] is True


def test_red_inside_corridor_is_reported():
    def draw(pixels):
        corridor(pixels)
        vertical(pixels, 150, RED)
    assert detect_transect(image(draw))['red_seen'] is True


def test_red_outside_corridor_is_ignored():
    def draw(pixels):
        corridor(pixels)
        vertical(pixels, 10, RED)
    assert detect_transect(image(draw))['red_seen'] is False


def test_black_bar_across_the_rails():
    def draw(pixels):
        corridor(pixels)
        horizontal(pixels, 110, 90, 230, BLACK)
    assert detect_transect(image(draw))['black_bar'] is True


def test_plain_tiles_detect_nothing():
    result = detect_transect(image(lambda pixels: None))
    assert result['blue_pair'] is False and result['blue_count'] == 0 and result['black_bar'] is False


def test_unsupported_encoding_is_rejected():
    message = image(corridor)
    message.encoding = 'mono8'
    with pytest.raises(ValueError):
        detect_transect(message)
