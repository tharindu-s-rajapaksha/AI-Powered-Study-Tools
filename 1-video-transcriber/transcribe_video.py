import os
import platform
import moviepy.editor as mp
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


class VideoTranscriber:
    def __init__(self, model_size="small", device="cuda", compute_type="int8"):
        """
        Initialize the VideoTranscriber with the specified Whisper model parameters.

        Parameters:
        model_size (str): Size of the Whisper model to use ("tiny", "base", "small", "medium", "large").
        device (str): Device to use for the model (e.g., "cuda", "cpu").
        compute_type (str): Compute type for the model (e.g., "int8", "float32").
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.sound_player = SoundPlayer()

    def load_model(self):
        """Load the Faster-Whisper model."""
        print(f"Loading Faster-Whisper {self.model_size} model...")
        self.sound_player.play_sound("step")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        print("Model loaded successfully!")
        self.sound_player.play_sound("step")

    def transcribe_video(self, video_path, output_path=None):
        """
        Transcribe a video file to text.

        Parameters:
        video_path (str): Path to the video file.
        output_path (str): Optional path to save the transcription. If None, uses the video filename.

        Returns:
        str: Path to the transcription file.
        """
        try:
            self.sound_player.play_sound("start")
            print("Extracting audio from video...")
            video = mp.VideoFileClip(video_path)
            audio = video.audio

            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            temp_audio = os.path.join(output_dir, "temp_audio.mp3")
            audio.write_audiofile(temp_audio)
            self.sound_player.play_sound("step")

            if self.model is None:
                self.load_model()

            print("Transcribing audio...")
            self.sound_player.play_sound("step")
            segments, _ = self.model.transcribe(temp_audio)

            transcription = ""
            for segment in segments:
                # transcription += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                transcription += f"{segment.text} "

            audio.close()
            video.close()
            os.remove(temp_audio)

            if output_path is None:
                output_path = os.path.splitext(video_path)[0] + "_transcription.txt"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcription)

            self.sound_player.play_sound("complete")
            return output_path
        
        except Exception as e:
            self.sound_player.play_sound("error")
            print(f"Error during transcription: {e}")
            raise

    def transcribe_folder(self, folder_path):
        """
        Transcribe all video files in a folder.

        Parameters:
        folder_path (str): Path to the folder containing video files.
        """
        self.sound_player.play_sound("start")
        for file in os.listdir(folder_path):
            if file.endswith(".mp4") or file.endswith(".mkv"):
                print(f"Processing video: {file}\n")
                transcription_file = os.path.splitext(file)[0] + "_transcription.txt"
                if os.path.exists(os.path.join(folder_path, transcription_file)):
                    print(f"Transcription already exists for video: {file}\n\n")
                    continue
                video_path = os.path.join(folder_path, file)
                transcription_path = self.transcribe_video(video_path)
                print(f"Transcription saved to: {transcription_path}\n\n")

        print("Transcription complete. All videos processed.")
        self.sound_player.play_sound("complete")

    def transcribe_one_video(self, video_path):
        """
        Transcribe a single video file to text.

        Parameters:
        video_path (str): Path to the video file.
        """
        print(f"Processing single video: {video_path}\n")
        transcription_path = self.transcribe_video(video_path)
        print(f"Transcription saved to: {transcription_path}\n\n")



if __name__ == "__main__":
    # Load inputs from JSON
    inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    transcriber = VideoTranscriber(device="cuda")
    # transcriber.transcribe_folder("D:/Desktop/UNI/~ACA - L3S1/CM3640 - Artificial Cognitive Systems/Recordings")
    transcriber.transcribe_one_video(inputs["video_transcriber"]["video_path"])