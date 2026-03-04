#!/usr/bin/env python3
"""
Video Silence Remover
Automatically removes silent parts from videos
"""

import os
import sys
import subprocess
import json
import logging
import platform
from pathlib import Path
import time
import shutil
import numpy as np
import re
import importlib.metadata as metadata
from packaging.requirements import Requirement
from packaging.version import Version

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
        """Play sound on Linux using paplay or beep."""
        sounds = {
            "start": "message",
            "step": "message-new-instant",
            "complete": "complete",
            "error": "dialog-error"
        }
        
        sound_name = sounds.get(sound_type, "message")
        
        # Try paplay first (works with PulseAudio)
        try:
            os.system(f"paplay /usr/share/sounds/freedesktop/stereo/{sound_name}.oga 2>/dev/null &")
        except:
            # Fallback to beep
            try:
                frequencies = {
                    "start": "800 -l 100",
                    "step": "600 -l 80",
                    "complete": "1000 -l 150",
                    "error": "400 -l 200"
                }
                freq = frequencies.get(sound_type, "600 -l 80")
                os.system(f"beep -f {freq} 2>/dev/null &")
            except:
                pass
    
    def _play_windows_sound(self, sound_type: str):
        """Play sound on Windows."""
        import winsound
        
        sounds = {
            "start": (1000, 200),
            "step": (2000, 200),
            "complete": (5000, 1000),
            "error": (150, 1000)
        }
        
        freq, duration = sounds.get(sound_type, (600, 80))
        winsound.Beep(freq, duration)
    
    def _play_macos_sound(self, sound_type: str):
        """Play sound on macOS."""
        sounds = {
            "start": "Glass",
            "step": "Pop",
            "complete": "Hero",
            "error": "Basso"
        }
        
        sound_name = sounds.get(sound_type, "Pop")
        os.system(f"afplay /System/Library/Sounds/{sound_name}.aiff &")

def install_package(package, extra_args=None):
    """Install a package using pip or fall back to uv pip."""
    extra_args = extra_args or []

    pip_cmd = [sys.executable, "-m", "pip", "install", package, *extra_args]
    uv_cli = shutil.which("uv")

    try:
        subprocess.check_call(pip_cmd)
        logger.info(f"Successfully installed {package}")
        return
    except Exception:
        if not uv_cli:
            logger.error(f"Failed to install {package}: pip unavailable")
            sys.exit(1)

    try:
        uv_cmd = [uv_cli, "pip", "install", package, *extra_args]
        subprocess.check_call(uv_cmd)
        logger.info(f"Successfully installed {package} (uv)")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package}: {e}")
        sys.exit(1)


def patch_moviepy_for_numpy2():
    """Patch moviepy's to_soundarray to work with NumPy 2.x stacker rules."""
    try:
        from moviepy.audio.AudioClip import AudioClip

        def to_soundarray(self, tt=None, fps=None, quantize=False, nbytes=2, buffersize=50000):
            if fps is None:
                fps = self.fps

            stacker = np.vstack if self.nchannels == 2 else np.hstack
            max_duration = 1.0 * buffersize / fps

            if tt is None:
                if self.duration > max_duration:
                    chunks = list(self.iter_chunks(fps=fps, quantize=quantize, nbytes=2, chunksize=buffersize))
                    return stacker(chunks)
                tt = np.arange(0, self.duration, 1.0 / fps)

            snd_array = self.get_frame(tt)

            if quantize:
                snd_array = np.maximum(-0.99, np.minimum(0.99, snd_array))
                inttype = {1: "int8", 2: "int16", 4: "int32"}[nbytes]
                snd_array = (2 ** (8 * nbytes - 1) * snd_array).astype(inttype)

            return snd_array

        AudioClip.to_soundarray = to_soundarray
    except Exception as e:
        logger.warning(f"Could not patch moviepy for NumPy 2.x: {e}")


def patch_moviepy_file_for_numpy2():
    """Persistently patch AudioClip.py so jumpcutter CLI uses the NumPy-safe stacker."""
    try:
        import moviepy.audio.AudioClip as ac
        audio_clip_path = Path(ac.__file__)
        text = audio_clip_path.read_text()

        pattern = r"return stacker\(self\.iter_chunks\(fps=fps, quantize=quantize,\s*nbytes=2, chunksize=buffersize\)\)"
        replacement = "chunks = list(self.iter_chunks(fps=fps, quantize=quantize,\n                               nbytes=2, chunksize=buffersize))\n                return stacker(chunks)"

        if re.search(pattern, text):
            new_text = re.sub(pattern, replacement, text)
            audio_clip_path.write_text(new_text)
            logger.info("Patched moviepy AudioClip.py for NumPy 2.x")
        else:
            logger.debug("MoviePy AudioClip.py already patched or pattern not found")
    except Exception as e:
        logger.warning(f"Could not persistently patch moviepy file: {e}")

def ensure_dependencies():
    """Ensure required dependencies are present; instruct user to sync otherwise."""
    required_packages = {
        "moviepy": "moviepy==1.0.3",
        "numpy": "numpy>=2.0.0",
        "tqdm": "tqdm>=4.60.0,<4.61.0",
        "jumpcutter": "jumpcutter==0.1.6",
    }

    logger.info("Checking dependencies...")

    def is_satisfied(install_spec: str) -> bool:
        req = Requirement(install_spec)
        try:
            installed_version = metadata.version(req.name)
        except metadata.PackageNotFoundError:
            return False
        if not req.specifier:
            return True
        try:
            return req.specifier.contains(Version(installed_version), prereleases=True)
        except Exception:
            return False

    missing = [spec for spec in required_packages.values() if not is_satisfied(spec)]
    if missing:
        logger.error(
            "Missing or incompatible packages: %s. "
            "Run 'UV_PROJECT_ENVIRONMENT=.venv uv sync' once, or activate .venv before running."
            % ", ".join(missing)
        )
        sys.exit(1)

def load_config():
    """Load configuration from inputs.json"""
    # Look for inputs.json in the parent directory (project root)
    config_file = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    
    if not os.path.exists(config_file):
        logger.error(f"Configuration file {config_file} not found!")
        sys.exit(1)
    
    try:
        with open(config_file, "r") as f:
            inputs = json.load(f)
        
        video_info = inputs.get("video_silence_remover")
        if not video_info:
            logger.error("video_silence_remover section not found in inputs.json")
            sys.exit(1)
            
        return video_info
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        sys.exit(1)

def validate_input_file(input_file):
    """Validate that input file exists"""
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Check if it's a video file
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    file_ext = Path(input_file).suffix.lower()
    
    if file_ext not in video_extensions:
        logger.warning(f"File extension {file_ext} might not be a supported video format")

def create_output_directory(output_file):
    """Create output directory if it doesn't exist"""
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

def get_codec_for_extension(file_path):
    """Get appropriate codec based on file extension"""
    ext = Path(file_path).suffix.lower()
    codec_mapping = {
        '.mp4': 'libx264',
        '.avi': 'libx264',
        '.mov': 'libx264',
        '.mkv': 'libx264',  # Force h264 codec for mkv
        '.wmv': 'libx264',
        '.flv': 'libx264',
        '.webm': 'libvpx',
        '.m4v': 'libx264'
    }
    return codec_mapping.get(ext, 'libx264')

def run_jumpcutter(input_file, output_file, params):
    """Run jumpcutter with specified parameters"""
    
    # Auto-detect codec if not specified
    codec = params["codec"] if params["codec"] else get_codec_for_extension(output_file)
    
    # For mkv files, also suggest changing to mp4 for better compatibility
    if Path(output_file).suffix.lower() == '.mkv' and not params["codec"]:
        logger.warning("MKV output detected. Consider using .mp4 extension for better compatibility.")
        logger.info(f"Using codec: {codec}")
    
    # Build jumpcutter command
    cmd = [
        "jumpcutter",
        "-i", input_file,
        "-o", output_file,
        "-m", str(params["magnitude_threshold_ratio"]),
        "-d", str(params["duration_threshold"]),
        "-f", str(params["failure_tolerance_ratio"]),
        "-s", str(params["space_on_edges"]),
        "-x", str(params["silence_part_speed"]),
        "-c", params["cut_mode"],
        "--codec", codec  # Always specify codec
    ]
    
    # Add bitrate if specified
    if params["bitrate"]:
        cmd.extend(["--bitrate", params["bitrate"]])
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully processed video. Output saved to: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Jumpcutter failed with error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Jumpcutter not found. Make sure it's installed correctly.")
        sys.exit(1)

def main():
    """Main function"""
    
    # Adjustable parameters for Jumpcutter
    # You can modify these values to fine-tune the silence removal
    JUMPCUTTER_PARAMS = {
        # Silence detection sensitivity (lower = more sensitive)
        "magnitude_threshold_ratio": 0.01, # (0.01-0.1)
        
        # Minimum silence duration to cut
        "duration_threshold": 0.5, # (in seconds)
        
        # Tolerance for audio spikes in silent parts 
        "failure_tolerance_ratio": 0.1, # (0.0-1.0)
        
        # Space to leave on edges of cuts
        "space_on_edges": 0.24, # (in seconds)
        
        # Speed up silent parts instead of cutting (use high number like 2000 to effectively remove)
        "silence_part_speed": 10,
        
        # What to cut: "silent", "voiced", or "both"
        "cut_mode": "silent",
        
        # Video codec (leave empty for auto, or specify like "libx264")
        "codec": "",
        
        # Bitrate (leave empty for auto, or specify like "5000k")
        "bitrate": ""
    }
    
    logger.info("Starting Video Silence Remover...")
    
    sound_player = SoundPlayer()
    sound_player.play_sound("start")

    # Validate dependencies (installed via uv sync or activated .venv)
    ensure_dependencies()

    # Patch moviepy for NumPy 2.x compatibility
    patch_moviepy_for_numpy2()
    patch_moviepy_file_for_numpy2()
    
    # Load configuration
    video_info = load_config()

    try:
        input_file = video_info["input_file"]
        output_file = video_info["output_file"]
            
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")

        # Validate input
        validate_input_file(input_file)
        
        # Create output directory
        create_output_directory(output_file)
        
        # Run jumpcutter
        start_time = time.time()
        run_jumpcutter(input_file, output_file, JUMPCUTTER_PARAMS)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Total processing time: {duration:.2f} seconds")
        
        sound_player.play_sound("complete")
        logger.info("Video processing completed successfully!")
    except Exception as e:
        sound_player.play_sound("error")
        logger.error(e)

if __name__ == "__main__":
    main()