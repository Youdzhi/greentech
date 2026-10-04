"""Compact Qt menu bar for LeSauveur commands."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QFileDialog, QMenuBar


class ControlPanel(QMenuBar):
    """Grouped command navbar with consistent native action sizing."""

    scenario_changed = pyqtSignal(object)
    reset_requested = pyqtSignal()
    import_requested = pyqtSignal(str)
    export_requested = pyqtSignal(str)
    theme_requested = pyqtSignal()
    add_asset_requested = pyqtSignal()
    add_line_requested = pyqtSignal()
    engineer_mode_requested = pyqtSignal(bool)
    settings_requested = pyqtSignal()
    information_requested = pyqtSignal(bool)
    builder_mode_requested = pyqtSignal(bool)
    builder_tool_requested = pyqtSignal(str)
    why_requested = pyqtSignal()
    prevent_requested = pyqtSignal()
    help_requested = pyqtSignal()
    simulation_speed_requested = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setNativeMenuBar(False)
        self.setObjectName("commandBar")
        self._build_menus()

    def _action(self, text: str, tooltip: str) -> QAction:
        action = QAction(text, self)
        action.setToolTip(tooltip)
        return action

    def _build_menus(self) -> None:
        file_menu = self.addMenu("File")
        self.import_button = self._action("Import City", "Load a city JSON file")
        self.export_button = self._action("Export City", "Save the current city as JSON")
        file_menu.addAction(self.import_button)
        file_menu.addAction(self.export_button)

        scenario_menu = self.addMenu("Scenario")
        self.scenario = self._action("Build Scenario", "Create a custom scenario")
        scenario_menu.addAction(self.scenario)

        simulation_menu = self.addMenu("Simulation")
        self.start = self._action("Run", "Start the simulation")
        self.pause = self._action("Pause", "Pause the simulation")
        self.reset = self._action("Reset", "Reset simulation state")
        simulation_menu.addAction(self.start)
        simulation_menu.addAction(self.pause)
        simulation_menu.addSeparator()
        simulation_menu.addAction(self.reset)

        map_menu = self.addMenu("Map Builder")
        self.add_asset_button = self._action("Add Asset", "Place a generator, substation, or consumer")
        self.add_line_button = self._action("Add Power Line", "Connect two assets")
        self.select_tool = self._action("Select / Move", "Drag assets to reposition them")
        self.connect_tool = self._action("Connect Assets", "Click two assets to create a power line")
        self.delete_tool = self._action("Delete", "Delete a selected asset or power line")
        for action in (self.select_tool, self.connect_tool, self.delete_tool):
            action.setCheckable(True)
        self.select_tool.setChecked(True)
        self.fit_map = self._action("Fit Map", "Reset map zoom and center")
        map_menu.addAction(self.add_asset_button)
        map_menu.addAction(self.add_line_button)
        map_menu.addSeparator()
        map_menu.addAction(self.select_tool)
        map_menu.addAction(self.connect_tool)
        map_menu.addAction(self.delete_tool)
        map_menu.addAction(self.fit_map)

        view_menu = self.addMenu("View")
        self.theme_button = self._action("Switch Theme", "Switch between dark and light themes")
        self.engineer_mode = self._action("Engineer Mode", "Show technical controls and details")
        self.engineer_mode.setCheckable(True)
        self.info_mode = self._action("Informative Mode", "Show map navigation guidance")
        self.info_mode.setCheckable(True)
        self.builder_mode = self._action("Builder Mode", "Enable direct editing on the map")
        self.builder_mode.setCheckable(True)
        self.view_mode_group = QActionGroup(self)
        self.view_mode_group.setExclusive(True)
        self.view_mode_group.addAction(self.engineer_mode)
        self.view_mode_group.addAction(self.info_mode)
        self.view_mode_group.addAction(self.builder_mode)
        self.settings_button = self._action("Settings and Keybinds", "Configure presentation and shortcuts")
        self.speed_menu = view_menu.addMenu("Speed of simulation")
        self.speed_group = QActionGroup(self)
        self.speed_group.setExclusive(True)
        self.speed_actions = {}
        for step in range(1, 11):
            speed = step / 2
            action = self._action(f"{speed:g}x", f"Run the simulation at {speed:g} times normal speed")
            action.setCheckable(True)
            action.setData(speed)
            self.speed_group.addAction(action)
            self.speed_menu.addAction(action)
            self.speed_actions[speed] = action
        self.speed_actions[1.0].setChecked(True)
        view_menu.addAction(self.theme_button)
        view_menu.addAction(self.engineer_mode)
        view_menu.addAction(self.info_mode)
        view_menu.addAction(self.builder_mode)
        view_menu.addSeparator()
        view_menu.addAction(self.settings_button)

        help_menu = self.addMenu("Help")
        self.why_action = self._action("Why Is the Grid Failing?", "Explain current network stress")
        self.prevent_action = self._action("Prevent the Failure", "Show available prevention paths")
        self.help_action = self._action("How to Use LeSauveur", "Show map controls and product guidance")
        help_menu.addAction(self.why_action)
        help_menu.addAction(self.prevent_action)
        help_menu.addSeparator()
        help_menu.addAction(self.help_action)

        self.scenario.triggered.connect(lambda: self.scenario_changed.emit(None))
        self.import_button.triggered.connect(self._import)
        self.export_button.triggered.connect(self._export)
        self.start.triggered.connect(lambda: self.window().timer.start())
        self.pause.triggered.connect(lambda: self.window().timer.stop())
        self.reset.triggered.connect(self.reset_requested)
        self.theme_button.triggered.connect(self.theme_requested)
        self.add_asset_button.triggered.connect(self.add_asset_requested)
        self.add_line_button.triggered.connect(self.add_line_requested)
        self.builder_mode.toggled.connect(self.builder_mode_requested)
        self.select_tool.triggered.connect(lambda: self._set_tool("select"))
        self.connect_tool.triggered.connect(lambda: self._set_tool("connect"))
        self.delete_tool.triggered.connect(lambda: self._set_tool("delete"))
        self.fit_map.triggered.connect(lambda: self.window().map.reset_view())
        self.engineer_mode.toggled.connect(self.engineer_mode_requested)
        self.info_mode.toggled.connect(self.information_requested)
        self.speed_group.triggered.connect(
            lambda action: self.simulation_speed_requested.emit(float(action.data()))
        )
        self.settings_button.triggered.connect(self.settings_requested)
        self.why_action.triggered.connect(self.why_requested)
        self.prevent_action.triggered.connect(self.prevent_requested)
        self.help_action.triggered.connect(self.help_requested)

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import city", "", "JSON (*.json)")
        if path:
            self.import_requested.emit(path)

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export city", "city.json", "JSON (*.json)")
        if path:
            self.export_requested.emit(path)

    def _set_tool(self, tool: str) -> None:
        self.select_tool.setChecked(tool == "select")
        self.connect_tool.setChecked(tool == "connect")
        self.delete_tool.setChecked(tool == "delete")
        self.builder_tool_requested.emit(tool)
