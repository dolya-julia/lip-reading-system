# import os
# import re
# import subprocess
# from math import ceil
#
# # ----------------- Параметры (настраиваемые) -----------------
# PAUSE_THRESHOLD = 0.4       # пауза между словами для основного разбиения (сек)
# BUFFER = 0.10               # базовый буфер вокруг сегмента (сек) -- минимальный
# COARTICULATION = 0.15       # дополнительный контекст слева/справа для коартикуляции (сек)
# MIN_SEGMENT_DURATION = 0.35 # игнорировать сегменты короче этого (сек)
# MAX_WORDS = 12              # максимальное кол-во слов в одном сегменте (иначе дробим)
# MAX_DURATION = 3.5          # максимальная длительность сегмента (сек) (иначе дробим)
# PREFERRED_SPLIT_TOKENS = set(["and", "so", "but", "then", "or", "because", "so", "then"])
# FFMPEG_PRESET = "fast"
# # ---------------------------------------------------------------
#
#
# def parse_words_from_textgrid(path):
#     """Возвращает интервалы слов только из tier 'words'."""
#     with open(path, "r", encoding="utf-8") as f:
#         tg = f.read()
#
#     tier_pattern = (
#         r'item \[\d+\]:\s*'
#         r'class = "IntervalTier"\s*'
#         r'name = "words"\s*'
#         r'xmin = .*?\s*xmax = .*?\s*'
#         r'intervals: size = \d+\s*(.*?)\s*(?=item \[\d+\]:|$)'
#     )
#
#     tier = re.search(tier_pattern, tg, flags=re.DOTALL)
#     if not tier:
#         return []
#
#     tier_text = tier.group(1)
#
#     interval_pattern = (
#         r"xmin = ([0-9.]+)\s+"
#         r"xmax = ([0-9.]+)\s+"
#         r'text = "(.*?)"'
#     )
#
#     intervals = re.findall(interval_pattern, tier_text, flags=re.DOTALL)
#
#     words = []
#     for start, end, text in intervals:
#         text = text.strip()
#         # пропускаем пустые, <eps>, <unk>
#         if text and text not in ("<eps>", "<unk>"):
#             words.append({
#                 "start": float(start),
#                 "end": float(end),
#                 "word": text.lower()
#             })
#
#     return words
#
#
# def ffmpeg_cut(input_video, start, end, output_video):
#     """Надёжная обрезка: -ss before -i, -t duration after; перекодируем для валидного контейнера."""
#     safe_start = max(0.0, start)
#     duration = max(0.0, end - safe_start)
#     if duration <= 0:
#         return False
#
#     cmd = [
#         "ffmpeg", "-y",
#         "-ss", f"{safe_start}",
#         "-i", input_video,
#         "-t", f"{duration}",
#         "-c:v", "libx264", "-preset", FFMPEG_PRESET,
#         "-c:a", "aac",
#         output_video
#     ]
#     # запускаем и ждём завершения (stderr захватываем для отладки)
#     proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     return proc.returncode == 0
#
#
# def split_long_segment_by_words(words_segment):
#     """
#     Надёжное не-рекурсивное деление длинного сегмента.
#     Делим только по количеству слов и длительности.
#     Никакого риска зависания.
#     """
#     n = len(words_segment)
#     duration = words_segment[-1]["end"] - words_segment[0]["start"]
#
#     # Если сегмент и так короткий - вернуть как есть
#     if n <= MAX_WORDS and duration <= MAX_DURATION:
#         return [words_segment]
#
#     chunks = []
#     current = []
#
#     for w in words_segment:
#         current.append(w)
#
#         # если текущий chunk стал слишком длинным — резать
#         if len(current) >= MAX_WORDS:
#             chunks.append(current)
#             current = []
#
#     if current:
#         chunks.append(current)
#
#     # теперь проверяем длительность каждого чанка
#     final_chunks = []
#     for chunk in chunks:
#         dur = chunk[-1]["end"] - chunk[0]["start"]
#
#         if dur <= MAX_DURATION:
#             final_chunks.append(chunk)
#         else:
#             # если чанк слишком длинный по времени — делим пополам
#             mid = len(chunk) // 2
#             if mid == 0:
#                 final_chunks.append(chunk)  # некуда делить
#             else:
#                 final_chunks.append(chunk[:mid])
#                 final_chunks.append(chunk[mid:])
#
#     return final_chunks
#
#
#
# def build_segments_from_words(words):
#     """Первичная группировка по паузам, затем дробление длинных сегментов."""
#     if not words:
#         return []
#
#     segments = []
#     current = [words[0]]
#
#     for i in range(1, len(words)):
#         prev = words[i - 1]
#         cur = words[i]
#         gap = cur["start"] - prev["end"]
#         if gap > PAUSE_THRESHOLD:
#             # текущий сегмент завершился — возможно вторично расколоть
#             segments.extend(split_long_segment_by_words(current))
#             current = [cur]
#         else:
#             current.append(cur)
#
#     segments.extend(split_long_segment_by_words(current))
#     return segments
#
#
# def make_segment_intervals(chunk):
#     """Возвращает (start_time_with_context, end_time_with_context) для чанка, учитывая коартикуляцию/буфер."""
#     start = chunk[0]["start"]
#     end = chunk[-1]["end"]
#
#     # добавляем буфер + коартикуляцию (суммируем, но ограничиваем по аудио начала)
#     ctx_left = BUFFER + COARTICULATION
#     ctx_right = BUFFER + COARTICULATION
#
#     seg_start = max(0.0, start - ctx_left)
#     seg_end = end + ctx_right
#
#     # минимальная длительность
#     if seg_end - seg_start < MIN_SEGMENT_DURATION:
#         # расширяем равномерно до минимальной длительности
#         mid = (seg_start + seg_end) / 2
#         seg_start = max(0.0, mid - MIN_SEGMENT_DURATION / 2)
#         seg_end = seg_start + MIN_SEGMENT_DURATION
#
#     return seg_start, seg_end
#
#
# def segment_one_video(video_path, textgrid_path, out_root):
#     base = os.path.splitext(os.path.basename(video_path))[0]
#     out_dir = os.path.join(out_root, base)
#     os.makedirs(out_dir, exist_ok=True)
#
#     words = parse_words_from_textgrid(textgrid_path)
#     if not words:
#         print(f"[WARN] No words found in {textgrid_path}")
#         return
#
#     chunks = build_segments_from_words(words)
#
#     seg_id = 0
#     for chunk in chunks:
#         seg_start, seg_end = make_segment_intervals(chunk)
#         duration = seg_end - seg_start
#         if duration < MIN_SEGMENT_DURATION:
#             # пропускаем очень короткие
#             continue
#
#         out_video = os.path.join(out_dir, f"segment_{seg_id:03d}.mp4")
#         out_text = os.path.join(out_dir, f"segment_{seg_id:03d}.txt")
#
#         ok = ffmpeg_cut(video_path, seg_start, seg_end, out_video)
#         if not ok:
#             print(f"[ERROR] ffmpeg failed for {out_video}")
#         else:
#             seg_text = " ".join([w["word"] for w in chunk])
#             with open(out_text, "w", encoding="utf-8") as f:
#                 f.write(seg_text)
#             print(f"[OK] {base}/segment_{seg_id:03d}.mp4  ({duration:.2f}s): {seg_text[:120]}")
#             seg_id += 1
#
#
# def process_folder(input_folder, output_root="segments"):
#     """
#     Проходит по всем *.mp4 в input_folder, находит соответствующий *.TextGrid
#     и режет сегменты в output_root/<video_base>/...
#     """
#     os.makedirs(output_root, exist_ok=True)
#
#     files = os.listdir(input_folder)
#     videos = [f for f in files if f.lower().endswith(".mp4")]
#
#     if not videos:
#         print("No .mp4 files found in", input_folder)
#         return
#
#     for v in sorted(videos):
#         base = os.path.splitext(v)[0]
#         video_path = os.path.join(input_folder, v)
#         textgrid_path = os.path.join(input_folder, base + ".TextGrid")
#         if not os.path.exists(textgrid_path):
#             print(f"[SKIP] No TextGrid for {v}")
#             continue
#
#         print(f"\n=== Processing {v} ===")
#         segment_one_video(video_path, textgrid_path, output_root)
#
#
# if __name__ == "__main__":
#     # Пример - поменяй на твою папку
#     INPUT_FOLDER = r"C:\Data\Projects\magistratura\prepare_dataset\video_segments\video_text\session55"
#     OUTPUT_ROOT = r"C:\Data\Projects\magistratura\prepare_dataset\video_segments\segments"
#     process_folder(INPUT_FOLDER, OUTPUT_ROOT)


# import os
# import glob
# import subprocess
# from textgrid import TextGrid
#
# TARGET_WORDS = {
#     "yes", "no", "hello", "sorry", "please", "thank",
#     "say", "okay", "right", "really",
#     "want", "need", "know", "think", "like",
#     "see", "look", "come", "go", "love",
#     "happy", "sad", "angry", "tired", "scared",
#     "stop", "wait", "help", "start", "again"
# }
#
# PADDING = 0.10
#
# CHUNKS_DIR = r"C:\Data\Projects\magistratura\cut_video_and_audio\chunks"
# OUTPUT_DATASET = r"C:\Data\Projects\magistratura\words_dataset\segments_dataset"
#
#
# def ensure_dir(path):
#     os.makedirs(path, exist_ok=True)
#
#
# def cut_video_segment(video_path, start, end, output_path):
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", video_path,
#         "-ss", str(start),
#         "-to", str(end),
#         "-c:v", "libx264",
#         "-crf", "18",
#         "-preset", "veryfast",
#         "-c:a", "aac",
#         output_path
#     ]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#
# def process_textgrid(textgrid_path, segment_video_path):
#     tg = TextGrid.fromFile(textgrid_path)
#
#     # ищем tier со словами
#     tier = None
#     for t in tg.tiers:
#         if t.name.lower() in ("words", "word", "transcript"):
#             tier = t
#             break
#     if tier is None:
#         print("❌ No word tier:", textgrid_path)
#         return
#
#     segment_name = os.path.splitext(os.path.basename(segment_video_path))[0]
#
#     for interval in tier.intervals:
#         word = interval.mark.lower().strip()
#
#         if word in TARGET_WORDS:
#             start = max(0, interval.minTime - PADDING)
#             end = interval.maxTime + PADDING
#
#             out_dir = os.path.join(OUTPUT_DATASET, word)
#             ensure_dir(out_dir)
#
#             out_name = f"{segment_name}_{word}_{int(start * 1000)}.mp4"
#             out_path = os.path.join(out_dir, out_name)
#
#             print(f"✂️ Вырезаю слово: {word} "
#                   f"({interval.minTime:.2f}-{interval.maxTime:.2f}, padded to {start:.2f}-{end:.2f}) "
#                   f"→ {out_path}")
#
#             cut_video_segment(segment_video_path, start, end, out_path)
#
#
# def main():
#     print("🚀 Сканирование всех сегментов...")
#
#     # ищем сегменты: chunks/*/<videoid>/<videoid_001>.mp4
#     segment_videos = glob.glob(os.path.join(CHUNKS_DIR, "*", "*", "*.mp4"))
#
#     for seg in segment_videos:
#         seg_dir = os.path.dirname(seg)
#         video_id = os.path.basename(seg_dir)  # например ddxHlkIuHqg
#
#         seg_file = os.path.basename(seg)      # ddxHlkIuHqg_001.mp4
#         base = os.path.splitext(seg_file)[0]  # ddxHlkIuHqg_001
#
#         # текстгрид лежит тут:
#         # chunks/collectX/output/<videoid>/<base>.TextGrid
#         collect_folder = os.path.basename(os.path.dirname(seg_dir))
#         tg_path = os.path.join(
#             CHUNKS_DIR,
#             collect_folder,
#             "output",
#             video_id,
#             base + ".TextGrid"
#         )
#
#         if not os.path.exists(tg_path):
#             print("⚠️ TextGrid не найден:", tg_path)
#             continue
#
#         print(f"\n📄 Обработка {base}")
#         process_textgrid(tg_path, seg)
#
#     print("\n✅ ГОТОВО! Слова разложены по папкам:", OUTPUT_DATASET)
#
#
# if __name__ == "__main__":
#     main()

# import os
# import glob
# import subprocess
# from textgrid import TextGrid
#
# TARGET_WORDS = {
#     "yes", "no", "hello", "sorry", "please", "thank",
#     "say", "okay", "right", "really",
#     "want", "need", "know", "think", "like",
#     "see", "look", "come", "go", "love",
#     "happy", "sad", "angry", "tired", "scared",
#     "stop", "wait", "help", "start", "again"
# }
#
# PADDING = 0.10
#
# CHUNKS_DIR = r"D:\new_chunks2"
# OUTPUT_DATASET = r"D:\word_dataset"
#
#
# def ensure_dir(path):
#     os.makedirs(path, exist_ok=True)
#
#
# def segment_already_processed(segment_name, word):
#     pattern = os.path.join(OUTPUT_DATASET, word, f"{segment_name}_{word}_*.mp4")
#     return len(glob.glob(pattern)) > 0
#
#
# def cut_video_segment(video_path, start, end, output_path):
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", video_path,
#         "-ss", str(start),
#         "-to", str(end),
#         "-c:v", "libx264",
#         "-crf", "18",
#         "-preset", "veryfast",
#         "-c:a", "aac",
#         output_path
#     ]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#
# def process_textgrid(textgrid_path, segment_video_path):
#     tg = TextGrid.fromFile(textgrid_path)
#
#     tier = None
#     for t in tg.tiers:
#         if t.name.lower() in ("words", "word", "transcript"):
#             tier = t
#             break
#     if tier is None:
#         print("❌ No word tier:", textgrid_path)
#         return
#
#     segment_name = os.path.splitext(os.path.basename(segment_video_path))[0]
#
#     for interval in tier.intervals:
#         word = interval.mark.lower().strip()
#
#         if word in TARGET_WORDS:
#
#             # Пропуск если уже обработано
#             if segment_already_processed(segment_name, word):
#                 print(f"⏩ Уже обработано: {segment_name} → {word}")
#                 continue
#
#             start = max(0, interval.minTime - PADDING)
#             end = interval.maxTime + PADDING
#
#             out_dir = os.path.join(OUTPUT_DATASET, word)
#             ensure_dir(out_dir)
#
#             out_name = f"{segment_name}_{word}_{int(start * 1000)}.mp4"
#             out_path = os.path.join(out_dir, out_name)
#
#             print(f"✂️ Вырезаю слово: {word} "
#                   f"({interval.minTime:.2f}-{interval.maxTime:.2f}, padded to {start:.2f}-{end:.2f}) "
#                   f"→ {out_path}")
#
#             cut_video_segment(segment_video_path, start, end, out_path)
#
#
# def main():
#     print("🚀 Сканирование всех сегментов...")
#
#     segment_videos = glob.glob(os.path.join(CHUNKS_DIR, "*", "*", "*.mp4"))
#
#     for seg in segment_videos:
#         seg_dir = os.path.dirname(seg)
#         video_id = os.path.basename(seg_dir)
#         seg_file = os.path.basename(seg)
#         base = os.path.splitext(seg_file)[0]
#
#         collect_folder = os.path.basename(os.path.dirname(seg_dir))
#         tg_path = os.path.join(
#             CHUNKS_DIR,
#             collect_folder,
#             "output",
#             video_id,
#             base + ".TextGrid"
#         )
#
#         if not os.path.exists(tg_path):
#             print("⚠️ TextGrid не найден:", tg_path)
#             continue
#
#         print(f"\n📄 Обработка {base}")
#         process_textgrid(tg_path, seg)
#
#     print("\n✅ ГОТОВО! Слова разложены по папкам:", OUTPUT_DATASET)
#
#
# if __name__ == "__main__":
#     main()


# import os
# import glob
# import subprocess
#
# # ===================== НАСТРОЙКИ =====================
#
# TARGET_WORDS = {
#     "bin", "lay", "place", "set",
#     "blue", "red", "green", "white",
#     "zero", "one", "two", "three", "four", "five",
#     "six", "seven", "eight", "nine",
#     "now", "again", "please", "soon"
# }
#
# PADDING = 0.10
# TICKS_PER_SECOND = 25000  # GRID alignment
#
# CHUNKS_DIR = r"D:\archive\data"
# OUTPUT_DATASET = r"D:\grid_word_dataset"
#
# # ====================================================
#
#
# def ensure_dir(path):
#     os.makedirs(path, exist_ok=True)
#
#
# def segment_already_processed(segment_name, word, start_ms):
#     """
#     Проверяем, вырезан ли уже конкретный сегмент
#     """
#     out_path = os.path.join(
#         OUTPUT_DATASET,
#         word,
#         f"{segment_name}_{word}_{start_ms}.mp4"
#     )
#     return os.path.exists(out_path)
#
#
# def cut_video_segment(video_path, start, end, output_path):
#     """
#     Вырезаем видеофрагмент (со звуком)
#     """
#     cmd = [
#         "ffmpeg", "-y",
#         "-ss", str(start),
#         "-to", str(end),
#         "-i", video_path,
#         "-c:v", "libx264",
#         "-preset", "veryfast",
#         "-c:a", "aac",
#         output_path
#     ]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#
# def process_align(align_path, video_path):
#     segment_name = os.path.splitext(os.path.basename(video_path))[0]
#
#     with open(align_path, "r", encoding="utf-8") as f:
#         for line in f:
#             start_tick, end_tick, word = line.strip().split()
#             word = word.lower()
#
#             # пропускаем паузы и фонемы
#             if word == "sil" or len(word) == 1:
#                 continue
#
#             if word not in TARGET_WORDS:
#                 continue
#
#             # ticks → seconds
#             start = int(start_tick) / TICKS_PER_SECOND
#             end = int(end_tick) / TICKS_PER_SECOND
#
#             # padding
#             start = max(0, start - PADDING)
#             end = end + PADDING
#
#             start_ms = int(start * 1000)
#
#             # защита от повторной обработки
#             if segment_already_processed(segment_name, word, start_ms):
#                 print(f"⏩ Уже есть: {segment_name} → {word} [{start_ms}ms]")
#                 continue
#
#             out_dir = os.path.join(OUTPUT_DATASET, word)
#             ensure_dir(out_dir)
#
#             out_name = f"{segment_name}_{word}_{start_ms}.mp4"
#             out_path = os.path.join(out_dir, out_name)
#
#             print(f"✂️ {segment_name} | {word}: {start:.2f}-{end:.2f}")
#             cut_video_segment(video_path, start, end, out_path)
#
#
# def main():
#     print("🚀 Обработка GRID align файлов")
#
#     videos = glob.glob(
#         os.path.join(CHUNKS_DIR, "**", "*.mpg"),
#         recursive=True
#     )
#
#     print(f"📼 Найдено видео: {len(videos)}")
#
#     for video in videos:
#         video_dir = os.path.dirname(video)
#         video_name = os.path.splitext(os.path.basename(video))[0]
#
#         align_path = os.path.join(
#             video_dir,
#             "align",
#             video_name + ".align"
#         )
#
#         if not os.path.exists(align_path):
#             print("⚠️ align не найден:", align_path)
#             continue
#
#         print(f"\n📄 {video_name}")
#         process_align(align_path, video)
#
#     print("\n✅ ГОТОВО! Датасет:", OUTPUT_DATASET)
#
#
# if __name__ == "__main__":
#     main()

import os
import glob
import subprocess
from textgrid import TextGrid

TARGET_WORDS = {
    "bin", "lay", "place", "set",
    "blue", "red", "green", "white",
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine",
    "now", "again", "please", "soon"
}

PADDING = 0.10

CHUNKS_DIR = r"D:\chunks_voxceleb_part5_mfa"
OUTPUT_DATASET = r"D:\word_dataset_part5_voxceleb"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def segment_already_processed(segment_name, word):
    pattern = os.path.join(OUTPUT_DATASET, word, f"{segment_name}_{word}_*.mp4")
    return len(glob.glob(pattern)) > 0


def cut_video_segment(video_path, start, end, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ss", str(start),
        "-to", str(end),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-c:a", "aac",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def process_textgrid(textgrid_path, segment_video_path):
    tg = TextGrid.fromFile(textgrid_path)

    tier = None
    for t in tg.tiers:
        if t.name.lower() in ("words", "word", "transcript"):
            tier = t
            break
    if tier is None:
        print("❌ No word tier:", textgrid_path)
        return

    segment_name = os.path.splitext(os.path.basename(segment_video_path))[0]

    for interval in tier.intervals:
        word = interval.mark.lower().strip()

        if word in TARGET_WORDS:

            # Пропуск если уже обработано
            if segment_already_processed(segment_name, word):
                print(f"⏩ Уже обработано: {segment_name} → {word}")
                continue

            start = max(0, interval.minTime - PADDING)
            end = interval.maxTime + PADDING

            out_dir = os.path.join(OUTPUT_DATASET, word)
            ensure_dir(out_dir)

            out_name = f"{segment_name}_{word}_{int(start * 1000)}.mp4"
            out_path = os.path.join(out_dir, out_name)

            print(f"✂️ Вырезаю слово: {word} "
                  f"({interval.minTime:.2f}-{interval.maxTime:.2f}, padded to {start:.2f}-{end:.2f}) "
                  f"→ {out_path}")

            cut_video_segment(segment_video_path, start, end, out_path)


def main():
    print("🚀 Сканирование всех сегментов...")

    segment_videos = glob.glob(os.path.join(CHUNKS_DIR, "*", "*", "*.mp4"))

    for seg in segment_videos:
        seg_dir = os.path.dirname(seg)
        video_id = os.path.basename(seg_dir)
        seg_file = os.path.basename(seg)
        base = os.path.splitext(seg_file)[0]

        collect_folder = os.path.basename(os.path.dirname(seg_dir))
        tg_path = os.path.join(
            CHUNKS_DIR,
            collect_folder,
            "output",
            video_id,
            base + ".TextGrid"
        )

        if not os.path.exists(tg_path):
            print("⚠️ TextGrid не найден:", tg_path)
            continue

        print(f"\n📄 Обработка {base}")
        process_textgrid(tg_path, seg)

    print("\n✅ ГОТОВО! Слова разложены по папкам:", OUTPUT_DATASET)


if __name__ == "__main__":
    main()

