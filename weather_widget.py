from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import requests

API_KEY = "156cd342920f5c1815ad71d053409cef"  # твой ключ
LAT, LON = 51.128, 71.432  # координаты для Астаны (пример)
WEATHER_URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=kk"

class WeatherWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.icon = QLabel()
        self.temp = QLabel()
        self.desc = QLabel()
        self.temp.setStyleSheet("color:#00ff5e; font-size:24px; font-weight:bold;")
        self.desc.setStyleSheet("color:#00ff5e; font-size:18px;")
        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.temp)
        self.layout.addWidget(self.desc)
        self.setLayout(self.layout)
        self.setStyleSheet("background: #232c28; border-radius: 12px;")
        self.refresh_weather()
        timer = QTimer(self)
        timer.timeout.connect(self.refresh_weather)
        timer.start(20 * 60 * 1000)  # обновлять каждые 20 минут

    def refresh_weather(self):
        try:
            resp = requests.get(WEATHER_URL)
            if resp.ok:
                data = resp.json()
                icon_code = data["weather"][0]["icon"]
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                pixmap = QPixmap()
                pixmap.loadFromData(requests.get(icon_url).content)
                self.icon.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio))
                self.temp.setText(f"{int(data['main']['temp'])}°C")
                self.desc.setText(data["weather"][0]["description"].capitalize())
        except Exception as e:
            self.temp.setText("--°C")
            self.desc.setText("No connection")
