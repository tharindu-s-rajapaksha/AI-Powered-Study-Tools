# AI-Powered Study Tools

Python utilities that automate the most time-consuming parts of studying: video transcription, AI-assisted note generation, Sinhala translation, PDF cleanup, and more. Every tool can be run individually or orchestrated via `run_batch.py` for larger processing queues.

## Highlights

- **Faster-Whisper transcription** for lectures (video or live audio)
- **Gemini-powered note builders** that emit Markdown and styled HTML
- **Sinhala translation & comparison viewer** to verify localized content
- **Video silence removal and PDF splitters** for smoothing raw materials
- **Single source of truth in `inputs.json`** keeps all scripts in sync

## Repository Layout

```text
AI-Powered-Study-Tools/
├── .env.example            # Sample secrets file (copy to .env)
├── inputs.json             # Central runtime configuration
├── run_batch.py            # Batch runner across any tool
├── requirements.txt
├── 1-video-transcriber/
│   ├── transcribe_video.py
│   └── output/
├── 2-real-time-transcriber/
│   └── real_time_transcription.py
├── 3-note-generator/
│   ├── extract_lecture_frames.py
│   ├── generate_notes.py
│   ├── generate_notes_sinhala.py
│   ├── html_comparison_viewer.py
│   ├── pdf_notes_generator.py
│   ├── translate_sinhala_html.py
│   └── translate_sinhala_md.py
├── 4-video-silence-remover/
│   └── remove_silence.py
├── 5-pdf-page-splitter/
│   └── split_pdf.py
├── output/
│   ├── frames/
│   │   ├── frames_metadata.json
│   │   └── frame_0000_at_0.00s.jpg (etc.)
│   └── transcript.txt
├── sample_data/
│   ├── comparison_view.html
│   ├── note.html
│   ├── transcription.txt
│   └── translated_sinhala.html
└── README.md
```

## Installation

1. **Python**: 3.8+ (CUDA-capable GPU recommended for transcription speed)
2. **Clone & env**
	 ```cmd
	 git clone https://github.com/tharindu-s-rajapaksha/AI-Powered-Study-Tools.git
	 cd AI-Powered-Study-Tools
	 python -m venv .venv
	 .venv\Scripts\activate
	 ```
3. **Install deps**
	 ```cmd
	 pip install -r requirements.txt
	 ```
4. **Secrets**: copy `.env.example` to `.env` and add a valid `GOOGLE_API_KEY`.

## Configure Once, Reuse Everywhere

`inputs.json` is read by every batch-based script. Update the paths before launching any tool.

```json
{
	"video_transcriber": {
		"video_path": "sample_data/my_lecture.mkv"
	},
	"note_generator": {
		"text_file": "output/my_lecture_transcription.txt"
	},
	"translate_sinhala_html": {
		"input_file": "output/my_lecture_notes.html",
		"output_file": "output/my_lecture_sinhala.html"
	},
	"html_comparison_viewer": {
		"original_file": "output/my_lecture_notes.html",
		"translated_file": "output/my_lecture_sinhala.html",
		"output_file": "output/comparison_view.html"
	},
	"pdf_note_generator": {
		"pdf_file": "lectures/week-03.pdf",
		"start_page": 1,
		"end_page": 8
	},
	"pdf_splitter": {
		"input_pdf": "handouts/slides.pdf",
		"rows": 2,
		"cols": 3,
		"remove_empty": true,
		"empty_threshold": 0.95
	},
	"video_silence_remover": {
		"input_file": "sample_data/lecture.mkv",
		"output_file": "output/lecture_clean.mp4"
	}
}
```

> Tip: keep paths relative to this repo so that `run_batch.py` and individual modules share the same configuration on any machine.

## Tooling Overview

| Tool | Entry Point | Reads `inputs.json`? | Output |
| --- | --- | --- | --- |
| Lecture transcription | `1-video-transcriber/transcribe_video.py` | ✅ `video_transcriber` | `<video>_transcription.txt` |
| Real-time transcription | `2-real-time-transcriber/real_time_transcription.py` | ❌ (inline config) | `output/transcript.txt` + console stream |
| AI note generator (English) | `3-note-generator/generate_notes.py` | ✅ `note_generator` | `_notes.txt` + `_notes.html` |
| AI note generator (Sinhala) | `3-note-generator/generate_notes_sinhala.py` | ✅ `note_generator` | Sinhala Markdown + HTML |
| Sinhala HTML translator | `3-note-generator/translate_sinhala_html.py` | ✅ `translate_sinhala_html` | Localized HTML |
| Sinhala Markdown translator | `3-note-generator/translate_sinhala_md.py` | ✅ `translate_sinhala_md` | Localized Markdown |
| HTML comparison viewer | `3-note-generator/html_comparison_viewer.py` | ✅ `html_comparison_viewer` | Side-by-side `comparison_view.html` |
| PDF → AI notes | `3-note-generator/pdf_notes_generator.py` | ✅ `pdf_note_generator` | Notes per PDF chunk |
| Video silence remover | `4-video-silence-remover/remove_silence.py` | ✅ `video_silence_remover` | Cleaned MP4 |
| PDF grid splitter | `5-pdf-page-splitter/split_pdf.py` | ✅ `pdf_splitter` | Individual slide pages |

Each script can be run directly, e.g. `python 1-video-transcriber/transcribe_video.py`. Most will beep between stages to signal progress.

## Batch Runner

`run_batch.py` lets you iterate over multiple configurations without touching each script manually. Edit the `tool_key` and `batch_configs` block near the top, then run:

```cmd
python run_batch.py
```

The runner will back up the original section from `inputs.json`, apply the overrides batch-by-batch, execute the matching script, and finally restore the original configuration automatically.

## Real-Time Transcriber Notes

- Configure devices inside `real_time_transcription.py` (`device_index`, chunk sizes, etc.).
- Uncomment `transcriber.list_devices("system")` to print audio devices once.
- Logs stream in the console while `output/transcript.txt` is updated continuously; stop with `Ctrl+C`.

## Sample Data and Outputs

- `sample_data/` holds ready-made transcripts, HTML notes, and comparison views for testing without running GPU workloads.
- `output/` stores extracted temporary data.

## Safety & Secrets

- `.env` must never be committed; `.env.example` documents required keys.
- Long-running tools (transcription, Gemini calls) may take minutes. Watch console output for timestamps.
- NVIDIA GPU with the latest CUDA drivers drastically improves Faster-Whisper throughput; fall back to `device="cpu"` if needed.

---

_Academic use only—double-check all AI-generated content before sharing or publishing._