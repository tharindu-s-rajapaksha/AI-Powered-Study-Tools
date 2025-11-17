"""
Batch Runner for AI-Powered Study Tools
Allows you to run any tool multiple times with different input configurations.
"""

import json
import subprocess
import sys
from pathlib import Path


# Tool configurations - maps tool names to their scripts
TOOL_CONFIGS = {
    "pdf_note_generator": {
        "script": "3-note-generator/pdf_notes_generator.py",
        "name": "PDF Notes Generator",
        "config_key": "pdf_note_generator"
    },
    "video_transcriber": {
        "script": "1-video-transcriber/transcribe_video.py",
        "name": "Video Transcriber",
        "config_key": "video_transcriber"
    },
    "note_generator": {
        "script": "3-note-generator/generate_notes.py",
        "name": "Note Generator",
        "config_key": "note_generator"
    },
    "note_generator_sinhala": {
        "script": "3-note-generator/generate_notes_sinhala.py",
        "name": "Sinhala Note Generator",
        "config_key": "note_generator"
    },
    "translate_sinhala_html": {
        "script": "3-note-generator/translate_sinhala_html.py",
        "name": "Translate Sinhala HTML",
        "config_key": "translate_sinhala_html"
    },
    "translate_sinhala_md": {
        "script": "3-note-generator/translate_sinhala_md.py",
        "name": "Translate Sinhala Markdown",
        "config_key": "translate_sinhala_md"
    },
    "pdf_splitter": {
        "script": "5-pdf-page-splitter/split_pdf.py",
        "name": "PDF Page Splitter",
        "config_key": "pdf_splitter"
    },
    "video_silence_remover": {
        "script": "4-video-silence-remover/remove_silence.py",
        "name": "Video Silence Remover",
        "config_key": "video_silence_remover"
    }
}


def load_inputs():
    """Load the inputs.json file."""
    inputs_path = Path(__file__).parent / "inputs.json"
    with open(inputs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_inputs(data):
    """Save the updated inputs.json file."""
    inputs_path = Path(__file__).parent / "inputs.json"
    with open(inputs_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def run_tool(tool_key):
    """Run the specified tool script."""
    tool_config = TOOL_CONFIGS[tool_key]
    script_path = Path(__file__).parent / tool_config["script"]
    
    print("\n" + "="*70)
    print(f"RUNNING {tool_config['name'].upper()}")
    print("="*70 + "\n")
    
    # Run the script and capture output in real-time
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        capture_output=False  # Show output in real-time
    )
    
    return result.returncode == 0


def update_config_with_values(config, updates):
    """Update configuration dictionary with new values."""
    updated_config = config.copy()
    for key, value in updates.items():
        updated_config[key] = value
    return updated_config


def main():
    """Main function to batch process tasks."""
    
    # =========================================================================
    # CONFIGURATION - Edit this section to customize your batch processing
    # =========================================================================
    
    # Select which tool to run (use the key from TOOL_CONFIGS)
    tool_key = "note_generator_sinhala"  # Change this to run different tools
    
    # Define your batch configurations here
    # For PDF Note Generator - specify page ranges:
    # batch_configs = [{
    #     "start_page": start,
    #     "end_page": end
    # } for start, end in [
    #     (196, 200),
    #     (206, 210),
    #     (216, 220),
    # ]]
    
    # For other tools, specify field values for each batch:
    # Example for video transcriber:
    batch_configs = [
        {"text_file": "D:/Desktop/UNI/~ACA - L3S2/CM3620 - Natural Language Processing/Lecture Recordings/2025-10-08 Lec_10_silence_removed_transcription.txt"},
        {"text_file": "D:/Desktop/UNI/~ACA - L3S2/CM3620 - Natural Language Processing/Lecture Recordings/2025-10-15 Lec_12_silence_removed_transcription.txt"}
    ]
    
    # Example for pdf_splitter:
    # batch_configs = [
    #     {"input_pdf": "path1.pdf", "rows": 2, "cols": 1},
    #     {"input_pdf": "path2.pdf", "rows": 2, "cols": 1},
    #     {"input_pdf": "path3.pdf", "rows": 3, "cols": 1}
    # ]
    
    # =========================================================================
    # END CONFIGURATION
    # =========================================================================
    
    print("\n" + "="*70)
    print("BATCH RUNNER - AI-POWERED STUDY TOOLS")
    print("="*70)
    
    tool_config = TOOL_CONFIGS[tool_key]
    config_key = tool_config["config_key"]
    
    # Load current configuration
    inputs = load_inputs()
    
    if config_key not in inputs:
        print(f"\nError: '{config_key}' not found in inputs.json")
        return
    
    original_config = inputs[config_key].copy()
    
    print(f"\nTool: {tool_config['name']}")
    print("-" * 70)
    print("\nOriginal configuration:")
    for key, value in original_config.items():
        print(f"  {key}: {value}")
    
    # Show summary
    print("\n" + "="*70)
    print(f"BATCH SUMMARY - {len(batch_configs)} batches")
    print("="*70)
    for i, batch in enumerate(batch_configs, 1):
        print(f"\nBatch {i}:")
        for key, value in batch.items():
            if value != original_config.get(key):
                print(f"  {key}: {value} ⬅ CHANGED")
            else:
                print(f"  {key}: {value}")
    
    print(f"\nStarting batch processing...")
    print("="*70)
    
    # Process batches
    successful_batches = 0
    failed_batches = 0
    
    for batch_num, batch_config in enumerate(batch_configs, 1):
        print("\n" + "="*70)
        print(f"BATCH {batch_num} of {len(batch_configs)}")
        print("="*70)
        
        # Update configuration
        print(f"\nUpdating inputs.json:")
        for key, value in batch_config.items():
            print(f"  {key}: {value}")
        
        inputs = load_inputs()
        inputs[config_key] = update_config_with_values(original_config, batch_config)
        save_inputs(inputs)
        
        # Run the tool
        success = run_tool(tool_key)
        
        if success:
            successful_batches += 1
            print(f"\n✅ Batch {batch_num} completed successfully!")
        else:
            failed_batches += 1
            print(f"\n❌ Batch {batch_num} failed!")
            
            # Continue automatically to next batch
            print("Continuing with remaining batches...")
    
    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"Total Batches Attempted: {batch_num}")
    print(f"Successful: {successful_batches}")
    print(f"Failed: {failed_batches}")
    print("="*70 + "\n")
    
    # Automatically restore original values
    print("Restoring original configuration in inputs.json...")
    inputs = load_inputs()
    inputs[config_key] = original_config
    save_inputs(inputs)
    print("Configuration restored.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBatch processing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
