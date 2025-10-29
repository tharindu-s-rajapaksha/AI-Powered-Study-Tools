import os
import re
import time
import random
import winsound
import markdown
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

class SimpleNoteGenerator:
    def __init__(self, api_key: str, text_file: str):
        self.text_file = text_file
        self.api_key = api_key
        self.model = None
        self.chunk_size = 8000  # Characters per chunk
        self.overlap = 500      # Overlap between chunks
        
        # Configure the API
        genai.configure(api_key=api_key)
        
    def print_progress(self, message: str):
        """Print a progress message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def setup_model(self):
        """Initialize the Gemini model."""
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.print_progress("Initialized Gemini 2.5 Flash model")
        except Exception as e:
            self.print_progress(f"Error setting up model: {e}")
            raise
            
    def read_transcript(self):
        """Read the lecture transcript file."""
        self.print_progress("Reading transcript file...")
        try:
            with open(self.text_file, "r", encoding='utf-8') as file:
                transcript_text = file.read()
            self.print_progress(f"Successfully read file ({len(transcript_text)} characters)")
            return transcript_text
        except FileNotFoundError:
            self.print_progress(f"Error: Could not find the file {self.text_file}")
            raise
        except Exception as e:
            self.print_progress(f"Error reading file: {e}")
            raise
            
    def split_text(self, text: str):
        """Split text into manageable chunks."""
        self.print_progress(f"Splitting text into chunks (size: {self.chunk_size}, overlap: {self.overlap})")
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a sentence or paragraph
            if end < len(text):
                # Look for good breaking points within the last 200 characters
                break_chars = ['\n\n', '\n', '. ', '! ', '? ']
                best_break = end
                
                for break_char in break_chars:
                    last_break = text.rfind(break_char, start + self.chunk_size - 200, end)
                    if last_break > start:
                        best_break = last_break + len(break_char)
                        break
                
                end = best_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap
            
        self.print_progress(f"Created {len(chunks)} chunks")
        return chunks
        
    def generate_chunk_summary(self, chunk: str, chunk_index: int, total_chunks: int):
        """Generate summary for a single chunk."""
        prompt = f"""Create comprehensive and detailed notes from this lecture transcription segment (Part {chunk_index + 1} of {total_chunks}):

{chunk}

CRITICAL Instructions:
1. Maintain the EXACT ORDER of topics as they appear in the transcription - do not rearrange or reorder
2. Extract and include ALL concepts, definitions, explanations, and examples mentioned
3. Preserve the original logical flow and sequence of the lecture content
4. Include every specific detail, example, and explanation from the transcription
5. Use clear, organized formatting with bullet points and sections
6. Do NOT skip, omit, or summarize any content - preserve everything
7. Highlight key points that would be important for exams
8. Keep the same teaching progression and order as the original lecture

DETAILED NOTES (maintaining exact order):"""

        try:
            self.print_progress(f"Processing chunk {chunk_index + 1}/{total_chunks}")
            
            # Add rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.print_progress(f"Error processing chunk {chunk_index + 1}: {e}")
            # Wait a bit longer and retry once
            time.sleep(5)
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e2:
                self.print_progress(f"Retry failed for chunk {chunk_index + 1}: {e2}")
                return f"[Error processing this section: {str(e2)}]"
                
    def combine_summaries(self, chunk_summaries: list):
        """Combine individual chunk summaries into a final comprehensive note."""
        combined_text = "\n\n".join(chunk_summaries)
        
        prompt = f"""Using the following detailed notes from different parts of a lecture, create a final, well-organized comprehensive study note:

{combined_text}

CRITICAL Instructions:
1. Preserve the EXACT ORDER of all topics and concepts as they appear in the notes above
2. Do NOT rearrange, reorganize, or change the sequence of topics
3. Include ALL content from every section - nothing should be omitted
4. Remove redundancy ONLY if the exact same information is repeated, but keep the order
5. Create clear sections and subsections with appropriate headings while maintaining sequence
6. Ensure smooth transitions between topics without changing their order
7. Highlight the most important concepts for exam preparation
8. Maintain all specific examples, definitions, and detailed explanations in their original positions
9. Use markdown formatting for better readability
10. The final note must follow the same teaching progression as the original lecture

Create a complete, exam-ready study note that maintains the exact order and includes all content:"""

        try:
            self.print_progress("Combining and organizing all sections...")
            time.sleep(2)  # Rate limiting
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.print_progress(f"Error combining summaries: {e}")
            # Return the concatenated version if combination fails
            return combined_text
            
    def process_transcript(self):
        """Main processing method."""
        try:
            # Read the transcript
            transcript_text = self.read_transcript()
            
            # Setup the model
            self.setup_model()
            
            # If text is short enough, process directly
            if len(transcript_text) <= self.chunk_size:
                self.print_progress("Text is short enough to process in one go")
                prompt = f"""Create comprehensive and detailed study notes from this lecture transcription:

{transcript_text}

CRITICAL Instructions:
1. Maintain the EXACT ORDER of topics as they appear in the transcription - do not rearrange
2. Extract and include ALL concepts, definitions, explanations, and examples mentioned
3. Preserve the original sequence and flow of the lecture content
4. Include every specific detail and explanation from the transcription
5. Organize content with clear headings and structure while maintaining the original order
6. Highlight key points important for exams
7. Use markdown formatting for better readability
8. Do NOT skip, omit, or reorder any content - preserve everything in sequence
9. The note must follow the same teaching progression as the original lecture

COMPREHENSIVE STUDY NOTES (maintaining exact order and all content):"""

                response = self.model.generate_content(prompt)
                return response.text
            
            # For longer texts, process in chunks
            else:
                chunks = self.split_text(transcript_text)
                chunk_summaries = []
                
                for i, chunk in enumerate(chunks):
                    summary = self.generate_chunk_summary(chunk, i, len(chunks))
                    chunk_summaries.append(summary)
                
                # Combine all summaries
                final_summary = self.combine_summaries(chunk_summaries)
                return final_summary
                
        except Exception as e:
            self.print_progress(f"Error during processing: {e}")
            return f"Error generating notes: {str(e)}"
            
    def save_notes(self, notes: str):
        """Save the generated notes to a text file."""
        output_file = f"{self.text_file}_notes.txt"
        self.print_progress(f"Saving notes to {output_file}")
        
        try:
            with open(output_file, "w", encoding='utf-8') as file:
                file.write(notes)
            self.print_progress("Notes saved successfully")
            return output_file
        except Exception as e:
            self.print_progress(f"Error saving notes: {e}")
            raise
            
    def convert_to_html(self, notes_file: str):
        """Convert the markdown notes to styled HTML."""
        self.print_progress("Converting notes to HTML...")
        
        try:
            with open(notes_file, "r", encoding='utf-8') as file:
                notes_text = file.read()
            
            # Clean up the markdown formatting
            notes_text = re.sub(r'(\*\*.*\*\*)\n', r'\1\n\n', notes_text)
            
            # Convert to HTML
            html_content = markdown.markdown(notes_text)
            
            # Add styling
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Study Notes</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        ul, ol {{
            margin-bottom: 15px;
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        code {{
            background-color: #f1f2f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #ecf0f1;
            font-style: italic;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 40px;
            border-top: 1px solid #bdc3c7;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <div class="timestamp">
            Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""
            
            output_html = notes_file.replace('.txt', '.html')
            with open(output_html, "w", encoding='utf-8') as file:
                file.write(styled_html)
                
            self.print_progress(f"HTML notes saved to {output_html}")
            return output_html
            
        except Exception as e:
            self.print_progress(f"Error creating HTML: {e}")
            return None
            
    def cleanup_text_file(self, text_file: str):
        """Delete the text notes file, keeping only HTML."""
        try:
            os.remove(text_file)
            self.print_progress("Cleaned up text file - keeping only HTML version")
        except Exception as e:
            self.print_progress(f"Could not delete text file: {e}")
            
    def run(self):
        """Main execution method."""
        self.print_progress("Starting note generation process...")
        start_time = time.time()
        
        try:
            # Generate notes
            notes = self.process_transcript()
            
            # Save notes
            notes_file = self.save_notes(notes)
            
            # Convert to HTML
            html_file = self.convert_to_html(notes_file)
            
            # Cleanup text file (optional - comment out if you want to keep both)
            # self.cleanup_text_file(notes_file)
            
            end_time = time.time()
            self.print_progress(f"Process completed successfully in {(end_time - start_time) / 60:.1f} minutes!")
            
            if html_file:
                self.print_progress(f"Final notes available at: {html_file}")
            
            return html_file
            
        except Exception as e:
            self.print_progress(f"Process failed: {e}")
            return None


def main():
    """Main function to run the note generator."""
    # Configuration
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
    
    # Load inputs from JSON
    inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    TEXT_FILE = inputs["note_generator"]["text_file"]
    
    # Sound notification - start
    try:
        winsound.Beep(480, 500)
    except:
        pass
    
    # Create and run the generator
    generator = SimpleNoteGenerator(api_key=API_KEY, text_file=TEXT_FILE)
    result = generator.run()
    
    # Sound notification - completion
    try:
        if result:
            # Success melody
            for freq in [480, 600, 720, 600, 480, 360]:
                winsound.Beep(freq, 300)
        else:
            # Error sound
            winsound.Beep(300, 1000)
    except:
        pass


if __name__ == "__main__":
    main()
