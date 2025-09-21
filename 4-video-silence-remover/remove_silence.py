#!/usr/bin/env python3
"""
Jumpcutter Video Silence Remover
Automatically removes silent parts from videos using the jumpcutter library
"""

import os
import sys
import subprocess
import json
import logging
import winsound
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package}: {e}")
        sys.exit(1)

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        "jumpcutter",
        "numpy"
    ]
    
    logger.info("Checking and installing dependencies...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"{package} is already installed")
        except ImportError:
            logger.info(f"Installing {package}...")
            install_package(package)

def load_config():
    """Load configuration from inputs.json"""
    config_file = "inputs.json"
    
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
        "magnitude_threshold_ratio": 0.02, # (0.01-0.1)
        
        # Minimum silence duration to cut
        "duration_threshold": 0.6, # (in seconds)
        
        # Tolerance for audio spikes in silent parts 
        "failure_tolerance_ratio": 0.1, # (0.0-1.0)
        
        # Space to leave on edges of cuts
        "space_on_edges": 0.25, # (in seconds)
        
        # Speed up silent parts instead of cutting (use high number like 2000 to effectively remove)
        "silence_part_speed": 10,
        
        # What to cut: "silent", "voiced", or "both"
        "cut_mode": "silent",
        
        # Video codec (leave empty for auto, or specify like "libx264")
        "codec": "",
        
        # Bitrate (leave empty for auto, or specify like "5000k")
        "bitrate": ""
    }
    
    logger.info("Starting Jumpcutter Video Silence Remover...")
    
    # Sound notification - start
    try:
        winsound.Beep(480, 500)
    except:
        pass

    try:
        # Install dependencies
        check_and_install_dependencies()
        
        # Load configuration
        video_info = load_config()
        input_file = video_info["input_file"]
        output_file = video_info["output_file"]
        
        logger.info(f"Input file: {input_file}")
        logger.info(f"Output file: {output_file}")
        
        # Validate input
        validate_input_file(input_file)
        
        # Create output directory
        create_output_directory(output_file)
        
        # Run jumpcutter
        run_jumpcutter(input_file, output_file, JUMPCUTTER_PARAMS)
        
        # Sound notification - completion
        for freq in [480, 600, 720, 600, 480, 360]:
            winsound.Beep(freq, 300)
        
        logger.info("Video processing completed successfully!")
    except Exception as e:
        # Error sound
        winsound.Beep(300, 1000)

        logger.error(e)

if __name__ == "__main__":
    main()