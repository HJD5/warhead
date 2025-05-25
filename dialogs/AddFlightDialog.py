from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
)
import sqlite3
import numpy as np
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from geopy.distance import geodesic
from datetime import datetime

def build_safe_route(route_points, no_fly_zones,
                     min_lat=51.125, max_lat=51.135, min_lon=71.428, max_lon=71.440, grid_size=50):
    if len(route_points) < 2:
        return route_points

    lats = np.linspace(min_lat, max_lat, grid_size)
    lons = np.linspace(min_lon, max_lon, grid_size)
    matrix = np.zeros((grid_size, grid_size), dtype=int)

    def gps_from_idx(i, j):
        return (lats[j], lons[i])

    def idx_from_gps(lat, lon):
        i = int((lon - min_lon) / (max_lon - min_lon) * (grid_size - 1))
        j = int((lat - min_lat) / (max_lat - min_lat) * (grid_size - 1))
        return i, j

    for zone in no_fly_zones:
        for i in range(grid_size):
            for j in range(grid_size):
                p = gps_from_idx(i, j)
                if geodesic(p, zone["center"]).meters < zone["radius"]:
                    matrix[j, i] = 1

    start_idx = idx_from_gps(*route_points[0])
    end_idx = idx_from_gps(*route_points[-1])

    grid = Grid(matrix=matrix.tolist())
    start = grid.node(*start_idx)
    end = grid.node(*end_idx)

    finder = AStarFinder()
    path_idx, _ = finder.find_path(start, end, grid)
    path_gps = [gps_from_idx(i, j) for i, j in path_idx]
    return path_gps if len(path_gps) > 1 else route_points

class AddFlightDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить полёт")
        self.layout = QVBoxLayout(self)

        # --- Выбор дрона ---
        self.layout.addWidget(QLabel("Выберите дрона:"))
        self.drone_combo = QComboBox()
        self.drone_ids = []
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("SELECT id, name FROM drones")
        for drone_id, name in c.fetchall():
            self.drone_combo.addItem(name, drone_id)
            self.drone_ids.append(drone_id)
        conn.close()
        self.layout.addWidget(self.drone_combo)

        # --- Выбор пилота ---
        self.layout.addWidget(QLabel("Выберите пилота:"))
        self.pilot_combo = QComboBox()
        self.pilot_ids = []
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("SELECT id, name FROM pilots")
        for pilot_id, name in c.fetchall():
            self.pilot_combo.addItem(name, pilot_id)
            self.pilot_ids.append(pilot_id)
        conn.close()
        self.layout.addWidget(self.pilot_combo)

        # --- Маршрут ---
        self.layout.addWidget(QLabel("Маршрут (формат: lat1,lon1;lat2,lon2;...):"))
        self.route = QLineEdit()
        self.route.setPlaceholderText("51.128,71.432;51.129,71.433;51.13,71.434")
        self.layout.addWidget(self.route)

        self.btn_save = QPushButton("Сохранить полёт")
        self.btn_save.clicked.connect(self.save_flight)
        self.layout.addWidget(self.btn_save)

    def save_flight(self):
        route_str = self.route.text()
        route_points = []
        try:
            for p in route_str.strip().split(';'):
                lat, lon = map(float, p.strip().split(','))
                route_points.append((lat, lon))
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Проверьте формат маршрута!")
            return

        no_fly_zones = [
            {"center": (51.128, 71.432), "radius": 400},
        ]

        safe_route = build_safe_route(route_points, no_fly_zones)

        if len(safe_route) != len(route_points) or safe_route != route_points:
            QMessageBox.information(self, "Маршрут скорректирован",
                                    "Маршрут был автоматически изменён для обхода запретной зоны!")

        safe_route_str = ';'.join([f"{lat:.6f},{lon:.6f}" for lat, lon in safe_route])
        original_route_str = ';'.join([f"{lat:.6f},{lon:.6f}" for lat, lon in route_points])

        drone_id = self.drone_combo.currentData()
        pilot_id = self.pilot_combo.currentData()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Записываем оба маршрута в базу с датой ---
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO flights (drone_id, pilot_id, route, original_route, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (drone_id, pilot_id, safe_route_str, original_route_str, "ожидание", now))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", f"Полёт успешно добавлен!\nМаршрут:\n{safe_route_str}")
        self.accept()
