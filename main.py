import sys
import sqlite3
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QComboBox
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer
from map_widget import MapWidget
from dialogs.AddDroneDialog import AddDroneDialog
from dialogs.AddPilotDialog import AddPilotDialog
from dialogs.AddFlightDialog import AddFlightDialog
from dialogs.login_dialog import LoginDialog
from db import init_db
from openpyxl import Workbook

# === ЛОКАЛИЗАЦИЯ ===
LANG = "kk"  # kk = казахский, ru = русский, en = english

def tr(text):
    translations = {
        "kk": {
            "UTM AIRSPACE COMMAND": "UTM ӘУЕ КЕҢІСТІГІН БАСҚАРУ",
            "Weather": "Ауа райы",
            "ID": "ID", "Drone": "Дрон", "Pilot": "Ұшқыш", "Route": "Маршрут", "Status": "Статус", "Date": "Күні",
            "Add Drone": "Дрон қосу", "Add Pilot": "Ұшқыш қосу", "New Flight": "Жаңа рейс", "START": "БАСТАУ",
            "REFRESH": "Жаңарту", "Export": "Экспорт", "Flights history": "Ұшулар тарихы",
            "DRONES": "ДРОНДАР", "PILOTS": "ҰШҚЫШТАР", "FLIGHTS": "ҰШУЛАР", "ACTIVE": "БЕЛСЕНДІ ҰШУЛАР",
            "Logged in as": "Кіру: "
        },
        "ru": {
            "UTM AIRSPACE COMMAND": "UTM УПРАВЛЕНИЕ ВОЗДУШНЫМ ПРОСТРАНСТВОМ",
            "Weather": "Погода",
            "ID": "ID", "Drone": "Дрон", "Pilot": "Пилот", "Route": "Маршрут", "Status": "Статус", "Date": "Дата",
            "Add Drone": "Добавить дрона", "Add Pilot": "Добавить пилота", "New Flight": "Новый полёт", "START": "СТАРТ",
            "REFRESH": "Обновить", "Export": "Экспорт", "Flights history": "История полётов",
            "DRONES": "ДРОНОВ", "PILOTS": "ПИЛОТОВ", "FLIGHTS": "ПОЛЁТОВ", "ACTIVE": "АКТИВНЫХ",
            "Logged in as": "Вы вошли как: "
        },
        "en": {
            "UTM AIRSPACE COMMAND": "UTM AIRSPACE COMMAND",
            "Weather": "Weather",
            "ID": "ID", "Drone": "Drone", "Pilot": "Pilot", "Route": "Route", "Status": "Status", "Date": "Date",
            "Add Drone": "Add Drone", "Add Pilot": "Add Pilot", "New Flight": "New Flight", "START": "START",
            "REFRESH": "REFRESH", "Export": "Export", "Flights history": "Flights history",
            "DRONES": "DRONES", "PILOTS": "PILOTS", "FLIGHTS": "FLIGHTS", "ACTIVE": "ACTIVE FLIGHTS",
            "Logged in as": "Logged in as: "
        }
    }
    return translations.get(LANG, {}).get(text, text)

# === Переводы погодных описаний ===
WEATHER_TRANSLATIONS = {
    "clear sky":    {"kk": "Ашық аспан",   "ru": "Ясно",         "en": "Clear sky"},
    "few clouds":   {"kk": "Аздаған бұлт", "ru": "Малооблачно",  "en": "Few clouds"},
    "scattered clouds": {"kk": "Бөлшектенген бұлт", "ru": "Рассеянные облака", "en": "Scattered clouds"},
    "broken clouds":    {"kk": "Бұлтты",    "ru": "Облачно",      "en": "Broken clouds"},
    "shower rain":  {"kk": "Күшті жаңбыр", "ru": "Ливень",       "en": "Shower rain"},
    "rain":         {"kk": "Жаңбыр",       "ru": "Дождь",        "en": "Rain"},
    "thunderstorm": {"kk": "Найзағай",     "ru": "Гроза",        "en": "Thunderstorm"},
    "snow":         {"kk": "Қар",          "ru": "Снег",         "en": "Snow"},
    "mist":         {"kk": "Тұман",        "ru": "Туман",        "en": "Mist"},
}

# === ПОГОДА ===
def get_weather(lat=51.128, lon=71.432, lang=LANG):
    API_KEY = "156cd342920f5c1815ad71d053409cef"
    # Для ru и en — напрямую, для kk вытаскиваем en и переводим вручную
    real_lang = lang if lang in ("ru", "en") else "en"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang={real_lang}"
    try:
        res = requests.get(url, timeout=6)
        data = res.json()
        temp = data["main"]["temp"]
        desc_api = data["weather"][0]["description"].lower()
        wind = data["wind"]["speed"]
        # Трёхязычный вывод
        if lang == "kk":
            desc = WEATHER_TRANSLATIONS.get(desc_api, {}).get("kk", desc_api.capitalize())
            return f"🌤 {desc}, {temp:.1f}°C, жел: {wind} м/с"
        elif lang == "ru":
            desc = WEATHER_TRANSLATIONS.get(desc_api, {}).get("ru", desc_api.capitalize())
            return f"🌤 {desc}, {temp:.1f}°C, вет: {wind} м/с"
        else:
            desc = WEATHER_TRANSLATIONS.get(desc_api, {}).get("en", desc_api.capitalize())
            return f"🌤 {desc}, {temp:.1f}°C, wind: {wind} m/s"
    except Exception as e:
        return {"kk": "Ауа райы: жоқ", "ru": "Погода: нет данных", "en": "Weather: no data"}.get(lang, "Weather: error")

class MainWindow(QMainWindow):
    def __init__(self, role="Оператор"):
        super().__init__()
        self.role = role
        self.setWindowTitle("UTM AIRSPACE OPERATIONS — Kazakhtelecom & DECENTRATHON")
        self.setGeometry(60, 60, 1500, 1000)
        self.setStyleSheet("QMainWindow { background-color: #151a1b; }")
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # HEADER
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap("resources/drone_icon_transparent.png").scaled(108, 108, Qt.KeepAspectRatio))
        logo.setFixedSize(140, 140)
        title = QLabel(tr("UTM AIRSPACE COMMAND"))
        title.setFont(QFont("Consolas", 36, QFont.Bold))
        title.setStyleSheet("color:#00ff5e; letter-spacing: 4px;")
        kazakhtelecom_logo = QLabel()
        kazakhtelecom_logo.setPixmap(QPixmap("resources/Казахтелеком.png").scaled(200, 68, Qt.KeepAspectRatio))
        decentrathon_logo = QLabel()
        decentrathon_logo.setPixmap(QPixmap("resources/DECENTRATHON.png").scaled(240, 76, Qt.KeepAspectRatio))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Қазақша", "Русский", "English"])
        self.lang_combo.setCurrentIndex({"kk": 0, "ru": 1, "en": 2}[LANG])
        self.lang_combo.setFixedWidth(120)
        self.lang_combo.currentIndexChanged.connect(self.change_lang)
        header.addWidget(logo)
        header.addSpacing(32)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(kazakhtelecom_logo)
        header.addSpacing(16)
        header.addWidget(decentrathon_logo)
        header.addSpacing(16)
        header.addWidget(self.lang_combo)
        self.main_layout.addLayout(header)

        # ПОГОДА
        self.weather_label = QLabel()
        self.weather_label.setFont(QFont("Consolas", 18, QFont.Bold))
        self.weather_label.setStyleSheet("color:#6ad5ff; background:#161a25; border-radius:10px; padding:8px 24px;")
        self.weather_label.setFixedHeight(48)
        self.main_layout.addWidget(self.weather_label)
        self.update_weather()

        # Роль
        self.role_label = QLabel(f"{tr('Logged in as')}{self.role}")
        self.role_label.setFont(QFont("Consolas", 14, QFont.Bold))
        self.role_label.setStyleSheet("color: #00ff5e; padding: 6px;")
        self.main_layout.addWidget(self.role_label)

        # Динамическая статистика
        self.dashboard = QHBoxLayout()
        self.dashboard.setSpacing(36)
        self.font = QFont("Consolas", 18, QFont.Bold)
        self.stat_style = """
            QLabel {
                background-color: #1c2421;
                color: #00ff5e;
                border: 2px solid #008c45;
                border-radius: 10px;
                padding: 18px 48px;
                font-size: 23px;
                letter-spacing: 2px;
            }
        """
        self.stat_drones = QLabel()
        self.stat_pilots = QLabel()
        self.stat_flights = QLabel()
        self.stat_active = QLabel()
        for stat in (self.stat_drones, self.stat_pilots, self.stat_flights, self.stat_active):
            stat.setFont(self.font)
            stat.setStyleSheet(self.stat_style)
            self.dashboard.addWidget(stat)
        self.dashboard.addStretch()
        self.main_layout.addLayout(self.dashboard)

        # КАРТА
        self.map_tab = MapWidget()
        self.map_tab.setMinimumHeight(500)
        self.main_layout.addWidget(self.map_tab, stretch=4)

        # Таблица + Экспорт
        row = QHBoxLayout()
        self.history_label = QLabel("<b>"+tr("Flights history")+"</b>", alignment=Qt.AlignLeft)
        row.addWidget(self.history_label, stretch=8)
        self.export_btn = QPushButton(tr("Export"))
        self.export_btn.setFont(QFont("Consolas", 13, QFont.Bold))
        self.export_btn.setStyleSheet("background:#00ff5e; color:#151a1b; border-radius:10px; padding:12px 34px; font-size:17px;")
        self.export_btn.clicked.connect(self.export_excel)
        row.addWidget(self.export_btn, stretch=2)
        row.addStretch()
        self.main_layout.addLayout(row, stretch=0)

        # История полётов (таблица)
        self.flights_table = QTableWidget()
        self.flights_table.setColumnCount(6)
        self.flights_table.setHorizontalHeaderLabels(
            [tr("ID"), tr("Drone"), tr("Pilot"), tr("Route"), tr("Status"), tr("Date")])
        self.flights_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flights_table.setMinimumHeight(210)
        self.flights_table.setStyleSheet("""
            QTableWidget { background-color: #202b22; color: #fff; font-size:16px; }
            QHeaderView::section { background:#232c28; color:#00ff5e; font-weight:bold; }
        """)
        self.main_layout.addWidget(self.flights_table, stretch=2)

        # ПАНЕЛЬ УПРАВЛЕНИЯ
        panel = QWidget()
        panel_layout = QHBoxLayout(panel)
        panel_layout.setSpacing(40)
        panel.setStyleSheet("""
            QWidget {
                background-color: #232c28;
                border-radius: 18px;
                border: 2px solid #00ff5e55;
            }
        """)
        def style_btn(btn, bg="#00ff5e"):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: #161c1d;
                    border-radius: 16px;
                    padding: 18px 48px;
                    font-size: 22px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-weight: bold;
                    border: 2px solid #008c45;
                }}
                QPushButton:hover {{
                    background-color: #005aff;
                    color: #fafafa;
                    border: 2px solid #ffffff;
                }}
            """)
            btn.setFont(QFont("Consolas", 17, QFont.Bold))
            btn.setMinimumWidth(190)
            btn.setMinimumHeight(58)
        self.btn_add_drone = QPushButton(tr("Add Drone"))
        self.btn_add_pilot = QPushButton(tr("Add Pilot"))
        self.btn_add_flight = QPushButton(tr("New Flight"))
        btn_start = QPushButton(tr("START"))
        btn_refresh = QPushButton(tr("REFRESH"))
        style_btn(self.btn_add_drone, "#00ff5e")
        style_btn(self.btn_add_pilot, "#005aff")
        style_btn(self.btn_add_flight, "#ffea00")
        style_btn(btn_start, "#ff3c00")
        style_btn(btn_refresh, "#fff")
        self.btn_add_drone.clicked.connect(self.add_drone)
        self.btn_add_pilot.clicked.connect(self.add_pilot)
        self.btn_add_flight.clicked.connect(self.add_flight)
        btn_start.clicked.connect(self.map_tab.start_flight)
        btn_refresh.clicked.connect(self.refresh_all)
        panel_layout.addWidget(self.btn_add_drone)
        panel_layout.addWidget(self.btn_add_pilot)
        panel_layout.addWidget(self.btn_add_flight)
        panel_layout.addWidget(btn_start)
        panel_layout.addWidget(btn_refresh)
        panel_layout.addStretch()
        self.main_layout.addWidget(panel, stretch=0)
        if self.role == "Оператор":
            self.btn_add_drone.setEnabled(False)
            self.btn_add_pilot.setEnabled(False)
            self.btn_add_flight.setEnabled(False)
        self.setCentralWidget(main_widget)
        self.refresh_stats()
        self.refresh_flights_table()

        # Таймер обновления погоды (каждые 15 мин)
        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.update_weather)
        self.weather_timer.start(15 * 60 * 1000)

    def change_lang(self, idx):
        global LANG
        LANG = {0: "kk", 1: "ru", 2: "en"}[idx]
        self.retranslate_ui()
        self.update_weather()

    def retranslate_ui(self):
        self.setWindowTitle("UTM AIRSPACE OPERATIONS — Kazakhtelecom & DECENTRATHON")
        self.role_label.setText(f"{tr('Logged in as')}{self.role}")
        self.history_label.setText("<b>"+tr("Flights history")+"</b>")
        self.export_btn.setText(tr("Export"))
        self.btn_add_drone.setText(tr("Add Drone"))
        self.btn_add_pilot.setText(tr("Add Pilot"))
        self.btn_add_flight.setText(tr("New Flight"))
        self.flights_table.setHorizontalHeaderLabels(
            [tr("ID"), tr("Drone"), tr("Pilot"), tr("Route"), tr("Status"), tr("Date")])
        self.refresh_stats()
        # Можно обновить другие части интерфейса если понадобится

    def update_weather(self):
        self.weather_label.setText(get_weather(lat=51.128, lon=71.432, lang=LANG))

    def get_stats(self):
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM drones")
        drones = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM pilots")
        pilots = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM flights")
        flights = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM flights WHERE status='active'")
        active = c.fetchone()[0]
        conn.close()
        return drones, pilots, flights, active

    def refresh_stats(self):
        drones, pilots, flights, active = self.get_stats()
        self.stat_drones.setText(f"{tr('DRONES')}: {drones}")
        self.stat_pilots.setText(f"{tr('PILOTS')}: {pilots}")
        self.stat_flights.setText(f"{tr('FLIGHTS')}: {flights}")
        self.stat_active.setText(f"{tr('ACTIVE')}: {active}")

    def refresh_flights_table(self):
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        try:
            c.execute("SELECT id, drone_id, pilot_id, route, status, created_at FROM flights ORDER BY id DESC LIMIT 20")
            rows = c.fetchall()
        except sqlite3.OperationalError:
            c.execute("SELECT id, drone_id, pilot_id, route, status FROM flights ORDER BY id DESC LIMIT 20")
            rows = [row + ("",) for row in c.fetchall()]
        drones_dict = {}
        pilots_dict = {}
        c.execute("SELECT id, name FROM drones")
        for id_, name in c.fetchall():
            drones_dict[id_] = name
        c.execute("SELECT id, name FROM pilots")
        for id_, name in c.fetchall():
            pilots_dict[id_] = name
        conn.close()
        self.flights_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            id_, drone_id, pilot_id, route, status, created_at = row
            self.flights_table.setItem(row_idx, 0, QTableWidgetItem(str(id_)))
            self.flights_table.setItem(row_idx, 1, QTableWidgetItem(drones_dict.get(drone_id, str(drone_id))))
            self.flights_table.setItem(row_idx, 2, QTableWidgetItem(pilots_dict.get(pilot_id, str(pilot_id))))
            self.flights_table.setItem(row_idx, 3, QTableWidgetItem(route or ""))
            self.flights_table.setItem(row_idx, 4, QTableWidgetItem(status or ""))
            self.flights_table.setItem(row_idx, 5, QTableWidgetItem(created_at or ""))

    def refresh_all(self):
        self.map_tab.refresh_routes()
        self.refresh_stats()
        self.refresh_flights_table()

    def add_drone(self):
        dialog = AddDroneDialog()
        dialog.exec_()
        self.refresh_stats()

    def add_pilot(self):
        dialog = AddPilotDialog()
        dialog.exec_()
        self.refresh_stats()

    def add_flight(self):
        dialog = AddFlightDialog()
        dialog.exec_()
        self.refresh_stats()
        self.refresh_flights_table()

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как Excel", "flights.xlsx", "Excel files (*.xlsx)")
        if not path:
            return
        wb = Workbook()
        ws = wb.active
        ws.append([tr("ID"), tr("Drone"), tr("Pilot"), tr("Route"), tr("Status"), tr("Date")])
        # Экспорт с именами дрона и пилота из базы
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        try:
            c.execute("SELECT id, drone_id, pilot_id, route, status, created_at FROM flights ORDER BY id DESC LIMIT 20")
            rows = c.fetchall()
        except sqlite3.OperationalError:
            c.execute("SELECT id, drone_id, pilot_id, route, status FROM flights ORDER BY id DESC LIMIT 20")
            rows = [row + ("",) for row in c.fetchall()]
        drones_dict = {}
        pilots_dict = {}
        c.execute("SELECT id, name FROM drones")
        for id_, name in c.fetchall():
            drones_dict[id_] = name
        c.execute("SELECT id, name FROM pilots")
        for id_, name in c.fetchall():
            pilots_dict[id_] = name
        conn.close()
        for row in rows:
            id_, drone_id, pilot_id, route, status, created_at = row
            drone_name = drones_dict.get(drone_id, str(drone_id))
            pilot_name = pilots_dict.get(pilot_id, str(pilot_id))
            ws.append([id_, drone_name, pilot_name, route or "", status or "", created_at or ""])
        wb.save(path)

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    login = LoginDialog()
    if not login.exec_():
        sys.exit(0)
    role = login.role
    win = MainWindow(role=role)
    win.show()
    sys.exit(app.exec_())
