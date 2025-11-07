***

### 🎞️ Video Block Converter – Simplified Installation

This project lets you play videos inside [ComputerCraft](https://tweaked.cc/) using a server and a client connected to a monitor and a speaker.

***

### 🧰 Server Requirements

- Python 3.7 or higher  
- [FFmpeg](https://ffmpeg.org/) installed  
- Python packages listed in `requirements.txt`  
  (install them with: `pip install -r requirements.txt`)

***

### ⚙️ Client Installation (monitor computer)

1. Open a computer in ComputerCraft.  
2. Download the client program:  

   ```
   wget run https://github.com/Arkowne/vbc-computercraft/raw/refs/heads/main/Client/install.lua
   ```

3. Set your server IP address:  

   ```
   set vbc.ip_server your_ip:4334
   ```

   Replace `your_ip` with your actual server address (e.g., `http://0.0.0.0:4334` if you are in localhost).

***

### 🖥️ Start the Server

On your host machine:  

```
python3 server.py
```

Then open in your browser:  
`http://your_ip:4334`  
You can now upload videos directly from the web interface.

***

### ⚙️ Access the server's video list

Enter your server aadress in your browser (e.g., `http://your_ip:4334`).
From this page, you can see your video's and there id's.

You can also directly upload .mp4, but the video will be resize for realy big screen (will be fixed in the next update).

***

### ▶️ Client Commands

There are two main client commands:

- Play a video from the server:  
  ```
  vbc play video_id
  ```

- Download a video from a direct link:  
  ```
  vbc download mp4_link
  ```

To disable audio:  
```
vbc play video_id no
```



***

### ⚠️ Important Notes

- If you use a http:// ip in vbc.ip_server, the HTTP API must be enabled in the ComputerCraft configuration.  
- DFPWM audio is not yet optimized for long videos (disable it if the client crashes).  
- The monitor size should match the video resolution for proper display.

***

## 💡 Task for the V3.0
- Create .exe, .app and .deb for video servers to make the installation easier.
- Split .dfpwm in tinyer files for long-format videos.
- Add a vbc replay to replay the last video played.
