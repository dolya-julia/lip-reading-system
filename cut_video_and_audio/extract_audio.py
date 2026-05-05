# import os
# import glob
# import subprocess
#
# VIDEO_DIR = r"C:\Data\Projects\magistratura\cut_video_and_audio\chunks"
# AUDIO_EXT = ".wav"   # WAV 16kHz для Whisper и Forced Aligner
#
# def extract_audio(video_path):
#     base = os.path.splitext(video_path)[0]
#     audio_path = base + AUDIO_EXT
#
#     if os.path.exists(audio_path):
#         print(f"🔹 Аудио уже существует, пропускаем: {audio_path}")
#         return audio_path
#
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", video_path,
#         "-vn",
#         "-acodec", "pcm_s16le",
#         "-ar", "16000",
#         "-ac", "1",
#         audio_path,
#     ]
#
#     print(f"🎧 Извлекаю аудио: {os.path.basename(video_path)}")
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#     return audio_path
#
#
# def main():
#     # Все mp4 в одной папке
#     videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
#     print(f"📹 Найдено {len(videos)} видео")
#
#     for v in videos:
#         extract_audio(v)
#
#     print("\n✅ Готово! Аудио извлечено.")
#
#
# if __name__ == "__main__":
#     main()


# import subprocess
# import re
# import os
#
# VIDEO = r"C:\Data\Projects\magistratura\words_dataset\downloaded_videos\5VE9nihee7o.mp4"
# CHUNK = 180  # 3 минуты в секундах
#
# # 1) анализируем тишину
# cmd = [
#     "ffmpeg", "-i", VIDEO, "-af",
#     "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-"
# ]
#
# proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
# stderr = proc.stderr.read()
#
# # собираем моменты тишины
# silence_points = []
# for match in re.finditer(r"silence_start: (\d+\.?\d*)", stderr):
#     silence_points.append(float(match.group(1)))
#
# # 2) создаём фрагменты
# output_id = 1
# start = 0
#
# while True:
#     target = start + CHUNK
#
#     # если больше длины — остановиться
#     duration_cmd = subprocess.check_output(
#         f"ffprobe -v error -show_entries format=duration "
#         f"-of default=nk=1:nw=1 {VIDEO}",
#         shell=True, text=True
#     )
#     duration = float(duration_cmd)
#
#     if start >= duration:
#         break
#
#     # ищем ближайшую паузу после target
#     cut_points = [x for x in silence_points if x > start]
#     safe_cuts = [x for x in cut_points if x <= target + 30]  # запас 30s
#
#     if safe_cuts:
#         end = safe_cuts[0]
#     else:
#         end = min(target, duration)
#
#     # 3) режем фрагмент
#     outfile = f"output_{output_id:03d}.mp4"
#     subprocess.run([
#         "ffmpeg", "-i", VIDEO,
#         "-ss", str(start), "-to", str(end),
#         "-c", "copy", outfile
#     ])
#
#     print(f"Создан файл: {outfile} ({start:.2f} → {end:.2f})")
#
#     start = end
#     output_id += 1

import os
import glob
import subprocess
import whisper

VIDEO_DIR = r"D:\chunks_voxceleb_part5"
AUDIO_EXT = ".wav"

# Загружаем модель Whisper (можно tiny/base/small/medium/large)
model = whisper.load_model("small")

def extract_audio(video_path):
    audio_path = os.path.splitext(video_path)[0] + AUDIO_EXT

    if os.path.exists(audio_path):
        print(f"🔹 Аудио уже существует, пропускаем: {audio_path}")
        return audio_path

    print(f"🎧 Извлекаю аудио: {os.path.basename(video_path)}")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return audio_path


def transcribe(audio_path):
    txt_path = os.path.splitext(audio_path)[0] + ".txt"

    if os.path.exists(txt_path):
        print(f"📝 Транскрипция уже существует, пропускаем: {txt_path}")
        return txt_path

    print(f"🔤 Делаю транскрипцию: {os.path.basename(audio_path)}")

    result = model.transcribe(audio_path)
    text = result["text"].strip()

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return txt_path


def main():

    # ищем ВСЕ mp4 по ВСЕМ подпапкам
    videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "**", "*.mp4"), recursive=True))

    print(f"📹 Найдено {len(videos)} видео-сегментов")

    for video in videos:
        print(f"\n=== 🎬 Обрабатываю: {video}")

        audio = extract_audio(video)
        transcribe(audio)

    print("\n✅ Готово! Все фрагменты обработаны.")


if __name__ == "__main__":
    main()
