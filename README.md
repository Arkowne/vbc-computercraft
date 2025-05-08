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




Installation Guide
------------------

### 1. Video Player (client) – On the monitor computer

This computer handles video playback and downloads video frames from a web server.

**Requirements**:
- A **monitor** peripheral (any size)
- A **modem** peripheral
- HTTP API must be enabled in ComputerCraft

**Installation**:

```
pastebin get 1234567 vbc
```

### 2. Audio Player (client) – On the speaker computer

This computer receives the audio file via HTTP and plays it using the `speaker` peripheral.

**Requirements**:
- A **speaker** peripheral
- A **modem** peripheral
- HTTP API enabled

**Installation**:

```
pastebin get 7654321 audio
```

---

Setup Instructions
------------------

### Step 1: Configure your monitor computer

Open the monitor computer and set the modem side:

```
settings.set("vbc.side_audio", "bottom")
settings.set("vbc.audio_id", 2)  -- Replace 2 with the actual ID of the audio computer
settings.save()
```

> You can get the ID of the audio computer by running:
> ```
> os.getComputerID()
> ```

### Step 2: Configure your audio computer

On the audio computer, set the modem side:

```
settings.set("vbc_hifi.side", "bottom")
settings.save()
```

Then run the audio server:

```
audio
```

### Step 3: Host your video

Host the folder containing your video data at:

```
http://<your-ip>:4334/videos/<video_id>/
```

Example:
```
http://192.168.1.42:4334/videos/demo_video/
```

### Step 4: Play a video

From the monitor computer:

```
vbc <video_id>
```

Example:

```
vbc demo_video
```

To disable audio:

```
vbc demo_video no
```

---

Required Server Folder Structure
--------------------------------

Each video must be structured like this:

```
videos/
└── <video_id>/
    ├── frame_00000.blt
    ├── frame_00001.blt
    ├── ...
    ├── audio.dfpwm
    └── metadata.txt
```

Example `metadata.txt`:

```
fps=7
frames=180
```

---

Notes
-----

- HTTP must be enabled in `ComputerCraft` config.
- Rednet communication is used for remote audio control.
- Monitor size should match the resolution of the video.
- The playback client adjusts to your `fps` setting.

---

License
-------

MIT License — Free to use, modify, and distribute.


Install dependencies:

```bash
pip install opencv-python Pillow nfp
