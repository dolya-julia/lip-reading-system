import cv2
import dlib
import numpy as np
from pathlib import Path
from tqdm import tqdm


# === Пути ===
SOURCE_ROOT = Path(r"D:\bbac2a_again_1700")
OUTPUT_ROOT = Path(r"D:\bbac2a_again_1700\dataset_lips_cropped")
BAD_FILES_PATH = Path(r"D:\bbac2a_again_1700\bad_files_cropping.txt")

# === Dlib модели ===
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    r"C:\Data\Projects\magistratura\cropped_mouth\shape_predictor_68_face_landmarks.dat"
)

# # === Настройки ===
PAD = 10  # отступ вокруг рта
SIZE = (96, 96)  # размер результирующего изображения

# === Подготовка файла ошибок ===
bad_files = open(BAD_FILES_PATH, "a", encoding="utf-8")

def process_image(image_path: Path):
    """Обрезает губы и сохраняет в новый датасет"""
    try:
        # --- Пропуск, если файл уже существует ---
        rel_path = image_path.relative_to(SOURCE_ROOT)
        output_path = OUTPUT_ROOT / rel_path
        if output_path.exists():
            return  # уже обработан

        # --- Загрузка изображения ---
        img = cv2.imread(str(image_path))
        if img is None:
            bad_files.write(f"Ошибка загрузки: {image_path}\n")
            return

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 1)
        if len(faces) == 0:
            bad_files.write(f"Лицо не обнаружено: {image_path}\n")
            return

        shape = predictor(gray, faces[0])
        mouth_points = np.array([(shape.part(i).x, shape.part(i).y) for i in range(48, 68)])
        x_min, y_min = np.min(mouth_points, axis=0)
        x_max, y_max = np.max(mouth_points, axis=0)

        # Добавляем отступ и проверяем границы
        x_min = max(0, x_min - PAD)
        y_min = max(0, y_min - PAD)
        x_max = min(img.shape[1], x_max + PAD)
        y_max = min(img.shape[0], y_max + PAD)

        if x_max <= x_min or y_max <= y_min:
            bad_files.write(f"Некорректная область: {image_path}\n")
            return

        mouth_crop = img[y_min:y_max, x_min:x_max]
        if mouth_crop.size == 0:
            bad_files.write(f"Пустое изображение: {image_path}\n")
            return

        mouth_resized = cv2.resize(mouth_crop, SIZE)

        # --- Сохранение ---
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), mouth_resized)

    except Exception as e:
        bad_files.write(f"Ошибка {type(e).__name__}: {image_path} — {e}\n")


# === Основной цикл ===
splits = ["train", "val", "test"]

for split in splits:
    split_dir = SOURCE_ROOT / split
    if not split_dir.exists():
        print(f"Пропущен {split_dir} — не найден.")
        continue

    all_images = list(split_dir.rglob("*.jpg"))
    print(f"\nОбработка сплита {split}: найдено {len(all_images)} изображений")

    for img_path in tqdm(all_images, desc=f"{split}"):
        process_image(img_path)


bad_files.close()
print(f"\n Обрезка завершена. Ошибки сохранены в {BAD_FILES_PATH}")