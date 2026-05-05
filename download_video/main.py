# import os
# import subprocess
# import pandas as pd
# import yt_dlp
# from tqdm import tqdm
# import argparse
# import sys
#
#
# def download_youtube_video(video_id, output_dir):
#     """Скачивает видео и субтитры по YouTube ID."""
#     video_path = os.path.join(output_dir, f"{video_id}.mp4")
#     subs_path = os.path.join(output_dir, f"{video_id}.en.vtt")  # пример для английских субтитров
#
#     if os.path.exists(video_path):
#         print(f"💾 Видео {video_id} уже скачано.")
#         return video_path
#
#     ydl_opts = {
#         "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
#         "outtmpl": os.path.join(output_dir, f"{video_id}.%(ext)s"),
#         "quiet": True,
#         "ignoreerrors": True,
#         "writesubtitles": True,              # ✅ скачать субтитры
#         "writeautomaticsub": True,           # ✅ если нет ручных — скачать авто
#         "subtitleslangs": ["en", "ru"],      # ✅ можно указать нужные языки
#         "skip_download": False,              # ✅ скачать и видео, и субтитры
#         "user_agent": "com.google.android.youtube/19.10.37 (Linux; U; Android 13) gzip",
#         "extractor_args": {"youtube": {"player_client": "android"}},
#     }
#
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
#             print(f"✅ Видео {video_id} успешно скачано.")
#
#             # Проверяем, были ли субтитры
#             subtitles = info.get("requested_subtitles")
#             if subtitles:
#                 print(f"💬 Найдены субтитры: {list(subtitles.keys())}")
#             else:
#                 print(f"⚠️ Субтитры отсутствуют для {video_id}")
#
#         return video_path
#
#     except Exception as e:
#         print(f"❌ Ошибка при загрузке {video_id}: {e}")
#         return None
#
#
#
# def cut_video_segment(video_path, start, end, output_path):
#     """Нарезает видео по временам start и end (в секундах)."""
#     start = float(start)
#     end = float(end)
#     duration = end - start
#     if duration <= 0:
#         print(f"⚠️ Пропуск сегмента — отрицательная длина: {start}–{end}")
#         return
#
#     cmd = [
#         "ffmpeg",
#         "-y",
#         "-i", video_path,
#         "-ss", str(start),
#         "-t", str(duration),
#         "-c:v", "libx264",
#         "-c:a", "aac",
#         "-loglevel", "error",
#         output_path
#     ]
#
#     try:
#         subprocess.run(cmd, check=True)
#         print(f"✂️ Сегмент {start:.2f}-{end:.2f} вырезан.")
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Ошибка при нарезке сегмента {start:.2f}-{end:.2f}: {e}")
#
#
# def main(csv_path, output_dir):
#     os.makedirs(output_dir, exist_ok=True)
#
#     try:
#         df = pd.read_csv(csv_path, header=None, names=["youtube_id", "start", "end", "x", "y"])
#     except Exception as e:
#         print(f"❌ Ошибка при чтении CSV: {e}")
#         return
#
#     print(f"Найдено {len(df)} сегментов.")
#
#     # Группируем по видео
#     grouped = df.groupby("youtube_id")
#
#     for video_id, group in tqdm(grouped, total=len(grouped), desc="Обработка видео"):
#         video_id = str(video_id).strip()
#         video_folder = os.path.join(output_dir, video_id)
#         os.makedirs(video_folder, exist_ok=True)
#
#         # Скачиваем оригинальное видео
#         video_path = download_youtube_video(video_id, output_dir)
#         if video_path is None or not os.path.exists(video_path):
#             print(f"❌ Пропуск видео {video_id}: недоступно")
#             continue
#
#         # Нарезаем все сегменты для этого видео
#         for _, row in group.iterrows():
#             start = float(row["start"])
#             end = float(row["end"])
#             x, y = row["x"], row["y"]
#
#             clip_name = f"{video_id}_{start:.2f}_{end:.2f}.mp4"
#             clip_path = os.path.join(video_folder, clip_name)
#             cut_video_segment(video_path, start, end, clip_path)
#
#             coords_path = clip_path.replace(".mp4", ".txt")
#             try:
#                 with open(coords_path, "w") as f:
#                     f.write(f"{x},{y}\n")
#             except Exception as e:
#                 print(f"❌ Ошибка при записи координат: {e}")
#
#         # Удаляем оригинальное видео после всех сегментов
#         try:
#             os.remove(video_path)
#             print(f"🗑️ Оригинальное видео {video_id} удалено")
#         except Exception as e:
#             print(f"❌ Ошибка при удалении оригинала {video_id}: {e}")
#
#     print("✅ Все сегменты успешно обработаны!")
#
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Скачивание и нарезка видео по CSV")
#     parser.add_argument("--csv", required=True, help="Путь к CSV файлу с сегментами")
#     parser.add_argument("--out", required=True, help="Папка для сохранения видео")
#
#     args = parser.parse_args()
#     main(args.csv, args.out)

# import os
# import re
# import subprocess
# import yt_dlp
# import whisper  # ⬅️ добавляем библиотеку для распознавания речи
#
#
# # ---------- 1. Разбор TXT ----------
# def parse_voxceleb_txt(txt_path):
#     with open(txt_path, "r", encoding="utf-8") as f:
#         lines = f.readlines()
#
#     video_id = None
#     segments = []
#
#     for line in lines:
#         if "Youtube ID" in line:
#             video_id = line.split(":")[1].strip()
#         elif re.match(r".*\s+\d+\.\d+\s+\d+\.\d+", line):
#             parts = line.strip().split()
#             if len(parts) >= 3:
#                 _, start, end = parts
#                 segments.append((float(start), float(end)))
#
#     if not video_id:
#         raise ValueError(f"❌ Не найден Youtube ID в {txt_path}")
#
#     return video_id, segments
#
#
# # ---------- 2. Скачивание ----------
# def download_youtube_video(video_id, output_dir):
#     os.makedirs(output_dir, exist_ok=True)
#     video_path = os.path.join(output_dir, f"{video_id}.mp4")
#
#     if os.path.exists(video_path):
#         print(f"💾 Видео {video_id} уже скачано.")
#         return video_path
#
#     ydl_opts = {
#         "format": "bestvideo+bestaudio/best",
#         "outtmpl": video_path,
#         "quiet": True,
#         "noprogress": True,
#     }
#
#     ydl_opts = {
#         "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
#         "outtmpl": video_path,
#         "quiet": True,
#         "noprogress": True,
#         "ignoreerrors": True,
#         "retries": 5,
#         "user_agent": "com.google.android.youtube/19.10.37 (Linux; U; Android 13) gzip",  # ✅ мобильный user-agent
#         "extractor_args": {"youtube": { "player_client": "android"}},
#     }
#
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
#         print(f"✅ Видео {video_id} скачано.")
#         return video_path
#     except Exception as e:
#         print(f"❌ Ошибка при скачивании {video_id}: {e}")
#         return None
#
#
# # ---------- 3. Вырезка ----------
# def cut_video_segment(video_path, start, end, output_path):
#     duration = end - start
#     if duration <= 0:
#         print(f"⚠️ Пропущен сегмент: некорректная длина ({start}-{end})")
#         return
#
#     cmd = [
#         "ffmpeg",
#         "-y",
#         "-i", video_path,
#         "-ss", str(start),
#         "-t", str(duration),
#         "-c:v", "libx264",
#         "-c:a", "aac",
#         "-loglevel", "error",
#         output_path,
#     ]
#
#     try:
#         subprocess.run(cmd, check=True)
#         print(f"✂️ Вырезан сегмент {start:.2f}-{end:.2f}")
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Ошибка при нарезке: {e}")
#
#
# # ---------- 4. Распознавание речи ----------
# def transcribe_audio(video_path, text_path, model):
#     """Распознаёт речь в видео и сохраняет текст."""
#     try:
#         result = model.transcribe(video_path, language="en")
#         text = result["text"].strip()
#
#         with open(text_path, "w", encoding="utf-8") as f:
#             f.write(text)
#
#         print(f"📝 Сохранён текст для {os.path.basename(video_path)}")
#     except Exception as e:
#         print(f"❌ Ошибка при распознавании речи: {e}")
#
#
# # ---------- 5. Основной цикл ----------
# def process_voxceleb_file(txt_path, output_dir, model):
#     try:
#         video_id, segments = parse_voxceleb_txt(txt_path)
#     except Exception as e:
#         print(f"⚠️ Пропуск {txt_path}: {e}")
#         return
#
#     print(f"\n🎬 Видео ID: {video_id}")
#     print(f"🔹 Найдено {len(segments)} сегментов в {txt_path}")
#
#     person_folder = os.path.basename(os.path.dirname(txt_path))
#     video_folder = os.path.join(output_dir, person_folder, video_id)
#     os.makedirs(video_folder, exist_ok=True)
#
#     video_path = download_youtube_video(video_id, output_dir)
#     if not video_path:
#         return
#
#     # --- Нарезаем и распознаём ---
#     for i, (start, end) in enumerate(segments, 1):
#         clip_name = f"{video_id}_{i:02d}.mp4"
#         clip_path = os.path.join(video_folder, clip_name)
#         text_path = clip_path.replace(".mp4", ".txt")
#
#         cut_video_segment(video_path, start, end, clip_path)
#         transcribe_audio(clip_path, text_path, model)
#
#     # --- 🧹 Удаляем оригинал после нарезки ---
#     try:
#         if os.path.exists(video_path):
#             os.remove(video_path)
#             print(f"🗑️ Удалено оригинальное видео: {video_path}")
#     except Exception as e:
#         print(f"⚠️ Не удалось удалить {video_path}: {e}")
#
#
#
# def process_all_txt_files(root_txt_dir, output_dir):
#     """Проходит по всем .txt файлам"""
#     model = whisper.load_model("base")  # ⚡ можно заменить на "small", "medium", "large"
#     print("🤖 Модель Whisper загружена.")
#
#     for root, _, files in os.walk(root_txt_dir):
#         for file in files:
#             if file.endswith(".txt"):
#                 txt_path = os.path.join(root, file)
#                 process_voxceleb_file(txt_path, output_dir, model)
#
#
# if __name__ == "__main__":
#     root_txt_dir = r"C:\Data\Projects\magistratura\voxceleb\txt"
#     output_dir = r"C:\Data\Projects\magistratura\download_video\voxceleb\videos"
#
#     print(f"🚀 Начинаю обработку всех файлов в {root_txt_dir}")
#     process_all_txt_files(root_txt_dir, output_dir)
#     print("✅ Все видео успешно скачаны, нарезаны и расшифрованы!")


import os
import yt_dlp

def video_already_downloaded(video_id, output_dir):
    """Проверяем, существует ли файл с данным ID независимо от расширения."""
    for ext in ["mp4", "mkv", "webm"]:
        if os.path.exists(os.path.join(output_dir, f"{video_id}.{ext}")):
            return True
    return False

def get_video_id(url):
    """Вынимаем ID из ссылки."""
    try:
        return yt_dlp.YoutubeDL().extract_info(url, download=False)["id"]
    except:
        return None

def download_one(url, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Получаем ID заранее
    video_id = get_video_id(url)
    if not video_id:
        print(f"❌ Не удалось получить ID: {url}")
        return

    # Проверяем, скачано ли уже
    if video_already_downloaded(video_id, output_dir):
        print(f"⏩ Пропускаем — уже скачано: {video_id}")
        return

    ydl_opts = {
        # ЛУЧШЕЕ КАЧЕСТВО
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        # просто склейка, без перекодирования
        "merge_output_format": "mp4",
        # устойчивость
        "retries": 10,
        "fragment_retries": 10,
        "ignoreerrors": True,

        # лог
        "quiet": False,
        "noprogress": False,


        # YouTube меньше режет
        "user_agent": "com.google.android.youtube/19.10.37 (Linux; Android 13)",
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Скачано: {url}")
    except Exception as e:
        print(f"❌ Ошибка при скачивании {url}: {e}")


def process_links_file(txt_path, output_dir):
    with open(txt_path, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    print(f"🔍 Найдено ссылок: {len(links)}")

    for url in links:
        download_one(url, output_dir)


if __name__ == "__main__":
    # links_file = r"D:\urls_voxceleb_filtered.txt"
    # output_dir = r"D:\new_downloaded_videos_part_voxceleb2"

    links_file = r"D:\urls3.txt"
    output_dir = r"D:\new_downloaded_videos_part5"

    process_links_file(links_file, output_dir)


