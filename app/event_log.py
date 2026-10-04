"""Compact simulation timeline."""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EventLog(QWidget):
    """Timeline card matching the reference right rail."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.body = QLabel()
        self.body.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.addWidget(self.body)
        self.engineer_mode = False

    def set_engineer_mode(self, enabled: bool) -> None:
        self.engineer_mode = enabled

    def update_events(self, events) -> None:
        if not events:
            self.body.setText("00:00    Normal operation")
            return
        rows = []
        for event in events[-8:]:
            marker = "[FAIL]" if "FAILED" in event.reason.upper() else "[WARN]"
            rows.append(f"{event.timestamp:05.0f}s    {marker}  {event.reason}")
        self.body.setText("\n".join(rows))
