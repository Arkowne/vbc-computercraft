import struct
import argparse

def read_ccraft_sparse_bitwise(path):
    """Lit un fichier .bmi sparse (1bit skip + 4bit bg + 4bit fg)"""
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 4:
        raise ValueError("Fichier trop court pour header")

    width, height = struct.unpack(">HH", data[:4])
    pixels = {}  # {(x,y): (bg, fg)}

    byte_pos = 4
    bit_pos = 7
    cur_byte = data[byte_pos] if byte_pos < len(data) else 0

    def read_bit():
        nonlocal byte_pos, bit_pos, cur_byte
        bit = (cur_byte >> bit_pos) & 1
        bit_pos -= 1
        if bit_pos < 0:
            byte_pos += 1
            cur_byte = data[byte_pos] if byte_pos < len(data) else 0
            bit_pos = 7
        return bit

    for y in range(height):
        for x in range(width):
            skip = read_bit()
            if skip:
                continue  # pas de pixel
            # pixel actif → lire 4 bits bg et 4 bits fg
            bg = 0
            fg = 0
            for i in range(3, -1, -1):
                bg |= read_bit() << i
            for i in range(3, -1, -1):
                fg |= read_bit() << i
            pixels[(x, y)] = (bg, fg)

    return width, height, pixels

def render_terminal(width, height, pixels):
    for y in range(height):
        row_str = ""
        for x in range(width):
            if (x, y) in pixels:
                row_str += "O"  # pixel actif
            else:
                row_str += "/"  # skip
        print(row_str)

def display_bmi_print(input):
    w, h, pixels = read_ccraft_sparse_bitwise(input)
    print(f"📄 Image {w}x{h}")
    render_terminal(w, h, pixels)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Fichier .bmi sparse à lire")
    args = parser.parse_args()

    w, h, pixels = read_ccraft_sparse_bitwise(args.input)
    print(f"📄 Image {w}x{h}")
    render_terminal(w, h, pixels)
