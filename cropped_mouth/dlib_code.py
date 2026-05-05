import cv2
import dlib
from pathlib import Path
from tqdm import tqdm

# === Пути ===
DATASET_ROOT = Path(r"C:\Data\Projects\magistratura\MIRACLE\dataset")  # исходные изображения
OUTPUT_ROOT = Path(r"C:\Data\Projects\magistratura\MIRACLE\dataset_cropped")  # куда сохранять
FAILED_IMAGES_PATH = Path(r"C:\Data\Projects\magistratura\MIRACLE\failed_images.txt")  # файл для ошибок

# === Dlib модели ===
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    r"C:\Data\Projects\magistratura\cropped_mouth\shape_predictor_68_face_landmarks.dat"
)

# Настройки
PADDING = 5
SIZE = (96, 96)
ALPHA = 1.5         # контраст (1.0 = без изменений)
BETA = -10          # яркость

# --- Открываем файл для логирования ---
failed_file = open(FAILED_IMAGES_PATH, "w", encoding="utf-8")

# --- Рекурсивный поиск всех изображений ---
all_images = list(DATASET_ROOT.rglob("*.jpg")) + list(DATASET_ROOT.rglob("*.png"))
print(f"Найдено {len(all_images)} изображений для обработки.")

for image_path in tqdm(all_images, desc="Обработка изображений"):
    try:
        if not image_path.exists():
            failed_file.write(f"{image_path}\n")
            continue

        img = cv2.imread(str(image_path))
        if img is None:
            failed_file.write(f"{image_path}\n")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # --- Обнаружение лиц ---
        faces = detector(gray, 0)
        if len(faces) == 0:
            failed_file.write(f"{image_path}\n")
            continue

        # Берём первое лицо
        face = faces[0]
        shape = predictor(gray, face)

        # Координаты рта (точки 48-67)
        mouth_points = [(shape.part(i).x, shape.part(i).y) for i in range(48, 68)]
        x_min = max(0, min(p[0] for p in mouth_points) - PADDING)
        y_min = max(0, min(p[1] for p in mouth_points) - PADDING)
        x_max = min(img.shape[1], max(p[0] for p in mouth_points) + PADDING)
        y_max = min(img.shape[0], max(p[1] for p in mouth_points) + PADDING)

        if x_max <= x_min or y_max <= y_min:
            failed_file.write(f"{image_path}\n")
            continue

        mouth_crop = img[y_min:y_max, x_min:x_max]
        if mouth_crop.size == 0:
            failed_file.write(f"{image_path}\n")
            continue

        scale_factor = 1.5  # увеличиваем всё лицо перед обрезкой
        img = cv2.resize(img, (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)),
                         interpolation=cv2.INTER_CUBIC)

        mouth_resized = cv2.resize(mouth_crop, SIZE, interpolation=cv2.INTER_CUBIC)

        # mouth_enhanced = cv2.convertScaleAbs(mouth_resized, alpha=ALPHA, beta=BETA)


        # --- Сохраняем ---
        rel_path = image_path.relative_to(DATASET_ROOT)
        output_path = OUTPUT_ROOT / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), mouth_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 95])


    except Exception as e:
        failed_file.write(f"{image_path}\n")

failed_file.close()
print(f"\nОбработка завершена. Неудачные изображения сохранены в {FAILED_IMAGES_PATH}")


