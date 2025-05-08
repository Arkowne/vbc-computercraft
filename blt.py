import cv2
import argparse
import os
import numpy as np
from sklearn.neighbors import KDTree
import palette

COLOR_MAP = palette.COLOR_PALETTE
DEFAULT = (" ", "0", "0")

_KEYS = np.array(list(COLOR_MAP.keys()))
_VALS = list(COLOR_MAP.values())
TREE = KDTree(_KEYS)

# Cache pour éviter de recalculer les mêmes couleurs
CACHE = {}

def find_nearest_color_kd(rgb):
    rgb_tuple = tuple(rgb)
    if rgb_tuple in CACHE:
        return CACHE[rgb_tuple]
    dist, ind = TREE.query([rgb], k=1)
    result = _VALS[ind[0][0]]
    CACHE[rgb_tuple] = result
    return result


def image_to_blt(infile, outfile, width, height):
    img = cv2.imread(infile)
    if img is None:
        raise IOError(f"Impossible de charger {infile}")
    
    # Conversion en RGB
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Redimensionnement à la taille cible
    resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA)

    # Création du dossier de sortie si nécessaire
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)

    # Génération du fichier .blt
    with open(outfile, "w") as f:
        for y in range(height):
            txt_line = []
            fg_line = []
            bg_line = []
            for x in range(width):
                pixel = tuple(resized[y, x])
                if pixel in COLOR_MAP:
                    char, fgh, bgh = COLOR_MAP[pixel]
                else:
                    char, fgh, bgh = find_nearest_color_kd(pixel)
                txt_line.append(char)
                fg_line.append(fgh)
                bg_line.append(bgh)
            f.write("".join(txt_line) + "\n")
            f.write("".join(fg_line) + "\n")
            f.write("".join(bg_line) + "\n")

    print(f"Généré {outfile}")



if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input",  help="Chemin image source")
    p.add_argument("--output", help="Fichier .blt en sortie")
    p.add_argument("--width",  type=int, default=50)
    p.add_argument("--height", type=int, default=30)
    args = p.parse_args()
    image_to_blt(args.input, args.output, args.width, args.height)
