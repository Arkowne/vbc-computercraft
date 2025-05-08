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


![](https://github.com/Arkowne/vbc-computercraft/raw/refs/heads/main/demo.mp4)

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
- HTTP API must be enabled in ComputerCraft if you use a HTTP server adress (usefull with local server)

**Installation**:

```
pastebin get JKN3hnq vbc
```

### 2. Audio Player (client) – On the speaker computer

This computer receives the audio file via HTTP and plays it using the `speaker` peripheral.

**Requirements**:
- A **speaker** peripheral
- A **modem** peripheral
- HTTP API enabled

**Installation**:

```
pastebin get cGG5rYn3 vbc_hifi
```

---

Setup Instructions
------------------

### Step 1: Configure your monitor computer

Open the monitor computer and set the modem side and your server IP:

```
settings.set("vbc.side_audio", "bottom")
settings.set("vbc.audio_id", 2)  -- Replace 2 with the actual ID of the audio computer
settings.set("vbc.ip_server", "your_ip:4334")  -- Replace your_ip with the actual IP of your VBC Server e.g. http://0.0.0.0:4334
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
vbc_hifi
```

### Step 3: Host your video
-----
Run the script via command line:

```bash
python3 convert.py -i path/to/your_video.mp4 -d 17 -f 7
```

Arguments:
- `-i` / `--input`: Path to your video file (required).
- `-d` / `--density`: Resolution scale for output frames (optional, default: 17).
- `-f` / `--fps`: Target frame rate (optional, default: 7). 

Example:
```bash
python3 convert.py -i funny_cat.mp4 -d 17 -f 7
```

Output
------
The script will create a folder inside `videos/` with a random ID name (e.g., `videos/abc123xyz`).
This folder will contain:
- `frame_00000.blt`, `frame_00001.blt`, etc. — All video frames converted to BLT.
- `audio.dfpwm` — The audio stream converted to DFPWM.
- `metadata.txt` — Contains:
    - `fps=7`
    - `frames=123`
- The program will also give you the id of your video, keep it in mind !
  (I will do a UI for the video upload/listing in the next update)

### Step 4: Start the server

```bash
python3 server.py
```

### Step 5: Play a video

From the monitor computer:

```
vbc <video_id>
```

To disable audio:

```
vbc <video_id> no
```

**Warning: The program does't support audio file of 1000KB or more yet, so disable the audio for long video or your audio computer will crash !**

---

Server Folder Structure
--------------------------------

Each video will be structured like this:

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

