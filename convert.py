#!/usr/bin/env python3
import os
import subprocess
import cv2
from PIL import Image
import nfp
import argparse
import random
import string
from blt import image_to_blt




def process_frame(frame, density):
    # Convertit l'image en RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    ratio = w / h
    new_w = int(density * ratio)
    new_h = density
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
    pil_img = Image.fromarray(resized)
    return pil_img, resized.shape[1], resized.shape[0]


def generate_id(length=10):
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=length))

def extract_audio_to_dfpwm(input_path, output_path):
    """
    Utilise ffmpeg avec l'encodeur dfpwm intégré pour générer
    un fichier mono 48kHz DFPWM compatible ComputerCraft.
    """
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vn',         # pas de vidéo
        '-ac', '1',    # mono
        '-ar', '48000',# 48 kHz
        '-c:a', 'dfpwm',
        output_path
    ]
    # Supprime la sortie standard/erreur pour plus de propreté
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True,
                        help="Fichier vidéo en entrée")
    parser.add_argument('-d', '--density', type=int, default=17,
                        help="Densité NFP par frame (contrôle la taille du redimensionnement)")
    parser.add_argument('-f', '--fps', type=int, default=7,
                        help="Images par seconde cible")
    args = parser.parse_args()

    video_id = generate_id()
    output_dir = os.path.join("videos", video_id)
    os.makedirs(output_dir, exist_ok=True)

    # Extrait l'audio en DFPWM via ffmpeg
    out_audio = os.path.join(output_dir, 'audio.dfpwm')
    print(f"🔊 Extraction audio vers {out_audio}")
    extract_audio_to_dfpwm(args.input, out_audio)

    # Processus vidéo -> NFP
    cap = cv2.VideoCapture(args.input)
    source_fps = cap.get(cv2.CAP_PROP_FPS) or args.fps
    skip_ratio = int(round(source_fps / args.fps)) if args.fps < source_fps else 1
    print(f"🎥 Source FPS: {source_fps:.2f}, Target FPS: {args.fps}, Skip ratio: {skip_ratio}")

    idx = 0
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_num % skip_ratio == 0:
            # Sauvegarde le frame temporairement
            temp_path = os.path.join(output_dir, f"_temp_{idx:05d}.png")
            cv2.imwrite(temp_path, frame)

            # Convertit la frame en image NFP
            pil_img, resized_width, resized_height = process_frame(frame, args.density)

            # Convertit en .blt avec image_to_blt
            blt_path = os.path.join(output_dir, f"frame_{idx:05d}.blt")
            image_to_blt(temp_path, blt_path, width=resized_width, height=resized_height)
            os.remove(temp_path)

            idx += 1
        frame_num += 1
    cap.release()

    # Fichier metadata
    meta = os.path.join(output_dir, 'metadata.txt')
    with open(meta, 'w') as m:
        m.write(f"fps={args.fps}\nframes={idx}\n")

    print(f"\n✅ Génération terminée !")
    print(f"📂 ID: {video_id}")
    print(f"📁 Dossier: {output_dir}")
    print(f"🖼️ {idx} frames | 🎵 audio.dfpwm | 📝 metadata.txt")

if __name__ == '__main__':
    main()
