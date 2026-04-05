# AI-Powered Study Tools

A comprehensive suite of Python utilities that automate the most time-consuming parts of studying: video transcription, AI-assisted note generation, Sinhala translation, PDF cleanup, and more. Run individual tools standalone or use the batch orchestrator for large-scale processing.

## 🎯 Key Features

- **🎙️ Faster-Whisper Transcription** — Transcribe lecture videos or live audio with GPU acceleration
- **✨ AI-Powered Note Generation** — Convert transcripts into structured Markdown and styled HTML notes using Google Gemini
- **🌐 Sinhala Translation** — Automatically translate notes to Sinhala with side-by-side comparison viewer
- **🎬 Video Processing** — Remove silence from raw lecture recordings; extract key frames
- **📄 PDF Tools** — Split multi-slide PDF pages into individual images; generate notes from PDF content
- **🔤 Subtitle Generation** — Auto-generate timestamped SRT/VTT subtitle files from lecture videos
- **⚙️ Unified Configuration** — Single `inputs.json` source of truth keeps all tools synchronized

## 📁 Repository Layout

```
AI-Powered-Study-Tools/
├── inputs.json                    # Central configuration for all tools
├── pyproject.toml                 # Python dependencies & project metadata
├── uv.lock                        # Locked dependency versions (auto-generated)
├── run_batch.py                   # Batch runner to execute tools sequentially
├── .env.example                   # Template for API keys (.env)
│
├── 0-audio-transcriber/
│   └── transcribe_audio.py        # Extract speech → text from audio files (mp3, m4a, wav, etc.)
│
├── 1-video-transcriber/
│   └── transcribe_video.py        # Extract speech → text from video files
│
├── 2-real-time-transcriber/
│   └── real_time_transcription.py # Live transcription from microphone or system audio
│
├── 3-note-generator/
│   ├── extract_lecture_frames.py        # Extract keyframes from video
│   ├── generate_notes.py                # AI note generation from transcripts
│   ├── generate_notes_sinhala.py        # Generate notes directly in Sinhala
│   ├── pdf_notes_generator.py           # Generate notes from PDF pages
│   ├── translate_sinhala_html.py        # Translate HTML notes → Sinhala
│   ├── translate_sinhala_md.py          # Translate Markdown notes → Sinhala
│   └── html_comparison_viewer.py        # Create side-by-side HTML comparison
│
├── 4-video-silence-remover/
│   └── remove_silence.py          # Remove silent segments from videos
│
├── 5-pdf-page-splitter/
│   └── split_pdf.py               # Split grid-layout PDFs into individual pages
│
├── 5-lecture-subtitle-generator/
│   └── generate_subtitles.py      # Generate SRT/VTT subtitles from lecture videos
│
├── output/                        # Generated files (transcripts, notes, frames)
├── sample_data/                   # Example outputs for testing
└── README.md
```

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/tharindu-s-rajapaksha/AI-Powered-Study-Tools.git
cd AI-Powered-Study-Tools

# 2. Install uv (if not already installed)
# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (with pipx):
pipx install uv
# Or download from: https://github.com/astral-sh/uv/releases

# 3. Install dependencies
uv sync

# 4. Set up API keys
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Configure inputs
# Edit inputs.json with your file paths

# 6. Run a tool
uv run python 1-video-transcriber/transcribe_video.py
# OR run batch
uv run python run_batch.py
```

## 📋 Installation & Requirements

- **Python 3.8+** (3.10+ recommended)
- **uv** — Ultra-fast Python package manager (https://github.com/astral-sh/uv)
- **CUDA-capable GPU** (optional but recommended for 10-100x transcription speedup)
- **FFmpeg** (for video/audio processing)
- **Google API Key** (for Gemini-powered note generation)

### Step 1: Install uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (with pipx):**
```bash
pipx install uv
```

Or download the latest release: https://github.com/astral-sh/uv/releases

### Step 2: Clone & Setup

```bash
git clone https://github.com/tharindu-s-rajapaksha/AI-Powered-Study-Tools.git
cd AI-Powered-Study-Tools

# Install all dependencies
uv sync

# Step 3: Activate Environment (Optional but Recommended)
# This allows you to run 'python' directly instead of 'uv run python'
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

### Step 4: Install Dependencies

All dependencies are managed through `pyproject.toml`. The `uv sync` command above handles everything:

- `faster-whisper` — Speech-to-text engine
- `google-generativeai` — Gemini API for note generation
- `PyMuPDF`, `PyPDF2` — PDF manipulation
- `moviepy` — Video processing
- `opencv-python` — Frame extraction & image processing
- `python-dotenv` — Environment variable management

### Step 4: Configure API Keys

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_API_KEY=your_google_api_key_here
```

Get a free Google API key: https://aistudio.google.com/app/apikey

## ⚙️ Configuration: inputs.json

**Every tool reads from `inputs.json`** — this is your single source of truth. Update paths once, and all tools stay synchronized.

### Full Configuration Template

```json
{
  "audio_transcriber": {
    "audio_path": "path/to/audio.mp3"
  },
  "video_transcriber": {
    "video_path": "path/to/lecture.mkv"
  },
  "real_time_transcriber": {
    "device_index": null,
    "model_size": "base",
    "input_source": "mic"
  },
  "note_generator": {
    "text_file": "output/lecture_transcription.txt",
    "video_path": "path/to/lecture.mkv",
    "start_page": 11,
    "end_page": 20
  },
  "note_generator_sinhala": {
    "text_file": "output/lecture_transcription.txt"
  },
  "extract_lecture_frames": {
    "video_path": "path/to/lecture.mkv",
    "output_folder": "output/frames"
  },
  "pdf_note_generator": {
    "pdf_file": "path/to/lecture.pdf",
    "start_page": 1,
    "end_page": 10
  },
  "translate_sinhala_html": {
    "input_file": "output/lecture_notes.html",
    "output_file": "output/lecture_sinhala.html"
  },
  "translate_sinhala_md": {
    "input_file": "output/lecture_notes.md",
    "output_file": "output/lecture_sinhala.md"
  },
  "html_comparison_viewer": {
    "original_file": "output/lecture_notes.html",
    "translated_file": "output/lecture_sinhala.html",
    "output_file": "output/comparison_view.html"
  },
  "video_silence_remover": {
    "input_file": "path/to/lecture.mkv",
    "output_file": "output/lecture_silence_removed.mp4"
  },
  "pdf_splitter": {
    "input_pdf": "path/to/slides.pdf",
    "rows": 2,
    "cols": 3,
    "output_dir": null,
    "remove_empty": true,
    "empty_threshold": 0.95
  },
  "subtitle_generator": {
    "video_path": "path/to/lecture.mp4",
    "output_path": "output/lecture.srt"
  }
}
```

### Configuration Tips

- **Use relative paths** whenever possible so the project works on any machine
- **Video paths** support: `.mkv`, `.mp4`, `.avi`, `.mov`, `.webm`
- **PDF paths** must point to valid PDF files
- **output_dir** (PDF splitter) — leave `null` to auto-generate from input filename
- **empty_threshold** — pages > 95% white are considered empty and discarded

## 🛠️ Tools Guide

### 0️⃣ Audio Transcriber

**Module**: `0-audio-transcriber/transcribe_audio.py`  
**Purpose**: Convert audio files to text transcripts using Faster-Whisper  
**Input** (from `inputs.json`):

- `audio_transcriber.audio_path` — path to audio file (`.mp3`, `.m4a`, `.wav`, `.flac`, `.ogg`, `.opus`, `.aac`, `.wma`)

**Output**:

- `<audio_name>_transcription.txt` — plain text transcript

**Usage**:

```bash
python 0-audio-transcriber/transcribe_audio.py
```

**Speed**: ~10-20x real-time with GPU; ~1-2x with CPU

**Supported Formats**: MP3, M4A, WAV, FLAC, OGG, Opus, AAC, WMA

---

### 1️⃣ Video Transcriber

**Module**: `1-video-transcriber/transcribe_video.py`  
**Purpose**: Convert lecture videos to text transcripts using Faster-Whisper  
**Input** (from `inputs.json`):

- `video_transcriber.video_path` — path to `.mkv/.mp4/.avi` file

**Output**:

- `<video_name>_transcription.txt` — plain text transcript
- Console logs with timestamps for each segment

**Usage**:

```bash
python 1-video-transcriber/transcribe_video.py
```

**Speed**: ~10-20x real-time with GPU; ~1-2x with CPU

---

### 2️⃣ Real-Time Transcriber

**Module**: `2-real-time-transcriber/real_time_transcription.py`  
**Purpose**: Transcribe live audio from microphone or system audio in real-time  
**Configuration** (edit file directly):

- `input_source` — `"mic"` (microphone) or `"system"` (system audio)
- `device_index` — optional explicit device ID
- `model_size` — `"tiny"`, `"base"`, `"small"`, `"medium"`

**Output**:

- `output/transcript.txt` — continuously updated
- Live console stream of recognized words

**Usage**:

```bash
python 2-real-time-transcriber/real_time_transcription.py
# Stop with Ctrl+C
```

**Tip**: Uncomment `transcriber.list_devices()` to see available audio devices

---

### 3️⃣ AI Note Generator (English)

**Module**: `3-note-generator/generate_notes.py`  
**Purpose**: Convert transcripts into structured AI-generated notes  
**Input** (from `inputs.json`):

- `note_generator.text_file` — path to transcript
- `note_generator.video_path` — (optional) for frame extraction
- `note_generator.start_page` / `end_page` — optional page range

**Output**:

- `<transcript>_notes.txt` — Markdown-formatted notes
- `<transcript>_notes.html` — Styled HTML with CSS

**Features**:

- Automatic chunking for large transcripts
- Gemini AI summarization & structuring
- Bullet points, headers, and key concepts extracted

**Usage**:

```bash
python 3-note-generator/generate_notes.py
```

---

### 4️⃣ AI Note Generator (Sinhala)

**Module**: `3-note-generator/generate_notes_sinhala.py`  
**Purpose**: Generate notes directly in Sinhala language  
**Input** (from `inputs.json`):

- `note_generator.text_file` — transcript to convert

**Output**:

- `<transcript>_notes_sinhala.md` — Markdown in Sinhala
- `<transcript>_notes_sinhala.html` — Styled HTML in Sinhala

**Usage**:

```bash
python 3-note-generator/generate_notes_sinhala.py
```

---

### 5️⃣ Extract Lecture Frames

**Module**: `3-note-generator/extract_lecture_frames.py`  
**Purpose**: Extract key frames from video at regular intervals  
**Input** (from `inputs.json`):

- `extract_lecture_frames.video_path` — lecture video file
- `extract_lecture_frames.output_folder` — where to save frames

**Output**:

- JPG images: `frame_0000_at_0.00s.jpg`, `frame_0001_at_5.00s.jpg`, etc.
- `frames_metadata.json` — timing and metadata for each frame

**Usage**:

```bash
python 3-note-generator/extract_lecture_frames.py
```

---

### 6️⃣ PDF Notes Generator

**Module**: `3-note-generator/pdf_notes_generator.py`  
**Purpose**: Generate AI notes from PDF pages  
**Input** (from `inputs.json`):

- `pdf_note_generator.pdf_file` — PDF file
- `pdf_note_generator.start_page` / `end_page` — page range (1-indexed)

**Output**:

- Notes for specified PDF range
- Both `.txt` and `.html` formats

**Usage**:

```bash
python 3-note-generator/pdf_notes_generator.py
```

---

### 7️⃣ Sinhala HTML Translator

**Module**: `3-note-generator/translate_sinhala_html.py`  
**Purpose**: Translate HTML notes to Sinhala  
**Input** (from `inputs.json`):

- `translate_sinhala_html.input_file` — English HTML notes
- `translate_sinhala_html.output_file` — output path

**Output**:

- Translated HTML file with Sinhala text

**Usage**:

```bash
python 3-note-generator/translate_sinhala_html.py
```

---

### 8️⃣ Sinhala Markdown Translator

**Module**: `3-note-generator/translate_sinhala_md.py`  
**Purpose**: Translate Markdown notes to Sinhala  
**Input** (from `inputs.json`):

- `translate_sinhala_md.input_file` — English Markdown file
- `translate_sinhala_md.output_file` — output path

**Output**:

- Translated Markdown file with Sinhala text

**Usage**:

```bash
python 3-note-generator/translate_sinhala_md.py
```

---

### 9️⃣ HTML Comparison Viewer

**Module**: `3-note-generator/html_comparison_viewer.py`  
**Purpose**: Create an interactive side-by-side comparison of original and translated content  
**Input** (from `inputs.json`):

- `html_comparison_viewer.original_file` — English HTML
- `html_comparison_viewer.translated_file` — Sinhala HTML
- `html_comparison_viewer.output_file` — comparison HTML output

**Output**:

- Interactive `comparison_view.html` with split-screen view

**Usage**:

```bash
python 3-note-generator/html_comparison_viewer.py
```

---

### 🔟 Video Silence Remover

**Module**: `4-video-silence-remover/remove_silence.py`  
**Purpose**: Automatically remove silent segments from videos  
**Input** (from `inputs.json`):

- `video_silence_remover.input_file` — video file
- `video_silence_remover.output_file` — output path

**Output**:

- Cleaned MP4 with silent parts removed
- Significantly reduced file size and duration

**Features**:

- Automatic silence detection
- Configurable silence threshold
- Works with any video format

**Usage**:

```bash
python 4-video-silence-remover/remove_silence.py
```

---

### 1️⃣1️⃣ PDF Page Splitter

**Module**: `5-pdf-page-splitter/split_pdf.py`  
**Purpose**: Split multi-slide PDF pages (grid layout) into individual slide images  
**Input** (from `inputs.json`):

- `pdf_splitter.input_pdf` — multi-slide PDF
- `pdf_splitter.rows` — number of slides per row
- `pdf_splitter.cols` — number of slides per column
- `pdf_splitter.output_dir` — output folder (auto-generated if null)
- `pdf_splitter.remove_empty` — remove blank pages (true/false)
- `pdf_splitter.empty_threshold` — whitespace % to consider empty (0.95 = 95%)

**Output**:

- Individual PNG/JPG files for each slide
- Metadata JSON with page info

**Example**: 2×3 grid → 6 slides per page → each saved individually

**Usage**:

```bash
python 5-pdf-page-splitter/split_pdf.py
```

---

### 1️⃣2️⃣ Lecture Subtitle Generator

**Module**: `5-lecture-subtitle-generator/generate_subtitles.py`  
**Purpose**: Generate timestamped SRT or VTT subtitle files from lecture videos using Faster-Whisper  
**Input** (from `inputs.json`):

- `subtitle_generator.video_path` — path to the lecture video (`.mp4`, `.mkv`, `.avi`, etc.)
- `subtitle_generator.output_path` — path for the output subtitle file (`.srt` or `.vtt`)

**Output**:

- `<video_name>.srt` or `<video_name>.vtt` — subtitle file with precise timestamps per segment

**Features**:

- Auto-detects GPU (CUDA) or falls back to CPU
- Supports both SRT and VTT formats (determined by output file extension)
- Beam search (beam_size=5) for high-accuracy transcription
- Cleans up temporary audio files automatically

**Usage**:

```bash
python 5-lecture-subtitle-generator/generate_subtitles.py
```

**Tip**: Rename the output to `.vtt` to embed subtitles directly in HTML5 video players

---

## 🎬 Batch Runner

**Module**: `run_batch.py`  
**Purpose**: Execute multiple tools sequentially with different configurations in a single command

Run multiple configurations without manually editing `inputs.json` each time.

### How It Works

1. Backs up the original `inputs.json` configuration
2. Applies batch-specific overrides one at a time
3. Executes the corresponding tool script
4. Restores original configuration after completion

### Edit & Run

Open `run_batch.py` and modify the `tool_key` and `batch_configs` section:

```python
# Example: Process 3 videos in sequence
TOOL_KEYS_TO_RUN = [
    "video_transcriber",
    "note_generator",
    "video_silence_remover"
]

BATCH_CONFIGS = [
    {
        "video_transcriber": {
            "video_path": "lectures/week-01.mkv"
        },
        "note_generator": {
            "text_file": "output/week-01_transcription.txt"
        }
    },
    {
        "video_transcriber": {
            "video_path": "lectures/week-02.mkv"
        },
        "note_generator": {
            "text_file": "output/week-02_transcription.txt"
        }
    }
]
```

Then run:

```bash
python run_batch.py
```

---

## 📚 Common Workflows

### Complete Lecture Processing Pipeline

```bash
# 1. Transcribe video
python 1-video-transcriber/transcribe_video.py

# 2. Generate AI notes
python 3-note-generator/generate_notes.py

# 3. Translate to Sinhala
python 3-note-generator/translate_sinhala_md.py

# 4. Create comparison view
python 3-note-generator/html_comparison_viewer.py
```

### Quick Note Generation from Transcript

```bash
# Already have a transcript? Just generate notes
# Update inputs.json with path to .txt file
python 3-note-generator/generate_notes.py
```

### PDF Slide Processing

```bash
# 1. Extract slides from grid PDF
python 5-pdf-page-splitter/split_pdf.py

# 2. Generate notes from specific pages
python 3-note-generator/pdf_notes_generator.py
```

### Clean Video Before Sharing

```bash
# Remove silence, then transcribe clean version
python 4-video-silence-remover/remove_silence.py
# Update inputs.json to reference the cleaned video
python 1-video-transcriber/transcribe_video.py
```

### Generate Subtitles for a Lecture Video

```bash
# 1. Set video_path and output_path in inputs.json under "subtitle_generator"
# 2. Run the subtitle generator
python 5-lecture-subtitle-generator/generate_subtitles.py
# Output: an .srt file you can load in VLC, YouTube, or any media player
```

### Live Lecture Transcription

```bash
# Transcribe live as you record
python 2-real-time-transcriber/real_time_transcription.py
# Stop with Ctrl+C
# Later, generate notes from output/transcript.txt
```

---

## ⚙️ Output Locations

| Tool                  | Output          | Location                      |
| --------------------- | --------------- | ----------------------------- |
| Video Transcriber     | Transcript      | Same directory as input video |
| Real-Time Transcriber | Transcript      | `output/transcript.txt`       |
| Note Generator        | Markdown + HTML | Same as input transcript      |
| Frame Extractor       | JPG images      | `output/frames/`              |
| PDF Splitter          | PNG slides      | Auto-folder next to PDF       |
| Silence Remover       | Clean video     | As specified in config        |
| Subtitle Generator    | SRT / VTT file  | As specified in config        |
| Comparison Viewer     | HTML            | As specified in config        |

---

## 🎧 Tips & Optimization

### Performance Tips

- **GPU for Transcription**: Install CUDA/cuDNN for 10-100x speedup

  ```bash
  # Verify GPU is being used:
  uv pip show faster-whisper  # Should show CUDA support
  ```

- **Use Smaller Models for Testing**:
  - `tiny` — fastest, ~1.5GB VRAM (≈95% accuracy)
  - `base` — balanced, ~3GB VRAM (≈98% accuracy) [default]
  - `small`/`medium` — most accurate, 6-10GB VRAM

- **Batch Process at Night**: Use `run_batch.py` for large queues so your machine can process while you sleep

- **Incremental Translation**: Translate one file at a time instead of bulk translations to catch errors early

### Streaming Audio Devices

To find available audio devices for real-time transcription:

```python
# In real_time_transcription.py, uncomment:
transcriber.list_devices("system")
# OR list_devices("audio") for all devices
```

Then set `device_index` in `inputs.json`

### PDF Tips

- **Grid Layout**: Set `rows` and `cols` to match your PDF's slide arrangement
- **Empty Page Detection**: Adjust `empty_threshold` (0.90 = 90% whitespace = empty)
- **Color PDFs**: Slower to process; grayscale PDFs are faster

---

## 🔧 Troubleshooting

### Transcription is Slow

**Problem**: Transcription takes hours  
**Solution**:

- Check if GPU is available: `nvidia-smi`
- If no GPU, fall back to CPU (will be slow)
- Use smaller model: `tiny` or `base` instead of `small`

### "No module named 'google.generativeai'"

**Problem**: Import error for Gemini API  
**Solution**:

```bash
uv pip install --upgrade google-generativeai
```

### "GOOGLE_API_KEY not found in .env"

**Problem**: Note generator fails  
**Solution**:

1. Create `.env` file (copy from `.env.example`)
2. Add your API key: `GOOGLE_API_KEY=sk-...`
3. Get free key: https://aistudio.google.com/app/apikey

### "File not found" Errors

**Problem**: Scripts can't find input files  
**Solution**:

- Use **absolute paths** in `inputs.json` OR
- Use **relative paths** but ensure you're in the project root when running scripts
- Check file extensions (case-sensitive on macOS/Linux)

### Video Won't Transcribe

**Problem**: "Unsupported video codec" error  
**Solution**:

- Convert to `.mp4` first: `ffmpeg -i input.mkv output.mp4`
- Or install `ffmpeg-python`: `uv pip install ffmpeg-python`

### PDF Splitter Adds Extra Blank Pages

**Problem**: Too many empty pages in output  
**Solution**:

- Increase `empty_threshold` from 0.95 to 0.98 (stricter)
- Or manually inspect PDF for partial-blank pages

### Real-Time Transcriber Gets No Audio

**Problem**: "No audio detected"  
**Solution**:

- Verify device: `transcriber.list_devices("system")`
- Try `input_source="system"` (not just "mic")
- Check system audio isn't muted

### Sinhala Translation is Garbled

**Problem**: Characters appear as boxes or wrong text  
**Solution**:

- Verify `.env` has correct `GOOGLE_API_KEY`
- Ensure output HTML has UTF-8 encoding
- Try opening in different browser (Chrome > Edge > Safari)

---

## 🔒 Security & Safety

### Environment Secrets

- **Never commit `.env`** — it contains API keys
- `.gitignore` already includes `.env`
- Keep `GOOGLE_API_KEY` private; rotate if exposed
- Use free tier keys for personal/academic use only

### API Rate Limits

- Google Gemini free tier: ~60 calls/min
- If you hit rate limits, add delays between tool runs:
  ```python
  import time
  time.sleep(2)  # Wait 2 seconds between runs
  ```

### Data Privacy

- Transcripts and notes are stored locally; nothing uploaded to cloud except Gemini API calls
- PDFs are processed locally; only text sent to Gemini
- Videos stay on your machine; only extracted text goes to API

### Academic Integrity

- **Always review AI-generated notes** before submission
- AI may hallucinate facts or misquote sources
- Use as study aid, not as primary source
- Cite original lecture, not the AI summary

---

## 📦 What's Included

### Dependencies Summary

| Package               | Purpose           | Included? |
| --------------------- | ----------------- | --------- |
| `faster-whisper`      | Speech-to-text    | ✅        |
| `google-generativeai` | Gemini API access | ✅        |
| `moviepy`             | Video editing     | ✅        |
| `PyMuPDF`             | PDF rendering     | ✅        |
| `opencv-python`       | Image processing  | ✅        |
| `PyAudio`             | Microphone input  | ✅        |
| `Pillow`              | Image I/O         | ✅        |
| `python-dotenv`       | Env file loading  | ✅        |

See `pyproject.toml` for full list and pinned versions.

---

## 📝 Sample Outputs

Check `sample_data/` for example outputs:

- `transcription.txt` — Sample lecture transcript
- `note.html` — Generated study notes
- `translated_sinhala.html` — Sinhala translation
- `comparison_view.html` — Side-by-side comparison

---

## 🤝 Contributing

Found a bug? Have a feature request? Feel free to:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📖 References & Resources

- **[Faster-Whisper GitHub](https://github.com/SYSTRAN/faster-whisper)** — Speech recognition engine
- **[Google Gemini API](https://aistudio.google.com)** — AI note generation
- **[PyMuPDF Docs](https://pymupdf.readthedocs.io/)** — PDF processing
- **[MoviePy Tutorial](https://zulko.github.io/moviepy/)** — Video editing

---

## 📄 License

This project is provided as-is for **academic and personal use only**. Please review all AI-generated content for accuracy before sharing or publishing.

**⚠️ Academic Integrity Notice**: AI-generated notes are study aids. Always verify facts against original sources and properly cite your references.

---

_Last updated: February 2026_  
_Developer: Tharindu S Rajapaksha_
