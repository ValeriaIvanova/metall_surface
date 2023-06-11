import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QProgressBar, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ImageProcessor(QThread):
    progress_update = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""

    def set_image_path(self, path):
        self.image_path = path

    def run(self):
        for i in range(101):
            self.progress_update.emit(i)
            self.msleep(50)

class DefectoscopyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Дефектоскопия")
        self.setGeometry(200, 200, 1280, 720)

        self.load_button = QPushButton(self)
        self.load_button.setText("Загрузить")
        self.load_button.move(200, 200)
        self.load_button.setFixedSize(200, 50)
        self.load_button.setStyleSheet("background-color: green; border-radius: 25px;")
        self.load_button.clicked.connect(self.load_image)


        self.process_button = QPushButton(self)
        self.process_button.setText("Обработать")
        self.process_button.move(450, 200)
        self.process_button.setFixedSize(200, 50)
        self.process_button.setStyleSheet("background-color: yellow; border-radius: 25px;")
        self.process_button.clicked.connect(self.process_image)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.move(700, 200)
        self.progress_bar.setFixedSize(200, 50)

        self.show_button = QPushButton(self)
        self.show_button.setText("Результат")
        self.show_button.move(900, 200)
        self.show_button.setFixedSize(200, 50)
        self.show_button.setStyleSheet("background-color: orange; border-radius: 25px;")
        self.show_button.clicked.connect(self.show_image)

        self.image_label = QLabel(self)
        self.image_label.move(200, 400)
        self.image_label.setFixedSize(400, 200)

        self.process_label = QLabel(self)
        self.process_label.move(900, 400)
        self.process_label.setFixedSize(400, 200)

        self.image_processor = ImageProcessor()
        self.image_processor.progress_update.connect(self.update_progress_bar)

    def load_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.xpm *.jpg *.bmp *.gif)", options=options)
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio))

    def process_image(self):
        self.image_processor.set_image_path(self.image_path)
        self.image_processor.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def show_image(self):
        pixmap = QPixmap(self.image_path)
        self.process_label.setPixmap(pixmap.scaled(self.process_label.width(), self.process_label.height(), Qt.KeepAspectRatio))
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                   "Images (*.png *.xpm *.jpg *.bmp *.gif)", options=options)
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(
                pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = DefectoscopyGUI()
    gui.show()
    sys.exit(app.exec_())




'''КОД С ВКЛЮЧЕНИЕМ МОДЕЛИ'''
#
# import sys
# from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QLineEdit
# import torch
# import torchvision.transforms as transforms
# import argparse
#
# # загрузка обученной модели
# model = torch.load('model.pth')
#
# # преобразование изображения
# transform = transforms.Compose([
#     transforms.Resize(256),
#     transforms.CenterCrop(224),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
# ])
#
# # класс для обработки изображения
# class ImageProcessor:
#     def __init__(self):
#         self.image = None
#         self.result = None
#
#     # функция для загрузки изображения
#     def load_image(self, filename):
#         self.image = QPixmap(filename)
#
#     # функция для обработки изображения
#     def process_image(self, threshold):
#         if self.image:
#             # обработка изображения
#             image = self.image.toImage()
#             image_tensor = transform(image).unsqueeze(0)
#             with torch.no_grad():
#                 output = model(image_tensor)
#             result = output.argmax(dim=1).item()
#
#             # создание изображения с результатом
#             self.result = QPixmap(self.image.size())
#             self.result.fill(Qt.transparent)
#             painter = QPainter(self.result)
#             painter.drawPixmap(0, 0, self.image)
#             painter.setPen(QPen(Qt.red, 2))
#             painter.drawRect(10, 10, 100, 100)
#             painter.setPen(QPen(Qt.green, 2))
#             painter.drawText(10, 30, 'Класс: {}'.format(result))
#             painter.end()
#
#     # функция для показа результата
#     def show_result(self):
#         if self.result:
#             return self.result
#
# # класс для создания интерфейса
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#
#         # создание кнопок
#         self.load_button = QPushButton(self)
#         self.load_button.setGeometry(10, 10, 100, 30)
#         self.load_button.setStyleSheet('background-color: red; border-radius: 15px;')
#         self.load_button.clicked.connect(self.load_image)
#
#         self.process_button = QPushButton(self)
#         self.process_button.setGeometry(10, 50, 100, 30)
#         self.process_button.setStyleSheet('background-color: yellow; border-radius: 15px;')
#         self.process_button.clicked.connect(self.process_image)
#
#         self.show_button = QPushButton(self)
#         self.show_button.setGeometry(10, 90, 100, 30)
#         self.show_button.setStyleSheet('background-color: green; border-radius: 15px;')
#         self.show_button.clicked.connect(self.show_result)
#
#         # создание полей ввода
#         self.input_edit = QLineEdit(self)
#         self.input_edit.setGeometry(120, 10, 256, 30)
#
#         self.threshold_edit = QLineEdit(self)
#         self.threshold_edit.setGeometry(120, 50, 256, 30)
#
#         # создание изображений
#         self.image_label = QLabel(self)
#         self.image_label.setGeometry(400, 10, 256, 256)
#
#         self.result_label = QLabel(self)
#         self.result_label.setGeometry(700, 10, 256, 256)
#
#         # инициализация переменных
#         self.image_processor = ImageProcessor()
#
#     # функция для загрузки изображения
#     def load_image(self):
#         filename, _ = QFileDialog.getOpenFileName(self, 'Выбрать изображение', '', 'Images (*.png *.xpm *.jpg *.bmp)')
#         if filename:
#             self.input_edit.setText(filename)
#             self.image_processor.load_image(filename)
#             self.image_label.setPixmap(self.image_processor.image)
#
#     # функция для обработки изображения
#     def process_image(self):
#         threshold = float(self.threshold_edit.text())
#         self.image_processor.process_image(threshold)
#         self.result_label.setPixmap(self.image_processor.result)
#
#     # функция для показа результата
#     def show_result(self):
#         self.result_label.setPixmap(self.image_processor.show_result())
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.setGeometry(100, 100, 1000, 300)
#     window.show()
#     sys.exit(app.exec_())
