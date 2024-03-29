from typing import NamedTuple

from PySide2.QtCore import (
    QPoint,
    QRect,
    QSize,
)
from PySide2.QtGui import (
    QColor,
    QImage,
    QPainter,
)

from mapeditor.utils import scaled


def transparent(image, ref_color, tile_size):
    image = image.convertToFormat(QImage.Format_ARGB32)
    for x in range(image.width()):
        for y in range(image.height()):
            if image.pixelColor(x, y) == ref_color:
                image.setPixelColor(x, y, QColor(0, 0, 0, 0))
    return image


class TilePattern(NamedTuple):
    region: QRect
    image: QImage


def preview_pattern(
    origin: tuple[int, int],
    target: tuple[int, int],
    pattern: TilePattern,
    tile_size: int,
) -> TilePattern:
    ox, oy = origin
    target_x, target_y = target

    scaled_region = scaled(pattern.region, tile_size)

    image = QImage(
        QSize(pattern.image.width(), pattern.image.height()),
        QImage.Format_ARGB32,
    )
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.fillRect(pattern.image.rect(), QColor(255, 255, 255))
    offset_x = (ox - target_x) % pattern.region.width()
    offset_y = (oy - target_y) % pattern.region.height()
    for x in (offset_x + offset for offset in (-pattern.region.width(), 0, pattern.region.width())):
        for y in (offset_y + offset for offset in (-pattern.region.height(), 0, pattern.region.height())):
            src_rect = QRect(
                x * tile_size,
                y * tile_size,
                pattern.image.width(),
                pattern.image.height(),
            )
            painter.drawImage(src_rect, pattern.image)
    painter.end()

    return TilePattern(
        region=pattern.region,
        image=image,
    )


class Tileset:
    def __init__(self, filename=None, tile_size=8):
        self.filename = filename
        self.tile_size = tile_size

        self.image = None
        self.tiles_per_row = 1
        if filename:
            image = QImage(filename)
            self.image = transparent(image, image.pixelColor(0, 0), tile_size)
            self.tiles_per_row = self.image.width() // tile_size

    def get(self, rect):
        w = self.image.width() // self.tile_size
        return [
            rect.x() + px + w * (rect.y() + py)
            for py in range(rect.height())
            for px in range(rect.width())
        ]


class Layer:
    def __init__(self, tileset, size=(32, 32), tile_size=8):
        self.size = size
        self.tile_size = tile_size
        self.tileset = tileset
        self.image = QImage(*self.pixel_size(), QImage.Format_ARGB32)
        self.image.fill(QColor(0, 0, 0, 0))
        self.scaling = 4
        self.data = [0] * size[0] * size[1]

    def place(self, x, y, pattern: TilePattern):
        """
        Inserts pattern on coordinates

        Args:
            x(int): x on map coordinates (not pixel's!)
            y(int): y on map coordinates (not pixel's!)
        """
        pattern_width = pattern.region.width()
        pattern_height = pattern.region.height()
        data = self.tileset.get(pattern.region)
        w = self.size[0]

        print(f"drawing pattern at {x, y}")
        for py in range(pattern_height):
            for px in range(pattern_width):
                dx = px + x
                dy = py + y
                self.data[dx + w * dy] = data[px + pattern_width * py]

        x *= self.tile_size
        y *= self.tile_size

        painter = QPainter(self.image)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawImage(QPoint(x, y), pattern.image)
        painter.end()

    def pixel_size(self):
        return (self.size[0] * self.tile_size, self.size[1] * self.tile_size)


class Map:
    def __init__(self, name, tileset, size=(32, 32), tile_size=8, layers=4):
        """
        An entire map.

        Args:
            tileset(Tileset): reference to map's tileset
        """
        self.name = name
        self.size = size
        self.tile_size = tile_size
        self.tileset = tileset
        self.layers = [
            Layer(tileset, size=size, tile_size=tile_size) for i in range(layers)
        ]
        for layer in self.layers:
            layer.hidden = False

    def remake_image(self):
        tile_size = self.tile_size
        w = self.tileset.tiles_per_row
        tileset = self.tileset.image
        for layer in self.layers:
            dx, dy = 0, 0
            for value in layer.data:
                x, y = value % w, value // w
                painter = QPainter(layer.image)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.drawImage(
                    QPoint(tile_size * dx, tile_size * dy),
                    tileset.copy(
                        QRect(tile_size * x, tile_size * y, tile_size, tile_size)
                    ),
                )
                painter.end()
                dx += 1
                if dx == self.size[0]:
                    dx = 0
                    dy += 1

    def pixel_width(self):
        return self.pixel_size()[0]

    def pixel_height(self):
        return self.pixel_size()[1]

    def pixel_size(self):
        return (self.size[0] * self.tile_size, self.size[1] * self.tile_size)


def make_image(map):
    layers = map.layers
    image = layers[0].image
    image = QImage(image.size(), image.format())
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    for layer in layers:
        if not layer.hidden:
            painter.setOpacity(1)
        else:
            painter.setOpacity(0.5)
        painter.drawImage(QPoint(0, 0), layer.image)
    painter.end()
    return image
