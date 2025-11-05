"""
PDF Multi-Page Splitter with Empty Page Detection

This tool splits PDF pages containing multiple slides arranged in a grid
and automatically removes empty or nearly-empty pages (95% blank).
"""

import fitz  # PyMuPDF
from pathlib import Path
import json
import os


class PDFPageSplitter:
    def __init__(self, input_pdf, rows, cols, output_dir=None, remove_empty=True, empty_threshold=0.95):
        """
        Initialize PDF splitter.
        
        Args:
            input_pdf: Path to input PDF file
            rows: Number of rows in grid
            cols: Number of columns in grid
            output_dir: Output directory (optional)
            remove_empty: Whether to remove empty pages (default: True)
            empty_threshold: Threshold for empty detection (0.95 = 95% blank)
        """
        self.input_pdf = input_pdf
        self.rows = rows
        self.cols = cols
        self.remove_empty = remove_empty
        self.empty_threshold = empty_threshold
        
        if output_dir is None:
            base_name = Path(input_pdf).stem
            parent_dir = Path(input_pdf).parent
            self.output_dir = parent_dir / f"{base_name}_split"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def is_page_empty(self, page):
        """
        Check if a page is empty or nearly empty.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            True if page is empty (above threshold), False otherwise
        """
        try:
            # Get page as pixmap (image)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # Lower resolution for speed
            
            # Get image data
            img_data = pix.samples
            
            # Calculate percentage of white/blank pixels
            # Assuming white pixels have high RGB values
            total_pixels = len(img_data) // pix.n
            
            # Count near-white pixels (RGB values > 240)
            white_count = 0
            for i in range(0, len(img_data), pix.n):
                # Check if pixel is mostly white
                if pix.n >= 3:  # RGB or RGBA
                    r, g, b = img_data[i], img_data[i+1], img_data[i+2]
                    if r > 240 and g > 240 and b > 240:
                        white_count += 1
            
            blank_percentage = white_count / total_pixels if total_pixels > 0 else 0
            
            return blank_percentage >= self.empty_threshold
            
        except Exception as e:
            print(f"    Warning: Could not check if page is empty: {e}")
            return False
    
    def split_pdf(self):
        """Split PDF and optionally remove empty pages."""
        doc = fitz.open(self.input_pdf)
        
        print(f"\n{'='*70}")
        print(f"PDF SPLITTER")
        print(f"{'='*70}")
        print(f"Input:  {Path(self.input_pdf).name}")
        print(f"Output: {self.output_dir}")
        print(f"Pages:  {len(doc)}")
        print(f"Grid:   {self.rows} rows × {self.cols} columns = {self.rows*self.cols} slides per page")
        if self.remove_empty:
            print(f"Empty page detection: Enabled (threshold: {self.empty_threshold*100:.0f}% blank)")
        print(f"{'-'*70}")
        
        output_pdf = fitz.open()
        total_created = 0
        empty_removed = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            rect = page.rect
            
            print(f"\nPage {page_num + 1}: {rect.width:.0f}×{rect.height:.0f}px", end="")
            
            # Calculate cell dimensions
            cell_width = rect.width / self.cols
            cell_height = rect.height / self.rows
            
            print(f" → Splitting into {self.rows*self.cols} cells ({cell_width:.0f}×{cell_height:.0f} each)")
            
            # Create individual pages for each cell
            for row in range(self.rows):
                for col in range(self.cols):
                    # Create new page
                    new_page = output_pdf.new_page(width=cell_width, height=cell_height)
                    
                    # Define the clip rectangle
                    x0 = col * cell_width
                    y0 = row * cell_height
                    x1 = x0 + cell_width
                    y1 = y0 + cell_height
                    clip = fitz.Rect(x0, y0, x1, y1)
                    
                    # Show the clipped area on the new page
                    new_page.show_pdf_page(
                        new_page.rect,
                        doc,
                        page_num,
                        clip=clip
                    )
                    
                    # Check if page is empty
                    if self.remove_empty and self.is_page_empty(new_page):
                        # Remove the empty page
                        output_pdf.delete_page(output_pdf.page_count - 1)
                        empty_removed += 1
                        print(f"    Cell [{row+1},{col+1}]: Empty - Removed")
                    else:
                        total_created += 1
        
        # Save output
        output_path = self.output_dir / f"{Path(self.input_pdf).stem}_split.pdf"
        output_pdf.save(output_path)
        output_pdf.close()
        doc.close()
        
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS!")
        print(f"{'='*70}")
        print(f"Created: {total_created} pages")
        if self.remove_empty:
            print(f"Removed: {empty_removed} empty pages")
        print(f"Saved to: {output_path}")
        print(f"{'='*70}\n")
        
        return output_path, total_created, empty_removed


def main():
    """Main function using inputs.json configuration."""
    try:
        # Load configuration from inputs.json
        inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
        
        if not os.path.exists(inputs_path):
            print("Error: inputs.json not found!")
            print(f"Expected location: {inputs_path}")
            return
        
        with open(inputs_path, "r") as f:
            inputs = json.load(f)
        
        # Get PDF splitter configuration
        if "pdf_splitter" not in inputs:
            print("Error: 'pdf_splitter' configuration not found in inputs.json")
            print("\nPlease add the following to inputs.json:")
            print("""
{
  "pdf_splitter": {
    "input_pdf": "path/to/your/document.pdf",
    "rows": 3,
    "cols": 2,
    "output_dir": null,
    "remove_empty": true,
    "empty_threshold": 0.95
  }
}
""")
            return
        
        config = inputs["pdf_splitter"]
        
        # Validate required fields
        if "input_pdf" not in config:
            print("Error: 'input_pdf' not specified in inputs.json")
            return
        
        if not os.path.exists(config["input_pdf"]):
            print(f"Error: Input PDF not found: {config['input_pdf']}")
            return
        
        # Get configuration with defaults
        input_pdf = config["input_pdf"]
        rows = config.get("rows", 2)
        cols = config.get("cols", 3)
        output_dir = config.get("output_dir", None)
        remove_empty = config.get("remove_empty", True)
        empty_threshold = config.get("empty_threshold", 0.95)
        
        # Create splitter and process
        splitter = PDFPageSplitter(
            input_pdf=input_pdf,
            rows=rows,
            cols=cols,
            output_dir=output_dir,
            remove_empty=remove_empty,
            empty_threshold=empty_threshold
        )
        
        splitter.split_pdf()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
