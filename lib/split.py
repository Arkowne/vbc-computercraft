import cv2
import numpy as np
import os
import subprocess
from PIL import Image
import argparse
import random

def preprocess_video(input_path, output_path, width=None, height=None, fps=None, output_dir="oiia"):
    v=input_path;f=cv2.VideoCapture(v);f.set(cv2.CAP_PROP_POS_FRAMES,random.randint(0,int(f.get(cv2.CAP_PROP_FRAME_COUNT))-1));_,i=f.read();cv2.imwrite(output_dir + "preview.jpg",i)
    print("---------------------------------")
    print(output_dir)
    
    """
    Redimensionne la vidéo, met les barres noires si besoin, et change le FPS.
    """
    vf_filters = []
    if width and height:
        # Resize en conservant le ratio et ajout de padding noir
        vf_filters.append(
            f"scale=w={width}:h={height}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,unsharp"
        )

    vf = ",".join(vf_filters) if vf_filters else None

    cmd = ['ffmpeg', '-y', '-i', input_path]
    if vf:
        cmd += ['-vf', vf]
    if fps:
        cmd += ['-r', str(fps)]
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'rgb24', output_path]

    subprocess.run(cmd, check=True)



def extract_delta_frames(video_path, output_dir, force_full_every=10):
    """
    Convertit la vidéo en frames PNG delta (pixels modifiés par rapport à la frame précédente).
    La première frame est toujours complète.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    prev_frame = None
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convertir BGR -> RGBA
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        # Initialiser alpha à 255 (opaque)
        frame_rgba[:, :, 3] = 255

        # Appliquer delta uniquement si ce n'est pas la première frame
        if prev_frame is not None and frame_idx != 0 and (frame_idx % force_full_every != 0):
            # Comparer avec la frame précédente pour créer le delta
            diff_mask = np.any(frame_rgba[:, :, :3] != prev_frame[:, :, :3], axis=2)
            frame_rgba[:, :, 3] = diff_mask.astype(np.uint8) * 255
        # Sinon alpha reste 255 = frame complète (première frame et frames forcées)

        # Sauvegarder PNG
        Image.fromarray(frame_rgba).save(os.path.join(output_dir, f"frame_{frame_idx:05}.png"))

        prev_frame = frame_rgba.copy()
        frame_idx += 1

    cap.release()
    print(f"✅ {frame_idx} frames exportées dans {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Chemin de la vidéo source")
    parser.add_argument("--temp", default="video_temp.mp4", help="Vidéo prétraitée")
    parser.add_argument("--output_dir", default="frames", help="Dossier pour les frames PNG")
    parser.add_argument("--width", type=int, help="Largeur cible")
    parser.add_argument("--height", type=int, help="Hauteur cible")
    parser.add_argument("--fps", type=int, default=15, help="FPS cible")
    parser.add_argument("--force_full_every", type=int, default=10, help="Frame complète toutes les X frames")
    args = parser.parse_args()

    print("🎬 Prétraitement vidéo...")
    preprocess_video(args.input, args.temp, width=args.width, height=args.height, fps=args.fps, output_dir=args.output_dir)

    print("🖼️ Extraction des frames delta...")
    extract_delta_frames(args.temp, args.output_dir, force_full_every=args.force_full_every)
