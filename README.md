# AI-Powered Study Tools

A collection of Python scripts designed to streamline academic workflows by leveraging AI for transcription, note-generation, and translation.

## Features

-   **Video Transcriber**: Transcribe lecture recordings (`.mp4`, `.mkv`) into plain text using Faster-Whisper.
-   **Real-Time Transcriber**: Capture and transcribe system audio or microphone input live.
-   **AI Note Generator**: Convert a raw transcript into well-structured, summarized study notes in Markdown and HTML format using a Generative AI model.
-   **HTML Translator & Viewer**: Translate the generated HTML notes into Sinhala and create a side-by-side comparison view to review the translation.

---

## Getting Started

### Prerequisites

-   Python 3.8+
-   An NVIDIA GPU with CUDA is highly recommended for transcription performance.
-   A Google AI API Key for note generation and translation.

### Installation & Setup

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
    -   Open the new `.env` file and paste your Google API key.
    ```ini
    # .env file
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
    ```

5.  **Configure File Paths in `inputs.json`:**
    This file is the central control panel for the scripts. Before running, you must edit the paths in `inputs.json` to point to your own files.

    **Recommendation:** Use relative paths (e.g., `sample_data/lecture.mkv`) instead of absolute paths (`D:\\...`) to make your project portable.

    ```json
    // inputs.json
    {
      "video_transcriber": {
        "video_path": "sample_data/my_lecture.mkv"
      },
      "note_generator": {
        "text_file": "output/my_lecture_transcription"
      },
      "translate_sinhala_html": {
        "input_file": "output/my_lecture_transcription_notes.html",
        "output_file": "output/my_lecture_translated_sinhala.html"
      },
      "html_comparison_viewer": {
        "original_file": "output/my_lecture_transcription_notes.html",
        "translated_file": "output/my_lecture_translated_sinhala.html",
        "output_file": "output/comparison_view.html"
      }
    }
    ```

---

## Workflow & Usage

The project is designed to be used in a sequential workflow. All scripts (except the real-time transcriber) read their configuration from `inputs.json`. After editing the file, simply run the desired Python script without any arguments.

### Step 1: Transcribe a Video

This script extracts audio from a video file and transcribes it to a text file.

-   **Configure:** Edit the `video_path` in the `video_transcriber` section of `inputs.json`.
-   **Run:**
    ```bash
    python 1-video-transcriber/transcribe_video.py
    ```
-   **Output:** A `_transcription.txt` file will be created in the same directory as the video.

### Step 2: Generate Study Notes

This script takes the raw text transcript and uses a generative AI model to create structured, styled HTML notes.

-   **Configure:** Edit the `text_file` path in the `note_generator` section of `inputs.json`. **Important:** Provide the path *without* the `.txt` extension.
-   **Run:**
    ```bash
    python 3-note-generator/generate_notes.py
    ```
-   **Output:** Creates `_notes.txt` and `_notes.html` files based on the input path.

### Step 3: Translate HTML Notes to Sinhala

This script translates the content of the generated HTML notes into Sinhala while preserving all HTML tags and styling.

-   **Configure:** Edit the `input_file` and `output_file` paths in the `translate_sinhala_html` section of `inputs.json`.
-   **Run:**
    ```bash
    python 3-note-generator/translate_sinhala_html.py
    ```
-   **Output:** A new, translated HTML file at the specified `output_file` path.

### Step 4: Create a Comparison View

This utility generates a single HTML file that displays the original and translated documents side-by-side with synchronized scrolling, making it easy to review the translation.

-   **Configure:** Edit the `original_file`, `translated_file`, and `output_file` paths in the `html_comparison_viewer` section of `inputs.json`.
-   **Run:**
    ```bash
    python 3-note-generator/html_comparison_viewer.py
    ```
-   **Output:** A `comparison_view.html` file that you can open in any web browser.

---

## Bonus Tool: Real-Time Transcription

This script captures audio directly from your microphone or system output (e.g., a live online lecture) and transcribes it in real-time.

-   **This script does not use `inputs.json`**. Configuration is done directly in the file.
-   **Setup:**
    1.  Open `2-real-time-transcriber/real_time_transcription.py`.
    2.  Find the `if __name__ == "__main__":` block at the bottom.
    3.  Modify the `device_index` parameter. To find the correct index for your system's speaker or microphone, you can uncomment the line `# transcriber.list_devices("system")` and run the script once to see a list of available devices.
-   **Run:**
    ```bash
    python 2-real-time-transcriber/real_time_transcription.py
    ```
-   **Output:** The live transcript is printed to the console and saved continuously to `output/transcript.txt`. Press `Ctrl+C` to stop.

---
*Disclaimer: This is an academic project. Do not commit sensitive information or API keys directly into version control. Ensure the `.env` file is listed in your `.gitignore`.*