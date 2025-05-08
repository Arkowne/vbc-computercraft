# 🎞️ Video to .blt Converter for ComputerCraft

This project converts standard video files into frame-by-frame `.blt` images and DFPWM audio, fully compatible with the [ComputerCraft](https://tweaked.cc/) mod in Minecraft.

Each video is processed and split into individual frames, resized and exported in the `.blt` format using a custom NFP (Notchian Frame Protocol) rendering style. The audio is also extracted and encoded in `dfpwm` format, which is supported by in-game audio players like `speaker.playDFPWM`.

---

## ✨ Features

- Converts any video into `.blt` frames
- Preserves original aspect ratio (no padding)
- DFPWM audio extraction (mono, 48kHz)
- Adjustable FPS and image density
- Metadata generation for playback
- CLI interface for batch processing

---

## 🧰 Requirements for the server

- Python 3.7+
- [FFmpeg](https://ffmpeg.org/)
- Python packages:
  - `opencv-python`
  - `Pillow`
  - `nfp` (custom/notched pixel format converter)
  - `blt` (you must provide your own `image_to_blt` function)

Install dependencies:

```bash
pip install opencv-python Pillow nfp
