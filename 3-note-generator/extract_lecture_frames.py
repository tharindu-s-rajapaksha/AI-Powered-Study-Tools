import os
import cv2
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import winsound


class LectureFrameExtractor:
    def __init__(self, video_path: str, output_folder: str = "output/frames"):
        """
        Initialize the frame extractor for lecture videos.
        
        Args:
            video_path: Path to the input video file
            output_folder: Folder to save extracted frames
        """
        self.video_path = video_path
        self.output_folder = output_folder
        
        # Frame extraction parameters
        self.similarity_threshold = 0.95  # Higher = more similar frames needed to skip
        self.min_stable_duration = 5.0    # Minimum seconds a frame should be stable
        self.check_interval = 1.0         # Check frames every 1 second
        self.motion_threshold = 0.20      # Threshold to detect fast motion (lower = more sensitive)
        self.duplicate_threshold = 0.98   # Threshold to prevent extracting duplicate frames
        
        # Create output directory
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        
        self.extracted_frames = []
        self.saved_frames_cache = []  # Cache of all saved frames to prevent duplicates
        
    def print_progress(self, message: str):
        """Print progress message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def calculate_frame_similarity(self, frame1, frame2):
        """
        Calculate similarity between two frames using histogram comparison.
        Returns a value between 0 (completely different) and 1 (identical).
        """
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate histograms
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        # Normalize histograms
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # Calculate correlation
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        return correlation
        
    def calculate_structural_similarity(self, frame1, frame2):
        """
        Calculate structural similarity using feature matching.
        Returns a value indicating how similar the structure is.
        """
        # Resize for faster processing
        height, width = frame1.shape[:2]
        max_dim = 800
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame1 = cv2.resize(frame1, (new_width, new_height))
            frame2 = cv2.resize(frame2, (new_width, new_height))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Calculate mean difference
        mean_diff = np.mean(diff) / 255.0
        
        # Return similarity (1 - difference)
        return 1.0 - mean_diff
        
    def detect_fast_motion(self, frames_buffer):
        """
        Detect if there's fast motion in a sequence of frames.
        Returns True if fast motion is detected.
        """
        if len(frames_buffer) < 3:
            return False
            
        # Calculate similarities between consecutive frames
        similarities = []
        for i in range(len(frames_buffer) - 1):
            sim = self.calculate_structural_similarity(frames_buffer[i], frames_buffer[i + 1])
            similarities.append(sim)
        
        # If average similarity is low, it means fast motion
        avg_similarity = np.mean(similarities)
        
        return avg_similarity < (1.0 - self.motion_threshold)
        
    def is_duplicate_frame(self, current_frame):
        """
        Check if this frame has already been saved (to prevent duplicates).
        Compares against all previously saved frames.
        """
        if not self.saved_frames_cache:
            return False
            
        for saved_frame in self.saved_frames_cache:
            similarity = self.calculate_frame_similarity(current_frame, saved_frame)
            structural_sim = self.calculate_structural_similarity(current_frame, saved_frame)
            
            # If very similar to any saved frame, it's a duplicate
            if similarity > self.duplicate_threshold and structural_sim > self.duplicate_threshold:
                return True
                
        return False
        
    def is_frame_stable(self, current_frame, stable_frame, duration):
        """
        Check if the current frame is stable (similar to the reference stable frame).
        """
        if stable_frame is None:
            return True, current_frame
            
        # Calculate similarity
        similarity = self.calculate_frame_similarity(current_frame, stable_frame)
        structural_sim = self.calculate_structural_similarity(current_frame, stable_frame)
        
        # Combined similarity check
        is_similar = (similarity > self.similarity_threshold and 
                     structural_sim > self.similarity_threshold)
        
        if is_similar:
            return True, stable_frame
        else:
            # New scene detected
            return False, current_frame
            
    def save_frame(self, frame, timestamp, frame_number):
        """Save a frame to disk and add to cache."""
        # Check if this is a duplicate of any previously saved frame
        if self.is_duplicate_frame(frame):
            # Don't print for every duplicate - too verbose
            return None
            
        filename = f"frame_{frame_number:04d}_at_{timestamp:.2f}s.jpg"
        filepath = os.path.join(self.output_folder, filename)
        
        cv2.imwrite(filepath, frame)
        
        # Add to cache to prevent future duplicates
        self.saved_frames_cache.append(frame.copy())
        
        frame_info = {
            'frame_number': frame_number,
            'timestamp': timestamp,
            'filename': filename,
            'filepath': filepath
        }
        
        self.extracted_frames.append(frame_info)
        self.print_progress(f"✓ Extracted frame {frame_number} at {timestamp:.2f}s")
        
        return filepath
        
    def extract_frames(self):
        """
        Main method to extract stable frames from the video.
        """
        self.print_progress(f"Opening video: {self.video_path}")
        
        # Open video
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        self.print_progress(f"Video properties: {fps:.2f} FPS, {total_frames} frames, {duration:.2f}s duration")
        
        # Frame processing variables
        stable_frame = None
        stable_start_time = 0
        last_saved_time = -999  # Initialize to ensure first frame can be saved
        frame_count = 0
        frames_buffer = []  # Buffer to detect fast motion
        buffer_size = 5
        
        check_frame_interval = int(fps * self.check_interval)
        
        self.print_progress("Starting frame extraction...")
        self.print_progress(f"Analyzing 1 frame per second (every {check_frame_interval} frames)")
        
        try:
            frame_index = 0
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                    
                frame_index += 1
                
                # Only process frames at intervals (e.g., every 1 second)
                if frame_index % check_frame_interval != 0:
                    continue
                
                current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Add to buffer for motion detection
                frames_buffer.append(frame.copy())
                if len(frames_buffer) > buffer_size:
                    frames_buffer.pop(0)
                
                # Check for fast motion
                if self.detect_fast_motion(frames_buffer):
                    # Fast motion detected - reset stable frame tracking
                    stable_frame = None
                    stable_start_time = current_time
                    continue
                
                # Check if frame is stable
                is_stable, reference_frame = self.is_frame_stable(
                    frame, stable_frame, current_time - stable_start_time
                )
                
                if is_stable:
                    # Frame is similar to stable frame
                    stable_duration = current_time - stable_start_time
                    
                    # If stable for long enough and not recently saved, save it
                    if (stable_duration >= self.min_stable_duration and 
                        current_time - last_saved_time >= self.min_stable_duration):
                        
                        saved_path = self.save_frame(reference_frame, stable_start_time, frame_count)
                        if saved_path:  # Only increment if actually saved (not a duplicate)
                            last_saved_time = stable_start_time
                            frame_count += 1
                        
                        # Keep tracking this stable frame
                        stable_frame = reference_frame
                else:
                    # New scene detected
                    stable_frame = reference_frame
                    stable_start_time = current_time
                
                # Progress update
                if frame_index % (fps * 30) == 0:  # Every 30 seconds
                    progress = (frame_index / total_frames) * 100
                    elapsed_time = frame_index / fps
                    self.print_progress(f"Progress: {progress:.1f}% - {elapsed_time:.0f}s analyzed - {len(self.extracted_frames)} frames extracted")
        
        finally:
            cap.release()
            
        self.print_progress(f"Extraction complete! Total frames extracted: {len(self.extracted_frames)}")
        
        return self.extracted_frames
        
    def save_metadata(self):
        """Save metadata about extracted frames to JSON."""
        metadata = {
            'video_path': self.video_path,
            'extraction_time': datetime.now().isoformat(),
            'total_frames_extracted': len(self.extracted_frames),
            'parameters': {
                'similarity_threshold': self.similarity_threshold,
                'min_stable_duration': self.min_stable_duration,
                'check_interval': self.check_interval,
                'motion_threshold': self.motion_threshold
            },
            'frames': self.extracted_frames
        }
        
        metadata_path = os.path.join(self.output_folder, 'frames_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        self.print_progress(f"Metadata saved to: {metadata_path}")
        return metadata_path
        
    def cleanup_old_frames(self):
        """Remove old frames from the output folder."""
        self.print_progress("Cleaning up old frames...")
        
        frame_files = list(Path(self.output_folder).glob("frame_*.jpg"))
        for file in frame_files:
            try:
                os.remove(file)
            except Exception as e:
                self.print_progress(f"Could not remove {file}: {e}")
                
        # Also remove old metadata
        metadata_file = Path(self.output_folder) / 'frames_metadata.json'
        if metadata_file.exists():
            try:
                os.remove(metadata_file)
            except Exception as e:
                self.print_progress(f"Could not remove metadata: {e}")
                
        self.print_progress("Cleanup complete")
        
    def run(self, cleanup_first=True):
        """
        Run the complete frame extraction process.
        
        Args:
            cleanup_first: Whether to clean up old frames before extraction
        """
        try:
            # Sound notification - start
            try:
                winsound.Beep(480, 500)
            except:
                pass
            
            if cleanup_first:
                self.cleanup_old_frames()
            
            # Extract frames
            frames = self.extract_frames()
            
            # Save metadata
            metadata_path = self.save_metadata()
            
            # Sound notification - completion
            try:
                # Success melody
                for freq in [480, 600, 720]:
                    winsound.Beep(freq, 300)
            except:
                pass
            
            return frames, metadata_path
            
        except Exception as e:
            self.print_progress(f"Error during extraction: {e}")
            
            # Error sound
            try:
                winsound.Beep(300, 1000)
            except:
                pass
                
            raise


def main():
    """Main function to run the frame extractor."""
    
    # Load inputs from JSON
    try:
        inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
        with open(inputs_path, "r") as f:
            inputs = json.load(f)
        
        # Get video path from inputs
        # Assuming you'll add a video_path field to inputs.json
        if "note_generator" in inputs and "video_path" in inputs["note_generator"]:
            VIDEO_PATH = inputs["note_generator"]["video_path"]
        else:
            # Fallback: ask user or use a default
            print("Please add 'video_path' to inputs.json under 'note_generator'")
            print("Example: \"video_path\": \"path/to/your/lecture_video.mp4\"")
            return
            
    except Exception as e:
        print(f"Error loading inputs.json: {e}")
        return
    
    # Output folder
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "output", "frames")
    
    # Create and run the extractor
    extractor = LectureFrameExtractor(
        video_path=VIDEO_PATH,
        output_folder=OUTPUT_FOLDER
    )
    
    # You can adjust these parameters for fine-tuning
    # Higher similarity_threshold = more strict (fewer frames extracted)
    # Higher min_stable_duration = only extract slides shown for longer
    # Lower motion_threshold = more sensitive to fast motion
    
    extractor.similarity_threshold = 0.95  # 95% similarity required (more strict)
    extractor.min_stable_duration = 5.0    # 5 seconds minimum (longer duration)
    extractor.motion_threshold = 0.20      # 20% change threshold for fast motion
    extractor.duplicate_threshold = 0.98   # 98% similarity = duplicate
    
    try:
        frames, metadata = extractor.run(cleanup_first=True)
        
        print("\n" + "="*60)
        print(f"Extraction Summary:")
        print(f"Total frames extracted: {len(frames)}")
        print(f"Frames saved to: {OUTPUT_FOLDER}")
        print(f"Metadata saved to: {metadata}")
        print("="*60)
        
        # Print frame details
        print("\nExtracted frames:")
        for frame_info in frames:
            print(f"  - Frame {frame_info['frame_number']}: {frame_info['timestamp']:.2f}s - {frame_info['filename']}")
            
    except Exception as e:
        print(f"Failed to extract frames: {e}")


if __name__ == "__main__":
    main()
