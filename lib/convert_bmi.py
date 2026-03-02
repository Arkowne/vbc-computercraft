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
    output_dir.mkdir(exist_ok=True)

    # Step 1: Split to wav segments
    wav_pattern = output_dir / "audio_%d.wav"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", "48000",
        "-f", "segment", "-segment_time", str(segment_sec),
        "-reset_timestamps", "1",
        str(wav_pattern)
    ], check=True)

    # Step 2: Encode each wav to dfpwm
    for wav_file in output_dir.glob("audio_*.wav"):
        dfpwm_file = wav_file.with_suffix(".dfpwm")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(wav_file),
            "-ac", "1", "-ar", "48000",
            "-c:a", "dfpwm",
            str(dfpwm_file)
        ], check=True)
        wav_file.unlink()  # remove the intermediate WAV

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
    process_audio(temp_video, output_dir)

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
