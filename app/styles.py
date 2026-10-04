"""Reference-inspired control-room theme."""

THEMES = {
    "dark": """
    * { font-family: Segoe UI; }
    QMainWindow, QWidget { background: #03111a; color: #d8e7ef; }
    QLabel { color: #d8e7ef; }
    QLabel#brand { color: #f4fbff; font-size: 27px; font-weight: 700; letter-spacing: 1px; }
    QLabel#tagline { color: #eff8fb; font-size: 13px; }
    QLabel#subtitle { color: #7b9eb0; font-size: 12px; }
    QLabel#modeIndicator { color: #527786; font-size: 10px; font-weight: 700; letter-spacing: 1px; padding-right: 4px; }
    QLabel#sectionTitle { color: #a9c8d5; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
    QLabel#statusCard { background: #120e19; border: 1px solid #7a2536; border-radius: 6px; padding: 14px; }
    QLabel#secondaryMetrics, QLabel#comparison { background: #061a25; border: 1px solid #0c3b4d; border-radius: 6px; padding: 10px; }
    QLabel#panelTitle { color: #69efd0; font-size: 13px; font-weight: 700; }
    QLabel#resultCritical { background: #24101a; border: 1px solid #7a2536; border-radius: 6px; padding: 11px; color: #ff5a64; font-weight: 700; }
    QLabel#resultNormal { background: #071e20; border: 1px solid #0b5b59; border-radius: 6px; padding: 11px; color: #55e1c1; font-weight: 700; }
    QGroupBox { border: 1px solid #0c3b4d; border-radius: 6px; margin-top: 8px; padding: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #83aabb; }
    QPushButton { background: #071d29; color: #cce8ef; border: 1px solid #14506a; border-radius: 5px; padding: 8px 12px; }
    QPushButton:hover { background: #0b3041; border-color: #35dcb9; }
    QPushButton#primary { background: #38e0bd; color: #03111a; border: none; font-weight: 700; }
    QPushButton#primary:hover { background: #63f0d1; }
    QPushButton#danger { color: #ff727a; border-color: #8b2f41; }
    QMenuBar#commandBar { background: #061a25; border: 1px solid #0c3b4d; border-radius: 5px; padding: 2px; }
    QMenuBar#commandBar::item { background: transparent; color: #cce8ef; padding: 7px 12px; margin: 1px; }
    QMenuBar#commandBar::item:selected, QMenuBar#commandBar::item:pressed { background: #0b3041; color: #69efd0; border-radius: 3px; }
    QMenu { background: #071d29; color: #d8e7ef; border: 1px solid #14506a; padding: 4px; }
    QMenu::item { padding: 7px 28px 7px 12px; }
    QMenu::item:selected { background: #0b3041; color: #69efd0; }
    QMenu::item:checked { background: #123c48; color: #69efd0; font-weight: 700; }
    QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox { background: #061a25; color: #d8e7ef; border: 1px solid #14506a; border-radius: 4px; padding: 7px; }
    QListWidget, QTextEdit { background: #04151f; color: #d8e7ef; border: 1px solid #0c3b4d; border-radius: 6px; }
    QListWidget#riskList { padding: 4px; }
    QListWidget::item { border-bottom: 1px solid #0c3040; padding: 7px; }
    QListWidget::item:selected { background: #102d3b; border-left: 3px solid #38e0bd; }
    QCheckBox { color: #9ab9c6; }
    QGraphicsView { border: 1px solid #0c3b4d; border-radius: 6px; background: #03141d; }
    QScrollBar:vertical { background: #061a25; width: 8px; }
    QScrollBar::handle:vertical { background: #185069; border-radius: 4px; }
    """,
    "light": """
    * { font-family: Segoe UI; }
    QMainWindow, QWidget { background: #f4f7f8; color: #23343d; }
    QLabel { color: #23343d; }
    QLabel#brand { color: #102832; font-size: 27px; font-weight: 700; }
    QLabel#tagline { color: #1d3946; font-size: 13px; }
    QLabel#subtitle { color: #59727d; font-size: 12px; }
    QLabel#modeIndicator { color: #719099; font-size: 10px; font-weight: 700; letter-spacing: 1px; padding-right: 4px; }
    QLabel#sectionTitle { color: #385b68; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
    QLabel#statusCard { background: #fff8f8; border: 1px solid #c94d5a; border-radius: 6px; padding: 14px; }
    QLabel#secondaryMetrics, QLabel#comparison { background: #ffffff; border: 1px solid #bfd0d6; border-radius: 6px; padding: 10px; }
    QLabel#panelTitle { color: #075c45; font-size: 13px; font-weight: 700; }
    QLabel#resultCritical { background: #fff1f2; border: 1px solid #c94d5a; border-radius: 6px; padding: 11px; color: #b52235; font-weight: 700; }
    QLabel#resultNormal { background: #eafaf7; border: 1px solid #54bca7; border-radius: 6px; padding: 11px; color: #087b69; font-weight: 700; }
    QGroupBox { border: 1px solid #bfd0d6; border-radius: 6px; margin-top: 8px; padding: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #59727d; }
    QPushButton { background: #ffffff; color: #23343d; border: 1px solid #9db6bf; border-radius: 5px; padding: 8px 12px; }
    QPushButton:hover { background: #e5f1f0; border-color: #075c45; }
    QPushButton#primary { background: #075c45; color: #ffffff; border: none; font-weight: 700; }
    QPushButton#danger { color: #b52235; border-color: #c94d5a; }
    QMenuBar#commandBar { background: #ffffff; border: 1px solid #9db6bf; border-radius: 5px; padding: 2px; }
    QMenuBar#commandBar::item { background: transparent; color: #23343d; padding: 7px 12px; margin: 1px; }
    QMenuBar#commandBar::item:selected, QMenuBar#commandBar::item:pressed { background: #dcebe7; color: #075c45; border-radius: 3px; }
    QMenu { background: #ffffff; color: #23343d; border: 1px solid #9db6bf; padding: 4px; }
    QMenu::item { padding: 7px 28px 7px 12px; }
    QMenu::item:selected { background: #dcebe7; color: #075c45; }
    QMenu::item:checked { background: #cfe5dc; color: #075c45; font-weight: 700; }
    QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox { background: #ffffff; color: #23343d; border: 1px solid #9db6bf; border-radius: 4px; padding: 7px; }
    QListWidget, QTextEdit { background: #ffffff; color: #23343d; border: 1px solid #bfd0d6; border-radius: 6px; }
    QGraphicsView { border: 1px solid #bfd0d6; border-radius: 6px; background: #eaf2f3; }
    """,
}
