"""Reference-layout diagnostic panels."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from simulation import get_status


class StatisticsPanel(QWidget):
    """Left-side grid status, key metrics, and vulnerability ranking."""

    asset_selected = pyqtSignal(str)
    why_requested = pyqtSignal()
    prevent_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.status = QLabel()
        self.status.setObjectName("statusCard")
        self.metrics = QLabel()
        self.metrics.setObjectName("secondaryMetrics")
        self.risk_list = QListWidget()
        self.risk_list.setObjectName("riskList")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("GRID STATUS"), 0)
        layout.addWidget(self.status)
        layout.addWidget(QLabel("KEY METRICS"), 0)
        layout.addWidget(self.metrics)
        layout.addWidget(QLabel("MOST VULNERABLE ASSETS"), 0)
        layout.addWidget(self.risk_list, 1)
        self.risk_list.itemClicked.connect(lambda item: self.asset_selected.emit(item.data(256)))

    @staticmethod
    def _asset_label(asset) -> str:
        return getattr(asset, "name", f"Line {asset.id.removeprefix('l')}")

    @staticmethod
    def _clock(seconds: float | None) -> str:
        if seconds is None:
            return "SAFE"
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def update_engine(self, engine) -> None:
        metrics = engine.get_metrics()
        status = get_status(metrics.network_utilisation)
        if status.value == "NORMAL":
            headline, description, color = "STABLE", "Grid operating within safe limits", "#35dcb9"
        elif status.value in {"WARNING", "HIGH"}:
            headline, description, color = "WARNING", "Grid approaching capacity limits", "#ffb332"
        else:
            headline, description, color = "CRITICAL", "Grid operating beyond safe capacity", "#ff4d5f"
        vulnerable = engine.get_vulnerable_assets()
        first_failure = next((eta for _, _, eta in vulnerable if eta is not None), None)
        over_safe = max(0.0, (metrics.network_utilisation - 1.0) * 100)
        capacity_note = (
            f"<span style='color:{color}'>&nbsp;&nbsp;&nbsp;{over_safe:.0f}% over safe capacity</span>"
            if over_safe > 0
            else "<span style='color:#4aa88b'>&nbsp;&nbsp;&nbsp;Within safe capacity</span>"
        )
        self.status.setText(
            f"<span style='color:{color}; font-size:23px; font-weight:700'>[{headline}]</span>"
            f"<br><span style='font-size:12px'>{description}</span>"
            f"<hr><b>Grid load</b><br><span style='font-size:27px'>{metrics.network_utilisation:.0%}</span>"
            f"{capacity_note}"
            f"<br><br><b>Predicted failure</b><br><span style='font-size:21px'>{self._clock(first_failure)}</span>"
            f"<hr><b>{metrics.critical_assets}</b> critical assets   "
            f"<b>{metrics.predicted_failures}</b> predicted failures   "
            f"<b>{metrics.affected_consumers}</b> affected areas"
        )
        self.metrics.setText(
            f"<b>DEMAND</b>  {metrics.total_demand_mw:.0f} MW     "
            f"<b>AVAILABLE CAPACITY</b>  {metrics.available_capacity_mw:.0f} MW     "
            f"<b>GRID LOAD</b>  {metrics.network_utilisation:.0%}<br><br>"
            f"<b>CRITICAL ASSETS</b>  {metrics.critical_assets}     "
            f"<b>PREDICTED FAILURES</b>  {metrics.predicted_failures}     "
            f"<b>AFFECTED AREAS</b>  {metrics.affected_consumers}"
        )
        self.risk_list.clear()
        for asset, value, eta in vulnerable[:5]:
            severity = "CRITICAL" if value > 1 else "WARNING" if value >= .85 else "NORMAL"
            item = QListWidgetItem(
                f"[{severity}]  {self._asset_label(asset)}\n"
                f"   {value:.0%} capacity"
                + (f"   Failure in ~{self._clock(eta)}" if eta else "")
                + f"\n   {asset.id}"
            )
            item.setData(256, asset.id)
            self.risk_list.addItem(item)

    def set_comparison(self, before, after) -> None:
        """Compatibility hook for scenario comparison."""
