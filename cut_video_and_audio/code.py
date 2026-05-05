# import os
# import glob
# import whisper
# import re
#
# # --- Конфигурация ---
# VIDEO_INPUT_DIR = r"C:\Data\Projects\magistratura\initial_dataset\female_session\session01"
# AUDIO_INPUT_DIR = r"C:\Data\Projects\magistratura\initial_dataset\female_session\session01"
# TRANSCRIPT_OUTPUT_DIR = "final_transcriptions"
# WHISPER_MODEL_SIZE = "medium"
# WHISPER_LANGUAGE = "en"
# # --- ---
#
#
# def ensure_dir(directory):
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#
#
# def transcribe_audio_whisper(audio_path, model_size, language):
#     print(f"Транскрибация аудио: {audio_path} с моделью {model_size} ({language})...")
#     try:
#         model = whisper.load_model(model_size)
#         result = model.transcribe(audio_path, language=language)
#         print("Транскрибация завершена.")
#         return result["text"]
#     except Exception as e:
#         print(f"Ошибка при транскрибации {audio_path}: {e}")
#         return ""
#
#
# def normalize_text(text):
#     text = text.lower()
#     text = re.sub(r'[^\w\s]', '', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text
#
#
# def main():
#     ensure_dir(TRANSCRIPT_OUTPUT_DIR)
#
#     # Находим все подпапки вида session01, session02, session03...
#     base_dir = r"C:\Data\Projects\magistratura\initial_dataset\female_session"
#     session_dirs = sorted(
#         d for d in glob.glob(os.path.join(base_dir, "session*"))
#         if os.path.isdir(d)
#     )
#
#     if not session_dirs:
#         print("Не найдено ни одной папки sessionXX")
#         return
#
#     print(f"Найдено {len(session_dirs)} сессий: {session_dirs}")
#
#     # Загружаем модель Whisper один раз (оптимизация!)
#     model = whisper.load_model(WHISPER_MODEL_SIZE)
#
#     for session_dir in session_dirs:
#
#         print(f"\n=== Обработка сессии: {session_dir} ===")
#
#         video_files = sorted(glob.glob(os.path.join(session_dir, "*.mp4")))
#
#         if not video_files:
#             print(f"Нет видео в папке: {session_dir}, пропускаем...")
#             continue
#
#         session_name = os.path.basename(session_dir)
#         session_output_dir = os.path.join(TRANSCRIPT_OUTPUT_DIR, session_name)
#         session_draft_dir = os.path.join(session_output_dir, "drafts")
#
#         ensure_dir(session_output_dir)
#         ensure_dir(session_draft_dir)
#
#         for i, video_path in enumerate(video_files):
#             video_name = os.path.basename(video_path)
#             base_name, _ = os.path.splitext(video_name)
#
#             # Ищем соответствующее аудио в той же папке
#             audio_wav = os.path.join(session_dir, f"{base_name}.wav")
#             audio_mp3 = os.path.join(session_dir, f"{base_name}.mp3")
#
#             if os.path.exists(audio_wav):
#                 audio_path = audio_wav
#             elif os.path.exists(audio_mp3):
#                 audio_path = audio_mp3
#             else:
#                 print(f"Нет аудио для {video_name}. Пропускаем.")
#                 continue
#
#             final_path = os.path.join(session_output_dir, f"{base_name}.txt")
#             draft_path = os.path.join(session_draft_dir, f"{base_name}_draft.txt")
#
#             print(f"\n--- [{session_name}] Обработка {i+1}/{len(video_files)}: {video_name} ---")
#
#             if os.path.exists(final_path):
#                 print("Финальная транскрипция уже существует. Пропускаем.")
#                 continue
#
#             # Whisper → черновик
#             try:
#                 print(f"Транскрибация аудио: {audio_path}")
#                 result = model.transcribe(audio_path, language=WHISPER_LANGUAGE)
#                 draft_text = result["text"]
#             except Exception as e:
#                 print(f"Ошибка транскрибации {audio_path}: {e}")
#                 continue
#
#             with open(draft_path, "w", encoding="utf-8") as f:
#                 f.write(draft_text)
#
#             final_text = normalize_text(draft_text)
#
#             with open(final_path, "w", encoding="utf-8") as f:
#                 f.write(final_text)
#
#             print(f"Сохранено → {final_path}")
#
#     print("\n=== Все сессии обработаны ===")
#
#
# if __name__ == "__main__":
#     main()

# import os
# import glob
# import subprocess
# import whisper
# import re
#
# # --- Конфигурация ---
# VIDEO_DIR = r"C:\Data\Projects\magistratura\words_dataset\downloaded_videos"
# TRANSCRIPT_OUTPUT_DIR = r"C:\Data\Projects\magistratura\words_dataset\transcriptions"
# WHISPER_MODEL_SIZE = "medium"
# WHISPER_LANGUAGE = "en"
# SEGMENT_LENGTH = 60  # секунд
# OVERLAP = 2          # перекрытие сегментов в секундах
# AUDIO_EXT = ".wav"
# # -------------------
#
# def ensure_dir(directory):
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#
# def normalize_text(text):
#     text = text.lower()
#     text = re.sub(r'[^\w\s]', '', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text
#
# def extract_audio(video_path):
#     """Извлекает аудио из видео в WAV 16 kHz"""
#     base = os.path.splitext(video_path)[0]
#     audio_path = base + AUDIO_EXT
#     if os.path.exists(audio_path):
#         return audio_path
#
#     cmd = [
#         "ffmpeg", "-y", "-i", video_path,
#         "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
#         audio_path
#     ]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#     return audio_path
#
# def split_audio_with_overlap(audio_path, segment_length=60, overlap=2):
#     """Разделяет длинное аудио на сегменты с перекрытием"""
#     base = os.path.splitext(audio_path)[0]
#     output_files = []
#
#     # Получаем длительность аудио
#     duration_cmd = [
#         "ffprobe", "-v", "error", "-show_entries",
#         "format=duration", "-of",
#         "default=noprint_wrappers=1:nokey=1", audio_path
#     ]
#     total_duration = float(subprocess.check_output(duration_cmd).strip())
#
#     start = 0
#     idx = 0
#     while start < total_duration:
#         end = min(start + segment_length, total_duration)
#         segment_file = f"{base}_{idx:03d}.wav"
#         cmd = [
#             "ffmpeg", "-y", "-i", audio_path,
#             "-ss", str(start), "-to", str(end),
#             "-c", "copy", segment_file
#         ]
#         subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         output_files.append(segment_file)
#         start += segment_length - overlap
#         idx += 1
#     return output_files
#
# def transcribe_segment(segment_path, model):
#     """Транскрибирует один сегмент"""
#     try:
#         result = model.transcribe(segment_path, language=WHISPER_LANGUAGE)
#         return result["text"]
#     except Exception as e:
#         print(f"❌ Ошибка транскрибации сегмента {segment_path}: {e}")
#         return ""
#
# def process_video(video_path, model):
#     base_name = os.path.splitext(os.path.basename(video_path))[0]
#     final_path = os.path.join(TRANSCRIPT_OUTPUT_DIR, f"{base_name}.txt")
#     if os.path.exists(final_path):
#         print(f"Файл {final_path} уже существует. Пропускаем.")
#         return
#
#     print(f"\n🎬 Обрабатываем видео: {video_path}")
#
#     # 1️⃣ Извлекаем аудио
#     audio_path = extract_audio(video_path)
#
#     # 2️⃣ Разделяем аудио на сегменты с перекрытием
#     segments = split_audio_with_overlap(audio_path, SEGMENT_LENGTH, OVERLAP)
#     full_text = ""
#
#     # 3️⃣ Транскрибируем сегменты и склеиваем
#     for seg in segments:
#         segment_text = transcribe_segment(seg, model)
#         full_text += " " + segment_text
#         os.remove(seg)  # удаляем сегмент после обработки
#
#     # 4️⃣ Нормализуем и сохраняем
#     full_text = normalize_text(full_text)
#     ensure_dir(TRANSCRIPT_OUTPUT_DIR)
#     with open(final_path, "w", encoding="utf-8") as f:
#         f.write(full_text)
#
#     print(f"✅ Транскрипция сохранена → {final_path}")
#
# def main():
#     # Загружаем Whisper один раз
#     model = whisper.load_model(WHISPER_MODEL_SIZE)
#     print(f"🤖 Модель Whisper '{WHISPER_MODEL_SIZE}' загружена.")
#
#     # Ищем все видео
#     video_files = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
#     if not video_files:
#         print("❌ Видео не найдены!")
#         return
#
#     # Обрабатываем видео последовательно
#     for video_path in video_files:
#         process_video(video_path, model)
#
# if __name__ == "__main__":
#     main()
#


import subprocess
import re
import os
import glob

VIDEO_DIR = r"D:\new_downloaded_videos_part5"
OUTPUT_ROOT = r"D:\chunks_voxceleb_part5"
CHUNK = 240        # 4 минуты
MIN_CHUNK = 20
SILENCE_LEEWAY = 30

def get_duration(path):
    cmd = (
        f"ffprobe -v error -show_entries format=duration "
        f"-of default=nk=1:nw=1 \"{path}\""
    )
    return float(subprocess.check_output(cmd, shell=True, text=True).strip())

def detect_silence(path):
    print(f"🔎 Анализ тишины: {os.path.basename(path)}")
    cmd = [
        "ffmpeg", "-i", path, "-af",
        "silencedetect=noise=-30dB:d=0.3", "-f", "null", "-"
    ]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    stderr = proc.stderr.read()
    silence_points = [
        float(m.group(1))
        for m in re.finditer(r"silence_start: (\d+\.?\d*)", stderr)
    ]
    print(f"📌 Найдено {len(silence_points)} точек тишины")
    return silence_points

def process_video(video_path):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.join(OUTPUT_ROOT, video_name)

    # Пропуск уже обработанных видео
    if os.path.exists(out_dir) and os.listdir(out_dir):
        print(f"⚡ Видео {video_name} уже обработано, пропускаем.")
        return

    os.makedirs(out_dir, exist_ok=True)

    duration = get_duration(video_path)
    print(f"🎞 Длительность видео {video_name}: {duration:.2f} секунд")


    if duration <= CHUNK:
        outfile = os.path.join(out_dir, f"{video_name}.mp4")
        print(f"⚡ Короткое видео — копируем без нарезки: {outfile}")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", outfile
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    silence_points = detect_silence(video_path)
    start = 0
    index = 1

    print("\n🚀 Начинаю резку видео...\n")
    while start < duration:
        target = start + CHUNK
        cut_candidates = [t for t in silence_points if t > start]
        safe_cuts = [t for t in cut_candidates if t <= target + SILENCE_LEEWAY]

        if safe_cuts:
            end = safe_cuts[0]
        else:
            end = min(target, duration)

        if end - start < MIN_CHUNK:
            print(f"⚠️ Фрагмент слишком короткий ({end-start:.2f}s), пропускаем точку")
            end = min(target, duration)

        outfile = os.path.join(out_dir, f"{video_name}_{index:03d}.mp4")
        print(f"✂️ [{index}] {start:.2f} → {end:.2f} → {outfile}")

        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(start), "-to", str(end),
            "-i", video_path,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", outfile
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        start = end
        index += 1



    print("\n✅ Готово! Фрагменты сохранены в:", out_dir)


def main():
    video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    print(f"🔍 Найдено видео: {len(video_files)}")

    for video_path in video_files:
        process_video(video_path)

if __name__ == "__main__":
    main()

#
# import os
# import glob
# import subprocess
# import re
#
# VIDEO_DIR = r"D:\new_downloaded_videos_v"
# OUTPUT_ROOT = r"D:\new_chunks_v"
#
# CHUNK = 240        # 4 минуты
# MIN_CHUNK = 20
# SILENCE_LEEWAY = 30
#
#
# def get_duration(path):
#     cmd = (
#         f"ffprobe -v error -show_entries format=duration "
#         f"-of default=nk=1:nw=1 \"{path}\""
#     )
#     return float(subprocess.check_output(cmd, shell=True, text=True).strip())
#
#
# def detect_silence(path):
#     print(f"🔎 Анализ тишины: {os.path.basename(path)}")
#     cmd = [
#         "ffmpeg", "-i", path, "-af",
#         "silencedetect=noise=-30dB:d=0.3",
#         "-f", "null", "-"
#     ]
#     proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
#     stderr = proc.stderr.read()
#
#     silence_points = [
#         float(m.group(1))
#         for m in re.finditer(r"silence_start: (\d+\.?\d*)", stderr)
#     ]
#
#     print(f"📌 Найдено {len(silence_points)} точек тишины")
#     return silence_points
#
#
# def process_video(video_path):
#     video_name = os.path.splitext(os.path.basename(video_path))[0]
#     out_dir = os.path.join(OUTPUT_ROOT, video_name)
#
#     # Пропуск уже обработанных
#     if os.path.exists(out_dir) and os.listdir(out_dir):
#         print(f"⚡ Видео {video_name} уже обработано, пропускаем.")
#         return
#
#     os.makedirs(out_dir, exist_ok=True)
#
#     duration = get_duration(video_path)
#     print(f"🎞 Длительность видео {video_name}: {duration:.2f} секунд")
#
#     # === Короткое видео → просто копируем ===
#     if duration <= CHUNK:
#         outfile = os.path.join(out_dir, f"{video_name}.mp4")
#         print(f"⚡ Короткое видео — копируем без перекодирования")
#
#         subprocess.run([
#             "ffmpeg", "-y",
#             "-i", video_path,
#             "-c", "copy",
#             outfile
#         ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#         return
#
#     # === Анализ тишины (один раз) ===
#     silence_points = detect_silence(video_path)
#
#     start = 0
#     index = 1
#
#     print("\n🚀 Начинаю резку видео...\n")
#
#     while start < duration:
#         target = start + CHUNK
#
#         cut_candidates = [t for t in silence_points if t > start]
#         safe_cuts = [t for t in cut_candidates if t <= target + SILENCE_LEEWAY]
#
#         if safe_cuts:
#             end = safe_cuts[0]
#         else:
#             end = min(target, duration)
#
#         if end - start < MIN_CHUNK:
#             print(f"⚠️ Фрагмент слишком короткий ({end-start:.2f}s), пропускаем")
#             start = end
#             continue
#
#         outfile = os.path.join(out_dir, f"{video_name}_{index:03d}.mp4")
#         print(f"✂️ [{index}] {start:.2f} → {end:.2f}")
#
#         # === БЫСТРАЯ РЕЗКА БЕЗ ПЕРЕКОДИРОВАНИЯ ===
#         subprocess.run([
#             "ffmpeg", "-y",
#             "-ss", str(start),
#             "-to", str(end),
#             "-i", video_path,
#             "-c", "copy",
#             outfile
#         ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#         start = end
#         index += 1
#
#     print("\n✅ Готово! Фрагменты сохранены в:", out_dir)
#
#
# def main():
#     video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
#     print(f"🔍 Найдено видео: {len(video_files)}")
#
#     for video_path in video_files:
#         process_video(video_path)
#
#
# if __name__ == "__main__":
#     main()
