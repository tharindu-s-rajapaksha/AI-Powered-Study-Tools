import os
import moviepy.editor as mp
from faster_whisper import WhisperModel
import json

class VideoTranscriber:
    def __init__(self, model_size="base", device="cuda", compute_type="int8"):
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

    def load_model(self):
        """Load the Faster-Whisper model."""
        print(f"Loading Faster-Whisper {self.model_size} model...")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe_video(self, video_path, output_path=None):
        """
        Transcribe a video file to text.

        Parameters:
        video_path (str): Path to the video file.
        output_path (str): Optional path to save the transcription. If None, uses the video filename.

        Returns:
        str: Path to the transcription file.
        """
        print("Extracting audio from video...")
        video = mp.VideoFileClip(video_path)
        audio = video.audio

        temp_audio = "output/temp_audio.mp3"
        audio.write_audiofile(temp_audio)

        if self.model is None:
            self.load_model()

        print("Transcribing audio...")
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

        return output_path

    def transcribe_folder(self, folder_path):
        """
        Transcribe all video files in a folder.

        Parameters:
        folder_path (str): Path to the folder containing video files.
        """
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