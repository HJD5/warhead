from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWidgets import QVBoxLayout, QWidget
import folium
import os
import sqlite3
from math import radians, cos, sin, sqrt, atan2

D_COLORS = ['blue', 'green', 'purple', 'orange', 'black', 'cadetblue']

class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()
        self.routes_info = self.load_last_routes(limit=5)
        self.smooth_routes = [self.interpolate_route(info['points'], steps=12) for info in self.routes_info]
        self.current_points = [0 for _ in self.routes_info]
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_drones)
        self.alert_shown = False  # Флаг для алерта
        layout = QVBoxLayout(self)
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.init_map()

    def load_last_routes(self, limit=5):
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("SELECT drone_id, pilot_id, route, original_route FROM flights ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        info = []
        for idx, row in enumerate(rows):
            drone_id, pilot_id, route, original_route = row
            drone_name, pilot_name = "", ""
            if drone_id:
                c.execute("SELECT name FROM drones WHERE id = ?", (drone_id,))
                dr = c.fetchone()
                if dr: drone_name = dr[0]
            if pilot_id:
                c.execute("SELECT name FROM pilots WHERE id = ?", (pilot_id,))
                pl = c.fetchone()
                if pl: pilot_name = pl[0]
            points = []
            if route:
                for pair in route.split(';'):
                    lat, lon = map(float, pair.split(','))
                    points.append([lat, lon])
            original_points = []
            if original_route:
                for pair in original_route.split(';'):
                    lat, lon = map(float, pair.split(','))
                    original_points.append([lat, lon])
            info.append({'points': points, 'drone_name': drone_name, 'pilot_name': pilot_name, 'original_points': original_points})
        conn.close()
        return info

    def interpolate_route(self, points, steps=10):
        if not points or len(points) < 2:
            return points
        result = []
        for i in range(len(points)-1):
            start, end = points[i], points[i+1]
            result.append(start)
            for j in range(1, steps):
                lat = start[0] + (end[0] - start[0]) * j / steps
                lon = start[1] + (end[1] - start[1]) * j / steps
                result.append([lat, lon])
        result.append(points[-1])
        return result

    def refresh_routes(self):
        self.routes_info = self.load_last_routes(limit=5)
        self.smooth_routes = [self.interpolate_route(info['points'], steps=12) for info in self.routes_info]
        self.current_points = [0 for _ in self.routes_info]
        # self.alert_shown = False  # Не сбрасываем здесь!
        self.init_map()

    def init_map(self):
        m = folium.Map(location=[51.128, 71.432], zoom_start=14)
        nfz_center = [51.128, 71.432]
        nfz_radius = 400
        folium.Circle(
            radius=nfz_radius,
            location=nfz_center,
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
        icon_path = os.path.abspath("resources/drone_icon_transparent.png")
        # --- используем self.alert_shown, а не alert_shown локально
        for idx, info in enumerate(self.routes_info):
            smooth_points = self.interpolate_route(info['points'], steps=12)
            color = D_COLORS[idx % len(D_COLORS)]

            # Старый маршрут (пунктир)
            if info.get('original_points') and info['original_points'] and info['original_points'] != info['points']:
                folium.PolyLine(
                    info['original_points'],
                    color="red",
                    weight=3,
                    opacity=0.7,
                    dash_array='8'
                ).add_to(m)

            # Новый маршрут (жирная линия)
            if info['points']:
                folium.PolyLine(
                    info['points'],
                    color=color,
                    weight=5,
                    opacity=0.95
                ).add_to(m)
                cur_idx = min(self.current_points[idx], len(smooth_points)-1)
                popup_text = f"Дрон: {info['drone_name'] or 'Без имени'}<br>Пилот: {info['pilot_name'] or 'Без имени'}"
                folium.Marker(
                    location=smooth_points[cur_idx],
                    popup=popup_text,
                    icon=folium.CustomIcon(icon_path, icon_size=(40, 40))
                ).add_to(m)
                # ---- Показываем алерт только один раз за запуск анимации ----
                if not self.alert_shown and self.check_no_fly_zone(info['points'], nfz_center, nfz_radius):
                    m.get_root().html.add_child(
                        folium.Element(
                            f'<script>alert("Маршрут дрона {info["drone_name"] or idx+1} входит в запретную зону!");</script>'
                        )
                    )
                    self.alert_shown = True

        m.save("resources/map.html")
        self.web_view.load(QUrl.fromLocalFile(os.path.abspath("resources/map.html")))

    def start_flight(self):
        self.current_points = [0 for _ in self.routes_info]
        self.alert_shown = False  # сбрасываем при старте анимации!
        self.timer.start(100)

    def move_drones(self):
        changed = False
        for i, smooth_points in enumerate(self.smooth_routes):
            if self.current_points[i] < len(smooth_points) - 1:
                self.current_points[i] += 1
                changed = True
        self.init_map()
        if not changed:
            self.timer.stop()

    def check_no_fly_zone(self, points, center, radius_m):
        for lat, lon in points:
            if self.haversine(lat, lon, center[0], center[1]) < radius_m:
                return True
        return False

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2-lat1)
        dlambda = radians(lon2-lon1)
        a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
        return 2*R*atan2(sqrt(a), sqrt(1 - a))
