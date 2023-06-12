# metall_surface

# Реализация метода поиска повреждений и дефектов поверхности изделия на основе сверточной нейронной сети

Для обучения использовались архитектуры Yolov7 и Faster R-CNN

В ветке models представлены процессы обучения обеих моделей
Обучение проходило в Google Colab с использованием GPU для ускорения процесса обучения


## Yolo
Для обучения модели 
### 1 этап. Конирование данных yolo
`!git clone https://github.com/WongKinYiu/yolov7.git       # клонирование
%cd yolov7
!pip install -r requirements.txt      # установка модуля
!wget https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7.pt # загрузить предварительно тренировочных весов`

### 2 этап. 
Создаем в папке yolov7/cfg файл data.yaml, который содержит информацию об изображениях и путях к txt-файлам. Наряду с этим, он также содержит имена классов и количество классов в наборе данных. (рис. 1)
 
![image](https://github.com/ValeriaIvanova/metall_surface/assets/62417917/551641a8-faff-49ef-af75-6bd5c41dcb79)

Рисунок 1 – Файл конфигурации


### 3 этап. Запуск обучения
Необходимо выполнить команду:

`!python train.py --weights yolov7.pt --data "data/data.yaml" --workers 4 --batch-size 32 --img 200 --cfg cfg/training/yolov7.yaml --name yolov7 --epochs 20 --hyp data/hyp.scratch.p5.yaml`
--weights - веса модели
--data - файл конфигурации
--workers - количество ядер 
--img - размер изображения
--cfg - файл конфигурации предобученной модели Yolo
--name - имя папки
--epoch - количество эпох
--hyp - Настройки улучшения данных

### 4 этап. Тестирование модели
Выполняем команду:
`!python test.py --data data/data.yaml --img 200 --batch 32 --conf 0.64 --iou 0.67 --device cpu --weights runs/train/yolov77/weights/best.pt --name yolov7_417_val`

![image](https://github.com/ValeriaIvanova/metall_surface/assets/62417917/df1f4d3c-04f9-4cd3-b63b-f47513ad8daa)
Рисунок 2 - Тестирование модели

## Faster RCNN

- data - папка хранящая данные о файлах
   -   dataset
      - train - данные для обучение
      - test - данные для тестирования
   -   data_config - файлы конфигураций для обучения и тестирования
- models - модели обучения faster r-cnn
- outputs - сохранения обученной модели
- torch_utils  - необходимые утилиты для PyTorch
- utils - пользовательские утилиты


Для обучения модели необходимо выполнить команду:

`!python train.py --model fasterrcnn_resnet50_fpn_v2 --config data_configs/dataset.yaml --epochs 40 --project-name fasterrcnn _dataset --use-train-aug --no-mosaic –batch-size 32 `
--modell: Здесь мы используем faster rcnn_resnet50_fpn_v2, чтобы указать, что мы хотим обучить новую модель Faster RCNN.
--config: Он принимает путь к файлу конфигурации набора данных – data/dataset.yaml
-- epoch: Мы обучаем модель для 40 эпох.
--project-name: Предоставление строкового значения этому аргументу сохранит результаты с этим именем папки внутри results / train.
--batch-size: Количество итераций в одной эпохе, в данном случае – 32.

Результаты обучения (график точности)
![image](https://github.com/ValeriaIvanova/metall_surface/assets/62417917/95f373fb-2409-44ee-9e8e-b3d9785d0266)

Рисунок 3 - График точности

Для тестирования модели необходимо в консоли ввести команду: 

`python testing.py --weights outputs/training/fasterrcnn_dataset/best_model.pth --input data/dataset/test1 --show-image --threshold 0.7`
-- weights - веса задаются на основе обученной нами модели
-- input - указываем путь к данным для теста
-- show-image - показать результат
-- threshold - порог точности определения (распознавания)


Чтобы запустить GUI, необходимо выполнить команду:

`python gui.py --weights outputs/training/fasterrcnn_dataset/best_model.pth --show-image --threshold 0.7`
-- weights - веса задаются на основе обученной нами модели
-- show-image - показать результат
-- threshold - порог точности определения (распознавания)

Результат приведен ниже (рис. 4)

![image](https://github.com/ValeriaIvanova/metall_surface/assets/62417917/8319aa2a-9a62-4ec2-86ea-8d4530d8ed74)
Рисунок 4 - Пример работы приложения

©️Ivanova Valeria, 2023
