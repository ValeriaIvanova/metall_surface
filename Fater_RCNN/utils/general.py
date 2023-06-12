import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
import os

plt.style.use('ggplot')

# этот класс отслеживает значения потерь при обучении и проверке
# и помогает получить среднее значение для каждой эпохи
class Averager:
    def __init__(self):
        self.current_total = 0.0
        self.iterations = 0.0
        
    def send(self, value):
        self.current_total += value
        self.iterations += 1
    
    @property
    def value(self):
        if self.iterations == 0:
            return 0
        else:
            return 1.0 * self.current_total / self.iterations
    
    def reset(self):
        self.current_total = 0.0
        self.iterations = 0.0

class SaveBestModel:
    """
    Class to save the best model while training. If the current epoch's 
    validation mAP @0.5:0.95 IoU higher than the previous highest, then save the
    model state.
    Класс для сохранения лучшей модели во время тренировки. Показатели
    текущей эпохи на 0,5:0,95 IoU выше, чем предыдущее максимальное значение, то сохранение состояния
    модели.
    """
    def __init__(
        self, best_valid_map=float(0)
    ):
        self.best_valid_map = best_valid_map
        
    def __call__(
        self, 
        model, 
        current_valid_map, 
        epoch, 
        OUT_DIR,
        config,
        model_name
    ):
        if current_valid_map > self.best_valid_map:
            self.best_valid_map = current_valid_map
            print(f"\nBEST VALIDATION mAP: {self.best_valid_map}")
            print(f"\nSAVING BEST MODEL FOR EPOCH: {epoch+1}\n")
            torch.save({
                'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'config': config,
                'model_name': model_name
                }, f"{OUT_DIR}/best_model.pth")

def show_tranformed_image(train_loader, device, classes, colors):
    """
    Функция показывает преобразованные изображения из `train_loader`.
    Помогает проверить, соответствуют ли обработанные изображения с соответствующими -
    верны надписи или нет.
    
    """
    if len(train_loader) > 0:
        for i in range(2):
            images, targets = next(iter(train_loader))
            images = list(image.to(device) for image in images)
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            boxes = targets[i]['boxes'].cpu().numpy().astype(np.int32)
            labels = targets[i]['labels'].cpu().numpy().astype(np.int32)
            # Получение всех предсказанных имен классов.
            pred_classes = [classes[i] for i in targets[i]['labels'].cpu().numpy()]
            sample = images[i].permute(1, 2, 0).cpu().numpy()
            sample = cv2.cvtColor(sample, cv2.COLOR_RGB2BGR)
            for box_num, box in enumerate(boxes):
                class_name = pred_classes[box_num]
                color = colors[classes.index(class_name)]
                cv2.rectangle(sample,
                            (box[0], box[1]),
                            (box[2], box[3]),
                            color, 2,
                            cv2.LINE_AA)
                cv2.putText(sample, classes[labels[box_num]], 
                            (box[0], box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 
                            1.0, color, 2, cv2.LINE_AA)
            cv2.imshow('Transformed image', sample)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

def save_loss_plot(
    OUT_DIR, 
    train_loss_list, 
    x_label='iterations',
    y_label='train loss',
    save_name='train_loss_iter'
):
    """
    Функция для сохранения графика функции потерь.

    :параметр OUT_DIR: Путь для сохранения графиков.
    :параметр train_loss_list: список, содержащий значения потерь при обучении.
    """
    figure_1 = plt.figure(figsize=(10, 7), num=1, clear=True)
    train_ax = figure_1.add_subplot()
    train_ax.plot(train_loss_list, color='tab:blue')
    train_ax.set_xlabel(x_label)
    train_ax.set_ylabel(y_label)
    figure_1.savefig(f"{OUT_DIR}/{save_name}.png")
    print('SAVING PLOTS COMPLETE...')
    # plt.close('all')

def save_mAP(OUT_DIR, map_05, map):
    """
    Сохраняет mAP@0.5 и mAP@0.5:0.95 за эпоху.

    :параметр OUT_DIR: Путь для сохранения графиков.
    :параметр map_05: Список, содержащий значения карты по 0,5 IoU.
    :параметр map: Список, содержащий значения карты в 0,5:0,95 IoU.
    """
    figure = plt.figure(figsize=(10, 7), num=1, clear=True)
    ax = figure.add_subplot()
    ax.plot(
        map_05, color='tab:orange', linestyle='-', 
        label='mAP@0.5'
    )
    ax.plot(
        map, color='tab:red', linestyle='-', 
        label='mAP@0.5:0.95'
    )
    ax.set_xlabel('Epochs')
    ax.set_ylabel('mAP')
    ax.legend()
    figure.savefig(f"{OUT_DIR}/map.png")
    # plt.close('all')

def visualize_mosaic_images(boxes, labels, image_resized, classes):
    print(boxes)
    print(labels)
    image_resized = cv2.cvtColor(image_resized, cv2.COLOR_RGB2BGR)
    for j, box in enumerate(boxes):
        color = (0, 255, 0)
        classn = labels[j]
        cv2.rectangle(image_resized,
                    (int(box[0]), int(box[1])),
                    (int(box[2]), int(box[3])),
                    color, 2)
        cv2.putText(image_resized, classes[classn], 
                    (int(box[0]), int(box[1]-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 
                    2, lineType=cv2.LINE_AA)
    cv2.imshow('Mosaic', image_resized)
    cv2.waitKey(0)

def save_model(
    epoch, 
    model, 
    optimizer, 
    train_loss_list,
    train_loss_list_epoch, 
    val_map,
    val_map_05,
    OUT_DIR,
    config,
    model_name
):
    """
    Функция для сохранения обученной модели до текущей эпохи или при каждом вызове.
    Сохраняет множество других словарей и параметров, а также помогает возобновить обучение.
    Может быть больше по размеру.

    :параметр epoch: номер эпохи.
    :параметр model: Модель нейронной сети.
    :параметр optimizer: Оптимизатор параметров.
    :параметр optimizer: Функция потерь для обучения.
    :параметр train_loss_list_epoch: список, содержащий потери для каждой эпохи.
    :параметр val_map: карта для 0.5:0.95 IoU.
    :параметр val_map_05: Карта для 0.5 IoU.
    :параметр OUT_DIR: Выходная папка для сохранения модели.
    """
    torch.save({
                'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss_list': train_loss_list,
                'train_loss_list_epoch': train_loss_list_epoch,
                'val_map': val_map,
                'val_map_05': val_map_05,
                'config': config,
                'model_name': model_name
                }, f"{OUT_DIR}/last_model.pth")

def save_model_state(model, OUT_DIR, config, model_name):
    """
    Сохраняет только словарь состояний модели. Имеет меньший размер по сравнению
    с сохраненной моделью со всеми остальными параметрами и словарями.
    Предпочтительнее для выводов и обмена информацией.

    :параметр model: Модель нейронной сети.
    :параметр OUT_DIR: Выходная папка для сохранения модели.
    """
    torch.save({
                'model_state_dict': model.state_dict(),
                'config': config,
                'model_name': model_name
                }, f"{OUT_DIR}/last_model_state.pth")

def denormalize(x, mean=None, std=None):
    # Shape of x here should be [B, 3, H, W].
    for t, m, s in zip(x, mean, std):
        t.mul_(s).add_(m)
    # Returns tensor of shape [B, 3, H, W].
    return torch.clamp(x, 0, 1)

def save_validation_results(images, detections, counter, out_dir, classes, colors):
    """
    Функция сохранения результатов проверки.
    :param images: Все изображения из текущей иттерации.
    :param detections: все результаты обнаружения.
    :param counter: Step counter for saving with unique ID.



    :параметры обнаружения: все результаты обнаружения.
    :счетчик параметров: Счетчик шагов для сохранения с уникальным идентификатором.
    """
    IMG_MEAN = [0.485, 0.456, 0.406]
    IMG_STD = [0.229, 0.224, 0.225]
    image_list = [] # List to store predicted images to return.
    for i, detection in enumerate(detections):
        image_c = images[i].clone()
        # image_c = denormalize(image_c, IMG_MEAN, IMG_STD)
        image_c = image_c.detach().cpu().numpy().astype(np.float32)
        image = np.transpose(image_c, (1, 2, 0))

        image = np.ascontiguousarray(image, dtype=np.float32)

        scores = detection['scores'].cpu().numpy()
        labels = detection['labels']
        bboxes = detection['boxes'].detach().cpu().numpy()
        boxes = bboxes[scores >= 0.5].astype(np.int32)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        # Получение всех предсказанных имен классов.
        pred_classes = [classes[i] for i in labels.cpu().numpy()]
        for j, box in enumerate(boxes):
            class_name = pred_classes[j]
            color = colors[classes.index(class_name)]
            cv2.rectangle(
                image, 
                (int(box[0]), int(box[1])),
                (int(box[2]), int(box[3])),
                color, 2, lineType=cv2.LINE_AA
            )
            cv2.putText(image, class_name, 
                    (int(box[0]), int(box[1]-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 
                    2, lineType=cv2.LINE_AA)
        cv2.imwrite(f"{out_dir}/image_{i}_{counter}.jpg", image*255.)
        image_list.append(image[:, :, ::-1])
    return image_list

def set_infer_dir():
    """
    Эта функция подсчитывает количество уже имеющихся каталогов results
    и создает новый в `outputs/result/`.
    И возвращает путь к каталогу.
    """
    if not os.path.exists('outputs/results'):
        os.makedirs('outputs/results')
    num_infer_dirs_present = len(os.listdir('outputs/results/'))
    next_dir_num = num_infer_dirs_present + 1
    new_dir_name = f"outputs/results/res_{next_dir_num}"
    os.makedirs(new_dir_name, exist_ok=True)
    return new_dir_name

def set_training_dir(dir_name=None):
    """
    Эта функция подсчитывает количество уже имеющихся папок для обучения
    и создает новый каталог в разделе ``outputs/training/``.
    И возвращает путь к каталогу.
    """
    if not os.path.exists('outputs/training'):
        os.makedirs('outputs/training')
    if dir_name:
        new_dir_name = f"outputs/training/{dir_name}"
        os.makedirs(new_dir_name, exist_ok=True)
        return new_dir_name
    else:
        num_train_dirs_present = len(os.listdir('outputs/training/'))
        next_dir_num = num_train_dirs_present + 1
        new_dir_name = f"outputs/training/res_{next_dir_num}"
        os.makedirs(new_dir_name, exist_ok=True)
        return new_dir_name
