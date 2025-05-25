from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox
from db import add_drone_to_db, add_pilot_to_db, add_flight_to_db, get_all_drones, get_all_pilots

class AddDroneDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить дрона")
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.model = QLineEdit()
        self.serial = QLineEdit()
        layout.addRow("Название", self.name)
        layout.addRow("Модель", self.model)
        layout.addRow("Серийный номер", self.serial)
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save_drone)
        layout.addWidget(btn)

    def save_drone(self):
        add_drone_to_db(self.name.text(), self.model.text(), self.serial.text())
        self.accept()

class AddPilotDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить пилота")
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.contacts = QLineEdit()
        layout.addRow("Имя", self.name)
        layout.addRow("Контакты", self.contacts)
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save_pilot)
        layout.addWidget(btn)

    def save_pilot(self):
        add_pilot_to_db(self.name.text(), self.contacts.text())
        self.accept()

class AddFlightDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить заявку")
        layout = QFormLayout(self)
        # Дроны
        self.drone_box = QComboBox()
        drones = get_all_drones()
        for d in drones:
            self.drone_box.addItem(f"{d[1]} (id {d[0]})", d[0])
        # Пилоты
        self.pilot_box = QComboBox()
        pilots = get_all_pilots()
        for p in pilots:
            self.pilot_box.addItem(f"{p[1]} (id {p[0]})", p[0])
        self.route = QLineEdit("51.134,71.428;51.134,71.440;51.132,71.445")
        layout.addRow("Дрон", self.drone_box)
        layout.addRow("Пилот", self.pilot_box)
        layout.addRow("Маршрут (lat,lon;...)", self.route)
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save_flight)
        layout.addWidget(btn)

    def save_flight(self):
        drone_id = self.drone_box.currentData()
        pilot_id = self.pilot_box.currentData()
        add_flight_to_db(drone_id, pilot_id, self.route.text())
        self.accept()
