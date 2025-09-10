import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from queue import Queue
from threading import Thread
import time
import os
from typing import Optional

# substring to match speaker devices (customizable via SPEAKER_MATCH env var)
COMPUTER_SPEAKER_MATCH = os.environ.get("SPEAKER_MATCH", "Speaker")

class RealtimeTranscriber:
    def __init__(self, model_size="base", input_source: str = "mic", device_index: Optional[int] = None):
        """
        input_source: "mic" for microphone, "system" for system audio (WASAPI loopback on Windows).
        device_index: Optional explicit device index from list_devices().
        """
        # Initialize Whisper model
        self.model = WhisperModel(model_size, device="cuda", compute_type="int8")

        # Audio parameters
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.TARGET_RATE = 16000  # Whisper expects 16kHz mono float32
        self.CHUNK = 1024 * 8  # Larger chunk size for better processing
        self.RECORD_SECONDS = 4  # Process audio in ~4-second segments

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()

        # Source selection
        self.input_source = input_source.lower()
        self.device_index = device_index
        self.stream_rate = None  # Actual stream sample rate (may differ from TARGET_RATE)
        self.stream_channels = 1  # Actual stream channels

        # Create a queue for audio chunks
        self.audio_queue = Queue()

        # Flag to control recording
        self.is_recording = False

        # Where to append transcripts
        self.transcript_path = "output/transcript.txt"

    # ---------- Device Helpers ----------
    def list_devices(self, input_source: Optional[str] = None):
        """Print usable audio devices (safe to open) with indices and recommended channels.

        input_source: None (default) => show devices with input channels (>0).
                      "mic" => devices suitable for microphone capture (input channels >= 1).
                      "system" => prefer WASAPI loopback / speaker capture devices.
        """
        src = (input_source or "any").lower()
        print(f"Available audio devices (safe for '{src}'):")
        hostapis = {i: self.audio.get_host_api_info_by_index(i) for i in range(self.audio.get_host_api_count())}
        found = 0
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            host = hostapis.get(info.get("hostApi"), {}).get("name", "?")
            name = (info.get("name") or "").strip()
            is_loop = bool(info.get("isLoopbackDevice", False))
            max_in = int(info.get("maxInputChannels") or 0)
            max_out = int(info.get("maxOutputChannels") or 0)
            default_sr = int(info.get("defaultSampleRate")) if info.get("defaultSampleRate") else 0

            # Filtering logic: only show devices that are usable for capture
            if src == "system":
                # Prefer loopback devices; also include devices whose name suggests loopback/speakers
                lname = name.lower()
                speaker_match = COMPUTER_SPEAKER_MATCH.lower()
                if not (is_loop or "loopback" in lname or "stereo mix" in lname or speaker_match in lname or max_in > 0):
                    continue
            else:
                # mic or any: require at least 1 input channel
                if max_in <= 0:
                    continue

            # Recommend channels: prefer stereo for system loopback if available, otherwise mono
            recommended = 2 if (src == "system" and max_in >= 2) else 1

            print(f"[{i:02d}] {name} | host={host} | in={max_in} out={max_out} | sr={default_sr} | loopback={is_loop} | rec_ch={recommended}")
            found += 1

        if found == 0:
            print("(no suitable devices found for the requested input_source)\nUse list_devices(None) to show all devices and pick one manually.")

    def _find_default_mic_index(self):
        try:
            return self.audio.get_default_input_device_info().get("index")
        except Exception:
            return None

    def _find_default_loopback_index(self):
        """Try to locate a WASAPI loopback input device on Windows (PyAudio 0.2.13+)."""
        # Prefer devices flagged as isLoopbackDevice
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info.get("isLoopbackDevice", False):
                return i
        # Fallback heuristic: look for devices with "loopback" or typical speaker names as inputs
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            name = (info.get("name") or "").lower()
            speaker_match = COMPUTER_SPEAKER_MATCH.lower()
            if info.get("maxInputChannels", 0) > 0 and ("loopback" in name or speaker_match in name):
                return i
        return None

    # ---------- Streaming and Processing ----------

    def callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream. Converts to mono float32 before enqueuing."""
        buf = np.frombuffer(in_data, dtype=np.float32)
        if self.stream_channels and self.stream_channels > 1:
            try:
                frames = buf.reshape(-1, self.stream_channels)
                mono = frames.mean(axis=1).astype(np.float32)
            except Exception:
                # Fallback if reshape fails for any reason
                mono = buf[:: self.stream_channels].astype(np.float32)
        else:
            mono = buf
        self.audio_queue.put(mono)
        return (in_data, pyaudio.paContinue)

    def _resample_to_target(self, audio: np.ndarray, src_rate: int) -> np.ndarray:
        """Resample mono float32 audio to TARGET_RATE using linear interpolation."""
        if src_rate == self.TARGET_RATE or audio.size == 0:
            return audio
        # Compute new sample positions
        duration = audio.size / float(src_rate)
        new_length = int(round(duration * self.TARGET_RATE))
        if new_length <= 0:
            return np.array([], dtype=np.float32)
        x_old = np.linspace(0.0, duration, num=audio.size, endpoint=False)
        x_new = np.linspace(0.0, duration, num=new_length, endpoint=False)
        resampled = np.interp(x_new, x_old, audio).astype(np.float32)
        return resampled

    def process_audio(self):
        """Process audio chunks and transcribe"""
        while self.is_recording:
            # Collect audio for RECORD_SECONDS
            audio_data = []
            # Determine rate for timing (use actual stream rate if known)
            rate = self.stream_rate or self.TARGET_RATE
            chunks_to_collect = max(1, int(rate / self.CHUNK * self.RECORD_SECONDS))
            for _ in range(chunks_to_collect):
                if not self.is_recording:
                    break
                if not self.audio_queue.empty():
                    audio_data.append(self.audio_queue.get())
                else:
                    # Brief sleep to avoid busy-wait when queue is empty
                    time.sleep(0.005)

            if audio_data:
                # Combine all chunks
                audio_segment = np.concatenate(audio_data)

                # Resample to 16k if stream rate differs
                audio_segment = self._resample_to_target(audio_segment, int(rate))

                # Transcribe
                segments, _ = self.model.transcribe(
                    audio_segment,
                    beam_size=5,
                    language="en",
                    vad_filter=True,
                )

                # Print and append transcription
                for segment in segments:
                    text = segment.text.strip()
                    if not text:
                        continue
                    line = f"{text}"
                    print(f"Transcription: {line}")
                    try:
                        with open(self.transcript_path, "a", encoding="utf-8") as f:
                            f.write(line + "\n")
                            f.flush()
                    except Exception as e:
                        # Don't crash on file I/O issues; just report
                        print(f"[warn] Failed to append to transcript.txt: {e}")

    def start_transcription(self):
        """Start real-time transcription"""
        # Determine device index and stream rate based on input source
        if self.device_index is None:
            if self.input_source == "system":
                dev_idx = self._find_default_loopback_index()
                if dev_idx is None:
                    print("[warn] No loopback device found. Falling back to default microphone.")
                    self.input_source = "mic"
                    dev_idx = self._find_default_mic_index()
            else:
                dev_idx = self._find_default_mic_index()
        else:
            dev_idx = self.device_index

        if dev_idx is None:
            raise RuntimeError("No suitable input device found. Use list_devices() to pick a device index.")

        dev_info = self.audio.get_device_info_by_index(dev_idx)
        # Use device's default sample rate for the stream; we'll resample to TARGET_RATE later
        self.stream_rate = int(dev_info.get("defaultSampleRate") or self.TARGET_RATE)

        # Validate device input channel capability and pick channels to use
        max_in_ch = int(dev_info.get("maxInputChannels") or 0)
        if max_in_ch <= 0:
            # Try to find a fallback device with input channels
            found = None
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if self.input_source == "system":
                    if info.get("isLoopbackDevice", False) and int(info.get("maxInputChannels") or 0) > 0:
                        found = (i, info)
                        break
                else:
                    if int(info.get("maxInputChannels") or 0) > 0:
                        found = (i, info)
                        break
            if found is None:
                raise RuntimeError(
                    f"Device {dev_idx} ('{dev_info.get('name')}') has no input channels and no fallback was found.\nUse list_devices() to pick a device with input channels."
                )
            # Switch to fallback
            dev_idx, dev_info = found
            max_in_ch = int(dev_info.get("maxInputChannels") or 1)

        # Choose desired channels (prefer stereo for system loopback if available)
        if self.input_source == "system":
            desired_channels = 2 if max_in_ch >= 2 else 1
        else:
            desired_channels = 1 if max_in_ch >= 1 else 1
        # Ensure we don't request more channels than the device supports
        channels_to_use = min(desired_channels, max_in_ch if max_in_ch > 0 else 1)
        channels_to_use = max(1, channels_to_use)
        self.stream_channels = channels_to_use

        self.is_recording = True

        # Start audio stream. Try with chosen channels, fall back to mono if the driver rejects the channel count.
        try:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.stream_channels,
                rate=self.stream_rate,
                input=True,
                input_device_index=dev_idx,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.callback,
            )
        except OSError as e:
            # Try a safe mono fallback to avoid Errno -9998
            print(f"[warn] Opening stream with {self.stream_channels} channels failed: {e}. Trying mono fallback...")
            try:
                self.stream = self.audio.open(
                    format=self.FORMAT,
                    channels=1,
                    rate=self.stream_rate,
                    input=True,
                    input_device_index=dev_idx,
                    frames_per_buffer=self.CHUNK,
                    stream_callback=self.callback,
                )
                self.stream_channels = 1
            except Exception as e2:
                raise RuntimeError(f"Failed to open audio stream (tried {self.stream_channels} and mono): {e2}") from e2

        # Start processing thread
        self.process_thread = Thread(target=self.process_audio, daemon=True)
        self.process_thread.start()

        src_desc = "system audio (loopback)" if dev_info.get("isLoopbackDevice") else ("system audio" if self.input_source == "system" else "microphone")
        print(
            f"Started recording from {src_desc} [{dev_idx}: {dev_info.get('name')}] at {self.stream_rate} Hz, {self.stream_channels} ch... Press Ctrl+C to stop"
        )

    def stop_transcription(self):
        """Stop real-time transcription"""
        if not getattr(self, "is_recording", False):
            return
        self.is_recording = False

        # Stop and close the stream
        if getattr(self, "stream", None) is not None:
            try:
                self.stream.stop_stream()
            except Exception:
                pass
            try:
                self.stream.close()
            except Exception:
                pass

        # Wait for processing thread to finish
        if getattr(self, "process_thread", None) is not None:
            try:
                self.process_thread.join(timeout=2.0)
            except Exception:
                pass

        # Clean up PyAudio
        try:
            self.audio.terminate()
        except Exception:
            pass
        print("\nStopped recording and transcribing")

# Example usage
if __name__ == "__main__":
    # Try system audio capture using the 'Stereo Mix' device (index 14) as a likely candidate.
    transcriber = RealtimeTranscriber(model_size="base", input_source="system", device_index=14)
    try:
        # Show system-capable devices and the chosen device
        # transcriber.list_devices("system")
        try:
            info = transcriber.audio.get_device_info_by_index(transcriber.device_index)
            print(f"\nAttempting to open device {transcriber.device_index}: {info.get('name')}")
        except Exception:
            pass
        transcriber.start_transcription()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        transcriber.stop_transcription()