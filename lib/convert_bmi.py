import lib.split as split
import lib.frames_to_bmi as frames_to_bmi
import argparse
import os
import string
from pathlib import Path
import random
import subprocess

default_fps = 10

def delete_png_in_folder(folder_path):
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Le dossier {folder_path} n'existe pas ou n'est pas un dossier.")
        return

    png_files = list(folder.glob("*.png"))
    if not png_files:
        print(f"⚠️ Aucun fichier PNG trouvé dans {folder_path}.")
        return

    for png in png_files:
        try:
            png.unlink()
            #print(f"🗑️ Supprimé : {png.name}")
        except Exception as e:
            print(f"❌ Impossible de supprimer {png.name} : {e}")

    print(f"✅ Tous les fichiers PNG supprimés dans {folder_path}.")

def extract_audio_to_dfpwm(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'dfpwm',
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_audio(input_path, output_dir):
    out_audio = os.path.join(output_dir, 'audio.dfpwm')
    extract_audio_to_dfpwm(input_path, out_audio)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Chemin de la vidéo source")
    parser.add_argument("--temp", default="video_temp.mp4", help="Vidéo prétraitée")
    parser.add_argument("--output_dir", default="single_video", help="Dossier pour les frames PNG")
    parser.add_argument("--width", type=int, help="Largeur cible")
    parser.add_argument("--height", type=int, help="Hauteur cible")
    parser.add_argument("--fps", type=int, default=default_fps, help="FPS cible")
    parser.add_argument("--force_full_every", type=int, default=10, help="Frame complète toutes les X frames")
    args = parser.parse_args()

    #Genere l'id de la video
    id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


    #print("🎬 Prétraitement vidéo...")
    split.preprocess_video(args.input, args.temp, width=args.width, height=args.height, fps=args.fps, output_dir=args.output_dir)

    print("🔊 Traitement du son...")
    process_audio(args.input, args.output_dir)

    print("🖼️ Extraction des frames delta...")
    split.extract_delta_frames(args.temp, args.output_dir, force_full_every=args.force_full_every)

    print("📁 Création des fichiers .bmi ...")
    frames_to_bmi.convert_png_folder_to_bmi(
    png_dir=args.output_dir, 
    output_dir=args.output_dir,
    width=args.width,
    height=args.height
    )
    delete_png_in_folder(args.output_dir)

    # Trouver le nombre de frame
    count = 1 + sum(1 for f in os.listdir(args.output_dir) if f.startswith("frame_") and os.path.isfile(os.path.join(args.output_dir, f)))
    print("Nombre de frames :", count)

    with open(os.path.join(args.output_dir, 'metadata.txt'), 'w') as m:
        m.write(f"fps={args.fps}\nframes={count}\n")



    with open(os.path.join(args.output_dir, 'lock.txt'), 'w') as m:
        m.write("")  # ou tu peux écrire "locked" ou autre





def convert_main(input_path, video_id='', width=230, height=100, fps=default_fps, force_full_every=10):
    #Genere l'id de la video
    
    if video_id == '':
        video_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    output_dir = "videos/" + video_id + "/"
    temp_video = "temp_" + video_id + ".mp4"

    os.makedirs(output_dir, exist_ok=True)

    print("🎬 Prétraitement vidéo...")
    split.preprocess_video(input_path, temp_video, width=width, height=height, fps=fps, output_dir=output_dir)

    print("🔊 Traitement du son...")
    process_audio(temp_video, output_dir)

    print("🖼️ Extraction des frames delta...")
    split.extract_delta_frames(temp_video, output_dir, force_full_every=force_full_every)

    print("📁 Création des fichiers .bmi ...")
    frames_to_bmi.convert_png_folder_to_bmi(
    png_dir=output_dir, 
    output_dir=output_dir,
    width=width,
    height=height
    )
    delete_png_in_folder(output_dir)

    # Trouver le nombre de frame
    count = sum(1 for f in os.listdir(output_dir) if f.startswith("frame_") and os.path.isfile(os.path.join(output_dir, f))) - 1
    print("Nombre de frames :", count)

    with open(os.path.join(output_dir, 'metadata.txt'), 'w') as m:
        m.write(f"fps={fps}\nframes={count}\n")

    with open(os.path.join(output_dir, 'lock.txt'), 'w') as m:
        m.write("")  # ou tu peux écrire "locked" ou autre
    return video_id