import os
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QProgressBar)
import cv2
import numpy as np
import torch
import yaml
from models.create_fasterrcnn_model import create_model
from utils.annotations import metall_annotations
from utils.general import set_infer_dir
from utils.transforms import infer_transforms
from testing import collect_all_images, parse_opt


class ImageProcessor(QThread):
    finished = pyqtSignal()

    def __init__(self, device, classes, parent=None):
        super().__init__(parent)
        self.image_path = None
        self.model = None
        self.threshold = None
        self.device = device
        self.classes = classes

    def set_image_path(self, image_path):
        self.image_path = image_path

    def set_model(self, model):
        self.model = model

    def set_threshold(self, threshold):
        self.threshold = threshold

    def run(self):
        if self.image_path is not None and self.model is not None:
            image = cv2.imread(self.image_path)
            orig_image = image.copy()
            # BGR to RGB
            image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2GRAY)
            image = infer_transforms(image)
            # Add batch dimension.
            image = torch.unsqueeze(image, 0)
            with torch.no_grad():
                outputs = self.model(image.to(self.device))
            # Load all detection to CPU for further operations.
            outputs = [{k: v.to('cpu') for k, v in t.items()} for t in outputs]
            COLORS = np.random.uniform(0, 255, size=(len(self.classes), 3))
            orig_image = metall_annotations(outputs, self.threshold, self.classes, COLORS, orig_image)
            self.output_image = orig_image
        else:
            self.output_image = None
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle('Дефектоскопия')

        # Загрузка данных конфигураций
        data_configs = None
        if args['config'] is not None:
            with open(args['config']) as file:
                data_configs = yaml.safe_load(file)
            NUM_CLASSES = data_configs['NC']
            self.CLASSES = data_configs['CLASSES']

        self.DEVICE = args['device']
        self.OUT_DIR = set_infer_dir()

        # Загрузка предварительно обученной модели

        if args['weights'] is None:
            # Если конфигурационный файл по-прежнему отсутствует,
            # то загрузите файл весов для COCO.
            if data_configs is None:
                with open(os.path.join('data_configs', 'test_image.yaml')) as file:
                    data_configs = yaml.safe_load(file)
                NUM_CLASSES = data_configs['NC']
                self.CLASSES = data_configs['CLASSES']
            try:
                build_model = create_model[args['model']]
            except:
                build_model = create_model['fasterrcnn_resnet50_fpn_v2']
            self.model = build_model(num_classes=NUM_CLASSES, coco_model=True)
        # Загрузка весов, если путь указан
        if args['weights'] is not None:
            checkpoint = torch.load(args['weights'], map_location=self.DEVICE)
            # If config file is not given, load from model dictionary.
            if data_configs is None:
                data_configs = True
                NUM_CLASSES = checkpoint['config']['NC']
                self.CLASSES = checkpoint['config']['CLASSES']
            try:
                print('Building from model name arguments...')
                build_model = create_model[str(args['model'])]
            except:
                build_model = create_model[checkpoint['model_name']]
            self.model = build_model(num_classes=NUM_CLASSES, coco_model=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.DEVICE).eval()

        self.threshold = 0.3
        self.input_image = None
        self.output_image = None

        # Создание кнопок
        self.load_button = QPushButton(self, text="Загрузить")
        font = self.load_button.font()
        font.setPointSize(14)
        self.load_button.setFont(font)
        self.load_button.clicked.connect(self.load_image)

        self.process_button = QPushButton(self, text="Обработать")
        font = self.process_button.font()
        font.setPointSize(14)
        self.process_button.setFont(font)
        self.process_button.clicked.connect(self.process_image)

        # Создание QLabel для исходного изображения
        self.input_image_label = QLabel()
        self.input_image_label.setAlignment(Qt.AlignCenter)

        # Создание QLabel для размеченного изображения
        self.output_image_label = QLabel()
        self.output_image_label.setAlignment(Qt.AlignCenter)

        # Создание прогресс-бара
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        # Создание layout и добавление виджетов
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.input_image_label)
        left_layout.addWidget(self.load_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.output_image_label)
        right_layout.addWidget(self.process_button)

        centr_layout = QVBoxLayout()
        centr_layout.addWidget((self.progress_bar))

        main_layout = QHBoxLayout()
        main_layout.setSpacing(150)
        main_layout.setContentsMargins(100, 250, 250, 100)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(centr_layout)
        main_layout.addLayout(right_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

        # стиль кнопок
        self.load_button.setStyleSheet('background-color: green; width: 250px; height: 50px; border-radius: 15px')
        self.process_button.setStyleSheet("background-color: yellow; width: 250px; height: 50px; border-radius: 15px")
        self.progress_bar.setStyleSheet("width: 250px; height: 50px; border-radius: 15px")


    def load_image(self):
        self.file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image', '.', 'Image Files (*.png *.jpg *.jpeg)')
        if self.file_name:
            self.input_image = QImage(self.file_name)
            pixmap = QPixmap.fromImage(self.input_image)
            self.input_image_label.setPixmap(pixmap.scaled(400, 400, aspectRatioMode=Qt.KeepAspectRatio))


    def process_image(self):
        if not self.input_image:
            return

        self.process_button.setEnabled(False)
        self.progress_bar.setValue(0)

        self.image_processor = ImageProcessor(self.DEVICE, self.CLASSES)
        self.image_processor.set_image_path(self.file_name)
        self.image_processor.set_model(self.model)
        self.image_processor.set_threshold(self.threshold)
        self.image_processor.finished.connect(self.update_image)
        self.image_processor.start()

    def update_image(self):
        if self.image_processor.output_image is not None:  # Проверяем, что было получено распознанное изображение
            output_image = self.image_processor.output_image  # Получаем распознанное изображение
            h, w, c = output_image.shape
            q_output_image = QImage(output_image.data, w, h, c * w,
                                    QImage.Format_RGB888)  # Конвертируем изображение из numpy array в QImage
            pixmap = QPixmap.fromImage(q_output_image)
            self.output_image_label.setPixmap(
                pixmap.scaled(400, 400, aspectRatioMode=Qt.KeepAspectRatio))  # Устанавливаем распознанное изображение на QLabel, чтобы отобразить его на форме
        self.process_button.setEnabled(True)  # Включаем кнопку "Process Image"
        self.progress_bar.setValue(100)  # Устанавливаем значение прогресс-бара на 100%
        self.progress_bar.setStyleSheet("width: 250px; height: 50px; border-radius: 15px")

    def closeEvent(self, event):
        if hasattr(self, 'image_processor'):
            self.image_processor.quit()
            self.image_processor.wait()
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow(parse_opt())
    main_window.show()
    sys.exit(app.exec_())
