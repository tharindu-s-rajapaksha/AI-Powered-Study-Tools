import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
import json
import winsound

# Load environment variables from .env file
load_dotenv()

class MarkdownTranslator:
    def __init__(self, api_key: str):
        """Initialize the translator with Google API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Configuration for text chunking
        self.chunk_size = 2000
        self.chunk_overlap = 200
        
        # Markdown separators for intelligent splitting
        self.markdown_separators = ["\n\n", "\n# ", "\n## ", "\n### ", "\n#### ", "\n- ", "\n* ", "\n1. ", "\n", " ", ""]
        
        # Translation prompt template
        self.prompt_template = """Translate the following Markdown chunk to Sinhala.
IMPORTANT:
- Keep ALL Markdown formatting (like #, *, -, etc.).
- Preserve ALL Markdown structure, formatting, and links.
- Keep special characters and punctuation unchanged.
- Maintain a good indentation and formatting. Correct if any mistakes in previous formatting.
- Maintain a story like, conversational tone in Sinhala.
- If lecturer has fogot to explain complex English words, keep those words in English but explain their meaning.
- Try to maintain the full note as a flow like a story for maintaining context and understanding.

TRANSLATION STYLE:
- සරලව කතා කරන විදිහට සිංහලෙන් කියන්න. ගොඩක් අමාරු වචන යොදන්න එපා. 
- දවසේ කතා කරද්දි යොදන සාමාන්‍ය වචන යොදන්න. 
- සිංහලෙන් කතා කරන විදිහට ලස්සනට පිලිවෙලට කියන්න. 
- සංකීර්ණ ඉංග්‍රීසි වචන තියෙනවා නම් ඒවා ඉංග්‍රීසිම ලියන්න, ඒත් ඒ වචන මොනවද කියලා සිංහලෙන් වරහන් ඇතුලෙ පැහැදිලි කරන්න.
- උදාහරණ : "Volatility: Rapid changes." :- "Volatility(විචල්‍යතාවය): ඉක්මන් වෙනස්කම්."

Markdown Chunk:
{markdown_chunk}
"""
    
    def split_text(self, text: str) -> list:
        """Split text into chunks using Markdown-aware splitting."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Try to split on Markdown separators first
        for separator in self.markdown_separators:
            if separator in text:
                parts = text.split(separator)
                for i, part in enumerate(parts):
                    if i > 0:
                        part = separator + part
                    
                    if len(current_chunk) + len(part) <= self.chunk_size:
                        current_chunk += part
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
                
                if current_chunk:
                    chunks.append(current_chunk)
                return chunks
        
        # Fallback to simple chunking if no separators found
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def translate_chunk(self, chunk: str) -> str:
        """Translate a single chunk of Markdown."""
        try:
            # Create the prompt for this chunk
            prompt = self.prompt_template.format(markdown_chunk=chunk)
            
            # Generate translation using Google Generative AI
            response = self.model.generate_content(prompt)
            translated_chunk = response.text
            time.sleep(1)  # Respect API rate limits
            
            return translated_chunk.strip()
            
        except Exception as e:
            print(f"Error translating chunk: {e}")
            
            # Error sound for chunk translation failure
            winsound.Beep(300, 500)
            
            return chunk  # Return original chunk if translation fails
    
    def translate_markdown(self, input_file: str, output_file: str):
        """Translate entire Markdown document to Sinhala."""
        try:
            # Read input Markdown
            with open(input_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Split content into chunks
            chunks = self.split_text(markdown_content)
            
            print(f"Split document into {len(chunks)} chunks")
            
            # Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks, 1):
                print(f"Translating chunk {i}/{len(chunks)}...")
                translated_chunk = self.translate_chunk(chunk)
                translated_chunks.append(translated_chunk)
                print(f"Chunk {i} translation completed")
            
            # Combine translated chunks
            translated_markdown = '\n'.join(translated_chunks)
            
            # Write translated content to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_markdown)
            
            print(f"Translation completed. Output saved to {output_file}")
            
            # Success melody
            for freq in [480, 600, 720, 600, 480, 360]:
                winsound.Beep(freq, 300)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Original error details:", str(e))
            
            # Error sound
            winsound.Beep(300, 1000)
            
            raise


# Example usage
if __name__ == "__main__":
    try:
        # Load inputs from JSON
        inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
        with open(inputs_path, "r") as f:
            inputs = json.load(f)
        
        # Get Google API key from environment variable
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
        
        # Initialize translator
        translator = MarkdownTranslator(GOOGLE_API_KEY)
        
        # Success beep for initialization
        winsound.Beep(600, 200)
        
        # Translate Markdown file
        translator.translate_markdown(
            input_file=inputs["translate_sinhala_md"]["input_file"],
            output_file=inputs["translate_sinhala_md"]["output_file"]
        )
    except Exception as e:
        print(f"Script execution failed: {e}")
        
        # Error sound for script failure
        winsound.Beep(300, 1000)