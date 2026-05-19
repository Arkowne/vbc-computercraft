import cv2
import os
import numpy as np
import struct
import argparse
import io
import av
from scipy.spatial import KDTree

COLOR_MAP = {
    (240, 240, 240): ("/127", '0', '0'),
    (241, 209, 145): ("/127", '0', '1'),
    (234, 183, 228): ("/127", '0', '2'),
    (196, 209, 241): ("/127", '0', '3'),
    (231, 231, 174): ("/127", '0', '4'),
    (183, 222, 132): ("/127", '0', '5'),
    (241, 209, 222): ("/127", '0', '6'),
    (158, 158, 158): ("/127", '0', '7'),
    (196, 196, 196): ("/127", '0', '8'),
    (158, 196, 209): ("/127", '0', '9'),
    (209, 171, 234): ("/127", '0', 'a'),
    (145, 171, 222): ("/127", '0', 'b'),
    (183, 171, 158): ("/127", '0', 'c'),
    (163, 203, 159): ("/127", '0', 'd'),
    (222, 158, 158): ("/127", '0', 'e'),
    (128, 128, 128): ("/127", '0', 'f'),
    (241, 209, 145): ("/127", '1', '0'),
    (242, 178, 51): ("/127", '1', '1'),
    (235, 152, 133): ("/127", '1', '2'),
    (197, 178, 146): ("/127", '1', '3'),
    (232, 200, 79): ("/127", '1', '4'),
    (184, 191, 38): ("/127", '1', '5'),
    (242, 178, 127): ("/127", '1', '6'),
    (159, 127, 63): ("/127", '1', '7'),
    (197, 165, 102): ("/127", '1', '8'),
    (159, 165, 114): ("/127", '1', '9'),
    (210, 140, 140): ("/127", '1', 'a'),
    (146, 140, 127): ("/127", '1', 'b'),
    (184, 140, 63): ("/127", '1', 'c'),
    (164, 172, 64): ("/127", '1', 'd'),
    (223, 127, 63): ("/127", '1', 'e'),
    (129, 97, 34): ("/127", '1', 'f'),
    (234, 183, 228): ("/127", '2', '0'),
    (235, 152, 133): ("/127", '2', '1'),
    (229, 127, 216): ("/127", '2', '2'),
    (191, 152, 229): ("/127", '2', '3'),
    (225, 174, 162): ("/127", '2', '4'),
    (178, 165, 120): ("/127", '2', '5'),
    (235, 152, 210): ("/127", '2', '6'),
    (152, 101, 146): ("/127", '2', '7'),
    (191, 140, 184): ("/127", '2', '8'),
    (152, 140, 197): ("/127", '2', '9'),
    (203, 114, 222): ("/127", '2', 'a'),
    (140, 114, 210): ("/127", '2', 'b'),
    (178, 114, 146): ("/127", '2', 'c'),
    (158, 146, 147): ("/127", '2', 'd'),
    (216, 101, 146): ("/127", '2', 'e'),
    (123, 72, 116): ("/127", '2', 'f'),
    (196, 209, 241): ("/127", '3', '0'),
    (197, 178, 146): ("/127", '3', '1'),
    (191, 152, 229): ("/127", '3', '2'),
    (153, 178, 242): ("/127", '3', '3'),
    (187, 200, 175): ("/127", '3', '4'),
    (140, 191, 133): ("/127", '3', '5'),
    (197, 178, 223): ("/127", '3', '6'),
    (114, 127, 159): ("/127", '3', '7'),
    (153, 165, 197): ("/127", '3', '8'),
    (114, 165, 210): ("/127", '3', '9'),
    (165, 140, 235): ("/127", '3', 'a'),
    (102, 140, 223): ("/127", '3', 'b'),
    (140, 140, 159): ("/127", '3', 'c'),
    (120, 172, 160): ("/127", '3', 'd'),
    (178, 127, 159): ("/127", '3', 'e'),
    (85, 97, 129): ("/127", '3', 'f'),
    (231, 231, 174): ("/127", '4', '0'),
    (232, 200, 79): ("/127", '4', '1'),
    (225, 174, 162): ("/127", '4', '2'),
    (187, 200, 175): ("/127", '4', '3'),
    (222, 222, 108): ("/127", '4', '4'),
    (174, 213, 66): ("/127", '4', '5'),
    (232, 200, 156): ("/127", '4', '6'),
    (149, 149, 92): ("/127", '4', '7'),
    (187, 187, 130): ("/127", '4', '8'),
    (149, 187, 143): ("/127", '4', '9'),
    (200, 162, 168): ("/127", '4', 'a'),
    (136, 162, 156): ("/127", '4', 'b'),
    (174, 162, 92): ("/127", '4', 'c'),
    (154, 194, 93): ("/127", '4', 'd'),
    (213, 149, 92): ("/127", '4', 'e'),
    (119, 119, 62): ("/127", '4', 'f'),
    (183, 222, 132): ("/127", '5', '0'),
    (184, 191, 38): ("/127", '5', '1'),
    (178, 165, 120): ("/127", '5', '2'),
    (140, 191, 133): ("/127", '5', '3'),
    (174, 213, 66): ("/127", '5', '4'),
    (127, 204, 25): ("/127", '5', '5'),
    (184, 191, 114): ("/127", '5', '6'),
    (101, 140, 50): ("/127", '5', '7'),
    (140, 178, 89): ("/127", '5', '8'),
    (101, 178, 101): ("/127", '5', '9'),
    (152, 153, 127): ("/127", '5', 'a'),
    (89, 153, 114): ("/127", '5', 'b'),
    (127, 153, 50): ("/127", '5', 'c'),
    (107, 185, 51): ("/127", '5', 'd'),
    (165, 140, 50): ("/127", '5', 'e'),
    (72, 110, 21): ("/127", '5', 'f'),
    (241, 209, 222): ("/127", '6', '0'),
    (242, 178, 127): ("/127", '6', '1'),
    (235, 152, 210): ("/127", '6', '2'),
    (197, 178, 223): ("/127", '6', '3'),
    (232, 200, 156): ("/127", '6', '4'),
    (184, 191, 114): ("/127", '6', '5'),
    (242, 178, 204): ("/127", '6', '6'),
    (159, 127, 140): ("/127", '6', '7'),
    (197, 165, 178): ("/127", '6', '8'),
    (159, 165, 191): ("/127", '6', '9'),
    (210, 140, 216): ("/127", '6', 'a'),
    (146, 140, 204): ("/127", '6', 'b'),
    (184, 140, 140): ("/127", '6', 'c'),
    (164, 172, 141): ("/127", '6', 'd'),
    (223, 127, 140): ("/127", '6', 'e'),
    (129, 97, 110): ("/127", '6', 'f'),
    (158, 158, 158): ("/127", '7', '0'),
    (159, 127, 63): ("/127", '7', '1'),
    (152, 101, 146): ("/127", '7', '2'),
    (114, 127, 159): ("/127", '7', '3'),
    (149, 149, 92): ("/127", '7', '4'),
    (101, 140, 50): ("/127", '7', '5'),
    (159, 127, 140): ("/127", '7', '6'),
    (76, 76, 76): ("/127", '7', '7'),
    (114, 114, 114): ("/127", '7', '8'),
    (76, 114, 127): ("/127", '7', '9'),
    (127, 89, 152): ("/127", '7', 'a'),
    (63, 89, 140): ("/127", '7', 'b'),
    (101, 89, 76): ("/127", '7', 'c'),
    (81, 121, 77): ("/127", '7', 'd'),
    (140, 76, 76): ("/127", '7', 'e'),
    (46, 46, 46): ("/127", '7', 'f'),
    (196, 196, 196): ("/127", '8', '0'),
    (197, 165, 102): ("/127", '8', '1'),
    (191, 140, 184): ("/127", '8', '2'),
    (153, 165, 197): ("/127", '8', '3'),
    (187, 187, 130): ("/127", '8', '4'),
    (140, 178, 89): ("/127", '8', '5'),
    (197, 165, 178): ("/127", '8', '6'),
    (114, 114, 114): ("/127", '8', '7'),
    (153, 153, 153): ("/127", '8', '8'),
    (114, 153, 165): ("/127", '8', '9'),
    (165, 127, 191): ("/127", '8', 'a'),
    (102, 127, 178): ("/127", '8', 'b'),
    (140, 127, 114): ("/127", '8', 'c'),
    (120, 159, 115): ("/127", '8', 'd'),
    (178, 114, 114): ("/127", '8', 'e'),
    (85, 85, 85): ("/127", '8', 'f'),
    (158, 196, 209): ("/127", '9', '0'),
    (159, 165, 114): ("/127", '9', '1'),
    (152, 140, 197): ("/127", '9', '2'),
    (114, 165, 210): ("/127", '9', '3'),
    (149, 187, 143): ("/127", '9', '4'),
    (101, 178, 101): ("/127", '9', '5'),
    (159, 165, 191): ("/127", '9', '6'),
    (76, 114, 127): ("/127", '9', '7'),
    (114, 153, 165): ("/127", '9', '8'),
    (76, 153, 178): ("/127", '9', '9'),
    (127, 127, 203): ("/127", '9', 'a'),
    (63, 127, 191): ("/127", '9', 'b'),
    (101, 127, 127): ("/127", '9', 'c'),
    (81, 159, 128): ("/127", '9', 'd'),
    (140, 114, 127): ("/127", '9', 'e'),
    (46, 85, 97): ("/127", '9', 'f'),
    (209, 171, 234): ("/127", 'a', '0'),
    (210, 140, 140): ("/127", 'a', '1'),
    (203, 114, 222): ("/127", 'a', '2'),
    (165, 140, 235): ("/127", 'a', '3'),
    (200, 162, 168): ("/127", 'a', '4'),
    (152, 153, 127): ("/127", 'a', '5'),
    (210, 140, 216): ("/127", 'a', '6'),
    (127, 89, 152): ("/127", 'a', '7'),
    (165, 127, 191): ("/127", 'a', '8'),
    (127, 127, 203): ("/127", 'a', '9'),
    (178, 102, 229): ("/127", 'a', 'a'),
    (114, 102, 216): ("/127", 'a', 'b'),
    (152, 102, 152): ("/127", 'a', 'c'),
    (132, 134, 153): ("/127", 'a', 'd'),
    (191, 89, 152): ("/127", 'a', 'e'),
    (97, 59, 123): ("/127", 'a', 'f'),
    (145, 171, 222): ("/127", 'b', '0'),
    (146, 140, 127): ("/127", 'b', '1'),
    (140, 114, 210): ("/127", 'b', '2'),
    (102, 140, 223): ("/127", 'b', '3'),
    (136, 162, 156): ("/127", 'b', '4'),
    (89, 153, 114): ("/127", 'b', '5'),
    (146, 140, 204): ("/127", 'b', '6'),
    (63, 89, 140): ("/127", 'b', '7'),
    (102, 127, 178): ("/127", 'b', '8'),
    (63, 127, 191): ("/127", 'b', '9'),
    (114, 102, 216): ("/127", 'b', 'a'),
    (51, 102, 204): ("/127", 'b', 'b'),
    (89, 102, 140): ("/127", 'b', 'c'),
    (69, 134, 141): ("/127", 'b', 'd'),
    (127, 89, 140): ("/127", 'b', 'e'),
    (34, 59, 110): ("/127", 'b', 'f'),
    (183, 171, 158): ("/127", 'c', '0'),
    (184, 140, 63): ("/127", 'c', '1'),
    (178, 114, 146): ("/127", 'c', '2'),
    (140, 140, 159): ("/127", 'c', '3'),
    (174, 162, 92): ("/127", 'c', '4'),
    (127, 153, 50): ("/127", 'c', '5'),
    (184, 140, 140): ("/127", 'c', '6'),
    (101, 89, 76): ("/127", 'c', '7'),
    (140, 127, 114): ("/127", 'c', '8'),
    (101, 127, 127): ("/127", 'c', '9'),
    (152, 102, 152): ("/127", 'c', 'a'),
    (89, 102, 140): ("/127", 'c', 'b'),
    (127, 102, 76): ("/127", 'c', 'c'),
    (107, 134, 77): ("/127", 'c', 'd'),
    (165, 89, 76): ("/127", 'c', 'e'),
    (72, 59, 46): ("/127", 'c', 'f'),
    (163, 203, 159): ("/127", 'd', '0'),
    (164, 172, 64): ("/127", 'd', '1'),
    (158, 146, 147): ("/127", 'd', '2'),
    (120, 172, 160): ("/127", 'd', '3'),
    (154, 194, 93): ("/127", 'd', '4'),
    (107, 185, 51): ("/127", 'd', '5'),
    (164, 172, 141): ("/127", 'd', '6'),
    (81, 121, 77): ("/127", 'd', '7'),
    (120, 159, 115): ("/127", 'd', '8'),
    (81, 159, 128): ("/127", 'd', '9'),
    (132, 134, 153): ("/127", 'd', 'a'),
    (69, 134, 141): ("/127", 'd', 'b'),
    (107, 134, 77): ("/127", 'd', 'c'),
    (87, 166, 78): ("/127", 'd', 'd'),
    (145, 121, 77): ("/127", 'd', 'e'),
    (52, 91, 47): ("/127", 'd', 'f'),
    (222, 158, 158): ("/127", 'e', '0'),
    (223, 127, 63): ("/127", 'e', '1'),
    (216, 101, 146): ("/127", 'e', '2'),
    (178, 127, 159): ("/127", 'e', '3'),
    (213, 149, 92): ("/127", 'e', '4'),
    (165, 140, 50): ("/127", 'e', '5'),
    (223, 127, 140): ("/127", 'e', '6'),
    (140, 76, 76): ("/127", 'e', '7'),
    (178, 114, 114): ("/127", 'e', '8'),
    (140, 114, 127): ("/127", 'e', '9'),
    (191, 89, 152): ("/127", 'e', 'a'),
    (127, 89, 140): ("/127", 'e', 'b'),
    (165, 89, 76): ("/127", 'e', 'c'),
    (145, 121, 77): ("/127", 'e', 'd'),
    (204, 76, 76): ("/127", 'e', 'e'),
    (110, 46, 46): ("/127", 'e', 'f'),
    (128, 128, 128): ("/127", 'f', '0'),
    (129, 97, 34): ("/127", 'f', '1'),
    (123, 72, 116): ("/127", 'f', '2'),
    (85, 97, 129): ("/127", 'f', '3'),
    (119, 119, 62): ("/127", 'f', '4'),
    (72, 110, 21): ("/127", 'f', '5'),
    (129, 97, 110): ("/127", 'f', '6'),
    (46, 46, 46): ("/127", 'f', '7'),
    (85, 85, 85): ("/127", 'f', '8'),
    (46, 85, 97): ("/127", 'f', '9'),
    (97, 59, 123): ("/127", 'f', 'a'),
    (34, 59, 110): ("/127", 'f', 'b'),
    (72, 59, 46): ("/127", 'f', 'c'),
    (52, 91, 47): ("/127", 'f', 'd'),
    (110, 46, 46): ("/127", 'f', 'e'),
    (17, 17, 17): ("/127", 'f', 'f'),
}

COLOR_MAP_DEFAULT = {
    (240, 240, 240): ("/127", "0", "0"),
    (242, 178,  51): ("/127", "1", "1"),
    (229, 127, 216): ("/127", "2", "2"),
    (153, 178, 242): ("/127", "3", "3"),
    (222, 222, 108): ("/127", "4", "4"),
    (127, 204,  25): ("/127", "5", "5"),
    (242, 178, 204): ("/127", "6", "6"),
    ( 76,  76,  76): ("/127", "7", "7"),
    (153, 153, 153): ("/127", "8", "8"),
    ( 76, 153, 178): ("/127", "9", "9"),
    (178, 102, 229): ("/127", "a", "a"),
    ( 51, 102, 204): ("/127", "b", "b"),
    (127, 102,  76): ("/127", "c", "c"),
    ( 87, 166,  78): ("/127", "d", "d"),
    (204,  76,  76): ("/127", "e", "e"),
    ( 17,  17,  17): ("/127", "f", "f"),
}

# ── Structures pré-calculées (init unique au chargement du module) ──────────
_VALS = list(COLOR_MAP.values())
_KEYS = np.array(list(COLOR_MAP.keys()), dtype=np.float32)

# Conversion LAB des clés couleur (pour la quantification)
_keys_rgb_uint8 = _KEYS.reshape((-1, 1, 3)).astype(np.uint8)
_keys_lab = cv2.cvtColor(_keys_rgb_uint8, cv2.COLOR_RGB2LAB).reshape((-1, 3)).astype(np.float32)

# KDTree pour la recherche du plus proche voisin en O(N·log K)
_KDTREE = KDTree(_keys_lab)

# Tableaux bg/fg pré-calculés : évite int(hex,16) à chaque pixel
_BG = np.array([int(v[1], 16) for v in _VALS], dtype=np.uint8)
_FG = np.array([int(v[2], 16) for v in _VALS], dtype=np.uint8)


# ── Helpers image ────────────────────────────────────────────────────────────

def enhance_contrast(image, alpha=1.5, beta=0):
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


def unsharp_mask(image, sigma=1.0, amount=1.5, threshold=0):
    blurred = cv2.GaussianBlur(image, (0, 0), sigma)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    if threshold > 0:
        low_contrast = np.abs(image.astype(np.int16) - blurred.astype(np.int16)) < threshold
        sharpened[low_contrast] = image[low_contrast]
    return np.clip(sharpened, 0, 255).astype(np.uint8)


# ── Quantification vectorisée via KDTree ─────────────────────────────────────

def quantize_nearest_vectorised(img_lab):
    """Retourne un tableau 2D d'indices dans COLOR_MAP."""
    flat = img_lab.reshape(-1, 3).astype(np.float32)
    _, indices_flat = _KDTREE.query(flat, workers=-1)   # multithread automatique
    return indices_flat.reshape(img_lab.shape[:2])


# ── Encodage bit-stream vectorisé ────────────────────────────────────────────

def _encode_to_bitstream(indices_2d, alpha_2d):
    """
    Encode l'image quantifiée en flux de bits BMI.

    Format par pixel :
      - pixel transparent (alpha < 128) : 1 bit  → '1'
      - pixel actif                      : 9 bits → '0' + 4 bits bg + 4 bits fg

    Retourne bytes (sans l'entête width/height).
    """
    h, w = indices_2d.shape
    flat_idx   = indices_2d.flatten()          # (N,)
    flat_alpha = alpha_2d.flatten()            # (N,)
    N = len(flat_idx)

    skip   = flat_alpha < 128                  # booléen (N,)
    active = ~skip

    bg = _BG[flat_idx]                         # (N,) valeurs 0-15
    fg = _FG[flat_idx]                         # (N,)

    # ── Construire le tableau de bits ────────────────────────────────────────
    # Pire cas : N pixels × 9 bits chacun
    bits = np.zeros(N * 9, dtype=np.uint8)

    base = np.arange(N, dtype=np.int64) * 9

    # Pixels transparents : bit 0 = 1, les 8 suivants restent 0 (inutilisés)
    bits[base[skip]] = 1

    # Pixels actifs : bit 0 = 0 (déjà 0), bits 1-4 = bg MSB→LSB, bits 5-8 = fg
    base_a = base[active]
    bg_a   = bg[active].astype(np.uint8)
    fg_a   = fg[active].astype(np.uint8)

    for shift, offset in zip((3, 2, 1, 0), (1, 2, 3, 4)):
        bits[base_a + offset] = (bg_a >> shift) & 1
    for shift, offset in zip((3, 2, 1, 0), (5, 6, 7, 8)):
        bits[base_a + offset] = (fg_a >> shift) & 1

    # ── Calcul de la longueur réelle du flux ─────────────────────────────────
    # pixels transparents : 1 bit,  pixels actifs : 9 bits
    n_bits = int(skip.sum()) * 1 + int(active.sum()) * 9

    # Construire le flux compacté sans les bits inutilisés des pixels skip
    # Pour éviter une boucle Python, on repack directement avec np.packbits
    # après avoir retiré les zéros de rembourrage des pixels skip.
    # Stratégie : reconstruire un flux dense sans trous.
    real_bits = np.empty(n_bits, dtype=np.uint8)
    pos = 0
    # Vecteurisation par bloc de pixels (skip = 1 bit, active = 9 bits)
    # On reconstruit le flux dense en NumPy grâce aux masques.

    # Indices de pixels dans l'ordre raster
    skip_mask   = skip
    active_mask = active

    # Bits des pixels skip (juste le bit '1')
    skip_bits = np.ones(int(skip.sum()), dtype=np.uint8)

    # Bits des pixels actifs (9 bits chacun, déjà dans `bits`)
    active_indices = np.where(active_mask)[0]
    # Récupérer les 9 bits de chaque pixel actif
    active_base = base[active_indices]
    # Forme (n_active, 9)
    active_bits_matrix = bits[active_base[:, None] + np.arange(9)]  # broadcasting

    # Reconstruire le flux ordonné pixel par pixel
    # On crée un tableau d'objets indiquant pour chaque pixel sa contribution
    # puis on les concatène dans l'ordre.
    pixel_order = np.arange(N)
    skip_pos   = np.where(skip_mask)[0]
    active_pos = np.where(active_mask)[0]

    # Construire un tableau de tailles : 1 pour skip, 9 pour active
    sizes = np.where(skip_mask, 1, 9)
    offsets = np.concatenate([[0], np.cumsum(sizes)[:-1]])

    # Remplir real_bits
    real_bits = np.zeros(n_bits, dtype=np.uint8)
    # skip pixels
    real_bits[offsets[skip_pos]] = 1
    # active pixels : 9 bits
    act_off = offsets[active_pos]  # (n_active,)
    for k in range(9):
        real_bits[act_off + k] = active_bits_matrix[:, k]

    # Padding à un multiple de 8 et packbits
    pad = (8 - n_bits % 8) % 8
    if pad:
        real_bits = np.concatenate([real_bits, np.zeros(pad, dtype=np.uint8)])

    return np.packbits(real_bits).tobytes()


# ── Pipeline commun ───────────────────────────────────────────────────────────

def _preprocess(rgb, alpha_channel, width, height,
                blur_sigma, contrast_alpha, contrast_beta,
                unsharp_sigma, unsharp_amount, unsharp_threshold):
    """Redimensionne, filtre, contraste, netteté → retourne (sharpened_rgb, alpha_resized)."""
    h0, w0 = rgb.shape[:2]
    aspect = w0 / h0

    if width and not height:
        height = int(width / aspect)
    elif height and not width:
        width = int(height * aspect)
    elif not width and not height:
        width, height = w0, h0

    if blur_sigma > 0:
        rgb          = cv2.GaussianBlur(rgb,          (3, 3), blur_sigma)
        alpha_channel = cv2.GaussianBlur(alpha_channel, (3, 3), blur_sigma)

    resized      = cv2.resize(rgb,          (width, height), interpolation=cv2.INTER_AREA)
    alpha_resized = cv2.resize(alpha_channel, (width, height), interpolation=cv2.INTER_AREA)

    contrasted = enhance_contrast(resized, alpha=contrast_alpha, beta=contrast_beta)
    sharpened  = unsharp_mask(contrasted, sigma=unsharp_sigma,
                               amount=unsharp_amount, threshold=unsharp_threshold)
    return sharpened, alpha_resized, width, height


def _build_bmi_bytes(sharpened, alpha_resized, width, height):
    """Quantifie et encode → retourne les bytes BMI complets (avec entête)."""
    lab     = cv2.cvtColor(sharpened, cv2.COLOR_RGB2LAB).astype(np.float32)
    indices = quantize_nearest_vectorised(lab)

    header  = struct.pack(">HH", width, height)
    payload = _encode_to_bitstream(indices, alpha_resized)
    return header + payload


# ── API publique ──────────────────────────────────────────────────────────────

def _load_input_with_pyav(infile):
    """
    Essaie d'abord PyAV.
    - Si c'est une vidéo : prend la première frame.
    - Si PyAV échoue : fallback OpenCV (pour garder la compatibilité avec les images).
    Retourne (rgb, alpha) en uint8.
    """
    try:
        container = av.open(infile)
        try:
            frame = next(container.decode(video=0), None)
            if frame is not None:
                rgba = frame.to_ndarray(format="rgba")  # HxWx4
                rgb = rgba[:, :, :3]
                alpha = rgba[:, :, 3]
                return rgb, alpha
        finally:
            container.close()
    except av.AVError:
        pass

    # Fallback image classique
    img = cv2.imread(infile, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise IOError(f"Impossible de charger {infile}")

    if img.ndim == 2:
        rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        alpha = np.full(img.shape, 255, dtype=np.uint8)
    elif img.shape[2] == 4:
        rgb = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGB)
        alpha = img[:, :, 3]
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        alpha = np.full(img.shape[:2], 255, dtype=np.uint8)

    return rgb, alpha


def image_to_bmi_sparse(infile, outfile, width=None, height=None,
                        blur_sigma=0.5, contrast_alpha=1.5, contrast_beta=0,
                        unsharp_sigma=1.0, unsharp_amount=1.5, unsharp_threshold=0,
                        silent=False):

    rgb, alpha_channel = _load_input_with_pyav(infile)

    sharpened, alpha_resized, width, height = _preprocess(
        rgb, alpha_channel, width, height,
        blur_sigma, contrast_alpha, contrast_beta,
        unsharp_sigma, unsharp_amount, unsharp_threshold,
    )

    data = _build_bmi_bytes(sharpened, alpha_resized, width, height)

    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    with open(outfile, "wb") as f:
        f.write(data)

    if not silent:
        print(f"✅ Fichier .bmi généré : {outfile} ({width}x{height})")


def image_array_to_bmi_bytes(img, width=None, height=None,
                              blur_sigma=0.5, contrast_alpha=1.5, contrast_beta=0,
                              unsharp_sigma=1.0, unsharp_amount=1.5, unsharp_threshold=0):
    if img is None:
        raise ValueError("Image invalide")

    rgb           = img[:, :, :3]
    alpha_channel = np.full(img.shape[:2], 255, dtype=np.uint8)

    sharpened, alpha_resized, width, height = _preprocess(
        rgb, alpha_channel, width, height,
        blur_sigma, contrast_alpha, contrast_beta,
        unsharp_sigma, unsharp_amount, unsharp_threshold,
    )

    return _build_bmi_bytes(sharpened, alpha_resized, width, height)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",            required=True,        help="Image source")
    parser.add_argument("--output",           required=True,        help=".bmi de sortie")
    parser.add_argument("--width",            type=int)
    parser.add_argument("--height",           type=int)
    parser.add_argument("--blur_sigma",       type=float, default=0.5)
    parser.add_argument("--contrast_alpha",   type=float, default=1.5)
    parser.add_argument("--contrast_beta",    type=float, default=0)
    parser.add_argument("--unsharp_sigma",    type=float, default=1.0)
    parser.add_argument("--unsharp_amount",   type=float, default=1.5)
    parser.add_argument("--unsharp_threshold",type=float, default=0.0)
    args = parser.parse_args()

    image_to_bmi_sparse(
        args.input, args.output, args.width, args.height,
        args.blur_sigma, args.contrast_alpha, args.contrast_beta,
        args.unsharp_sigma, args.unsharp_amount, args.unsharp_threshold,
    )
