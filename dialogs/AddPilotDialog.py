from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
import sqlite3

class AddPilotDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить пилота")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Имя пилота:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Контакты:"))
        self.contact_edit = QLineEdit()
        layout.addWidget(self.contact_edit)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_pilot)
        layout.addWidget(btn_save)

    def save_pilot(self):
        name = self.name_edit.text().strip()
        contact = self.contact_edit.text().strip()
        if not name or not contact:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        conn = sqlite3.connect("utm.db")
        c = conn.cursor()
        c.execute("INSERT INTO pilots (name, contact) VALUES (?, ?)", (name, contact))
        conn.commit()
        conn.close()
        self.accept()
