from PySide2.QtCore import (
    QRect,
    Qt,
)

from PySide2.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from PySide2.QtGui import (
    QColor,
    QPainter,
    QPen,
    QPixmap,
)

from mapeditor.map import TilePattern, Tileset, Map, make_image, preview_pattern
from mapeditor.utils import scaled


class MapEditor(QWidget):
    def __init__(self, *args, tileset=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.map = Map(
            name="Map001",
            tileset=Tileset(filename=tileset),
            size=(32, 32),
            tile_size=8,
            layers=4,
        )

        contents = QHBoxLayout(self)

        self.tileset_selector = TilesetSelector(self, tileset=self.map.tileset)
        left = QScrollArea()
        left.setWidget(self.tileset_selector)
        left.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left.setStyleSheet("background: url('mapeditor/square.png') repeat;")

        self.tilemap = TilemapEditor(self.map, tileset_selector=self.tileset_selector)
        self.tilemap.setStyleSheet("background: url('mapeditor/square.png') repeat;")
        right = QScrollArea()
        right.setWidget(self.tilemap)

        contents.addWidget(left)
        contents.addWidget(right)

        left.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        contents.setContentsMargins(0, 0, 0, 0)

    def load(self, data):
        self.map = data
        self.tileset_selector.change_tileset(self.map.tileset)
        self.tilemap.change_map(self.map)

    def select_layer(self, index):
        print(f"selected {index}")
        for layer in self.map.layers:
            layer.hidden = True
        self.tilemap._current_layer = index
        self.map.layers[index].hidden = False

        self.tilemap.remake_image()
        self.repaint()


class TilesetSelector(QLabel):
    """
    Widget for selecting tiles used to fill map.
    """

    def __init__(self, *args, tileset=None, tile_size=32, **kwargs):
        super().__init__(*args, **kwargs)

        self._width = 256
        self.sel_rect = None
        self.scaling = 4

        self.change_tileset(tileset)

        self.mousePressEvent = self.on_click
        self.mouseMoveEvent = self.on_drag

    def change_tileset(self, tileset):
        self.tileset = tileset
        self.tile_size = self.tileset.tile_size
        self.tiles_per_row = self._width // (self.tile_size * self.scaling)

        if self.tileset.image:
            self.setPixmap(
                QPixmap.fromImage(self.tileset.image).scaledToWidth(self._width)
            )

    def scale(self):
        return self.tile_size * self.scaling

    def scaled(self, x, y):
        scale = self.scale()
        return self.scale() * (x // scale), self.scale() * (y // scale)

    def on_drag(self, event):
        scale = self.scale()

        ox, oy = self.origin
        pos = event.pos()
        ex, ey = pos.x() // scale, pos.y() // scale

        r1 = QRect(ox, oy, 1, 1)
        r2 = QRect(ex, ey, 1, 1)
        self.sel_rect = r1 | r2

        self.repaint()

    def on_click(self, event):
        scale = self.scale()

        pos = event.pos()
        x, y = self.scaled(pos.x(), pos.y())

        self.origin = x // scale, y // scale
        self.sel_rect = QRect(*self.origin, 1, 1)
        self.repaint()

    def paintEvent(self, e):
        super().paintEvent(e)

        if not self.sel_rect:
            return

        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0), 3))

        rect = scaled(self.sel_rect, self.scale())
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        painter.drawRect(rect)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(rect)
        painter.end()


class TilemapEditor(QLabel):
    """
    Widget to show and edit the map itself.
    """

    def __init__(self, map, *args, tileset_selector=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.map = map
        self._current_layer = 0
        self.tileset_selector = tileset_selector
        self.scaling = 4
        self.sel_rect = None

        self.remake_image()

        self.mousePressEvent = self.on_click
        self.mouseMoveEvent = self.on_mouse_move
        self.setMouseTracking(True)

    def change_map(self, data):
        self.map = data
        self.remake_image()

    def current_layer(self):
        return self.map.layers[self._current_layer]

    def remake_image(self):
        width = self.map.pixel_width() * self.scaling
        self.setPixmap(QPixmap.fromImage(make_image(self.map)).scaledToWidth(width))

    def on_click(self, e):
        sel_rect = self.tileset_selector.sel_rect
        if sel_rect is None:
            return

        scale = self.map.tile_size * self.scaling
        pos = e.pos()
        x, y = pos.x() // scale, pos.y() // scale
        self.last_point = self.origin = x, y

        if not self.contentsRect().contains(pos.x(), pos.y()):
            return

        tileset = self.map.tileset

        rect = scaled(sel_rect, self.map.tile_size)
        pattern = TilePattern(region=sel_rect, image=tileset.image.copy(rect))
        self.current_layer().place(x, y, pattern)
        self.remake_image()

    def paintEvent(self, e):
        super().paintEvent(e)

        SHADOW_COLOR = QColor(0, 0, 0)
        BORDER_COLOR = QColor(255, 255, 255)

        if not self.sel_rect:
            return

        painter = QPainter(self)
        painter.setPen(QPen(SHADOW_COLOR, 3))

        scale = self.scaling * self.map.tile_size
        rect = scaled(self.sel_rect, scale)
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        painter.drawRect(rect)
        painter.setPen(QPen(BORDER_COLOR, 1))
        painter.drawRect(rect)
        painter.end()

    def on_mouse_move(self, e):
        scale = self.map.tile_size * self.scaling

        rect = self.tileset_selector.sel_rect

        if rect:
            self.sel_rect = QRect(rect)
            x, y = e.x(), e.y()
            self.sel_rect.moveTo(x // scale, y // scale)
            self.repaint()

        if e.buttons() != Qt.NoButton:
            self.on_drag(e)

    def on_drag(self, e):
        scale = self.map.tile_size * self.scaling

        pos = e.pos()
        x, y = pos.x() // scale, pos.y() // scale
        sel_rect = self.tileset_selector.sel_rect

        if sel_rect is None or (x, y) == self.last_point:
            return

        tileset = self.map.tileset
        ox, oy = self.origin

        last_x, last_y = self.last_point

        if x != last_x or y != last_y:
            scaled_source = scaled(sel_rect, self.map.tile_size)

            pattern = TilePattern(
                region=sel_rect, image=tileset.image.copy(scaled_source)
            )

            pattern = preview_pattern((ox, oy), (x, y), pattern, self.map.tile_size)
            self.current_layer().place(x, y, pattern)

        self.remake_image()
        self.last_point = x, y
