import os
import platform
import site
from pathlib import Path


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

import ctranslate2
from faster_whisper import WhisperModel
import json

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
            print(f"Could not play sound: {e}")
    
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


class AudioTranscriber:
    """Transcribe audio files (mp3, m4a, wav, flac, etc.) to text using Faster-Whisper."""
    
    def __init__(self, model_size="small", device=None, compute_type=None):
        """
        Initialize the AudioTranscriber with the specified Whisper model parameters.

        Parameters:
        model_size (str): Size of the Whisper model to use ("tiny", "base", "small", "medium", "large").
        device (str): Device to use for the model (e.g., "cuda", "cpu"). If None, auto-detected.
        compute_type (str): Compute type for the model. If None, set based on device.
        """
        self.model_size = model_size
        if device is None:
            self.device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        else:
            self.device = device

        if compute_type is None:
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type

        self.model = None
        self.sound_player = SoundPlayer()
        
        # Supported audio formats
        self.supported_formats = ('.mp3', '.m4a', '.wav', '.flac', '.ogg', '.opus', '.aac', '.wma')

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
        print(f"Loading Faster-Whisper {self.model_size} model...")
        self.sound_player.play_sound("step")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        except Exception as e:
            if self.device == "cuda" and self._is_cuda_library_error(e):
                print("CUDA libraries are not available. Falling back to CPU mode.")
                self._switch_to_cpu()
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            else:
                raise
        print(f"Model loaded successfully! (device={self.device}, compute_type={self.compute_type})")
        self.sound_player.play_sound("step")

    def transcribe_audio(self, audio_path, output_path=None):
        """
        Transcribe an audio file to text.

        Parameters:
        audio_path (str): Path to the audio file.
        output_path (str): Optional path to save the transcription. If None, uses the audio filename.

        Returns:
        str: Path to the transcription file.
        """
        try:
            self.sound_player.play_sound("start")
            
            # Validate audio file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Validate audio format
            audio_ext = os.path.splitext(audio_path)[1].lower()
            if audio_ext not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {audio_ext}. Supported formats: {', '.join(self.supported_formats)}")
            
            print(f"Transcribing audio file: {os.path.basename(audio_path)}")
            self.sound_player.play_sound("step")

            if self.model is None:
                self.load_model()

            print("Transcribing audio...")
            self.sound_player.play_sound("step")
            try:
                segments, _ = self.model.transcribe(audio_path)
            except Exception as e:
                if self.device == "cuda" and self._is_cuda_library_error(e):
                    print("CUDA runtime failed during transcription. Retrying on CPU...")
                    self._switch_to_cpu()
                    self.load_model()
                    segments, _ = self.model.transcribe(audio_path)
                else:
                    raise

            transcription = ""
            for segment in segments:
                # transcription += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                transcription += f"{segment.text} "

            if output_path is None:
                output_path = os.path.splitext(audio_path)[0] + "_transcription.txt"

            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcription)

            self.sound_player.play_sound("complete")
            print(f"Transcription saved to: {output_path}")
            return output_path
        
        except Exception as e:
            self.sound_player.play_sound("error")
            print(f"Error during transcription: {e}")
            raise

    def transcribe_folder(self, folder_path):
        """
        Transcribe all audio files in a folder.

        Parameters:
        folder_path (str): Path to the folder containing audio files.
        """
        self.sound_player.play_sound("start")
        
        # Find all supported audio files
        audio_files = []
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(fmt) for fmt in self.supported_formats):
                audio_files.append(file)
        
        if not audio_files:
            print(f"No audio files found in folder: {folder_path}")
            return
        
        print(f"Found {len(audio_files)} audio file(s) to transcribe\n")
        
        for file in audio_files:
            print(f"Processing audio: {file}\n")
            transcription_file = os.path.splitext(file)[0] + "_transcription.txt"
            
            if os.path.exists(os.path.join(folder_path, transcription_file)):
                print(f"Transcription already exists for audio: {file}\n\n")
                continue
            
            audio_path = os.path.join(folder_path, file)
            self.transcribe_audio(audio_path)
            print()

        print("Transcription complete. All audio files processed.")
        self.sound_player.play_sound("complete")

    def transcribe_one_audio(self, audio_path):
        """
        Transcribe a single audio file to text.

        Parameters:
        audio_path (str): Path to the audio file.
        """
        print(f"Processing single audio file: {audio_path}\n")
        self.transcribe_audio(audio_path)
        print()



if __name__ == "__main__":
    # Load inputs from JSON
    inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    transcriber = AudioTranscriber()
    transcriber.transcribe_one_audio(inputs["audio_transcriber"]["audio_path"])
