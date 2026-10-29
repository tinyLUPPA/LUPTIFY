# LUPTIFY 🎵
> A Modern, Lossless Web Music Streaming Platform inspired by modern streaming interfaces (Spotube, ViMusic, InnerTune, and Apple Music).

![LUPTIFY Logo](luptify-logo.svg)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/tinyLUPPA/LUPTIFY)

## ✨ Overview
**LUPTIFY** is a full-featured, high-performance music streaming application built with a lightweight Python/FastAPI backend and a vanilla HTML5/CSS3/JavaScript frontend powered by the WebAudio API.

It seamlessly integrates with the YouTube Music catalog, supports offline storage via IndexedDB, word-follow synchronized lyrics with multi-language translation, and dynamic cosmic ambient aura lighting that adapts to album artwork colors.

---

## ☁️ Run Straight from GitHub (No Setup Required!)

### Option 1: 1-Click GitHub Codespaces (Run in Browser)
You can run LUPTIFY directly in your web browser from GitHub without downloading or configuring anything on your computer:
1. Open [https://github.com/tinyLUPPA/LUPTIFY](https://github.com/tinyLUPPA/LUPTIFY).
2. Click the green **`<> Code`** button, switch to the **Codespaces** tab, and click **"Create codespace on main"** (or click the badge above).
3. GitHub automatically spins up a cloud container, installs the requirements, and opens LUPTIFY in your browser with a live public URL.

### Option 2: 24/7 Cloud Deployment (Always Online)
To keep LUPTIFY running 24/7 without needing your personal computer powered on:
- **Render.com**: Connect your GitHub repository (`tinyLUPPA/LUPTIFY`), choose **Web Service**, and deploy for free using the included `render.yaml`.
- **Railway / Koyeb / Hugging Face**: Import `tinyLUPPA/LUPTIFY` to get a permanent HTTPS domain.

---

## 🚀 Key Features

- **🎧 High-Fidelity Lossless WebAudio Pipeline**:
  - WebAudio 32-bit Float 48,000Hz audio rendering engine with dual-track crossfading.
  - Interactive Graphic Equalizer with real-time spectrum visualizer.
  - ReplayGain volume normalization and adjustable playback speed (0.75x – 2.0x).

- **🌌 Dynamic Cosmic Ambient Aura**:
  - Multi-layer fluid ambient background with breathing glowing orbs.
  - Real-time dominant color extraction from album artwork that transitions smoothly across glassmorphic panels.

- **🎤 Synchronized & Translated Lyrics**:
  - Word-follow and line-by-line synchronized lyrics powered by LRCLib.
  - Live multi-language lyric translation (Malay, English, Spanish, Japanese, Korean, French, German, and more).
  - Clean solid-white lyrics view with auto-scrolling.

- **💾 100% Offline Music Storage**:
  - Download songs and lyrics directly into browser storage using IndexedDB.
  - Dedicated "Downloaded" tab with instant offline playback and zero network usage.

- **📱 Device Aspect-Ratio Auto-Matching (Android & Desktop)**:
  - Built with dynamic viewport units (`100dvh`) and safe-area inset adaptation for modern smartphones.
  - Floating mini player docked above bottom navigation with touch-friendly controls.
  - Fullscreen stage overlay with vinyl disc animation and responsive 1:1 artwork scaling.

- **🔥 Curated Recommendations & YouTube Music Charts**:
  - Live trending hits, curated genre playlists, and quick picks.
  - Instant radio generation based on currently playing songs.
  - Fast in-memory catalog caching for sub-millisecond navigation.

- **⌨️ Desktop Productivity Shortcuts**:
  - `Space`: Play / Pause
  - `ArrowLeft` / `ArrowRight`: Seek ±5 seconds
  - `ArrowUp` / `ArrowDown`: Volume ±5%
  - `M`: Mute / Unmute
  - `L`: Open Lyrics Stage
  - `Q`: Toggle Play Queue
  - `S`: Shuffle Queue
  - `R`: Cycle Repeat Mode
  - `F`: Fullscreen Stage

---

## 📦 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/tinyLUPPA/LUPTIFY.git
cd LUPTIFY
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Server
```bash
# Windows quick launch
start.bat

# Or via command line
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to `http://127.0.0.1:8000`.

---

## 📄 License
This project is for personal and educational use. Audio content is provided via YouTube / YouTube Music.
