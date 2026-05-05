import cv2
from pathlib import Path
from tqdm import tqdm

# Корневая папка датасета
DATASET_DIR = Path(
    r"D:\word_dataset_part2_voxceleb"
)

TARGET_FPS = 25


def extract_frames(video_path: Path, output_dir: Path, fps: int = 25):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("❌ Не удалось открыть видео:", video_path)
        return 0

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(int(video_fps / fps), 1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    frame_idx = 0
    saved_idx = 0

    for _ in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0:
            frame_path = output_dir / f"frame_{saved_idx:04d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            saved_idx += 1

        frame_idx += 1

    cap.release()
    return saved_idx


def main():
    videos = list(DATASET_DIR.rglob("*.mp4"))
    print(f"🎬 Найдено видео: {len(videos)}")

    for video_path in tqdm(videos, desc="Извлечение кадров"):
        video_name = video_path.stem  # без .mp4

        # папка с кадрами рядом с видео
        output_dir = video_path.parent / video_name

        # 🔹 если уже обработано — пропускаем
        if output_dir.exists() and any(output_dir.glob("*.jpg")):
            continue

        output_dir.mkdir(exist_ok=True)

        saved = extract_frames(video_path, output_dir, TARGET_FPS)

        if saved == 0:
            print(f"⚠️ Нет кадров: {video_path}")
        else:
            print(f"✔ {video_name}: {saved} кадров")

    print("\n✅ Готово! Все видео разбиты на кадры.")


if __name__ == "__main__":
    main()