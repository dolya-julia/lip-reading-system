import random
from pathlib import Path
import cv2
from tqdm import tqdm

# === Настройки ===
DATASET_DIR = Path(r"C:\Data\Projects\magistratura\prepare_dataset\final_dataset\train\female_session50")  # структура train/female_session01/...
FRAME_RATE = 25  # 20 или 25 FPS

# === Функция извлечения кадров ===
def extract_frames(video_path: Path, fps: int = 25):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Не удалось открыть видео:", video_path)
        return 0

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(int(video_fps / fps), 1)

    frame_idx = 0
    saved_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    for _ in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % step == 0:
            frame_path = video_path.parent / f"frame_{saved_idx:04d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            saved_idx += 1
        frame_idx += 1

    cap.release()
    return saved_idx

# === Основной проход по уже существующей структуре ===
for split in ["train", "val", "test"]:
    split_dir = DATASET_DIR / split
    if not split_dir.exists():
        continue

    for parent_folder in tqdm(sorted(split_dir.iterdir()), desc=f"Processing {split}"):
        if not parent_folder.is_dir():
            continue

        for fragment_folder in sorted(parent_folder.iterdir()):
            if not fragment_folder.is_dir():
                continue

            for mp4_file in sorted(fragment_folder.glob("*.mp4")):
                saved = extract_frames(mp4_file, fps=FRAME_RATE)
                if saved == 0:
                    print(f"Внимание: для {mp4_file} извлечено 0 кадров.")

print("Кадры извлечены, текстовые файлы оставлены без изменений.")