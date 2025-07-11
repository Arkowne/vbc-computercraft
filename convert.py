#!/usr/bin/env python3
import os
import subprocess
import cv2
from PIL import Image
import argparse
import random
import string
from blt import image_to_blt

def process_frame(frame, density):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    target_ratio = 4 / 3
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = w
        new_h = int(w / target_ratio)
        pad = (new_h - h) // 2
        padded = cv2.copyMakeBorder(rgb, pad, new_h - h - pad, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    elif current_ratio < target_ratio:
        new_h = h
        new_w = int(h * target_ratio)
        pad = (new_w - w) // 2
        padded = cv2.copyMakeBorder(rgb, 0, 0, pad, new_w - w - pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    else:
        padded = rgb
        new_w, new_h = w, h

    resized = cv2.resize(padded, (int(density * 5 / 3), density), interpolation=cv2.INTER_AREA)
    pil_img = Image.fromarray(resized)
    return pil_img, resized.shape[1], resized.shape[0]

def generate_id(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def extract_audio_to_dfpwm(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'dfpwm',
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def convert_video(input_path, density=60, fps=7):
    video_id = generate_id()
    output_dir = os.path.join("videos", video_id)
    os.makedirs(output_dir, exist_ok=True)

    out_audio = os.path.join(output_dir, 'audio.dfpwm')
    extract_audio_to_dfpwm(input_path, out_audio)

    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if not source_fps or source_fps <= 0:
        source_fps = fps
    step = source_fps / fps
    next_capture = 0.0
    frame_num = 0
    idx = 0

    # Générer preview
    rand_index = random.randint(0, max(0, total_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, rand_index)
    ret, frame = cap.read()
    if ret:
        pil_img, _, _ = process_frame(frame, density)
        preview_path = os.path.join(output_dir, "preview.jpg")
        pil_img.save(preview_path)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num >= round(next_capture):
            temp_path = os.path.join(output_dir, f"_temp_{idx:05d}.png")
            blt_path = os.path.join(output_dir, f"frame_{idx:05d}.blt")
            pil_img, w, h = process_frame(frame, density)
            pil_img.save(temp_path)
            image_to_blt(temp_path, blt_path, width=w, height=h)
            os.remove(temp_path)

            idx += 1
            next_capture += step
        frame_num += 1

    cap.release()
    with open(os.path.join(output_dir, 'metadata.txt'), 'w') as m:
        m.write(f"fps={fps}\nframes={idx}\n")

    return video_id, output_dir

# Entrée CLI
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-d', '--density', type=int, default=60)
    parser.add_argument('-f', '--fps', type=int, default=7)
    args = parser.parse_args()
    convert_video(args.input, args.density, args.fps)
