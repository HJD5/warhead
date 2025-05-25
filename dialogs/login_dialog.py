from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему")
        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.combo.addItems(["Админ", "Оператор"])
        layout.addWidget(QLabel("Выберите роль:"))
        layout.addWidget(self.combo)
        layout.addWidget(QLabel("Пароль:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_input)
        self.btn = QPushButton("Войти")
        self.btn.clicked.connect(self.check_login)
        layout.addWidget(self.btn)
        self.role = None

    def check_login(self):
        role = self.combo.currentText()
        password = self.pass_input.text()
        if (role == "Админ" and password == "admin") or (role == "Оператор" and password == "operator"):
            self.role = role
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
