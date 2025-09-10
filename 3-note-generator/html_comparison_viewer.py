import os
from pathlib import Path
import json

class HTMLComparisonViewer:
    def __init__(self):
        """Initialize the HTML comparison viewer."""
        pass
    
    def create_comparison_html(self, original_file: str, translated_file: str, output_file: str):
        """Create a side-by-side comparison HTML file."""
        try:
            # Read original HTML file
            with open(original_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Read translated HTML file
            with open(translated_file, 'r', encoding='utf-8') as f:
                translated_content = f.read()
            
            # Extract body content from both files
            original_body = self.extract_body_content(original_content)
            translated_body = self.extract_body_content(translated_content)
            
            # Create the comparison HTML
            comparison_html = self.generate_comparison_template(
                original_body, 
                translated_body,
                Path(original_file).name,
                Path(translated_file).name
            )
            
            # Write the comparison HTML to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(comparison_html)
            
            print(f"Comparison HTML created successfully: {output_file}")
            
        except Exception as e:
            print(f"Error creating comparison HTML: {e}")
            raise
    
    def extract_body_content(self, html_content: str) -> str:
        """Extract content between <body> tags, or return full content if no body tags."""
        try:
            # Find body content
            body_start = html_content.find('<body')
            if body_start != -1:
                body_start = html_content.find('>', body_start) + 1
                body_end = html_content.rfind('</body>')
                if body_end != -1:
                    return html_content[body_start:body_end].strip()
            
            # If no body tags found, return content without head section
            head_end = html_content.find('</head>')
            if head_end != -1:
                return html_content[head_end + 7:].strip()
            
            # Return full content if no structure found
            return html_content.strip()
            
        except Exception:
            return html_content.strip()
    
    def generate_comparison_template(self, original_content: str, translated_content: str, 
                                   original_filename: str, translated_filename: str) -> str:
        """Generate the HTML template for side-by-side comparison."""
        
        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Comparison Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            height: 100vh;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            position: relative;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 300;
        }}
        
        .controls {{
            margin-top: 10px;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .btn {{
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }}
        
        .container {{
            min-height: calc(100vh - 120px);
            background: white;
            position: relative;
        }}
        
        .pane {{
            width: 50%;
            min-height: calc(100vh - 120px);
            float: left;
            position: relative;
            border-right: 2px solid #e0e0e0;
            box-sizing: border-box;
        }}
        
        .pane:last-child {{
            border-right: none;
        }}
        
        .pane-header {{
            background: linear-gradient(to right, #f8f9fa, #e9ecef);
            padding: 12px 20px;
            border-bottom: 1px solid #dee2e6;
            font-weight: 600;
            color: #495057;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 50px;
            box-sizing: border-box;
        }}
        
        .filename {{
            font-family: 'Courier New', monospace;
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        .content {{
            max-height: calc(100vh - 170px);
            overflow-y: auto;
            padding: 20px;
            background: white;
            position: relative;
            box-sizing: border-box;
        }}
        
        .content::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .content::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        .content::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 4px;
        }}
        
        .content::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        
        /* Synchronize scrolling */
        .sync-scroll {{
            scroll-behavior: smooth;
        }}
        
        /* Clear float */
        .container:after {{
            content: "";
            display: table;
            clear: both;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .pane {{
                width: 100%;
                float: none;
                border-right: none;
                border-bottom: 2px solid #e0e0e0;
                height: 50%;
            }}
            
            .pane:last-child {{
                border-bottom: none;
            }}
            
            .controls {{
                flex-wrap: wrap;
            }}
        }}
        
        /* Content styling */
        .content h1, .content h2, .content h3, .content h4, .content h5, .content h6 {{
            margin-top: 20px;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .content p {{
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        
        .content ul, .content ol {{
            margin: 15px 0;
            padding-left: 20px;
        }}
        
        .content li {{
            margin-bottom: 5px;
        }}
        
        .loading {{
            display: none;
            text-align: center;
            padding: 50px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 HTML Comparison Viewer</h1>
        <div class="controls">
            <button class="btn" onclick="syncScroll()">🔄 Sync Scroll</button>
            <button class="btn" onclick="resetView()">↺ Reset View</button>
            <button class="btn" onclick="toggleFullscreen()">⛶ Toggle Fullscreen</button>
        </div>
    </div>
    
    <div class="container">
        <div class="pane">
            <div class="pane-header">
                <span>📄 Original Document</span>
                <span class="filename">{original_filename}</span>
            </div>
            <div class="content sync-scroll" id="original-content">
                {original_content}
            </div>
        </div>
        
        <div class="pane">
            <div class="pane-header">
                <span>🌐 Translated Document (සිංහල)</span>
                <span class="filename">{translated_filename}</span>
            </div>
            <div class="content sync-scroll" id="translated-content">
                {translated_content}
            </div>
        </div>
    </div>
    
    <script>
        let syncScrollEnabled = true;
        
        // Sync scroll functionality
        function syncScroll() {{
            syncScrollEnabled = !syncScrollEnabled;
            const btn = event.target;
            if (syncScrollEnabled) {{
                btn.textContent = '🔄 Sync Scroll';
                btn.style.background = 'rgba(255,255,255,0.2)';
            }} else {{
                btn.textContent = '⏸️ Sync Off';
                btn.style.background = 'rgba(255,100,100,0.3)';
            }}
        }}
        
        // Add scroll event listeners
        const originalContent = document.getElementById('original-content');
        const translatedContent = document.getElementById('translated-content');
        
        originalContent.addEventListener('scroll', function() {{
            if (syncScrollEnabled) {{
                const scrollPercentage = this.scrollTop / (this.scrollHeight - this.clientHeight);
                const targetScrollTop = scrollPercentage * (translatedContent.scrollHeight - translatedContent.clientHeight);
                translatedContent.scrollTop = targetScrollTop;
            }}
        }});
        
        translatedContent.addEventListener('scroll', function() {{
            if (syncScrollEnabled) {{
                const scrollPercentage = this.scrollTop / (this.scrollHeight - this.clientHeight);
                const targetScrollTop = scrollPercentage * (originalContent.scrollHeight - originalContent.clientHeight);
                originalContent.scrollTop = targetScrollTop;
            }}
        }});
        
        // Reset view
        function resetView() {{
            originalContent.scrollTop = 0;
            translatedContent.scrollTop = 0;
        }}
        
        // Toggle fullscreen
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.ctrlKey && e.key === 's') {{
                e.preventDefault();
                syncScroll();
            }}
            if (e.ctrlKey && e.key === 'r') {{
                e.preventDefault();
                resetView();
            }}
            if (e.key === 'F11') {{
                e.preventDefault();
                toggleFullscreen();
            }}
        }});
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('HTML Comparison Viewer loaded successfully');
        }});
    </script>
</body>
</html>"""
        
        return template


# Example usage
if __name__ == "__main__":
    # Load inputs from JSON
    inputs_path = os.path.join(os.path.dirname(__file__), "..", "inputs.json")
    with open(inputs_path, "r") as f:
        inputs = json.load(f)
    
    # Initialize the comparison viewer
    viewer = HTMLComparisonViewer()
    
    # Get file paths from inputs
    original_file = inputs["html_comparison_viewer"]["original_file"]
    translated_file = inputs["html_comparison_viewer"]["translated_file"]
    output_file = inputs["html_comparison_viewer"]["output_file"]
    
    # Check if files exist
    if os.path.exists(original_file) and os.path.exists(translated_file):
        viewer.create_comparison_html(original_file, translated_file, output_file)
        print(f"\n✅ Comparison view created successfully!")
        print(f"📂 Output file: {output_file}")
        print(f"🌐 Open in browser to view the side-by-side comparison")
    else:
        print("❌ Error: One or both input files not found.")
        print(f"Original file exists: {os.path.exists(original_file)}")
        print(f"Translated file exists: {os.path.exists(translated_file)}")
        
        # Use local example files for demonstration
        print("\n📝 Using example with local files...")
        local_original = "output.html"  # Assuming this exists in the Note Generator folder
        local_translated = "translated_sinhala.html"  # This would be created by your translator
        local_output = "comparison_view.html"
        
        if os.path.exists(local_original):
            print(f"✅ Found local original file: {local_original}")
            if not os.path.exists(local_translated):
                print(f"⚠️  Creating dummy translated file for demonstration...")
                # Create a dummy translated file for testing
                with open(local_original, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(local_translated, 'w', encoding='utf-8') as f:
                    f.write(content.replace('English', 'සිංහල'))
            
            viewer.create_comparison_html(local_original, local_translated, local_output)
