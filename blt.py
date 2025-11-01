import cv2
import argparse
import os
import numpy as np
import palette

# Palette fixe (ton mapping couleur → char/fg/bg)
COLOR_MAP = palette.COLOR_PALETTE

_KEYS = np.array(list(COLOR_MAP.keys()), dtype=np.float32)  # palette RGB
_VALS = list(COLOR_MAP.values())

# Pré‑conversion palette vers Lab
_keys_rgb_norm = (_KEYS / 255.0).reshape((-1,1,3))
_keys_lab = cv2.cvtColor(_keys_rgb_norm.astype(np.float32), cv2.COLOR_RGB2LAB).reshape((-1,3))

def unsharp_mask(image, sigma=1.0, amount=1.0, threshold=0):
    blurred = cv2.GaussianBlur(image, (0,0), sigma)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    if threshold > 0:
        low_contrast = np.abs(image.astype(np.int16) - blurred.astype(np.int16)) < threshold
        sharpened[low_contrast] = image[low_contrast]
    return np.clip(sharpened, 0, 255).astype(np.uint8)

def quantize_nearest_vectorised(img_lab, keys_lab):
    """
    Version rapide sans dithering, en vectorisant la recherche de palette.
    img_lab : shape (h, w, 3)
    keys_lab : shape (N, 3)
    retourne indices shape (h, w)
    """
    h, w, _ = img_lab.shape
    flat = img_lab.reshape((-1,3))  # (P, 3) où P=h*w
    dists = np.linalg.norm(flat[:, None, :] - keys_lab[None, :, :], axis=2)
    indices_flat = np.argmin(dists, axis=1)
    return indices_flat.reshape((h, w))

def quantize_with_error_diffusion_light(img_lab, keys_lab, vals, diffusion_factor=0.5):
    """Version allégée de diffusion d'erreur.
       diffusion_factor entre 0 et 1 : 1 = diffusion complète (comme avant), <1 = moindre diffusion.
    """
    h, w, _ = img_lab.shape
    indices = np.zeros((h, w), dtype=np.int32)
    err = np.zeros_like(img_lab, dtype=np.float32)
    for y in range(h):
        for x in range(w):
            original = img_lab[y, x] + err[y, x]
            dists = np.linalg.norm(keys_lab - original, axis=1)
            idx = int(np.argmin(dists))
            indices[y, x] = idx
            quant = keys_lab[idx]
            error = original - quant

            ef = diffusion_factor
            if x + 1 < w:
                err[y, x+1]     += error * (7/16 * ef)
            if y + 1 < h and x > 0:
                err[y+1, x-1]   += error * (3/16 * ef)
            if y + 1 < h:
                err[y+1, x]     += error * (5/16 * ef)
            if y + 1 < h and x + 1 < w:
                err[y+1, x+1]   += error * (1/16 * ef)
    return indices

def image_to_blt(infile, outfile, width, height,
                      blur_sigma=0.5,
                      unsharp_sigma=1.0, unsharp_amount=1.0, unsharp_threshold=0,
                      use_dithering=False, diffusion_factor=0.5):
    img = cv2.imread(infile)
    if img is None:
        raise IOError(f"Impossible de charger {infile}")
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

    if blur_sigma > 0:
        rgb = cv2.GaussianBlur(rgb, (3,3), blur_sigma)

    resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA)

    temp_uint8 = np.clip(resized * 255.0, 0, 255).astype(np.uint8)
    sharpened = unsharp_mask(temp_uint8, sigma=unsharp_sigma, amount=unsharp_amount, threshold=unsharp_threshold)
    sharpened_float = sharpened.astype(np.float32) / 255.0
    lab = cv2.cvtColor(sharpened_float, cv2.COLOR_RGB2LAB).astype(np.float32)

    if use_dithering:
        indices = quantize_with_error_diffusion_light(lab, _keys_lab, _VALS, diffusion_factor=diffusion_factor)
    else:
        indices = quantize_nearest_vectorised(lab, _keys_lab)

    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    with open(outfile, "w") as f:
        for y in range(height):
            txt_line = []
            fg_line = []
            bg_line = []
            for x in range(width):
                char, fgh, bgh = _VALS[indices[y, x]]
                txt_line.append(char)
                fg_line.append(fgh)
                bg_line.append(bgh)
            f.write("".join(txt_line) + "\n")
            f.write("".join(fg_line) + "\n")
            f.write("".join(bg_line) + "\n")

    print(f"Généré {outfile} (version rapide, dithering={'oui' if use_dithering else 'non'})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  help="Chemin image source", required=True)
    parser.add_argument("--output", help="Fichier .blt en sortie", required=True)
    parser.add_argument("--width",  type=int, default=50)
    parser.add_argument("--height", type=int, default=30)
    parser.add_argument("--blur_sigma",        type=float, default=0.5)
    parser.add_argument("--unsharp_sigma",     type=float, default=1.0)
    parser.add_argument("--unsharp_amount",    type=float, default=1.0)
    parser.add_argument("--unsharp_threshold", type=float, default=0.0)
    parser.add_argument("--dither",           action="store_true", help="Activer dithering")
    parser.add_argument("--diffusion_factor", type=float, default=0.5)
    args = parser.parse_args()

    image_to_blt(
        infile=args.input,
        outfile=args.output,
        width=args.width,
        height=args.height,
        blur_sigma=args.blur_sigma,
        unsharp_sigma=args.unsharp_sigma,
        unsharp_amount=args.unsharp_amount,
        unsharp_threshold=args.unsharp_threshold,
        use_dithering=args.dither,
        diffusion_factor=args.diffusion_factor
    )
