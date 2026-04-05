#!/usr/bin/env python3
"""
Lecture Subtitle Generator
Generates SRT/VTT subtitles for lecture videos using Faster-Whisper.
"""

import os
import sys
import platform
import site
import json
import logging
from datetime import timedelta
from pathlib import Path
import warnings


def _configure_windows_cuda_runtime():
    """Add NVIDIA runtime bin folders to PATH so ctranslate2 can load CUDA DLLs on Windows."""
    if platform.system() != "Windows":
        return

    search_roots = []
    try:
        search_roots.extend(site.getsitepackages())
    except Exception:
        pass

    user_site = site.getusersitepackages()
    if user_site:
        search_roots.append(user_site)

    cuda_bin_dirs = []
    for root in search_roots:
        nvidia_dir = Path(root) / "nvidia"
        if not nvidia_dir.exists():
            continue

        for bin_dir in nvidia_dir.rglob("bin"):
            if bin_dir.is_dir():
                cuda_bin_dirs.append(str(bin_dir))

    if cuda_bin_dirs:
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(cuda_bin_dirs + [current_path])


_configure_windows_cuda_runtime()
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"moviepy(\.|$)")

from moviepy.editor import VideoFileClip
import ctranslate2
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SoundPlayer:
    """Handle sound playback across different platforms."""
    
    def __init__(self):
        self.system = platform.system()
        
    def play_sound(self, sound_type: str):
        """Play system sound based on event type."""
        try:
            if self.system == "Linux":
                self._play_linux_sound(sound_type)
            elif self.system == "Windows":
                self._play_windows_sound(sound_type)
            elif self.system == "Darwin":  # macOS
                self._play_macos_sound(sound_type)
        except Exception as e:
            logger.debug(f"Could not play sound: {e}")
    
    def _play_linux_sound(self, sound_type: str):
        """Play sound on Linux."""
        sounds = {"start": "message", "step": "message-new-instant", "complete": "complete", "error": "dialog-error"}
        sound_name = sounds.get(sound_type, "message")
        try: os.system(f"paplay /usr/share/sounds/freedesktop/stereo/{sound_name}.oga 2>/dev/null &")
        except: pass
    
    def _play_windows_sound(self, sound_type: str):
        """Play sound on Windows."""
        import winsound
        sounds = {"start": (1000, 200), "step": (2000, 200), "complete": (5000, 1000), "error": (150, 1000)}
        freq, duration = sounds.get(sound_type, (600, 80))
        winsound.Beep(freq, duration)
    
    def _play_macos_sound(self, sound_type: str):
        """Play sound on macOS."""
        sounds = {"start": "Glass", "step": "Pop", "complete": "Hero", "error": "Basso"}
        sound_name = sounds.get(sound_type, "Pop")
        os.system(f"afplay /System/Library/Sounds/{sound_name}.aiff &")

class LectureSubtitleGenerator:
    def __init__(self, model_size="small", device=None, compute_type=None):
        self.model_size = model_size
        
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        else:
            self.device = device
            
        # Set compute type based on device if not specified
        if compute_type is None:
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type
            
        self.model = None
        self.sound_player = SoundPlayer()

    def _is_cuda_library_error(self, error: Exception) -> bool:
        """Return True when Faster-Whisper fails due to missing CUDA runtime libs."""
        message = str(error).lower()
        return "cublas" in message or "cuda" in message

    def _switch_to_cpu(self):
        """Switch runtime settings to CPU-safe defaults."""
        self.device = "cpu"
        self.compute_type = "int8"
        self.model = None

    def load_model(self):
        """Load the Faster-Whisper model."""
        logger.info(f"Loading Faster-Whisper {self.model_size} model on {self.device}...")
        self.sound_player.play_sound("step")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        except Exception as e:
            if self.device == "cuda" and self._is_cuda_library_error(e):
                logger.warning("CUDA libraries are not available. Falling back to CPU mode.")
                self._switch_to_cpu()
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            else:
                raise
        logger.info(f"Model loaded successfully! (device={self.device}, compute_type={self.compute_type})")
        self.sound_player.play_sound("step")

    def format_timestamp(self, seconds: float, format_type: str = "srt") -> str:
        """Format seconds into SRT or VTT timestamp strings."""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        milliseconds = int(td.microseconds / 1000)
        
        if format_type == "vtt":
            return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"
        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

    def generate_subtitles(self, video_path, output_path=None):
        """Extract audio, transcribe, and generate subtitle file."""
        try:
            self.sound_player.play_sound("start")
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            logger.info(f"Processing video: {video_path}")
            
            # Use MoviePy to extract audio
            video = VideoFileClip(video_path)
            audio = video.audio
            
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            temp_audio = os.path.join(output_dir, "temp_subtitle_audio.mp3")
            
            logger.info("Extracting audio...")
            audio.write_audiofile(temp_audio, logger=None)
            self.sound_player.play_sound("step")

            if self.model is None:
                self.load_model()

            logger.info("Transcribing and generating timestamps...")
            self.sound_player.play_sound("step")
            try:
                segments, _ = self.model.transcribe(temp_audio, beam_size=5)
            except Exception as e:
                if self.device == "cuda" and self._is_cuda_library_error(e):
                    logger.warning("CUDA runtime failed during subtitle generation. Retrying on CPU...")
                    self._switch_to_cpu()
                    self.load_model()
                    segments, _ = self.model.transcribe(temp_audio, beam_size=5)
                else:
                    raise

            if output_path is None:
                output_path = os.path.splitext(video_path)[0] + ".srt"

            format_type = "vtt" if output_path.endswith(".vtt") else "srt"
            
            logger.info(f"Writing subtitles to: {output_path}")
            with open(output_path, "w", encoding="utf-8") as f:
                if format_type == "vtt":
                    f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(segments, start=1):
                    start = self.format_timestamp(segment.start, format_type)
                    end = self.format_timestamp(segment.end, format_type)
                    
                    if format_type == "srt":
                        f.write(f"{i}\n")
                    
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{segment.text.strip()}\n\n")

            # Cleanup
            audio.close()
            video.close()
            if os.path.exists(temp_audio):
                os.remove(temp_audio)

            self.sound_player.play_sound("complete")
            logger.info("Subtitle generation complete!")
            return output_path

        except Exception as e:
            self.sound_player.play_sound("error")
            logger.error(f"Error during subtitle generation: {e}")
            raise

def main():
    # Load configuration
    base_dir = os.path.dirname(os.path.dirname(__file__))
    inputs_path = os.path.join(base_dir, "inputs.json")
    
    if not os.path.exists(inputs_path):
        logger.error(f"inputs.json not found at {inputs_path}")
        sys.exit(1)
        
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    config = inputs.get("subtitle_generator")
    if not config:
        logger.error("subtitle_generator section not found in inputs.json")
        sys.exit(1)
        
    video_path = config.get("video_path")
    output_path = config.get("output_path")
    
    if not video_path:
        logger.error("video_path not specified in inputs.json")
        sys.exit(1)
        
    generator = LectureSubtitleGenerator() # Now auto-detects device
    generator.generate_subtitles(video_path, output_path)

if __name__ == "__main__":
    main()
