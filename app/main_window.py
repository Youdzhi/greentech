"""Pitch-first LeSauveur control-room window."""

from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from models import City, Consumer, Generator, PowerLine, Substation
from simulation import Scenario, ScenarioEngine, SimulationEngine

from .control_panel import ControlPanel
from .event_log import EventLog
from .map_view import MapView
from .statistics_panel import StatisticsPanel
from .styles import THEMES


class MainWindow(QMainWindow):
    """Reference-inspired three-column pitch and engineer interface."""

    def __init__(self, city: City) -> None:
        super().__init__()
        self.setWindowTitle("LeSauveur - Urban Electricity Network Digital Twin")
        self.setMinimumSize(900, 600)
        self.engine = SimulationEngine(city)
        self.theme = "dark"
        self.simulation_speed = 1.0
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(lambda: self._advance(self.simulation_speed))
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(650)
        self.animation_timer.timeout.connect(self.map_pulse)
        self.animation_timer.start()
        self.map = MapView()
        self.map.set_theme(self.theme)
        self.map.setMinimumSize(0, 0)
        self.controls = ControlPanel()
        self.stats = StatisticsPanel()
        self.stats.setMaximumWidth(390)
        self.log = EventLog()
        self._scenario_before = None
        self.animations_enabled = True
        self.show_map_labels = True

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(10)
        root_layout.addWidget(self.controls)

        content = QHBoxLayout()
        content.setSpacing(10)
        content.addWidget(self.stats, 25)
        center = QVBoxLayout()
        center.setSpacing(8)
        self.mode_indicator = QLabel()
        self.mode_indicator.setObjectName("modeIndicator")
        self.mode_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
        center.addWidget(self.mode_indicator)
        center.addWidget(self.map, 1)
        self.builder_hint = QLabel("Builder ready: choose Build Scenario, Add Asset, or Add Power Line from the command bar.")
        self.builder_hint.setObjectName("subtitle")
        center.addWidget(self.builder_hint)
        center.addWidget(self._build_bottom_story(), 0)
        content.addLayout(center, 55)
        self.right_rail = self._build_right_rail()
        self.right_rail.setMaximumWidth(430)
        content.addWidget(self.right_rail, 25)
        root_layout.addLayout(content, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(THEMES[self.theme])

        self.controls.reset_requested.connect(self._reset)
        self.controls.scenario_changed.connect(self._scenario)
        self.controls.import_requested.connect(self._import)
        self.controls.export_requested.connect(self._export)
        self.controls.theme_requested.connect(self._toggle_theme)
        self.controls.add_asset_requested.connect(self._start_asset_creation)
        self.controls.add_line_requested.connect(self._start_line_creation)
        self.controls.builder_mode_requested.connect(self._set_builder_mode)
        self.controls.builder_tool_requested.connect(self._set_builder_tool)
        self.controls.engineer_mode_requested.connect(self._engineer_mode)
        self.controls.settings_requested.connect(self._show_settings)
        self.controls.information_requested.connect(self._set_information_mode)
        self.controls.simulation_speed_requested.connect(self._set_simulation_speed)
        self.map.asset_selected.connect(self._inspect)
        self.map.map_clicked.connect(self._place_asset)
        self.map.asset_moved.connect(self._move_asset)
        self.map.connection_requested.connect(self._connect_assets)
        self.map.node_creation_requested.connect(self._create_node_at)
        self.map.line_context_requested.connect(self._confirm_delete_line)
        self.map.line_selected.connect(self._inspect)
        self.map.asset_delete_requested.connect(self._delete_asset_by_id)
        self.map.line_delete_requested.connect(self._delete_line_by_id)
        self.stats.asset_selected.connect(self._focus_asset)
        self.stats.why_requested.connect(self._show_why)
        self.stats.prevent_requested.connect(self._show_prevention)
        self.controls.why_requested.connect(self._show_why)
        self.controls.prevent_requested.connect(self._show_prevention)
        self.controls.help_requested.connect(self._show_help)
        self._install_shortcuts()
        self._update_mode_indicator()
        self._refresh()

    def _install_shortcuts(self) -> None:
        """Documented keyboard controls for presenters and engineers."""
        from PyQt6.QtGui import QShortcut, QKeySequence
        shortcuts = {
            "Space": lambda: self.timer.stop() if self.timer.isActive() else self.timer.start(),
            "R": self._reset,
            "I": lambda: self.controls.info_mode.toggle(),
            "E": lambda: self.controls.engineer_mode.toggle(),
            "B": lambda: self.controls.builder_mode.toggle(),
            "T": self._toggle_theme,
            "F": self.map.reset_view,
            "Escape": lambda: self.map.set_editor_mode(False),
        }
        self._shortcuts = []
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def _build_right_rail(self):
        rail = QWidget()
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("SIMULATION RESULT"))
        self.current_result = QLabel()
        self.current_result.setObjectName("resultNormal")
        self.scenario_result = QLabel()
        self.scenario_result.setObjectName("resultCritical")
        row = QHBoxLayout()
        row.addWidget(self.current_result)
        row.addWidget(self.scenario_result)
        layout.addLayout(row)
        self.failure_result = QLabel()
        self.failure_result.setObjectName("resultCritical")
        layout.addWidget(self.failure_result)
        layout.addWidget(QLabel("SIMULATION TIMELINE"))
        layout.addWidget(self.log, 1)
        return rail

    def _build_bottom_story(self):
        row = QHBoxLayout()
        self.story_hint = QLabel(
            "Use Help for failure explanation, prevention guidance, map controls, and keybinds."
        )
        self.story_hint.setObjectName("subtitle")
        row.addWidget(self.story_hint)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    @staticmethod
    def _story_card(title, description, button_text, callback):
        box = QWidget()
        layout = QVBoxLayout(box)
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        button = QPushButton(button_text)
        button.clicked.connect(callback)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(button)
        return box

    def _advance(self, seconds: float) -> None:
        self.engine.tick(seconds)
        self._refresh()

    def _set_simulation_speed(self, speed: float) -> None:
        """Set the simulation time advanced by each timer tick."""
        self.simulation_speed = max(0.5, min(5.0, speed))

    def map_pulse(self) -> None:
        """Animate only critical map assets; keep motion subtle."""
        if self.animations_enabled:
            self.map.pulse_critical_assets()

    def _scenario(self, scenario: Scenario) -> None:
        if scenario is None:
            self._build_custom_scenario()
            return
        self.timer.stop()
        self._scenario_before = self.engine.get_metrics()
        self.engine.run_scenario(scenario)
        self._refresh()

    def _reset(self) -> None:
        self.timer.stop()
        self.engine.reset()
        self._scenario_before = None
        self.map.reset_view()
        self._refresh()

    def _refresh(self) -> None:
        self.map.render_city(self.engine.city)
        self.stats.update_engine(self.engine)
        metrics = self.engine.get_metrics()
        before = self._scenario_before or metrics
        self.current_result.setText(
            f"CURRENT GRID\n\n{before.network_utilisation:.0%}\nload\n"
            f"{before.critical_assets}\ncritical assets\n[{before.cascade_risk.value} RISK]"
        )
        self.scenario_result.setText(
            f"SCENARIO\n\n{metrics.network_utilisation:.0%}\nload\n"
            f"{metrics.critical_assets}\ncritical assets\n[{metrics.cascade_risk.value}]"
        )
        vulnerable = self.engine.get_vulnerable_assets()
        if vulnerable and vulnerable[0][2] is not None:
            asset, ratio, eta = vulnerable[0]
            name = getattr(asset, "name", asset.id)
            self.failure_result.setText(
                f"[FAILURE PREDICTED]   {name} reaches {ratio:.0%} capacity.\n"
                f"Predicted failure: {self._clock(eta)}   |   Affected areas: {metrics.affected_consumers}"
            )
        else:
            self.failure_result.setText("[NO IMMEDIATE FAILURE PREDICTED]   Grid is within current limits.")
        self.log.update_events(self.engine.events)

    @staticmethod
    def _clock(seconds: float | None) -> str:
        if seconds is None:
            return "SAFE"
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self.map.set_theme(self.theme)
        self.setStyleSheet(THEMES[self.theme])

    def _engineer_mode(self, enabled: bool) -> None:
        self.log.set_engineer_mode(enabled)
        for widget in (self.controls.import_button, self.controls.export_button, self.controls.add_asset_button, self.controls.add_line_button):
            widget.setVisible(enabled)
        self.builder_hint.setText(
            "Engineer mode active: select an asset for details, use Move on Map, Add Asset, or Add Power Line."
            if enabled
            else "Builder ready: choose Build Scenario, Add Asset, or Add Power Line from the command bar."
        )
        self._update_mode_indicator()
        self._refresh()

    def _set_builder_mode(self, enabled: bool) -> None:
        self.map.set_builder_mode(enabled)
        if not enabled:
            self.builder_hint.setText(
                "Builder ready: choose Build Scenario, Add Asset, or Add Power Line from the command bar."
            )
        else:
            self.builder_hint.setText(
                "BUILDER MODE: Select / Move drags nodes. Connect Assets links two nodes. "
                "Delete removes nodes or lines."
            )
        self._update_mode_indicator()

    def _set_builder_tool(self, tool: str) -> None:
        self.map.set_builder_tool(tool)
        labels = {
            "select": "BUILDER: Select / Move - drag a node to reposition it.",
            "place": "BUILDER: Place Asset - click an empty map location.",
            "connect": "BUILDER: Connect Assets - click the source, then the target.",
            "delete": "BUILDER: Delete - click a node or power line.",
        }
        self.builder_hint.setText(labels[tool])
        self._update_mode_indicator()

    def _update_mode_indicator(self) -> None:
        """Keep the active interaction mode visible but visually subordinate."""
        if self.controls.builder_mode.isChecked():
            mode = "BUILDER"
        elif self.controls.engineer_mode.isChecked():
            mode = "ENGINEER"
        elif self.controls.info_mode.isChecked():
            mode = "INFO"
        else:
            mode = "STANDARD"
        self.mode_indicator.setText(f"MODE  /  {mode}")

    def _move_asset(self, asset_id: str, x: float, y: float) -> None:
        asset = self._find_asset(asset_id)
        if asset is None:
            return
        asset.x = x
        asset.y = y
        self.engine.load_city(self.engine.city)
        self._refresh()

    def _connect_assets(self, source_id: str, target_id: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Power Line")
        form = QFormLayout(dialog)
        capacity = QDoubleSpinBox()
        capacity.setRange(1, 2000)
        capacity.setValue(80)
        length = QDoubleSpinBox()
        length.setRange(0.1, 500)
        length.setValue(1)
        form.addRow("Capacity (MW)", capacity)
        form.addRow("Length (km)", length)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if any(
            {line.from_node, line.to_node} == {source_id, target_id}
            for line in self.engine.city.power_lines
        ):
            QMessageBox.warning(self, "Connection exists", "These two assets are already connected.")
            return
        line_id = f"l{len(self.engine.city.power_lines) + 1}"
        self.engine.city.power_lines.append(
            PowerLine(line_id, source_id, target_id, capacity.value(), length_km=length.value())
        )
        self.engine.load_city(self.engine.city)
        self._refresh()

    def _create_node_at(self, x: float, y: float, preferred_type: str) -> None:
        """Open the compact node form after a radial builder gesture."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add map node")
        dialog.setMinimumWidth(320)
        form = QFormLayout(dialog)
        kind = QComboBox()
        kind.addItems(["Generator", "Substation", "Consumer"])
        kind.setCurrentText(preferred_type)
        name = QLineEdit()
        name.setPlaceholderText(f"{preferred_type} name")
        value = QDoubleSpinBox()
        value.setRange(1, 2000)
        value.setValue(100)
        form.addRow("Type", kind)
        form.addRow("Name", name)
        form.addRow("Capacity / demand (MW)", value)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted or not name.text().strip():
            return
        self._add_node(
            kind.currentText(),
            name.text().strip(),
            value.value(),
            x,
            y,
        )

    def _add_node(self, kind: str, name: str, value: float, x: float, y: float) -> None:
        prefix = {"Generator": "g", "Substation": "s", "Consumer": "c"}[kind]
        existing = [
            item.id
            for item in (
                *self.engine.city.generators,
                *self.engine.city.substations,
                *self.engine.city.consumers,
            )
        ]
        index = 1
        while f"{prefix}{index}" in existing:
            index += 1
        asset_id = f"{prefix}{index}"
        if kind == "Generator":
            self.engine.city.generators.append(Generator(asset_id, name, x, y, value))
        elif kind == "Substation":
            self.engine.city.substations.append(Substation(asset_id, name, x, y, value))
        else:
            self.engine.city.consumers.append(Consumer(asset_id, name, x, y, value, value))
        self.engine.load_city(self.engine.city)
        self._refresh()

    def _delete_asset_by_id(self, asset_id: str) -> None:
        asset = self._find_asset(asset_id)
        if asset is not None:
            self._delete_asset(asset)

    def _delete_line_by_id(self, line_id: str) -> None:
        line = next((item for item in self.engine.city.power_lines if item.id == line_id), None)
        if line is None:
            return
        self.engine.city.power_lines.remove(line)
        self.engine.load_city(self.engine.city)
        self._refresh()

    def _confirm_delete_line(self, line_id: str) -> None:
        """Confirm deletion when a power line is right-clicked in Builder Mode."""
        line = next((item for item in self.engine.city.power_lines if item.id == line_id), None)
        if line is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete power line",
            f"Are you sure you want to delete power line {line.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._delete_line_by_id(line_id)

    def _find_asset(self, asset_id: str):
        return next(
            (
                item
                for item in (
                    *self.engine.city.generators,
                    *self.engine.city.substations,
                    *self.engine.city.consumers,
                )
                if item.id == asset_id
            ),
            None,
        )

    def _set_information_mode(self, enabled: bool) -> None:
        """Show concise operational guidance without opening modal dialogs."""
        self.builder_hint.setText(
            "INFO: Wheel = zoom | Middle mouse = pan | Click asset = inspect | "
            "Builder: RMB-drag node to node = connect | RMB empty space = add node | "
            "F = fit map | E = engineer mode | T = theme | Space = run/pause"
            if enabled
            else "Builder ready: choose Build Scenario, Add Asset, or Add Power Line from the command bar."
        )
        self.map.setToolTip(
            "Wheel: zoom\nMiddle mouse: pan\nLeft click: select asset"
            if enabled else ""
        )
        self._update_mode_indicator()

    def _show_settings(self) -> None:
        """Expose presentation and interaction preferences."""
        dialog = QDialog(self)
        dialog.setWindowTitle("LeSauveur Settings and Keybinds")
        dialog.setMinimumWidth(480)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        animations = QCheckBox("Enable critical-asset pulse animation")
        animations.setChecked(self.animations_enabled)
        labels = QCheckBox("Show map asset labels")
        labels.setChecked(self.show_map_labels)
        form.addRow("Presentation", animations)
        form.addRow("Map labels", labels)
        layout.addLayout(form)
        keys = QLabel(
            "KEYBINDS\n"
            "Space  Run / pause simulation\n"
            "R      Reset simulation\n"
            "I      Toggle informative mode\n"
            "E      Toggle engineer mode\n"
            "T      Switch light / dark theme\n"
            "F      Fit map to default view\n"
            "Escape Cancel map placement or editing"
        )
        keys.setObjectName("comparison")
        layout.addWidget(keys)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.animations_enabled = animations.isChecked()
            self.show_map_labels = labels.isChecked()
            self.map.show_labels = self.show_map_labels
            self._refresh()

    def _focus_asset(self, asset_id: str) -> None:
        self.map.focus_asset(asset_id)
        self._inspect(asset_id)

    def _show_why(self) -> None:
        vulnerable = self.engine.get_vulnerable_assets(2)
        if not vulnerable:
            QMessageBox.information(self, "Why", "The grid is not currently showing a vulnerable asset.")
            return
        first = getattr(vulnerable[0][0], "name", vulnerable[0][0].id)
        second = getattr(vulnerable[1][0], "name", vulnerable[1][0].id) if len(vulnerable) > 1 else "downstream assets"
        QMessageBox.information(
            self,
            "Why is the grid failing?",
            f"1. Demand is routed through the operational network.\n"
            f"2. {first} is at {vulnerable[0][1]:.0%} capacity.\n"
            f"3. Power flow shifts load toward the most available paths.\n"
            f"4. {second} becomes the next stress point.\n"
            f"5. Failure risk is {self.engine.get_metrics().cascade_risk.value}.",
        )

    def _show_prevention(self) -> None:
        QMessageBox.information(
            self,
            "Prevent the failure",
            "Available intervention paths:\n\n"
            "A. Add solar generation or battery storage in What If?\n"
            "B. Reduce industrial load in What If?\n"
            "C. Add or upgrade infrastructure in Engineer mode.\n\n"
            "Outcome: simulation required. Costs are not calculated by this MVP.",
        )

    def _show_help(self) -> None:
        """Show consolidated product guidance from the navbar Help menu."""
        QMessageBox.information(
            self,
            "LeSauveur Help",
            "PRODUCT FLOW\n"
            "Build a scenario -> Run the simulation -> Inspect vulnerable assets -> "
            "Explain the failure -> Simulate prevention.\n\n"
            "MAP CONTROLS\n"
            "Wheel: zoom\n"
            "Middle mouse drag: pan\n"
            "Left click: inspect an asset\n"
            "Builder Mode: hold RMB on a node and drag to another node to connect.\n"
            "Builder Mode: hold RMB on empty space, move to choose a node type, release to configure it.\n"
            "F: fit the map\n\n"
            "BUILDER\n"
            "RMB gestures are the fastest way to add and connect map nodes.\n"
            "Map Builder > Add Asset places a generator, substation, or consumer.\n"
            "Map Builder > Add Power Line connects two assets.\n"
            "Engineer Mode exposes import, export, and technical editing controls.\n\n"
            "KEYBINDS\n"
            "Space run/pause   R reset   I informative mode   E engineer mode\n"
            "T theme   F fit map   Escape cancel map editing",
        )

    def _build_custom_scenario(self) -> None:
        """Create and immediately run a user-defined scenario."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Scenario Builder")
        dialog.setMinimumWidth(500)
        form = QFormLayout(dialog)
        name = QLineEdit("Custom scenario")
        demand = QDoubleSpinBox(); demand.setRange(0.1, 5.0); demand.setSingleStep(0.05); demand.setValue(1.0)
        generation = QDoubleSpinBox(); generation.setRange(0.1, 5.0); generation.setSingleStep(0.05); generation.setValue(1.0)
        industrial = QDoubleSpinBox(); industrial.setRange(0.1, 5.0); industrial.setSingleStep(0.05); industrial.setValue(1.0)
        added_generation = QDoubleSpinBox(); added_generation.setRange(0, 5000); added_generation.setValue(0)
        added_demand = QDoubleSpinBox(); added_demand.setRange(0, 5000); added_demand.setValue(0)
        storage = QDoubleSpinBox(); storage.setRange(0, 5000); storage.setValue(0)
        failed_substation = QComboBox()
        failed_substation.addItem("None", None)
        for item in self.engine.city.substations:
            failed_substation.addItem(f"{item.name} ({item.id})", item.id)
        failed_generator = QComboBox()
        failed_generator.addItem("None", None)
        for item in self.engine.city.generators:
            failed_generator.addItem(f"{item.name} ({item.id})", item.id)
        form.addRow("Scenario name", name)
        form.addRow("Demand multiplier", demand)
        form.addRow("Generation multiplier", generation)
        form.addRow("Industrial multiplier", industrial)
        form.addRow("Added generation (MW)", added_generation)
        form.addRow("Added demand (MW)", added_demand)
        form.addRow("Battery storage (MW)", storage)
        form.addRow("Fail substation", failed_substation)
        form.addRow("Fail generator", failed_generator)
        hint = QLabel("Create your own operating condition. No preset scenarios are used.")
        hint.setWordWrap(True)
        form.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        scenario = Scenario(
            name.text().strip() or "Custom scenario",
            demand_multiplier=demand.value(),
            generation_multiplier=generation.value(),
            failed_substation_id=failed_substation.currentData(),
            failed_generator_id=failed_generator.currentData(),
            industrial_multiplier=industrial.value(),
            demand_add_mw=added_demand.value(),
            generation_add_mw=added_generation.value(),
            battery_storage_mw=storage.value(),
        )
        self._scenario(scenario)

    def _what_if(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("What If? - Scenario Builder")
        form = QFormLayout(dialog)
        ev = QDoubleSpinBox(); ev.setRange(0, 100000); ev.setValue(5000)
        buildings = QDoubleSpinBox(); buildings.setRange(0, 100000); buildings.setValue(2000)
        solar = QDoubleSpinBox(); solar.setRange(0, 5000); solar.setValue(20)
        industrial = QDoubleSpinBox(); industrial.setRange(0, 500); industrial.setValue(5)
        battery = QDoubleSpinBox(); battery.setRange(0, 5000); battery.setValue(2)
        form.addRow("Add EV chargers", ev)
        form.addRow("Add buildings", buildings)
        form.addRow("Solar generation (MW)", solar)
        form.addRow("Industrial load (MW)", industrial)
        form.addRow("Battery storage (MW)", battery)
        form.addRow(QLabel("EV chargers and buildings are staged inputs until a calibrated demand model is connected."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        scenario = Scenario(
            "What-if scenario",
            demand_add_mw=industrial.value(),
            generation_add_mw=solar.value(),
            battery_storage_mw=battery.value(),
        )
        result = self.engine.simulate_what_if(scenario)
        before = self.engine.get_metrics()
        after = result.get_metrics()
        QMessageBox.information(
            self,
            "Projected impact",
            f"CURRENT GRID\n{before.network_utilisation:.0%} load | {before.critical_assets} critical | {before.cascade_risk.value}\n\n"
            f"SCENARIO\n{after.network_utilisation:.0%} load | {after.critical_assets} critical | {after.cascade_risk.value}\n\n"
            f"Failed assets: {after.failed_assets}\nAffected areas: {after.affected_consumers}",
        )

    def _inspect(self, asset_id: str) -> None:
        for asset in (*self.engine.city.generators, *self.engine.city.substations, *self.engine.city.consumers, *self.engine.city.power_lines):
            if asset.id == asset_id:
                self._show_asset_inspector(asset)
                return

    def _show_asset_inspector(self, asset) -> None:
        """Show structured asset information and safe edit/delete actions."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Asset Inspector - {getattr(asset, 'name', asset.id)}")
        dialog.setMinimumWidth(460)
        layout = QVBoxLayout(dialog)
        kind = type(asset).__name__
        name = getattr(asset, "name", f"Power Line {asset.id.removeprefix('l')}")
        if hasattr(asset, "max_capacity_mw"):
            capacity = asset.max_capacity_mw
            load = asset.current_load_mw
            utilisation = load / capacity if capacity else 0
            details = (
                f"Type: {kind}\n"
                f"Name: {name}\n"
                f"ID: {asset.id}\n"
                f"Capacity: {capacity:.1f} MW\n"
                f"Current load: {load:.1f} MW\n"
                f"Utilisation: {utilisation:.0%}\n"
                f"Operational: {'YES' if asset.operational else 'NO'}\n"
                f"Damage: {getattr(asset, 'damage', 0):.1f}%"
            )
        elif kind == "Generator":
            details = (
                f"Type: Generator\nName: {asset.name}\nID: {asset.id}\n"
                f"Capacity: {asset.capacity_mw:.1f} MW\n"
                f"Current output: {asset.current_output_mw:.1f} MW\n"
                f"Operational: {'YES' if asset.operational else 'NO'}"
            )
        else:
            details = (
                f"Type: Consumer\nName: {asset.name}\nID: {asset.id}\n"
                f"Base demand: {asset.base_demand_mw:.1f} MW\n"
                f"Current demand: {asset.current_demand_mw:.1f} MW\n"
                f"Priority: {asset.priority}"
            )
        info = QLabel(details)
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info)
        buttons = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.reject)
        move_button = QPushButton("Move on Map")
        move_button.clicked.connect(
            lambda: (
                setattr(self, "pending_move_asset", asset),
                self.map.set_editor_mode(True),
                dialog.accept(),
            )
        )
        delete_button = QPushButton("Delete Asset")
        delete_button.setObjectName("danger")
        delete_button.clicked.connect(lambda: self._delete_asset(asset, dialog))
        buttons.addWidget(move_button)
        buttons.addWidget(delete_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        dialog.exec()

    def _delete_asset(self, asset, dialog: QDialog | None = None) -> None:
        """Delete an asset and connected lines after explicit confirmation."""
        answer = QMessageBox.question(
            self,
            "Delete asset",
            f"Delete {getattr(asset, 'name', asset.id)} and its connected lines?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        collections = (self.engine.city.generators, self.engine.city.substations, self.engine.city.consumers)
        for collection in collections:
            if asset in collection:
                collection.remove(asset)
        self.engine.city.power_lines[:] = [
            line for line in self.engine.city.power_lines
            if line.from_node != asset.id and line.to_node != asset.id
        ]
        self.engine.load_city(self.engine.city)
        if dialog is not None:
            dialog.accept()
        self._refresh()

    def _import(self, path: str) -> None:
        try:
            self.engine.load_city(City.from_json(path))
            self._refresh()
        except ValueError as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def _export(self, path: str) -> None:
        self.engine.city.to_json(path)

    def _start_asset_creation(self) -> None:
        dialog = QDialog(self)
        form = QFormLayout(dialog)
        kind = QComboBox(); kind.addItems(["Generator", "Substation", "Consumer"])
        name = QLineEdit()
        value = QDoubleSpinBox(); value.setRange(1, 2000); value.setValue(100)
        form.addRow("Type", kind); form.addRow("Name", name); form.addRow("Capacity / demand MW", value)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted and name.text().strip():
            self.pending_asset_type = kind.currentText()
            self.pending_asset_name = name.text().strip()
            self.pending_asset_value = value.value()
            self.controls.builder_mode.setChecked(True)
            self._set_builder_mode(True)
            self._set_builder_tool("place")
            self.builder_hint.setText("Placement mode active: click an empty location on the map to place the new asset.")

    def _place_asset(self, x: float, y: float) -> None:
        if hasattr(self, "pending_move_asset"):
            asset = self.pending_move_asset
            asset.x = x
            asset.y = y
            del self.pending_move_asset
            self.map.set_editor_mode(False)
            self.engine.load_city(self.engine.city)
            self._refresh()
            return
        if not hasattr(self, "pending_asset_name"):
            self.map.set_editor_mode(False)
            return
        prefix = {"Generator": "g", "Substation": "s", "Consumer": "c"}[self.pending_asset_type]
        existing = [item.id for item in (*self.engine.city.generators, *self.engine.city.substations, *self.engine.city.consumers)]
        index = 1
        while f"{prefix}{index}" in existing:
            index += 1
        asset_id = f"{prefix}{index}"
        if self.pending_asset_type == "Generator":
            self.engine.city.generators.append(Generator(asset_id, self.pending_asset_name, x, y, self.pending_asset_value))
        elif self.pending_asset_type == "Substation":
            self.engine.city.substations.append(Substation(asset_id, self.pending_asset_name, x, y, self.pending_asset_value))
        else:
            self.engine.city.consumers.append(Consumer(asset_id, self.pending_asset_name, x, y, self.pending_asset_value, self.pending_asset_value))
        self.engine.load_city(self.engine.city)
        self.map.set_editor_mode(False)
        del self.pending_asset_name
        self.builder_hint.setText("Builder ready: choose Build Scenario, Add Asset, or Add Power Line from the command bar.")
        self._refresh()

    def _start_line_creation(self) -> None:
        self.controls.builder_mode.setChecked(True)
        self._set_builder_mode(True)
        self._set_builder_tool("connect")


def run_app(city: City) -> int:
    """Start the Qt application."""
    app = QApplication.instance() or QApplication([])
    window = MainWindow(city)
    screen = app.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        width = min(1600, max(900, available.width() - 32))
        height = min(980, max(600, available.height() - 32))
        window.resize(width, height)
        window.move(
            available.x() + max(0, (available.width() - width) // 2),
            available.y() + max(0, (available.height() - height) // 2),
        )
    window.show()
    return app.exec()
