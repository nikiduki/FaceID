from mtcnn.mtcnn import MTCNN
import statistics
import os
import cv2
import numpy
import keras
import imutils
import numpy as np


# Создание сети нахождения лиц
detector = MTCNN()
# Загрузка модели сети определения лиц
embedder = keras.models.load_model('model/keras/facenet_keras.h5', compile=False)


# Получить дистанцию лица
def get_distance(model, face):
    face = face.astype('float32')
    face = (face - face.mean()) / face.std()
    face = numpy.expand_dims(face, axis=0)
    return model.predict(face)[0]


# Созданием базы с размечеными лицами
def make_base(photos):
    base = []
    for image in photos:
            # Замена BGR на RGB
            frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Получить размеры изображения
            image_size = numpy.asarray(image.shape)[0:2]
            # Получение списка лиц с координатами и значением уверенности
            faces_boxes = detector.detect_faces(image)

            # Работа с лицами
            if faces_boxes:
                # Координаты лица
                x, y, w, h = faces_boxes[0]['box']
                # Выравнивание лица
                d = h - w  # Разница между высотой и шириной
                w = w + d  # Делаем изображение квадратным
                x = numpy.maximum(x - round(d / 2), 0)
                x1 = numpy.maximum(x, 0)
                y1 = numpy.maximum(y, 0)
                x2 = numpy.minimum(x + w, image_size[1])
                y2 = numpy.minimum(y + h, image_size[0])
                # Получение картинки с лицом
                cropped = image[y1:y2, x1:x2, :]
                face_image = cv2.resize(cropped, (160, 160), interpolation=cv2.INTER_AREA)
                # Сохранение суммы евклидова пространства
                base.append(get_distance(embedder, image))

    return base


def face_recognise(frame, base):

    face_n = 0  # Инициализация счётчика лиц

    # Увеличение/уменьшение наименьшей стороны изображения до 1000 пикселей
    if frame.shape[0] < frame.shape[1]:
        frame = imutils.resize(frame, height=1000)
    else:
        frame = imutils.resize(frame, width=1000)

    # Получить размеры изображения
    image_size = numpy.asarray(frame.shape)[0:2]
    # Получение списка лиц с координатами и значением уверенности
    faces_boxes = detector.detect_faces(frame)
    # Копия изображения для рисования рамок на нём
    image_detected = frame.copy()
    # Замена BGR на RGB (так находит в два раза больше лиц)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    success = False
    mes = '\033Я не нашел лица :c\033'
    # Работа с лицами
    if faces_boxes:
        for face_box in faces_boxes:
            # Увеличение счётчика файлов
            face_n += 1
            # Координаты лица
            x, y, w, h = face_box['box']
            # Выравнивание лица
            d = h - w  # Разница между высотой и шириной
            w = w + d  # Делаем изображение квадратным
            x = numpy.maximum(x - round(d / 2), 0)
            x1 = numpy.maximum(x, 0)
            y1 = numpy.maximum(y, 0)
            x2 = numpy.minimum(x + w, image_size[1])
            y2 = numpy.minimum(y + h, image_size[0])

            # Получение картинки с лицом
            cropped = frame[y1:y2, x1:x2, :]
            face_image = cv2.resize(cropped, (160, 160), interpolation=cv2.INTER_AREA)
            # Получение дистанции
            distance = get_distance(embedder, face_image)
            # Координаты лица
            x, y, w, h = face_box['box']

            # Отступы для увеличения рамки
            d = h - w  # Разница между высотой и шириной
            w = w + d  # Делаем изображение квадратным
            x = numpy.maximum(x - round(d / 2), 0)
            x1 = numpy.maximum(x - round(w / 4), 0)
            y1 = numpy.maximum(y - round(h / 4), 0)
            x2 = numpy.minimum(x + w + round(w / 4), image_size[1])
            y2 = numpy.minimum(y + h + round(h / 4), image_size[0])

            # Отборка лиц {selected|rejected}
            if face_box['confidence'] > 0.99:  # 0.99 - уверенность сети в процентах что это лицо
                identity = None
                difference = None
                min_difference = 8
                median = None
                min_median = 8
                faces = {}

                # Сверка расстояний с известными лицами
                for name, base_distances in base.items():
                    faces[name] = []
                    for base_distance in base_distances:
                        difference = numpy.linalg.norm(base_distance - distance)
                        if difference < min_difference:
                            print('difference - ' + str(difference))
                            faces[name].append(difference)

                # Нахождение минимальной мидианы среди проголосовавших лиц
                if faces:
                    for name, items in faces.items():
                        # Идентификация только участвуют два и больше лиц
                        if items and len(items) >= 2:
                            print(name)
                            print(items)
                            median = statistics.median(items)
                            if median < min_median:
                                print('median - ' + str(median))
                                min_median = median
                                identity = name

                # Если лицо опознано
                if identity:

                    # Пишем имя под лицом
                    cv2.putText(
                        image_detected,
                        identity,
                        (x1 + 10, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1
                    )

                    # Рисует зелёный квадрат на картинке по координатам
                    cv2.rectangle(
                        image_detected,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0, 1),
                        1
                    )

                    # Сохранение изображения лица на диск в директорию recognized
                    cv2.imwrite('demo/recognition_image/output/faces/recognized/' + str(median) + '.' + str(face_n)
                                + '.jpg', face_image)

                    # Информируем консоль
                    print('\033[92m' + str(identity) + ' - ' + str(min_median) + '\033[0m')
                    mes = '\n' + 'Вы авторизованы под именем ' + identity + '\n'
                    success = True

                else:
                    # Рисует белый квадрат на картинке по координатам
                    cv2.rectangle(
                        image_detected,
                        (x1, y1),
                        (x2, y2),
                        (255, 255, 255, 1),
                        1
                    )

                    # Информируем консоль
                    mes = '\033Не могу идентифицировать Вас. Пришлите более четкую фотографию.\n' \
                          'Если не выходит, зарегистрируйтесь заново, отправив видео вашего лица' \
                          ' (Желательно 1 сек).\033'

            else:

                # Рисует красный квадрат на картинке по координатам
                # cv2.rectangle(
                #     image_detected,
                #     (x1, y1),
                #     (x2, y2),
                #     (0, 0, 255, 1),
                #     1
                # )

                # Информируем консоль
                mes = '\033Я не нашел лица :c\033'

    # Сохраняем кадр с видео
    cv2.imwrite('demo/recognition_image/output/frames/' + '1' + '.jpg', image_detected)
    return mes, success


def main():
    image = cv2.imread(r"C:\Users\d5u5d\github\facedars\python-facedars\WIN_20221114_00_49_55_Pro.jpg")
    face_recognise(image, make_base(['nikita']))


if __name__ == "__main__":
    main()

