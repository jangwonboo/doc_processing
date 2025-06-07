#!/usr/bin/env python3
"""
input_to_txt.py: Simple Text Extraction Tool using Google Gemini API with streaming

This module extracts text from various input sources (PDF, images) using Google Gemini API
with streaming content generation for better memory efficiency.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import (MODEL_NAME, PROMPT_FILE)

class TextExtractor:
    """Text extractor using Gemini API with streaming"""
    
    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize with API key and model name"""
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Initialized with model: {model_name}")
    
    def _upload_file(self, file_path: Path):
        """Upload file using Gemini File API"""
        mime_type = self._get_mime_type(file_path)
        
        # Open file in binary mode and upload
        with open(file_path, 'rb') as f:
            uploaded_file = self.client.files.upload(
                file=f,
                config=dict(mime_type=mime_type)
            )
        return uploaded_file
            
    def process_file(self, input_path: Path, output_path: Path) -> None:
        """Process a single file and save the extracted text"""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        logger.info(f"Processing file: {input_path}")
        
        try:
            # Upload the file
            uploaded_file = self._upload_file(input_path)
            
            # Process with streaming
            self._process_streaming(
                uploaded_file=uploaded_file,
                output_path=output_path,
                prompt=PROMPT_FILE.read_text()
            )
            
        except Exception as e:
            logger.error(f"Error processing {input_path}: {str(e)}")
            raise
        finally:
            # Clean up
            try:
                if 'uploaded_file' in locals() and hasattr(uploaded_file, 'id'):
                    self.client.files.delete(file_id=uploaded_file.id)
                elif 'uploaded_file' in locals():
                    logger.debug("Skipping file cleanup - uploaded file has no 'id' attribute")
            except Exception as e:
                logger.warning(f"Failed to clean up file: {str(e)}")
                # Don't raise the cleanup error to avoid masking the original error
    
    def _process_streaming(self, uploaded_file, output_path: Path, prompt: str) -> None:
        """Process content with streaming and save to file"""
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate content with streaming
        response = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=[uploaded_file, prompt],
        )
        
        # Write to file as we receive chunks
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for chunk in response:
                f_out.write(chunk.text)
                f_out.flush()  # Ensure content is written immediately
                print(chunk.text, end='', flush=True)  # Show progress
    
    @staticmethod
    def _get_mime_type(file_path: Path) -> str:
        """Get MIME type based on file extension"""
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        elif ext == '.tiff':
            return 'image/tiff'
        elif ext == '.bmp':
            return 'image/bmp'
        elif ext == '.webp':
            return 'image/webp'
        else:
            raise ValueError(f"Unsupported file format: {ext}")

def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Extract text from documents using Gemini API')
    parser.add_argument('-i', '--input', required=True, help='Input file path')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('--model', default=MODEL_NAME, help='Model name')
    parser.add_argument('--log', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Log level (default: INFO)')
    args = parser.parse_args()
    
    # Set log level
    logging.basicConfig(level=getattr(logging, args.log.upper()),
                      format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Process the file
    extractor = TextExtractor(api_key=api_key, model_name=args.model)
    extractor.process_file(
        input_path=Path(args.input),
        output_path=Path(args.output)
    )
    logger.info(f"Successfully processed {args.input} -> {args.output}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)