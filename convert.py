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
    ratio = w / h
    new_w = int(density * ratio)
    new_h = density
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help="Fichier vidéo en entrée")
    parser.add_argument('-d', '--density', type=int, default=60, help="Densité NFP par frame")
    parser.add_argument('-f', '--fps', type=int, default=7, help="Images par seconde cible")
    args = parser.parse_args()

    video_id = generate_id()
    output_dir = os.path.join("videos", video_id)
    os.makedirs(output_dir, exist_ok=True)

    # 🎵 Extraction audio
    out_audio = os.path.join(output_dir, 'audio.dfpwm')
    print(f"🔊 Extraction audio vers {out_audio}")
    extract_audio_to_dfpwm(args.input, out_audio)

    # 🎞️ Ouverture vidéo
    cap = cv2.VideoCapture(args.input)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if not source_fps or source_fps <= 0:
        print(f"⚠️ Impossible de lire le FPS source, on utilise fps cible = {args.fps}")
        source_fps = args.fps
    else:
        print(f"✅ FPS source lu correctement : {source_fps:.2f}")
    if source_fps > args.fps:
        skip_ratio = max(1, int(round(source_fps / args.fps)))
    else:
        skip_ratio = 1
    print(f"🎥 Source FPS: {source_fps:.2f}, Target FPS: {args.fps}, Skip ratio: {skip_ratio}")

    # 📸 Génération preview.jpg à partir d'une frame aléatoire
    rand_index = random.randint(0, max(0, total_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, rand_index)
    ret, frame = cap.read()
    if ret:
        pil_img, _, _ = process_frame(frame, args.density)
        preview_path = os.path.join(output_dir, "preview.jpg")
        pil_img.save(preview_path)
        print(f"🖼️ Image de prévisualisation enregistrée : {preview_path}")
    else:
        print("❌ Impossible de capturer une frame pour la preview.")

    # 🔁 Recommencer depuis le début pour le vrai traitement
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    step = source_fps / args.fps
    next_capture = 0.0
    frame_num = 0
    idx = 0
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num >= round(next_capture):
            # on capture
            temp_path = os.path.join(output_dir, f"_temp_{idx:05d}.png")
            cv2.imwrite(temp_path, frame)
            pil_img, w, h = process_frame(frame, args.density)
            blt_path = os.path.join(output_dir, f"frame_{idx:05d}.blt")
            image_to_blt(temp_path, blt_path, width=w, height=h)
            os.remove(temp_path)

            idx += 1
            next_capture += step

        frame_num += 1
    cap.release()

    # 📝 Metadata
    meta = os.path.join(output_dir, 'metadata.txt')
    with open(meta, 'w') as m:
        m.write(f"fps={args.fps}\nframes={idx}\n")

    print(f"\n✅ Génération terminée !")
    print(f"📂 ID: {video_id}")
    print(f"📁 Dossier: {output_dir}")
    print(f"🖼️ {idx} frames | 🎵 audio.dfpwm | 📝 metadata.txt | 🖼️ preview.jpg")

if __name__ == '__main__':
    main()
