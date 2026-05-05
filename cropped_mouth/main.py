# import cv2
# import mediapipe as mp
# from pathlib import Path
# import numpy as np
#
# # === Пути ===
# img_path = r"C:\Data\Projects\magistratura\MIRACL-VC1\dataset_prepared\train\Well\M01_09\frame_009.jpg"
# output_path = r"C:\Data\Projects\magistratura\MIRACL-VC1\test_lip3.jpg"
# IMG_SIZE = (96, 96)
#
# # Проверка файла
# img_path = Path(img_path)
# if not img_path.exists():
#     print("Файл не найден:", img_path)
#     exit()
#
# img = cv2.imread(str(img_path))
# if img is None:
#     print("Не удалось загрузить изображение:", img_path)
#     exit()
#
# # Инициализация Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=True,
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5
# )
#
# # Проверенные индексы точек только для губ
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,  # верхняя губа
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308, 324, 318, 402, 317  # нижняя губа
# ]
#
# # --- Обработка изображения ---
# img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# results = face_mesh.process(img_rgb)
#
# if results.multi_face_landmarks:
#     face_landmarks = results.multi_face_landmarks[0]
#     h, w, _ = img.shape
#
#     # Получаем координаты точек губ в пикселях
#     xs = [int(face_landmarks.landmark[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(face_landmarks.landmark[i].y * h) for i in MOUTH_INDICES]
#
#     padding = 5
#     x_min = max(0, min(xs) - padding)
#     x_max = min(w, max(xs) + padding)
#     y_min = max(0, min(ys) - padding)
#     y_max = min(h, max(ys) + padding)
#
#     # Вырезаем рот
#     lip_img = img[y_min:y_max, x_min:x_max]
#     lip_img = cv2.resize(lip_img, IMG_SIZE)
#
#     # Сохраняем результат
#     cv2.imwrite(output_path, lip_img)
#     print(f"Обрезанное изображение сохранено: {output_path}")
#
#     # Отображаем точки губ для проверки
#     for x, y in zip(xs, ys):
#         cv2.circle(img, (x, y), 2, (0, 255, 0), -1)
#     img_large = cv2.resize(img, (img.shape[1]*2, img.shape[0]*2))
#     cv2.imshow("Lip Landmarks", img_large)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
# else:
#     print("Лицо не обнаружено на изображении.")
#
# face_mesh.close()

# import cv2
# import mediapipe as mp
# from pathlib import Path
# import numpy as np
# import os
# from tqdm import tqdm
#
# # --- Параметры ---
# RAW_DATASET_DIR = r"C:\Data\Projects\magistratura\MIRACL-VC1\dataset_prepared"
# OUTPUT_DATASET_DIR = r"C:\Data\Projects\magistratura\MIRACL-VC1\dataset_lips"
# IMG_SIZE = (96, 96)
# PADDING_X = 5  # ширина
# PADDING_Y = 5   # высота
#
# # Проверенные индексы точек только для губ
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,  # верхняя губа
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308, 324, 318, 402, 317  # нижняя губа
# ]
#
# # Инициализация Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=True,
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5
# )
#
# # Создаем структуру выходного датасета
# def create_output_dir_structure(input_root, output_root):
#     for split_dir in ["train", "val", "test"]:
#         for word_dir in (Path(input_root)/split_dir).glob("*"):
#             for speaker_dir in word_dir.glob("*"):
#                 out_dir = Path(output_root)/split_dir/word_dir.name/speaker_dir.name
#                 os.makedirs(out_dir, exist_ok=True)
#
# create_output_dir_structure(RAW_DATASET_DIR, OUTPUT_DATASET_DIR)
#
# # Функция для вырезания рта
# def crop_lips(img, landmarks):
#     h, w, _ = img.shape
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#
#     x_min = max(0, min(xs) - PADDING_X)
#     x_max = min(w, max(xs) + PADDING_X)
#     y_min = max(0, min(ys) - PADDING_Y)
#     y_max = min(h, max(ys) + PADDING_Y)
#
#     roi = img[y_min:y_max, x_min:x_max]
#     roi = cv2.resize(roi, IMG_SIZE)
#     return roi
#
# # --- Основной цикл ---
# for split_dir in ["train", "val", "test"]:
#     split_path = Path(RAW_DATASET_DIR)/split_dir
#     if not split_path.exists():
#         continue
#
#     for word_dir in split_path.iterdir():
#         if not word_dir.is_dir():
#             continue
#         for speaker_dir in word_dir.iterdir():
#             if not speaker_dir.is_dir():
#                 continue
#             for img_file in tqdm(list(speaker_dir.glob("*.jpg")), desc=f"{split_dir}/{word_dir.name}/{speaker_dir.name}"):
#                 img = cv2.imread(str(img_file))
#                 if img is None:
#                     print("Не удалось загрузить:", img_file)
#                     continue
#
#                 img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#                 results = face_mesh.process(img_rgb)
#
#                 if results.multi_face_landmarks:
#                     landmarks = results.multi_face_landmarks[0]
#                     lip_img = crop_lips(img, landmarks.landmark)
#
#                     # Сохраняем
#                     out_file = Path(OUTPUT_DATASET_DIR)/split_dir/word_dir.name/speaker_dir.name/img_file.name
#                     cv2.imwrite(str(out_file), lip_img)
#                 else:
#                     print("Лицо не обнаружено:", img_file)
#
# face_mesh.close()
# print("Обработка завершена!")

# import cv2
# import mediapipe as mp
# from pathlib import Path
# from tqdm import tqdm
# import os
#
# # Пути
# FAILED_IMAGES_PATH = Path(r"C:\Data\Projects\magistratura\AVDigits\failed_images.txt")
# RAW_DATASET_DIR = Path(r"C:\Data\Projects\magistratura\AVDigits\dataset")
# OUTPUT_DATASET_DIR = Path(r"C:\Data\Projects\magistratura\AVDigits\dataset_lips_cropped")
#
# # Параметры
# IMG_SIZE = (96, 96)
# PADDING_X = 5
# PADDING_Y = 5
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308, 324, 318, 402, 317
# ]
#
# # Инициализация Mediapipe
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
#
# # Функция обрезки рта
# def crop_lips(img, landmarks):
#     h, w, _ = img.shape
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#     x_min = max(0, min(xs) - PADDING_X)
#     x_max = min(w, max(xs) + PADDING_X)
#     y_min = max(0, min(ys) - PADDING_Y)
#     y_max = min(h, max(ys) + PADDING_Y)
#     roi = img[y_min:y_max, x_min:x_max]
#     return cv2.resize(roi, IMG_SIZE)
#
# # Загрузка неудачных изображений
# if not FAILED_IMAGES_PATH.exists():
#     print("❌ Файл failed_images.txt не найден!")
#     exit(1)
#
# with open(FAILED_IMAGES_PATH, "r", encoding="utf-8") as f:
#     failed_paths = [Path(line.strip()) for line in f if line.strip()]
#
# retry_failed_path = FAILED_IMAGES_PATH.parent / "failed_images_retry.txt"
# failed_file = open(retry_failed_path, "w", encoding="utf-8")
#
# print(f"🔁 Повторная обработка {len(failed_paths)} изображений")
#
# success_count = 0
# for img_file in tqdm(failed_paths, desc="Повторная попытка"):
#     if not img_file.exists():
#         failed_file.write(f"{img_file}\n")
#         continue
#
#     img = cv2.imread(str(img_file))
#     if img is None:
#         failed_file.write(f"{img_file}\n")
#         continue
#
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(img_rgb)
#
#     if results.multi_face_landmarks:
#         landmarks = results.multi_face_landmarks[0]
#         lip_img = crop_lips(img, landmarks.landmark)
#
#         # восстановим относительный путь
#         rel_path = img_file.relative_to(RAW_DATASET_DIR)
#         out_file = Path(OUTPUT_DATASET_DIR) / rel_path
#         out_file.parent.mkdir(parents=True, exist_ok=True)
#         cv2.imwrite(str(out_file), lip_img)
#         success_count += 1
#     else:
#         failed_file.write(f"{img_file}\n")
#
# failed_file.close()
# face_mesh.close()
#
# print(f"✅ Повторная обработка завершена! Успешно восстановлено {success_count} изображений")
# print(f"❌ Остались ошибки: см. {retry_failed_path}")


# import cv2
# import mediapipe as mp
# from pathlib import Path
# from tqdm import tqdm
#
# # === Пути ===
# FAILED_IMAGES_PATH = Path(r"C:\Data\Projects\magistratura\new_dataset\failed_images.txt")
#
# DATASET_ROOT = Path(r"C:\Data\Projects\magistratura\new_dataset\video_frames_dataset")
# OUTPUT_ROOT = Path(r"C:\Data\Projects\magistratura\new_dataset\mouth_dataset")
#
# retry_failed_path = FAILED_IMAGES_PATH.parent / "failed_images_retry.txt"
#
# # === Параметры ===
# IMG_SIZE = (96, 96)
# PADDING_X = 5
# PADDING_Y = 5
#
# # Индексы рта из Mediapipe FaceMesh
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308, 324, 318, 402, 317
# ]
#
# # === Mediapipe ===
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True,
#                                   max_num_faces=1,
#                                   refine_landmarks=True)
#
# # === Функция обрезки рта ===
# def crop_lips(img, landmarks):
#     h, w, _ = img.shape
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#
#     x_min = max(0, min(xs) - PADDING_X)
#     x_max = min(w, max(xs) + PADDING_X)
#     y_min = max(0, min(ys) - PADDING_Y)
#     y_max = min(h, max(ys) + PADDING_Y)
#
#     roi = img[y_min:y_max, x_min:x_max]
#     return cv2.resize(roi, IMG_SIZE)
#
# # === Проверка наличия файла ===
# if not FAILED_IMAGES_PATH.exists():
#     print("❌ Файл failed_images.txt не найден!")
#     exit(1)
#
# # === Читаем пути ===
# with open(FAILED_IMAGES_PATH, "r", encoding="utf-8") as f:
#     failed_paths = [Path(line.strip()) for line in f if line.strip()]
#
# print(f"🔁 Повторная обработка {len(failed_paths)} изображений")
# failed_file = open(retry_failed_path, "w", encoding="utf-8")
#
# success_count = 0
#
# # === Основной цикл ===
# for img_path in tqdm(failed_paths, desc="Mediapipe повторная обработка"):
#
#     if not img_path.exists():
#         failed_file.write(f"{img_path}\n")
#         continue
#
#     img = cv2.imread(str(img_path))
#     if img is None:
#         failed_file.write(f"{img_path}\n")
#         continue
#
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(img_rgb)
#
#     if results.multi_face_landmarks:
#         landmarks = results.multi_face_landmarks[0].landmark
#
#         try:
#             lip_img = crop_lips(img, landmarks)
#
#             # сохраняем в ту же структуру, что и dlib-скрипт
#             rel_path = img_path.relative_to(DATASET_ROOT)
#             out_path = OUTPUT_ROOT / rel_path
#             out_path.parent.mkdir(parents=True, exist_ok=True)
#
#             cv2.imwrite(str(out_path), lip_img)
#
#             # удаляем оригинал, как делал dlib
#             img_path.unlink()
#
#             success_count += 1
#
#         except Exception:
#             failed_file.write(f"{img_path}\n")
#     else:
#         failed_file.write(f"{img_path}\n")
#
# failed_file.close()
# face_mesh.close()
#
# print(f"✅ Готово! Повторно обработано успешно: {success_count}")
# print(f"❌ Остались ошибки → {retry_failed_path}")

# import cv2
# import mediapipe as mp
# import numpy as np
# from pathlib import Path
# from tqdm import tqdm
#
# INPUT_DIR = Path(r"D:\grid_word_dataset")
# FAILED_LIST_PATH = INPUT_DIR / "failed_images.txt"
#
# IMG_SIZE = 96
# PADDING_X = 5
# PADDING_Y = 5
#
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308,
#     324, 318, 402, 317
# ]
#
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=True,
#     max_num_faces=1,
#     refine_landmarks=True
# )
#
# failed_file = open(FAILED_LIST_PATH, "w", encoding="utf-8")
#
#
# def resize_keep_aspect(img, size=96):
#     h, w = img.shape[:2]
#     scale = size / max(h, w)
#
#     new_w = int(w * scale)
#     new_h = int(h * scale)
#
#     resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
#
#     result = np.zeros((size, size), dtype=np.uint8)
#
#     x_offset = (size - new_w) // 2
#     y_offset = (size - new_h) // 2
#
#     result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
#     return result
#
#
# def crop_lips(img, landmarks):
#     h, w, _ = img.shape
#
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#
#     x_min = max(0, min(xs) - PADDING_X)
#     x_max = min(w, max(xs) + PADDING_X)
#     y_min = max(0, min(ys) - PADDING_Y)
#     y_max = min(h, max(ys) + PADDING_Y)
#
#     roi = img[y_min:y_max, x_min:x_max]
#     roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
#
#     return resize_keep_aspect(roi_gray, size=IMG_SIZE)
#
#
# image_paths = list(INPUT_DIR.rglob("*.jpg"))
# print(f"Найдено {len(image_paths)} изображений.")
#
# success_count = 0
#
# for img_path in tqdm(image_paths, desc="Обработка"):
#     img = cv2.imread(str(img_path))
#     if img is None:
#         failed_file.write(str(img_path) + "\n")
#         continue
#
#     results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#
#     if results.multi_face_landmarks:
#         try:
#             landmarks = results.multi_face_landmarks[0].landmark
#             cropped = crop_lips(img, landmarks)
#             cv2.imwrite(str(img_path), cropped)
#             success_count += 1
#         except Exception:
#             failed_file.write(str(img_path) + "\n")
#     else:
#         failed_file.write(str(img_path) + "\n")
#
# failed_file.close()
# face_mesh.close()
#
# print("\n=== РЕЗУЛЬТАТ ===")
# print(f"✔ Успешно заменено изображений: {success_count}")
# print(f"❌ Ошибок: {len(open(FAILED_LIST_PATH).read().splitlines())}")
# print(f"➡ Лог ошибок: {FAILED_LIST_PATH}")

# import cv2
# import mediapipe as mp
# import numpy as np
# from pathlib import Path
# from tqdm import tqdm
#
# INPUT_DIR = Path(r"D:\bbac1a_again_1529")
# FAILED_LIST_PATH = INPUT_DIR / "failed_images.txt"
#
# IMG_SIZE = 96
# PADDING_X = 5
# PADDING_Y = 5
#
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308,
#     324, 318, 402, 317
# ]
#
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=True,
#     max_num_faces=1,
#     refine_landmarks=True
# )
#
# failed_file = open(FAILED_LIST_PATH, "w", encoding="utf-8")
#
#
# def crop_lips(img, landmarks, size=96):
#     h, w, _ = img.shape
#
#     # 1. Получаем координаты центра рта и его размеры
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#
#     center_x = (min(xs) + max(xs)) // 2
#     center_y = (min(ys) + max(ys)) // 2
#
#     # Определяем требуемый размер области (например, 2x ширина рта)
#     mouth_width = max(xs) - min(xs)
#
#     # Определяем размер кадрирования (например, 1.5x ширина рта)
#     # Используем квадратный ROI для простоты
#     crop_size = int(mouth_width * 1.5)
#
#     # 2. Вычисляем границы для обрезки
#     x_min = max(0, center_x - crop_size // 2)
#     x_max = min(w, center_x + crop_size // 2)
#     y_min = max(0, center_y - crop_size // 2)
#     y_max = min(h, center_y + crop_size // 2)
#
#     # Убедимся, что ROI квадратный (если возможно)
#     current_w = x_max - x_min
#     current_h = y_max - y_min
#
#     # 3. Обрезаем
#     roi = img[y_min:y_max, x_min:x_max]
#
#     # 4. Переводим в оттенки серого
#     roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
#
#     # 5. Масштабируем до 96x96 (без сохранения аспекта, но с заполнением всего пространства)
#     # Используем INTER_LINEAR для лучшего качества при масштабировании
#     resized = cv2.resize(roi_gray, (size, size), interpolation=cv2.INTER_LINEAR)
#
#     # 6. Применяем нормализацию контраста (Опционально, но рекомендуется)
#     # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#     # final_img = clahe.apply(resized)
#
#     return resized  # или final_img
#
#
# image_paths = list(INPUT_DIR.rglob("*.jpg"))
# print(f"Найдено {len(image_paths)} изображений.")
#
# success_count = 0
#
# for img_path in tqdm(image_paths, desc="Обработка"):
#     img = cv2.imread(str(img_path))
#     if img is None:
#         failed_file.write(str(img_path) + "\n")
#         continue
#
#     results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#
#     if results.multi_face_landmarks:
#         try:
#             landmarks = results.multi_face_landmarks[0].landmark
#             cropped = crop_lips(img, landmarks)
#             cv2.imwrite(str(img_path), cropped)
#             success_count += 1
#         except Exception:
#             failed_file.write(str(img_path) + "\n")
#     else:
#         failed_file.write(str(img_path) + "\n")
#
# failed_file.close()
# face_mesh.close()
#
# print("\n=== РЕЗУЛЬТАТ ===")
# print(f"✔ Успешно заменено изображений: {success_count}")
# print(f"❌ Ошибок: {len(open(FAILED_LIST_PATH).read().splitlines())}")
# print(f"➡ Лог ошибок: {FAILED_LIST_PATH}")




# import cv2
# import mediapipe as mp
# import numpy as np
# from pathlib import Path
# from tqdm import tqdm
#
# # ================== НАСТРОЙКИ ==================
# INPUT_DIR = Path(r"D:\word_dataset_part2_voxceleb")
# FAILED_LIST_PATH = INPUT_DIR / "failed_images.txt"
#
# IMG_SIZE = 96
# MIN_CROP_SIZE = 48
# CROP_SCALE = 2.3
#
# # индексы губ Mediapipe FaceMesh
# MOUTH_INDICES = [
#     61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
#     146, 91, 181, 84, 17, 314, 405, 321, 375, 308,
#     324, 318, 402, 317
# ]
#
# # ================== FaceMesh ==================
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=False,   # ВАЖНО
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )
#
# FAILED_LIST_PATH.parent.mkdir(parents=True, exist_ok=True)
# failed_file = open(FAILED_LIST_PATH, "w", encoding="utf-8")
#
# # ================== ФУНКЦИИ ==================
# def crop_lips_rgb(img, landmarks):
#     h, w, _ = img.shape
#
#     xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
#     ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]
#
#     min_x, max_x = min(xs), max(xs)
#     min_y, max_y = min(ys), max(ys)
#
#     center_x = (min_x + max_x) // 2
#     center_y = (min_y + max_y) // 2
#
#     mouth_width = max_x - min_x
#     crop_size = max(int(mouth_width * CROP_SCALE), MIN_CROP_SIZE)
#
#     x1 = max(0, center_x - crop_size // 2)
#     y1 = max(0, center_y - crop_size // 2)
#     x2 = min(w, x1 + crop_size)
#     y2 = min(h, y1 + crop_size)
#
#     # корректируем если вышли за границы
#     x1 = max(0, x2 - crop_size)
#     y1 = max(0, y2 - crop_size)
#
#     roi = img[y1:y2, x1:x2]
#
#     if roi.size == 0:
#         return None
#
#     resized = cv2.resize(
#         roi,
#         (IMG_SIZE, IMG_SIZE),
#         interpolation=cv2.INTER_CUBIC
#     )
#
#     return resized
#
#
# # ================== ОСНОВНОЙ ЦИКЛ ==================
# image_paths = list(INPUT_DIR.rglob("*.jpg"))
# print(f"Найдено изображений: {len(image_paths)}")
#
# success = 0
#
# for img_path in tqdm(image_paths, desc="Обрезка губ"):
#     img = cv2.imread(str(img_path))
#     if img is None:
#         failed_file.write(str(img_path) + "\n")
#         continue
#
#     h, w = img.shape[:2]
#     if h == IMG_SIZE and w == IMG_SIZE:
#         continue
#
#     results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#
#     if not results.multi_face_landmarks:
#         failed_file.write(str(img_path) + "\n")
#         continue
#
#     try:
#         landmarks = results.multi_face_landmarks[0].landmark
#         cropped = crop_lips_rgb(img, landmarks)
#
#         if cropped is None:
#             failed_file.write(str(img_path) + "\n")
#             continue
#
#         out_path = img_path
#
#         cv2.imwrite(str(out_path), cropped)
#
#         success += 1
#
#     except Exception:
#         failed_file.write(str(img_path) + "\n")
#
# failed_file.close()
# face_mesh.close()
#
# print("\n=== РЕЗУЛЬТАТ ===")
# print(f"✔ Успешно обработано: {success}")
# print(f"❌ Ошибок: {len(open(FAILED_LIST_PATH).read().splitlines())}")
# print(f"📄 Лог: {FAILED_LIST_PATH}")

import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ================== НАСТРОЙКИ ==================
INPUT_DIR = Path(r"D:\word_dataset_part2_voxceleb")

FAILED_LIST_PATH = INPUT_DIR / "failed_images.txt"
RETRY_FAILED_LIST_PATH = INPUT_DIR / "failed_images_retry.txt"

IMG_SIZE = 96
MIN_CROP_SIZE = 48
CROP_SCALE = 2.3

# индексы губ Mediapipe FaceMesh
MOUTH_INDICES = [
    61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
    146, 91, 181, 84, 17, 314, 405, 321, 375, 308,
    324, 318, 402, 317
]

# ================== FaceMesh ==================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,      # 👈 для retry лучше True
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# ================== ФУНКЦИИ ==================
def crop_lips_rgb(img, landmarks):
    h, w, _ = img.shape

    xs = [int(landmarks[i].x * w) for i in MOUTH_INDICES]
    ys = [int(landmarks[i].y * h) for i in MOUTH_INDICES]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2

    mouth_width = max_x - min_x
    crop_size = max(int(mouth_width * CROP_SCALE), MIN_CROP_SIZE)

    x1 = max(0, center_x - crop_size // 2)
    y1 = max(0, center_y - crop_size // 2)
    x2 = min(w, x1 + crop_size)
    y2 = min(h, y1 + crop_size)

    x1 = max(0, x2 - crop_size)
    y1 = max(0, y2 - crop_size)

    roi = img[y1:y2, x1:x2]

    if roi.size == 0:
        return None

    return cv2.resize(roi, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_CUBIC)

# ================== ЗАГРУЗКА FAILED ==================
if not FAILED_LIST_PATH.exists():
    print("❌ failed_images.txt не найден")
    exit()

with open(FAILED_LIST_PATH, "r", encoding="utf-8") as f:
    image_paths = [Path(line.strip()) for line in f if line.strip()]

print(f"🔁 Повторная обработка изображений: {len(image_paths)}")

retry_failed_file = open(RETRY_FAILED_LIST_PATH, "w", encoding="utf-8")

success = 0

# ================== ОСНОВНОЙ ЦИКЛ ==================
for img_path in tqdm(image_paths, desc="Retry lips crop"):
    if not img_path.exists():
        retry_failed_file.write(str(img_path) + "\n")
        continue

    img = cv2.imread(str(img_path))
    if img is None:
        retry_failed_file.write(str(img_path) + "\n")
        continue

    h, w = img.shape[:2]
    if h == IMG_SIZE and w == IMG_SIZE:
        success += 1
        continue

    results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    if not results.multi_face_landmarks:
        retry_failed_file.write(str(img_path) + "\n")
        continue

    try:
        landmarks = results.multi_face_landmarks[0].landmark
        cropped = crop_lips_rgb(img, landmarks)

        if cropped is None:
            retry_failed_file.write(str(img_path) + "\n")
            continue

        cv2.imwrite(str(img_path), cropped)
        success += 1

    except Exception:
        retry_failed_file.write(str(img_path) + "\n")

retry_failed_file.close()
face_mesh.close()

# ================== ОТЧЁТ ==================
remaining = len(open(RETRY_FAILED_LIST_PATH).read().splitlines())

print("\n=== РЕЗУЛЬТАТ RETRY ===")
print(f"✔ Успешно восстановлено: {success}")
print(f"❌ Всё ещё не удалось: {remaining}")
print(f"📄 Лог повторных ошибок: {RETRY_FAILED_LIST_PATH}")

