import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
import json
import winsound

# Load environment variables from .env file
load_dotenv()

class HTMLTranslator:
    def __init__(self, api_key: str):
        """Initialize the translator with Google API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Configuration for text chunking
        self.chunk_size = 2000
        self.chunk_overlap = 200
        
        # HTML separators for intelligent splitting
        self.html_separators = ["\n</body>", "\n</div>", "\n</section>", "\n</article>", 
                               "\n</h1>", "\n</h2>", "\n</h3>", "\n</h4>", "\n</h5>", "\n</h6>",
                               "\n</p>", "\n</ul>", "\n</ol>", "\n</li>", "\n", " ", ""]
        
        # Translation prompt template
        self.prompt_template = """Translate the following HTML chunk to Sinhala.
IMPORTANT:
- Keep ALL HTML tags exactly as they are
- Only translate the text content between tags
- Preserve ALL HTML structure, formatting, and attributes
- Keep special characters and punctuation unchanged
- Maintain exact HTML indentation and formatting

TRANSLATION STYLE:
- සරලව කතා කරන විදිහට සිංහලෙන් කියන්න. ගොඩක් අමාරු වචන යොදන්න එපා. 
- දවසේ කතා කරද්දි යොදන සාමාන්‍ය වචන යොදන්න. 
- සිංහලෙන් කතා කරන විදිහට ලස්සනට පිලිවෙලට කියන්න. 
- සංකීර්ණ ඉංග්‍රීසි වචන තියෙනවා නම් ඒවා ඉංග්‍රීසිම ලියන්න, ඒත් ඒ වචන මොනවද කියලා සිංහලෙන් වරහන් ඇතුලෙ පැහැදිලි කරන්න.
- උදාහරණ : "Volatility: Rapid changes." :- "Volatility(විචල්‍යතාවය): ඉක්මන් වෙනස්කම්."

HTML Chunk:
{html_chunk}

Translate the above HTML chunk to simple, conversational Sinhala while keeping ALL HTML tags and structure intact."""
    
    def split_text(self, text: str) -> list:
        """Split text into chunks using HTML-aware splitting."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Try to split on HTML separators first
        for separator in self.html_separators:
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
        """Translate a single chunk of HTML."""
        try:
            # Create the prompt for this chunk
            prompt = self.prompt_template.format(html_chunk=chunk)
            
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
    
    def translate_html(self, input_file: str, output_file: str):
        """Translate entire HTML document to Sinhala."""
        try:
            # Read input HTML
            with open(input_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Split into head and body sections
            if '</head>' in html_content:
                head_end = html_content.index('</head>') + 7
                head_section = html_content[:head_end]
                body_section = html_content[head_end:]
            else:
                head_section = '<head><meta charset="UTF-8"></head>'
                body_section = html_content
            
            # Split body content into chunks
            chunks = self.split_text(body_section)
            
            print(f"Split document into {len(chunks)} chunks")
            
            # Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks, 1):
                print(f"Translating chunk {i}/{len(chunks)}...")
                translated_chunk = self.translate_chunk(chunk)
                translated_chunks.append(translated_chunk)
                print(f"Chunk {i} translation completed")
            
            # Combine translated chunks
            translated_body = ''.join(translated_chunks)
            
            # Update head section with language tag and charset
            if '<html lang=' in head_section:
                head_section = head_section.replace('<html lang="en">', '<html lang="si">')
            else:
                head_section = head_section.replace('<html>', '<html lang="si">')
                
            if '<meta charset=' not in head_section:
                head_section = head_section.replace('</head>', '\n    <meta charset="UTF-8">\n</head>')
            
            # Combine final document
            translated_html = head_section + translated_body
            
            # Write translated content to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_html)
            
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
        translator = HTMLTranslator(GOOGLE_API_KEY)
        
        # Success beep for initialization
        winsound.Beep(600, 200)
        
        # Translate HTML file
        translator.translate_html(
            input_file=inputs["translate_sinhala_html"]["input_file"],
            output_file=inputs["translate_sinhala_html"]["output_file"]
        )
    except Exception as e:
        print(f"Script execution failed: {e}")
        
        # Error sound for script failure
        winsound.Beep(300, 1000)