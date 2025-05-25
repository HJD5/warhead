from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
import sqlite3

class AddDroneDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить дрона")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Имя дрона:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Модель:"))
        self.model_edit = QLineEdit()
        layout.addWidget(self.model_edit)

        layout.addWidget(QLabel("Серийный номер:"))
        self.serial_edit = QLineEdit()
        layout.addWidget(self.serial_edit)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_drone)
        layout.addWidget(btn_save)

    def save_drone(self):
        name = self.name_edit.text().strip()
        model = self.model_edit.text().strip()
        serial = self.serial_edit.text().strip()
        if not name or not model or not serial:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("INSERT INTO drones (name, model, serial) VALUES (?, ?, ?)", (name, model, serial))
        conn.commit()
        conn.close()
        self.accept()
