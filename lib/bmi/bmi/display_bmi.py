import struct
from PIL import Image
import argparse

# Palette 16 couleurs (ComputerCraft)
PALETTE = [
    (240, 240, 240), (242, 178,  51), (229, 127, 216), (153, 178, 242),
    (222, 222, 108), (127, 204,  25), (242, 178, 204), ( 76,  76,  76),
    (153, 153, 153), ( 76, 153, 178), (178, 102, 229), ( 51, 102, 204),
    (127, 102,  76), ( 87, 166,  78), (204,  76,  76), ( 17,  17,  17)
]

def read_bmi_sparse(path):
    """Lit un fichier .bmi optimisé (bitstream) et renvoie (w,h,pixels)"""
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 4:
        raise ValueError("Fichier trop court")
    width, height = struct.unpack(">HH", data[:4])
    pixels = [[(1,0,0) for _ in range(width)] for _ in range(height)]

    # Bit-buffer
    buffer = 0
    bits_left = 0
    idx = 4

    def read_bit():
        nonlocal buffer, bits_left, idx
        if bits_left == 0:
            if idx >= len(data):
                return 1  # fin → skip
            buffer = data[idx]
            idx += 1
            bits_left = 8
        bits_left -= 1
        return (buffer >> bits_left) & 1

    for y in range(height):
        for x in range(width):
            skip = read_bit()
            if skip:
                pixels[y][x] = (1,0,0)
            else:
                bg = 0
                fg = 0
                for _ in range(4):
                    bg = (bg << 1) | read_bit()
                for _ in range(4):
                    fg = (fg << 1) | read_bit()
                pixels[y][x] = (0, bg, fg)

    return width, height, pixels

def render_image(width, height, pixels, cell=10):
    """Rend une image PIL fidèle aux couleurs ComputerCraft"""
    img = Image.new("RGB", (width*cell, height*cell), PALETTE[0])
    px = img.load()
    for y in range(height):
        for x in range(width):
            skip, bg, fg = pixels[y][x]
            # Fond
            color_bg = PALETTE[bg]
            for yy in range(cell):
                for xx in range(cell):
                    px[x*cell+xx, y*cell+yy] = color_bg
            # Pixel actif
            if not skip:
                margin = cell // 4
                for yy in range(margin, cell-margin):
                    for xx in range(margin, cell-margin):
                        px[x*cell+xx, y*cell+yy] = PALETTE[fg]
    return img

def show_ccraft_file(path, cell=10, save_path=None):
    w, h, pixels = read_bmi_sparse(path)
    print(f"📄 Image : {w}x{h}, total {w*h} pixels")
    img = render_image(w, h, pixels, cell=cell)
    img.show()
    if save_path:
        img.save(save_path)
        print(f"💾 Image sauvegardée sous {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Fichier .bmi à lire")
    parser.add_argument("--cell", type=int, default=10, help="Taille d’un pixel (zoom)")
    parser.add_argument("--save", help="Chemin pour sauvegarder le rendu")
    args = parser.parse_args()

    show_ccraft_file(args.input, cell=args.cell, save_path=args.save)
