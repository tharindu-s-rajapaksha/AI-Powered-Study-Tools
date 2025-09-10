# AI-Powered Study Tools

A collection of Python scripts designed to streamline academic workflows by leveraging AI for transcription, note-generation, and translation.

## Features

-   **Video Transcriber**: Transcribe lecture recordings (`.mp4`, `.mkv`) into plain text.
-   **Real-Time Transcriber**: Capture and transcribe system audio or microphone input live.
-   **AI Note Generator**: Convert a raw transcript into well-structured, summarized study notes in Markdown and HTML format. Also includes tools to translate notes and compare versions.

## Getting Started

### Prerequisites

-   Python 3.8+
-   An NVIDIA GPU with CUDA is highly recommended for transcription performance.
-   A Google AI API Key for note generation and translation.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AI-Powered-Study-Tools.git
    cd AI-Powered-Study-Tools
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Key:**
    -   Rename the `.env.example` file to `.env`.
    -   Open `.env` and paste your Google API key.
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
    ```

## Usage

Each tool is located in its own numbered folder, suggesting a typical workflow. All generated files will be saved to the `output/` directory by default.

### 1. `1-video-transcriber`

Transcribes video files. For detailed instructions, see the [Video Transcriber README](./1-video-transcriber/README.md).

**Example:**
```bash
python 1-video-transcriber/transcribe_video.py "path/to/your/lecture.mp4"
```

### 2. `2-real-time-transcriber`

Transcribes audio live from your microphone or system output (e.g., a live online lecture). See the [Real-Time Transcriber README](./2-real-time-transcriber/README.md) for setup.

**Example:**
```bash
python 2-real-time-transcriber/transcribe_realtime.py
```

### 3. `3-note-generator`

A suite of tools to process your raw transcripts. For full details, visit the [Note Generator README](./3-note-generator/README.md).

**Example: Generate notes from a transcript**
```bash
python 3-note-generator/generate_notes.py "output/lecture_transcription.txt"
```

---
*Disclaimer: This is an academic project. Do not commit sensitive information or API keys directly into version control.*