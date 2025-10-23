import os
import re
import time
import pathlib
import markdown
import json
import platform
from datetime import datetime
from google import genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter

# Load environment variables from .env file
load_dotenv()

# Gemini LLM model name
LLM_MODEL = "models/gemini-2.5-flash"

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
            "start": (800, 100),
            "step": (600, 80),
            "complete": (1000, 150),
            "error": (400, 200)
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

class SimplePDFNotesGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Configure the client
        self.client = genai.Client(api_key=api_key)
        
        # Initialize sound player
        self.sound_player = SoundPlayer()
        
    def print_progress(self, message: str, sound_type: str = None):
        """Print a progress message with timestamp and optional sound."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
        if sound_type:
            self.sound_player.play_sound(sound_type)
        
    def create_output_folder(self, pdf_path: str, start_page: int, end_page: int):
        """Create output folder based on page range."""
        pdf_dir = os.path.dirname(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        folder_name = f"{base_name}_pages_{start_page}-{end_page}"
        output_folder = os.path.join(pdf_dir, folder_name)
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            self.print_progress(f"Created output folder: {output_folder}", "step")
        else:
            self.print_progress(f"Using existing folder: {output_folder}", "step")
            
        return output_folder
    
    def extract_pdf_pages(self, pdf_path: str, start_page: int, end_page: int, output_folder: str):
        """Extract specified pages from PDF and save to output folder."""
        try:
            # Adjust page numbers (subtract 1 for before, add 1 for after)
            # extract_start = max(1, start_page - 1)
            extract_start = start_page
            extract_end = end_page # end_page + 1
            
            self.print_progress(f"Extracting pages {extract_start}-{extract_end} from PDF")
            
            # Read the original PDF
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            # Adjust end page if it exceeds total pages
            extract_end = min(extract_end, total_pages)
            
            writer = PdfWriter()
            
            # Add pages to writer (PyPDF2 uses 0-based indexing)
            for page_num in range(extract_start - 1, extract_end):
                if page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
            
            # Save extracted PDF
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            extracted_pdf_name = f"{base_name}_pages_{extract_start}-{extract_end}.pdf"
            extracted_pdf_path = os.path.join(output_folder, extracted_pdf_name)
            
            with open(extracted_pdf_path, 'wb') as output_file:
                writer.write(output_file)
            
            self.print_progress(f"Extracted PDF saved to: {extracted_pdf_path}", "step")
            return extracted_pdf_path
            
        except Exception as e:
            self.print_progress(f"Error extracting PDF pages: {e}", "error")
            raise

            
    def upload_pdf_to_gemini(self, pdf_path):
        """Upload PDF to Gemini and return file object."""
        try:
            self.print_progress(f"Uploading PDF file: {os.path.basename(pdf_path)}")
            
            # Convert path to pathlib.Path and upload the PDF file
            file_path = pathlib.Path(pdf_path)
            pdf_file = self.client.files.upload(file=file_path)
            self.print_progress(f"PDF uploaded successfully", "step")
                
            self.print_progress("PDF processed successfully and ready for analysis")
            return pdf_file
            
        except Exception as e:
            self.print_progress(f"Error uploading PDF: {e}", "error")
            raise
            
    def generate_notes_from_pdf(self, pdf_file, start_page, end_page, summary: str = ""):
        """Generate notes from the uploaded PDF."""
        try:
            # Create the prompt for note generation with summary context
            prompt = f"""
CONTEXT - Full Lecture Note Summary:
{summary}

---

TASK:
This is a part of my note (PDF). 
I will provide the full note part by part. 
I need you to explain it simply in සිංහල language (Like explaining to a friend). 
First I will give you {end_page-start_page+1} pages part. 
(Sometimes the 2 pages may include many lecture slides. If so, organize them in a proper flow.)
You need to explain them with all the exact details in sinhala.
(I have to actually learn in english. so add important points in sinhala and english both.) 

Use the summary above to understand how this section fits into the overall lecture content.
Use Markdown formatting."""

            self.print_progress(f"Generating notes for pages {start_page}-{end_page}")
            
            response = self.client.models.generate_content(
                model=LLM_MODEL,
                contents=[pdf_file, prompt]
            )
            
            self.print_progress("Notes generated successfully", "step")
            return response.text
            
        except Exception as e:
            self.print_progress(f"Error generating notes: {e}", "error")
            return f"Error generating notes: {str(e)}"
            
    def save_notes(self, notes: str, pdf_path: str, start_page: int, end_page: int, output_folder: str):
        """Save the generated notes to a markdown file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"{base_name}_pages_{start_page}-{end_page}_notes.md"
        
        # Save in the output folder
        output_path = os.path.join(output_folder, output_file)
        
        self.print_progress(f"Saving notes to {output_path}")
        
        try:
            with open(output_path, "w", encoding='utf-8') as file:
                file.write(f"# {base_name} - Pages {start_page}-{end_page}\n\n")
                file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                file.write("---\n\n")
                file.write(notes)
                
            self.print_progress("Notes saved successfully", "step")
            return output_path
        except Exception as e:
            self.print_progress(f"Error saving notes: {e}", "error")
            raise
            
    def convert_to_html(self, notes_file: str):
        """Convert the markdown notes to styled HTML."""
        self.print_progress("Converting notes to HTML...")
        
        try:
            with open(notes_file, "r", encoding='utf-8') as file:
                notes_text = file.read()
            
            # Clean up the markdown formatting
            notes_text = re.sub(r'(:\n\*)', ':\n\n*', notes_text)
            notes_text = re.sub(r'(.\n\*)', '.\n\n*', notes_text)
            notes_text = re.sub(r'---\n\n.*\n\n---', '---', notes_text)
            
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
            
            # Save HTML in the same folder as the markdown file
            output_html = notes_file.replace('.md', '.html')
            with open(output_html, "w", encoding='utf-8') as file:
                file.write(styled_html)
                
            self.print_progress(f"HTML notes saved to {output_html}", "step")
            return output_html
            
        except Exception as e:
            self.print_progress(f"Error creating HTML: {e}", "error")
            return None
            
    def get_or_create_summary(self, pdf_path: str):
        """Get existing summary or create a new one for the full PDF."""
        pdf_dir = os.path.dirname(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        summary_file = os.path.join(pdf_dir, f"{base_name}_summary.txt")
        
        # Check if summary already exists
        if os.path.exists(summary_file):
            self.print_progress(f"Found existing summary: {summary_file}", "step")
            with open(summary_file, "r", encoding='utf-8') as f:
                return f.read()
        
        # Create new summary
        self.print_progress("No existing summary found. Generating summary of full PDF...", "step")
        
        pdf_file = None
        try:
            # Upload the full PDF
            pdf_file = self.upload_pdf_to_gemini(pdf_path)
            
            # Generate summary
            summary_prompt = """
Please provide a comprehensive summary of this entire PDF lecture note.
Include:
1. Main topics and concepts covered
2. Key themes and their relationships
3. Overall structure and flow of the content

Keep the summary detailed enough to give context for explaining specific sections later.
Write the summary in English."""

            self.print_progress("Generating full PDF summary...")
            
            response = self.client.models.generate_content(
                model=LLM_MODEL,
                contents=[pdf_file, summary_prompt]
            )
            
            summary = response.text
            
            # Save summary
            with open(summary_file, "w", encoding='utf-8') as f:
                f.write(f"Summary of {base_name}\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("="*80 + "\n\n")
                f.write(summary)
            
            self.print_progress(f"Summary saved to: {summary_file}", "step")
            return summary
            
        except Exception as e:
            self.print_progress(f"Error generating summary: {e}", "error")
            return ""
            
        finally:
            if pdf_file:
                self.cleanup_uploaded_file(pdf_file)
    
    def cleanup_uploaded_file(self, pdf_file):
        """Clean up the uploaded file from Gemini."""
        try:
            self.client.files.delete(name=pdf_file.name)
            self.print_progress("Cleaned up uploaded PDF file")
        except Exception as e:
            self.print_progress(f"Could not cleanup uploaded file: {e}")
            
    def generate_notes(self, pdf_path: str, start_page: int, end_page: int):
        """Main method to generate notes from PDF."""
        self.print_progress("Starting PDF note generation process...", "start")
        start_time = time.time()
        
        pdf_file = None
        try:
            # Check if PDF file exists
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Get or create summary of the full PDF
            summary = self.get_or_create_summary(pdf_path)
            
            # Create output folder
            output_folder = self.create_output_folder(pdf_path, start_page, end_page)
            
            # Extract pages from PDF
            extracted_pdf_path = self.extract_pdf_pages(pdf_path, start_page, end_page, output_folder)
            
            # Upload extracted PDF to Gemini
            pdf_file = self.upload_pdf_to_gemini(extracted_pdf_path)
            
            # Generate notes with summary context
            notes = self.generate_notes_from_pdf(pdf_file, start_page, end_page, summary)
            
            # Save notes
            notes_file = self.save_notes(notes, pdf_path, start_page, end_page, output_folder)
            
            # Convert to HTML
            html_file = self.convert_to_html(notes_file)
            
            end_time = time.time()
            self.print_progress(f"Process completed successfully in {(end_time - start_time) / 60:.1f} minutes!", "complete")
            self.print_progress(f"Notes saved to: {notes_file}")
            if html_file:
                self.print_progress(f"HTML version saved to: {html_file}")
            
            return html_file if html_file else notes_file
            
        except Exception as e:
            self.print_progress(f"Process failed: {e}", "error")
            return None
            
        finally:
            # Cleanup uploaded file
            if pdf_file:
                self.cleanup_uploaded_file(pdf_file)


def main():
    """Main function to run the PDF note generator."""
    # Configuration
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
    
    # Load inputs from JSON
    inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    pdf_config = inputs["pdf_note_generator"]
    PDF_FILE = pdf_config["pdf_file"]
    START_PAGE = pdf_config["start_page"]
    END_PAGE = pdf_config["end_page"]
    
    print("=== PDF Notes Generator ===")
    print("This tool generates detailed study notes in Sinhala from PDF files.")
    print(f"Processing: {PDF_FILE}")
    print(f"Pages: {START_PAGE}-{END_PAGE}")
    print()
    
    # Create generator and process PDF
    generator = SimplePDFNotesGenerator(api_key=API_KEY)
    result = generator.generate_notes(PDF_FILE, START_PAGE, END_PAGE)
    
    if result:
        print(f"\n✅ Success! Notes have been generated and saved.")
        print(f"📁 File location: {result}")
    else:
        print("\n❌ Failed to generate notes. Check the error messages above.")


if __name__ == "__main__":
    main()