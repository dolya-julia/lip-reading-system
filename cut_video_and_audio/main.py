# import torch
# import torchaudio
# from pydub import AudioSegment
# from silero_vad import get_speech_timestamps, read_audio, save_audio
# import os
#
# # === Пути ===
# audio_path = "C:\Data\Projects\magistratura\session01\session01_cut01.wav"
# output_dir = "C:\Data\Projects\magistratura\new_dataset"
# os.makedirs(output_dir, exist_ok=True)
#
# # === Загружаем аудио ===
# wav = read_audio(audio_path)
# model, utils = torch.hub.load('snakers4/silero-vad', 'silero_vad', onnx=False)
# (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
#
# # === Находим фрагменты речи ===
# speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
#
# # === Сохраняем каждый фрагмент в отдельный файл ===
# for i, ts in enumerate(speech_timestamps):
#     chunk = wav[ts['start']:ts['end']]
#     out_path = os.path.join(output_dir, f"frag_{i:03d}.wav")
#     save_audio(out_path, chunk, sampling_rate=16000)
#
# print(f"Сохранено {len(speech_timestamps)} фрагментов речи.")

# import whisper
#
#
# def transcribe_audio_whisper(audio_path, model_size="medium"):
#     """
#     Транскрибирует аудиофайл с помощью Whisper и объединяет короткие сегменты в смысловые блоки.
#
#     Args:
#         audio_path: Путь к аудиофайлу (*.wav).
#         model_size: Размер модели Whisper ("tiny", "base", "small", "medium", "large").
#
#     Returns:
#         Текст расшифровки и список объединённых сегментов.
#     """
#     try:
#         # Загружаем модель
#         print(f"Загрузка модели Whisper ({model_size})...")
#         model = whisper.load_model(model_size)
#
#         # Транскрибируем аудио
#         print("Выполняется распознавание речи...")
#         result = model.transcribe(audio_path, verbose=False)
#
#         text = result["text"]
#         segments = result["segments"]
#
#         # Объединяем близкие сегменты
#         merged_segments = merge_segments(segments, max_gap=1.0, max_length=25)
#
#         return text, merged_segments
#
#     except Exception as e:
#         print(f"Ошибка при распознавании речи Whisper: {e}")
#         return None, None
#
#
# def merge_segments(segments, max_gap=1.0, max_length=25):
#     """
#     Объединяет соседние сегменты Whisper в более крупные смысловые блоки.
#
#     Args:
#         segments: список сегментов Whisper [{start, end, text}, ...]
#         max_gap: допустимый разрыв между сегментами в секундах (если меньше — объединяем)
#         max_length: максимальное количество слов в объединённом сегменте
#
#     Returns:
#         Список объединённых сегментов.
#     """
#     if not segments:
#         return []
#
#     merged = []
#     current = segments[0].copy()
#
#     for next_seg in segments[1:]:
#         gap = next_seg["start"] - current["end"]
#         combined_text = (current["text"] + " " + next_seg["text"]).strip()
#         word_count = len(combined_text.split())
#
#         # Объединяем, если пауза маленькая и текст не слишком длинный
#         if gap < max_gap and word_count <= max_length:
#             current["end"] = next_seg["end"]
#             current["text"] = combined_text
#         else:
#             merged.append(current)
#             current = next_seg.copy()
#
#     merged.append(current)
#     return merged
#
#
# # Пример использования
# if __name__ == "__main__":
#     audio_file = r"C:\Data\Projects\magistratura\session01\session01_cut01.wav"
#     transcription, segments = transcribe_audio_whisper(audio_file, model_size="small")
#
#     if transcription:
#         print("\nТекст:", transcription)
#         print("\nСегменты:")
#         for i, segment in enumerate(segments, start=1):
#             print(f"{i:02d}. [{segment['start']:.2f} - {segment['end']:.2f}] сек → {segment['text']}")


# import os
# import whisper
# from moviepy.video.io.VideoFileClip import VideoFileClip
#
# def transcribe_audio_whisper(audio_path, model_size="medium", max_words_per_segment=6):
#     """
#     Транскрибирует аудиофайл с помощью Whisper с word-level timestamps.
#     Возвращает полный текст и сегменты слов, объединённых в блоки по max_words_per_segment.
#     """
#     try:
#         print(f"Загрузка модели Whisper ({model_size})...")
#         model = whisper.load_model(model_size)
#
#         print("Выполняется распознавание речи с точными временными метками слов...")
#         result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
#         text = result["text"]
#
#         # Собираем все слова с их временными метками
#         all_words = []
#         for seg in result["segments"]:
#             for w in seg.get("words", []):
#                 all_words.append(w)
#
#         # Объединяем слова в блоки по max_words_per_segment
#         segments = merge_words_to_segments(all_words, max_words=max_words_per_segment)
#
#         return text, segments
#
#     except Exception as e:
#         print(f"Ошибка при распознавании речи Whisper: {e}")
#         return None, None
#
# def merge_words_to_segments(words, max_words=6):
#     """
#     Делит последовательность слов с временными метками на сегменты длиной до max_words.
#     """
#     segments = []
#     i = 0
#     while i < len(words):
#         chunk = words[i:i+max_words]
#         segments.append({
#             "start": chunk[0]["start"],
#             "end": chunk[-1]["end"],
#             "text": " ".join([w["word"] for w in chunk])
#         })
#         i += max_words
#     return segments
#
# def split_video_by_segments(video_path, segments, output_dir_base, file_base_name):
#     """
#     Нарезает видео по сегментам и сохраняет видеофрагменты и текст.
#     """
#     output_dir = os.path.join(output_dir_base, file_base_name)
#     os.makedirs(output_dir, exist_ok=True)
#
#     print(f"\n--- Обработка видео: {os.path.basename(video_path)} ---")
#     clip = None
#     try:
#         clip = VideoFileClip(video_path)
#         processed_fragments_count = 0
#
#         for i, seg in enumerate(segments, start=1):
#             start_time = seg["start"]
#             end_time = seg["end"]
#             text = seg["text"].strip()
#
#             if end_time - start_time < 0.5:  # пропускаем слишком короткие фрагменты
#                 continue
#
#             fragment_path = os.path.join(output_dir, f"{file_base_name}_fragment_{i:03d}.mp4")
#             subtitle_path = os.path.join(output_dir, f"{file_base_name}_fragment_{i:03d}.txt")
#
#             print(f"Сохраняю фрагмент {i} [{start_time:.2f} - {end_time:.2f}] сек")
#
#             subclip = clip.subclipped(start_time, end_time)
#             subclip.write_videofile(fragment_path, codec="libx264", audio_codec="aac")
#             subclip.close()
#
#             with open(subtitle_path, "w", encoding="utf-8") as f:
#                 f.write(text)
#             processed_fragments_count += 1
#
#         print(f"\nСохранено {processed_fragments_count} фрагментов для {file_base_name} в {output_dir}.")
#
#     except Exception as e:
#         print(f"Ошибка при обработке видео {os.path.basename(video_path)}: {e}")
#     finally:
#         if clip:
#             clip.close()
#
# def process_single_file_pair(video_path, audio_path, output_base_dir, model_size="small"):
#     file_base_name = os.path.splitext(os.path.basename(video_path))[0]
#     transcription, segments = transcribe_audio_whisper(audio_path, model_size=model_size)
#     if segments:
#         split_video_by_segments(video_path, segments, output_base_dir, file_base_name)
#
# if __name__ == "__main__":
#     base_input_dir = r"C:\Data\Projects\magistratura\female_session"
#     output_base_dir = r"C:\Data\Projects\magistratura\new_dataset\female_session"
#     whisper_model_size = "medium"  # можно small/medium/large-v2
#
#     os.makedirs(output_base_dir, exist_ok=True)
#
#     # Сканируем все папки вида sessionXX
#     session_dirs = [
#         os.path.join(base_input_dir, d)
#         for d in os.listdir(base_input_dir)
#         if d.startswith("session") and os.path.isdir(os.path.join(base_input_dir, d))
#     ]
#     # session_dirs = [
#     #     os.path.join(base_input_dir, d)
#     #     for d in os.listdir(base_input_dir)
#     #     if d.startswith("session") and
#     #        d[7:].isdigit() and
#     #        1 <= int(d[7:]) <= 1 and
#     #        os.path.isdir(os.path.join(base_input_dir, d))
#     # ]
#
#     print(f"Найдено {len(session_dirs)} папок: {session_dirs}")
#
#     for input_dir in sorted(session_dirs):
#         print(f"\n🟦 Обработка каталога: {input_dir}")
#         video_files = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
#
#         for video_filename in video_files:
#             base_name_without_ext = os.path.splitext(video_filename)[0]
#             video_path = os.path.join(input_dir, video_filename)
#             audio_path = os.path.join(input_dir, f"{base_name_without_ext}.wav")
#
#             if os.path.exists(audio_path):
#                 process_single_file_pair(video_path, audio_path, output_base_dir, whisper_model_size)
#             else:
#                 print(f"⚠ Файл аудио не найден для {video_filename}")

# import os
# import whisper
# from moviepy.video.io.VideoFileClip import VideoFileClip
#
# # --- Настройки ---
# base_input_dir = r"C:\Data\Projects\magistratura\male_test_session"
# output_base_dir = r"C:\Data\Projects\magistratura\new_dataset\male_test_session"
# whisper_model_size = "medium"  # small / medium / large-v2
# max_words_per_segment = 6
#
# # --- Создаём выходной каталог ---
# os.makedirs(output_base_dir, exist_ok=True)
#
# # --- Загружаем модель Whisper один раз ---
# print(f"Загрузка модели Whisper ({whisper_model_size})...")
# model = whisper.load_model(whisper_model_size)
# print("Модель загружена!\n")
#
#
# def transcribe_audio_whisper(audio_path, max_words_per_segment=max_words_per_segment):
#     """
#     Транскрибирует аудиофайл с word-level timestamps и объединяет слова в блоки.
#     """
#     try:
#         print(f"Распознавание речи для {os.path.basename(audio_path)}...")
#         result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
#         text = result["text"]
#
#         all_words = []
#         for seg in result["segments"]:
#             for w in seg.get("words", []):
#                 all_words.append(w)
#
#         segments = merge_words_to_segments(all_words, max_words=max_words_per_segment)
#         return text, segments
#     except Exception as e:
#         print(f"Ошибка при распознавании речи Whisper: {e}")
#         return None, None
#
#
# def merge_words_to_segments(words, max_words=6):
#     segments = []
#     i = 0
#     while i < len(words):
#         chunk = words[i:i + max_words]
#         segments.append({
#             "start": chunk[0]["start"],
#             "end": chunk[-1]["end"],
#             "text": " ".join([w["word"] for w in chunk])
#         })
#         i += max_words
#     return segments
#
#
# def split_video_by_segments(video_path, segments, output_dir_base, file_base_name):
#     output_dir = os.path.join(output_dir_base, file_base_name)
#     os.makedirs(output_dir, exist_ok=True)
#     print(f"\n--- Нарезка видео: {os.path.basename(video_path)} ---")
#     clip = None
#     try:
#         clip = VideoFileClip(video_path)
#         processed_fragments_count = 0
#         for i, seg in enumerate(segments, start=1):
#             start_time = seg["start"]
#             end_time = seg["end"]
#             text = seg["text"].strip()
#             if end_time - start_time < 0.5:  # пропускаем слишком короткие фрагменты
#                 continue
#
#             fragment_path = os.path.join(output_dir, f"{file_base_name}_fragment_{i:03d}.mp4")
#             subtitle_path = os.path.join(output_dir, f"{file_base_name}_fragment_{i:03d}.txt")
#
#             print(f"Сохраняю фрагмент {i} [{start_time:.2f} - {end_time:.2f}] сек")
#             subclip = clip.subclipped(start_time, end_time)
#             subclip.write_videofile(fragment_path, codec="libx264", audio_codec="aac")
#             subclip.close()
#
#             with open(subtitle_path, "w", encoding="utf-8") as f:
#                 f.write(text)
#
#             processed_fragments_count += 1
#
#         print(f"\nСохранено {processed_fragments_count} фрагментов для {file_base_name} в {output_dir}.")
#     except Exception as e:
#         print(f"Ошибка при обработке видео {os.path.basename(video_path)}: {e}")
#     finally:
#         if clip:
#             clip.close()
#
#
# def process_single_file_pair(video_path, audio_path, output_base_dir):
#     file_base_name = os.path.splitext(os.path.basename(video_path))[0]
#     transcription, segments = transcribe_audio_whisper(audio_path)
#     if segments:
#         split_video_by_segments(video_path, segments, output_base_dir, file_base_name)
#
#
# # --- Сканируем все папки вида sessionXX ---
# session_dirs = [
#     os.path.join(base_input_dir, d)
#     for d in os.listdir(base_input_dir)
#     if d.startswith("session") and os.path.isdir(os.path.join(base_input_dir, d))
# ]
#
# # session_dirs = [
# #     os.path.join(base_input_dir, d)
# #     for d in os.listdir(base_input_dir)
# #     if d.startswith("session") and
# #        d[7:].isdigit() and
# #        20 <= int(d[7:]) <= 45 and
# #        os.path.isdir(os.path.join(base_input_dir, d))
# # ]
# print(f"Найдено {len(session_dirs)} папок: {session_dirs}\n")
#
# # --- Обрабатываем все видео ---
# for input_dir in sorted(session_dirs):
#     print(f"\n🟦 Обработка каталога: {input_dir}")
#     video_files = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
#     for video_filename in video_files:
#         base_name_without_ext = os.path.splitext(video_filename)[0]
#         video_path = os.path.join(input_dir, video_filename)
#         audio_path = os.path.join(input_dir, f"{base_name_without_ext}.wav")
#
#         if os.path.exists(audio_path):
#             process_single_file_pair(video_path, audio_path, output_base_dir)
#         else:
#             print(f"⚠ Файл аудио не найден для {video_filename}")

import os

VIDEO_DIR = r"D:\new_downloaded_videos_part4"
URLS_FILE = r"D:\urls.txt"
OUTPUT_FILE = r"D:\urls_filtered.txt"


def get_downloaded_ids(video_dir):
    """Собираем ID уже скачанных видео"""
    downloaded_ids = set()

    for filename in os.listdir(video_dir):
        if filename.endswith((".mp4", ".mkv", ".webm")):
            video_id = os.path.splitext(filename)[0]
            downloaded_ids.add(video_id)

    return downloaded_ids


def extract_id_from_url(url):
    """Извлекаем ID из YouTube-ссылки"""
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].strip()
    return None


def main():
    downloaded_ids = get_downloaded_ids(VIDEO_DIR)
    print(f"📁 Найдено скачанных видео: {len(downloaded_ids)}")

    kept = []
    removed = 0

    with open(URLS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        video_id = extract_id_from_url(url)

        if video_id in downloaded_ids:
            removed += 1
        else:
            kept.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in kept:
            f.write(url + "\n")

    print(f"🗑 Удалено ссылок: {removed}")
    print(f"💾 Осталось ссылок: {len(kept)}")
    print(f"📄 Новый файл: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

# import yt_dlp
#
# URLS_FILE = r"D:\urls_voxceleb_filtered.txt"
# OUTPUT_FILE = r"D:\urls_voxceleb_available.txt"
#
#
# def is_video_available(url):
#     ydl_opts = {
#         "quiet": True,
#         "skip_download": True,
#         "ignoreerrors": True,
#     }
#
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=False)
#             return info is not None
#     except Exception:
#         return False
#
#
# def main():
#     with open(URLS_FILE, "r", encoding="utf-8") as f:
#         urls = [line.strip() for line in f if line.strip()]
#
#     print(f"🔍 Проверяю {len(urls)} ссылок...\n")
#
#     valid_urls = []
#     removed = 0
#
#     for i, url in enumerate(urls, 1):
#         print(f"[{i}/{len(urls)}] Проверка: {url}")
#
#         if is_video_available(url):
#             valid_urls.append(url)
#         else:
#             print("❌ Недоступно")
#             removed += 1
#
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         for url in valid_urls:
#             f.write(url + "\n")
#
#     print("\n=== ГОТОВО ===")
#     print(f"🗑 Удалено недоступных: {removed}")
#     print(f"✅ Доступных осталось: {len(valid_urls)}")
#     print(f"📄 Новый файл: {OUTPUT_FILE}")
#
#
# if __name__ == "__main__":
#     main()

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

URLS_FILE = r"D:\urls_voxceleb_filtered.txt"
MAX_WORKERS = 20   # можно 20–40, если интернет нормальный

def is_video_available(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            return True
        return False
    except:
        return False


# читаем ссылки
with open(URLS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

print("Всего ссылок:", len(urls))

available_urls = []

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(is_video_available, url): url for url in urls}

    for i, future in enumerate(as_completed(futures)):
        url = futures[future]
        if future.result():
            available_urls.append(url)

        if i % 100 == 0:
            print(f"Проверено {i}/{len(urls)}")

# перезаписываем файл
with open(URLS_FILE, "w", encoding="utf-8") as f:
    for url in available_urls:
        f.write(url + "\n")

print("Готово.")
print("Удалено:", len(urls) - len(available_urls))