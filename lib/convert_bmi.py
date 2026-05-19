import lib.split as split
import lib.frames_to_bmi as frames_to_bmi
import argparse
import os
import string
from pathlib import Path
import random
import subprocess
import wave
import dfpwm
import math
import av
import numpy as np

default_fps = 10
default_force_full = 12

def delete_png_in_folder(folder_path):
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ The folder {folder_path} does not exist or is not a directory.")
        return

    png_files = list(folder.glob("*.png"))
    if not png_files:
        print(f"⚠️ No PNG files found in {folder_path}.")
        return

    for png in png_files:
        try:
            png.unlink()
        except Exception as e:
            print(f"❌ Unable to delete {png.name}: {e}")

    print(f"✅ All PNG files deleted in {folder_path}.")




def extract_audio_to_dfpwm(input_path, output_dir, segment_sec=30):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    SAMPLE_RATE = 48000
    segment_samples = SAMPLE_RATE * segment_sec

    container = av.open(str(input_path))
    audio_stream = next((s for s in container.streams if s.type == "audio"), None)

    if audio_stream is None:
        container.close()
        raise ValueError("Aucune piste audio trouvée")

    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=SAMPLE_RATE,
    )

    buffer_parts = []
    buffer_count = 0
    segment_index = 0

    def write_segment(pcm_int16: np.ndarray, index: int):
        # int16 mono -> float64 [-1.0, 1.0]
        audio_float64 = pcm_int16.astype(np.float64) / 32768.0

        encoded = dfpwm.compressor(audio_float64)

        out_file = output_dir / f"audio_{index}.dfpwm"

        with open(out_file, "wb") as f:
            f.write(encoded)

        print(f"✅ Segment écrit : {out_file}")

    def flush_if_needed(force=False):
        nonlocal buffer_parts, buffer_count, segment_index

        if buffer_count == 0:
            return

        joined = np.concatenate(buffer_parts)

        while len(joined) >= segment_samples:
            segment = joined[:segment_samples]
            joined = joined[segment_samples:]

            write_segment(segment, segment_index)
            segment_index += 1

        buffer_parts = [joined] if len(joined) else []
        buffer_count = len(joined)

        if force and buffer_count > 0:
            write_segment(joined, segment_index)
            segment_index += 1
            buffer_parts = []
            buffer_count = 0

    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            resampled_frames = resampler.resample(frame)

            if not resampled_frames:
                continue

            for rframe in resampled_frames:
                pcm = rframe.to_ndarray()
                pcm = np.asarray(pcm)

                # mono => parfois (1, N), parfois (N,)
                if pcm.ndim > 1:
                    pcm = pcm[0]

                pcm = pcm.astype(np.int16, copy=False)

                buffer_parts.append(pcm)
                buffer_count += len(pcm)

                while buffer_count >= segment_samples:
                    joined = np.concatenate(buffer_parts)
                    segment = joined[:segment_samples]
                    remain = joined[segment_samples:]

                    write_segment(segment, segment_index)
                    segment_index += 1

                    buffer_parts = [remain] if len(remain) else []
                    buffer_count = len(remain)

    # flush du resampler + reste du buffer
    tail_frames = resampler.resample(None)
    if tail_frames:
        for rframe in tail_frames:
            pcm = rframe.to_ndarray()
            pcm = np.asarray(pcm)
            if pcm.ndim > 1:
                pcm = pcm[0]
            pcm = pcm.astype(np.int16, copy=False)
            buffer_parts.append(pcm)
            buffer_count += len(pcm)

    if buffer_count > 0:
        joined = np.concatenate(buffer_parts)
        write_segment(joined, segment_index)

    container.close()
    print("✅ Segmented and encoded to DFPWM!")


def process_audio(input_path, output_dir):
    extract_audio_to_dfpwm(input_path, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the source video")
    parser.add_argument("--temp", default="video_temp.mp4", help="Preprocessed video")
    parser.add_argument("--output_dir", default="single_video", help="Directory for PNG frames")
    parser.add_argument("--width", type=int, help="Target width")
    parser.add_argument("--height", type=int, help="Target height")
    parser.add_argument("--fps", type=int, default=default_fps, help="Target FPS")
    parser.add_argument("--force_full_every", type=int, default=default_force_full, help="Full frame every X frames")
    args = parser.parse_args()

    id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    split.preprocess_video(args.input, args.temp, width=args.width, height=args.height, fps=args.fps, output_dir=args.output_dir)

    print("🔊 Processing audio...")
    process_audio(args.input, args.output_dir)

    print("🖼️ Extracting delta frames...")
    split.extract_delta_frames(args.temp, args.output_dir, force_full_every=args.force_full_every)

    print("📁 Creating .bmi files...")
    frames_to_bmi.convert_png_folder_to_bmi(
    png_dir=args.output_dir, 
    output_dir=args.output_dir,
    width=args.width,
    height=args.height
    )
    delete_png_in_folder(args.output_dir)

    count = 1 + sum(1 for f in os.listdir(args.output_dir) if f.startswith("frame_") and os.path.isfile(os.path.join(args.output_dir, f)))
    print("Number of frames:", count)

    with open(os.path.join(args.output_dir, 'metadata.txt'), 'w') as m:
        m.write(f"fps={args.fps}\nframes={count}\n")

    with open(os.path.join(args.output_dir, 'lock.txt'), 'w') as m:
        m.write("")

def convert_main(input_path, video_id='', width=230, height=100, fps=default_fps, force_full_every=default_force_full):
    if video_id == '':
        video_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    output_dir = "videos/" + video_id + "/"
    temp_video = "temp_" + video_id + ".mp4"

    os.makedirs(output_dir, exist_ok=True)

    print("🎬 Video preprocessing...")
    split.preprocess_video(input_path, temp_video, width=width, height=height, fps=fps, output_dir=output_dir)

    print("🔊 Processing audio...")
    process_audio(input_path, output_dir)

    print("🖼️ Extracting delta frames...")
    split.extract_delta_frames(temp_video, output_dir, force_full_every=force_full_every)

    print("📁 Creating .bmi files...")
    frames_to_bmi.convert_png_folder_to_bmi(
    png_dir=output_dir, 
    output_dir=output_dir,
    width=width,
    height=height
    )
    delete_png_in_folder(output_dir)

    count = sum(1 for f in os.listdir(output_dir) if f.startswith("frame_") and os.path.isfile(os.path.join(output_dir, f))) - 1
    print("Number of frames:", count)

    with open(os.path.join(output_dir, 'metadata.txt'), 'w') as m:
        m.write(f"fps={fps}\nframes={count}\n")

    with open(os.path.join(output_dir, 'lock.txt'), 'w') as m:
        m.write("")
    return video_id
