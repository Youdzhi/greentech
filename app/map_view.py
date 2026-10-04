"""Interactive fixed-coordinate network map."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
)
from PyQt6 import sip
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from simulation import get_status, get_status_color
from simulation.failure_model import utilisation


class NetworkLineItem(QGraphicsLineItem):
    """Power-line visual with an easy-to-hit hover target."""

    def __init__(self, x1, y1, x2, y2, color: str, width: float) -> None:
        super().__init__(x1, y1, x2, y2)
        self._base_width = width
        self._color = QColor(color)
        self.setPen(QPen(self._color, width))
        self.setAcceptHoverEvents(True)

    def shape(self) -> QPainterPath:
        """Keep the visible line thin while making hover targeting forgiving."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(max(14.0, self._base_width + 8.0))
        return stroker.createStroke(path)

    def hoverEnterEvent(self, event) -> None:
        self.setPen(QPen(self._color, self._base_width + 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setPen(QPen(self._color, self._base_width))
        super().hoverLeaveEvent(event)


class MapView(QGraphicsView):
    """Render the synthetic network and emit selected asset ids."""

    asset_selected = pyqtSignal(str)
    map_clicked = pyqtSignal(float, float)
    asset_moved = pyqtSignal(str, float, float)
    connection_requested = pyqtSignal(str, str)
    node_creation_requested = pyqtSignal(float, float, str)
    line_selected = pyqtSignal(str)
    line_context_requested = pyqtSignal(str)
    asset_delete_requested = pyqtSignal(str)
    line_delete_requested = pyqtSignal(str)
    builder_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMinimumSize(0, 0)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.editor_mode = False
        self.asset_positions: dict[str, tuple[float, float]] = {}
        self._zoom = 1.0
        self._middle_pan_start = None
        self._theme = "dark"
        self.show_labels = True
        self._critical_items = []
        self._pulse_on = False
        self.builder_mode = False
        self.builder_tool = "select"
        self._drag_asset_id: str | None = None
        self._drag_last_scene = None
        self._connect_start: str | None = None
        self._node_visuals: dict[str, dict[str, object]] = {}
        self._line_visuals: dict[str, NetworkLineItem] = {}
        self._current_line_endpoints: list[tuple[str, str, str]] = []
        self._preview_line: QGraphicsLineItem | None = None
        self._right_drag_source: str | None = None
        self._radial_origin = None
        self._radial_choice: str | None = None
        self._radial_visuals: list[object] = []

    def set_editor_mode(self, enabled: bool) -> None:
        """Compatibility alias for placement mode."""
        self.builder_mode = enabled
        self.set_builder_tool("place" if enabled else "select")

    def set_builder_mode(self, enabled: bool) -> None:
        """Enable or disable the map editing canvas."""
        self.builder_mode = enabled
        if not enabled:
            self.set_builder_tool("select")
        self.builder_changed.emit(self.builder_tool)

    def set_builder_tool(self, tool: str) -> None:
        """Select the active map editing tool."""
        if tool not in {"select", "place", "connect", "delete"}:
            raise ValueError(f"Unknown builder tool: {tool}")
        self.builder_tool = tool
        self.editor_mode = tool == "place"
        self._connect_start = None
        self._remove_preview_line()
        cursor = Qt.CursorShape.ArrowCursor
        if tool == "place":
            cursor = Qt.CursorShape.CrossCursor
        elif tool == "connect":
            cursor = Qt.CursorShape.PointingHandCursor
        elif tool == "delete":
            cursor = Qt.CursorShape.ForbiddenCursor
        self.setCursor(QCursor(cursor))
        self.builder_changed.emit(tool)

    def _item_metadata(self, scene_pos):
        item = self.scene.itemAt(scene_pos, self.transform())
        while item is not None:
            asset_id = item.data(1)
            line_id = item.data(2)
            if asset_id:
                return "asset", asset_id
            if line_id:
                return "line", line_id
            item = item.parentItem()
        return None, None

    def _nearest_asset_id(self, scene_pos, radius: float = 28.0) -> str | None:
        """Return the closest node within a screen-friendly scene radius."""
        radius = radius / max(self._zoom, 0.01)
        closest_id = None
        closest_distance = radius
        for asset_id, (x, y) in self.asset_positions.items():
            distance = ((x - scene_pos.x()) ** 2 + (y - scene_pos.y()) ** 2) ** 0.5
            if distance <= closest_distance:
                closest_id = asset_id
                closest_distance = distance
        return closest_id

    def _asset_item_pressed(self, event, asset_id: str) -> None:
        if self.builder_mode:
            event.ignore()
            return
        self.asset_selected.emit(asset_id)

    def _start_radial_menu(self, point) -> None:
        self._cancel_connection_gesture()
        self._radial_origin = point
        self._radial_choice = "Substation"
        self._radial_visuals = []
        ring = QGraphicsEllipseItem(point.x() - 48, point.y() - 48, 96, 96)
        ring.setPen(QPen(QColor("#69efd0"), 2))
        ring_color = QColor("#082b36")
        ring_color.setAlpha(215)
        ring.setBrush(QBrush(ring_color))
        ring.setZValue(20)
        ring.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.scene.addItem(ring)
        self._radial_visuals.append(ring)
        choices = {
            "Generator": (0, -72),
            "Consumer": (-72, 0),
            "Substation": (0, 72),
        }
        for kind, (dx, dy) in choices.items():
            label = QGraphicsTextItem(kind.upper())
            label.setDefaultTextColor(QColor("#e3faf5"))
            label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            label.setPos(point.x() + dx - 32, point.y() + dy - 8)
            label.setZValue(21)
            label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(label)
            self._radial_visuals.append(label)
        hint = QGraphicsTextItem("MOVE TO CHOOSE")
        hint.setDefaultTextColor(QColor("#8eb8bd"))
        hint.setFont(QFont("Segoe UI", 7))
        hint.setPos(point.x() - 46, point.y() + 15)
        hint.setZValue(21)
        hint.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.scene.addItem(hint)
        self._radial_visuals.append(hint)

    def _update_radial_choice(self, point) -> None:
        if self._radial_origin is None:
            return
        dx = point.x() - self._radial_origin.x()
        dy = point.y() - self._radial_origin.y()
        if abs(dx) < 18 and abs(dy) < 18:
            return
        if abs(dx) > abs(dy):
            self._radial_choice = "Substation" if dx > 0 else "Consumer"
        else:
            self._radial_choice = "Generator" if dy < 0 else "Substation"
        self.builder_changed.emit(f"radial:{self._radial_choice}")

    def _finish_radial_menu(self, point) -> None:
        choice = self._radial_choice
        origin = self._radial_origin
        self._remove_radial_menu()
        if choice and origin is not None:
            self.node_creation_requested.emit(
                max(0.0, min(100.0, origin.x() / 7)),
                max(0.0, min(100.0, origin.y() / 5)),
                choice,
            )

    def _remove_radial_menu(self) -> None:
        radial_visuals = self._radial_visuals
        self._radial_visuals = []
        self._radial_origin = None
        self._radial_choice = None
        for item in radial_visuals:
            if sip.isdeleted(item):
                continue
            try:
                self.scene.removeItem(item)
            except RuntimeError:
                pass

    def _cancel_connection_gesture(self) -> None:
        """Cancel a pending right-button connection without changing the city."""
        self._right_drag_source = None
        self._remove_preview_line()

    def mouseDoubleClickEvent(self, event) -> None:
        """Use a right-button double-click to cancel line creation."""
        if self.builder_mode and event.button() == Qt.MouseButton.RightButton:
            self._cancel_connection_gesture()
            self._remove_radial_menu()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_pan_start = event.position().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        if self.builder_mode and event.button() == Qt.MouseButton.LeftButton:
            point = self.mapToScene(event.position().toPoint())
            kind, object_id = self._item_metadata(point)
            if self.builder_tool == "place":
                self.map_clicked.emit(max(0.0, min(100.0, point.x() / 7)), max(0.0, min(100.0, point.y() / 5)))
                return
            if self.builder_tool == "delete":
                if kind == "asset":
                    self.asset_delete_requested.emit(object_id)
                elif kind == "line":
                    self.line_delete_requested.emit(object_id)
                return
            if self.builder_tool == "connect":
                if kind == "asset":
                    if self._connect_start is None:
                        self._connect_start = object_id
                    elif object_id != self._connect_start:
                        self.connection_requested.emit(self._connect_start, object_id)
                        self._connect_start = None
                        self._remove_preview_line()
                return
            if self.builder_tool == "select" and kind == "asset":
                self._drag_asset_id = object_id
                self._drag_last_scene = point
                return
            if self.builder_tool == "select" and kind == "line":
                self.line_selected.emit(object_id)
                return
        if self.builder_mode and event.button() == Qt.MouseButton.RightButton:
            point = self.mapToScene(event.position().toPoint())
            kind, object_id = self._item_metadata(point)
            if kind == "line":
                self._cancel_connection_gesture()
                self._remove_radial_menu()
                self.line_context_requested.emit(object_id)
                event.accept()
                return
            if kind != "asset":
                object_id = self._nearest_asset_id(point)
                kind = "asset" if object_id else None
            if kind == "asset":
                self._remove_radial_menu()
                self._right_drag_source = object_id
                self._update_preview_line(object_id, self._snap_point(object_id, point))
            else:
                self._start_radial_menu(point)
            event.accept()
            return
        if not self.builder_mode and event.button() == Qt.MouseButton.LeftButton:
            kind, object_id = self._item_metadata(self.mapToScene(event.position().toPoint()))
            if kind == "asset" or kind == "line":
                (self.asset_selected if kind == "asset" else self.line_selected).emit(object_id)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Pan the scene while the middle mouse button is held."""
        if self._middle_pan_start is not None:
            current = event.position().toPoint()
            delta = current - self._middle_pan_start
            self._middle_pan_start = current
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return
        if self.builder_mode and self.builder_tool == "select" and self._drag_asset_id:
            point = self.mapToScene(event.position().toPoint())
            delta = point - self._drag_last_scene
            self._drag_last_scene = point
            self._move_visual_asset(self._drag_asset_id, delta.x(), delta.y())
            event.accept()
            return
        if self.builder_mode and self.builder_tool == "connect" and self._connect_start:
            self._update_preview_line(self._connect_start, self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        if self.builder_mode and self._right_drag_source:
            point = self.mapToScene(event.position().toPoint())
            target_id = self._nearest_asset_id(point)
            if target_id and target_id != self._right_drag_source:
                point = self._snap_point(target_id, point)
            self._update_preview_line(self._right_drag_source, point)
            event.accept()
            return
        if self.builder_mode and self._radial_origin is not None:
            self._update_radial_choice(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Finish middle-button panning without affecting asset selection."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_pan_start = None
            self.setCursor(
                QCursor(
                    Qt.CursorShape.CrossCursor
                    if self.editor_mode
                    else Qt.CursorShape.ArrowCursor
                )
            )
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._drag_asset_id:
            asset_id = self._drag_asset_id
            self._drag_asset_id = None
            self._drag_last_scene = None
            x, y = self.asset_positions[asset_id]
            self.asset_moved.emit(asset_id, x / 7, y / 5)
            event.accept()
            return
        if self.builder_mode and event.button() == Qt.MouseButton.RightButton:
            point = self.mapToScene(event.position().toPoint())
            if self._right_drag_source:
                source_id = self._right_drag_source
                target_id = self._nearest_asset_id(point)
                self._cancel_connection_gesture()
                if target_id and target_id != source_id:
                    self.connection_requested.emit(source_id, target_id)
            elif self._radial_origin is not None:
                self._finish_radial_menu(point)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:
        """Zoom the map around the cursor with bounded scale."""
        steps = event.angleDelta().y() / 120
        if steps == 0:
            event.ignore()
            return
        factor = 1.15 ** steps
        next_zoom = max(0.55, min(3.5, self._zoom * factor))
        factor = next_zoom / self._zoom
        if factor != 1.0:
            self.scale(factor, factor)
            self._zoom = next_zoom
        event.accept()

    def reset_view(self) -> None:
        """Restore the default map scale and center."""
        self.resetTransform()
        self._zoom = 1.0
        self.centerOn(350, 250)

    def set_theme(self, theme: str) -> None:
        """Set map label contrast for the active application theme."""
        self._theme = theme

    def render_city(self, city) -> None:
        self._remove_preview_line()
        self._remove_radial_menu()
        self.scene.clear()
        self._critical_items = []
        self._node_visuals.clear()
        self._line_visuals.clear()
        self._current_line_endpoints = []
        nodes = {item.id: item for item in (*city.generators, *city.substations, *city.consumers)}
        self.asset_positions = {item.id: (item.x * 7, item.y * 5) for item in nodes.values()}
        for line in city.power_lines:
            if line.from_node not in nodes or line.to_node not in nodes:
                continue
            a, b = nodes[line.from_node], nodes[line.to_node]
            color = get_status_color(get_status(utilisation(line)))
            width = 4 if utilisation(line) > 1 else 2
            line_item = NetworkLineItem(
                a.x * 7,
                a.y * 5,
                b.x * 7,
                b.y * 5,
                color,
                width,
            )
            line_item.setData(2, line.id)
            line_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(line_item)
            self._line_visuals[line.id] = line_item
            self._current_line_endpoints.append((line.id, line.from_node, line.to_node))
        for item in nodes.values():
            radius = 9 if type(item).__name__ == "Consumer" else 13
            color = "#7ef0b1"
            if hasattr(item, "max_capacity_mw"):
                color = get_status_color(get_status(utilisation(item)))
            elif hasattr(item, "operational") and not item.operational:
                color = "#ff2d55"
            ellipse = QGraphicsEllipseItem(item.x * 7 - radius, item.y * 5 - radius, radius * 2, radius * 2)
            ellipse.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            pen = QPen(QColor(color), 2 if hasattr(item, "max_capacity_mw") and utilisation(item) > 1 else 1)
            ellipse.setPen(pen)
            display_name = getattr(item, "name", item.id)
            detail = f"{utilisation(item):.0%} capacity" if hasattr(item, "max_capacity_mw") else ""
            ellipse.setToolTip(f"{display_name}\n{item.id}\n{detail}")
            ellipse.mousePressEvent = lambda event, asset_id=item.id: self._asset_item_pressed(event, asset_id)
            ellipse.setData(1, item.id)
            ellipse.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(ellipse)
            icon = self._svg_icon(type(item).__name__, color)
            icon.setPos(item.x * 7 - 12, item.y * 5 - 12)
            icon.setToolTip(f"{display_name}\n{item.id}")
            icon.mousePressEvent = lambda event, asset_id=item.id: self._asset_item_pressed(event, asset_id)
            icon.setData(1, item.id)
            icon.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(icon)
            if hasattr(item, "max_capacity_mw") and utilisation(item) >= 1.0:
                self._critical_items.append((ellipse, icon))
            if self.show_labels:
                name_label = QGraphicsTextItem(display_name)
                name_label.setDefaultTextColor(QColor("#dbe4ef" if self._theme == "dark" else "#20343d"))
                name_label.setFont(QFont("Segoe UI", 8))
                name_label.setPos(item.x * 7 + 18, item.y * 5 - 8)
                name_label.setData(1, item.id)
                self.scene.addItem(name_label)
            self._node_visuals[item.id] = {
                "ellipse": ellipse,
                "icon": icon,
                "label": name_label if self.show_labels else None,
            }

    def pulse_critical_assets(self) -> None:
        """Apply a restrained opacity pulse to overloaded assets."""
        self._pulse_on = not self._pulse_on
        opacity = 0.62 if self._pulse_on else 1.0
        for ellipse, icon in self._critical_items:
            ellipse.setOpacity(opacity)
            icon.setOpacity(opacity)

    def focus_asset(self, asset_id: str) -> None:
        """Center the viewport on a selected or vulnerable asset."""
        if asset_id in self.asset_positions:
            x, y = self.asset_positions[asset_id]
            self.centerOn(x, y)

    def _move_visual_asset(self, asset_id: str, dx: float, dy: float) -> None:
        """Move a node's visuals and connected lines without rebuilding the scene."""
        visuals = self._node_visuals.get(asset_id)
        if not visuals:
            return
        for item in visuals.values():
            if item is not None:
                item.moveBy(dx, dy)
        current_x, current_y = self.asset_positions[asset_id]
        self.asset_positions[asset_id] = (current_x + dx, current_y + dy)
        self._update_connected_lines(asset_id)

    def _update_connected_lines(self, asset_id: str) -> None:
        for line in self._line_visuals.values():
            line_id = line.data(2)
            for endpoint in self._current_line_endpoints:
                if endpoint[0] == line_id and asset_id in endpoint[1:]:
                    a = self.asset_positions.get(endpoint[1])
                    b = self.asset_positions.get(endpoint[2])
                    if a and b:
                        line.setLine(a[0], a[1], b[0], b[1])

    def _update_preview_line(self, source_id: str, target_point) -> None:
        source = self.asset_positions.get(source_id)
        if not source:
            return
        if self._preview_line is None:
            self._preview_line = QGraphicsLineItem()
            self._preview_line.setPen(QPen(QColor("#69efd0"), 2, Qt.PenStyle.DashLine))
            self._preview_line.setZValue(10)
            self.scene.addItem(self._preview_line)
        self._preview_line.setLine(source[0], source[1], target_point.x(), target_point.y())

    def _snap_point(self, asset_id: str, point):
        """Use the node center when a gesture endpoint is close enough."""
        position = self.asset_positions.get(asset_id)
        if position is None:
            return point
        from PyQt6.QtCore import QPointF

        return QPointF(position[0], position[1])

    def _remove_preview_line(self) -> None:
        preview_line = self._preview_line
        self._preview_line = None
        if preview_line is None or sip.isdeleted(preview_line):
            return
        try:
            self.scene.removeItem(preview_line)
        except RuntimeError:
            # Qt may have deleted the graphics item during a scene rebuild.
            pass

    @staticmethod
    def _svg_icon(kind: str, color: str) -> QGraphicsSvgItem:
        """Create a small theme-independent SVG asset icon."""
        shapes = {
            "Generator": '<path d="M12 1 3 14h7l-1 9 9-13h-7z"/>',
            "Substation": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12h8M12 8v8"/>',
            "Consumer": '<circle cx="12" cy="12" r="7"/><path d="M12 5v14M5 12h14"/>',
        }
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            f'viewBox="0 0 24 24"><g fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{shapes.get(kind, shapes["Consumer"])}</g></svg>'
        )
        item = QGraphicsSvgItem()
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        item.setSharedRenderer(renderer)
        item._renderer = renderer
        return item
