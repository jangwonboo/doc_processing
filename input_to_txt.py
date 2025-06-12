#!/usr/bin/env python3
"""
input_to_txt.py: Simple Text Extraction Tool using Google Gemini API

This module extracts raw text from various input sources (PDF, images) using Google Gemini API.
It focuses only on text extraction without summarization.
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from google import genai

# For PDF processing
import fitz  # PyMuPDF


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import MODEL_NAME

class TextExtractor:
    """Text extractor using Gemini API with streaming"""
    
    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize with API key and model name"""
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Initialized with model: {model_name}")
    
    def extract_pdf_pages(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """Extract pages from a PDF as images
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            
        Returns:
            List of paths to extracted page images
        """
        logger.info(f"Extracting pages from PDF: {pdf_path}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        extracted_images = []

        total_pages = pdf_document.page_count
        logger.info(f"PDF has {total_pages} pages")
        
        padding = len(str(total_pages))

        # Extract each page as an image
        for page_num, page in enumerate(pdf_document):
            # Render page to an image (300 DPI for good OCR results)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            image_path = output_dir / f"{pdf_path.stem}_{page_num+1:0{padding}d}.png"
            pix.save(image_path)
            extracted_images.append(image_path)
            logger.info(f"Extracted page {page_num+1:0{padding}d} to {image_path}")
            
        pdf_document.close()
        return extracted_images
    
    def run_ocr_on_images(self, image_paths: List[Path], output_dir: Path) -> Tuple[Path, Path]:
        """Run OCR on extracted images using img_to_pdf.py
        
        Args:
            image_paths: List of paths to images
            output_dir: Directory to save OCR results
            
        Returns:
            Tuple of (merged PDF path, merged text path)
        """
        logger.info(f"Running OCR on {len(image_paths)} images")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Import functionality from img_to_pdf.py
        script_dir = Path(__file__).parent
        img_to_pdf_path = script_dir / "img_to_pdf.py"
        
        if not img_to_pdf_path.exists():
            raise FileNotFoundError(f"img_to_pdf.py not found at {img_to_pdf_path}")
        
        # Create a temporary directory for the image files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy all images to the temp directory
            for img_path in image_paths:
                shutil.copy(img_path, temp_path / img_path.name)
            
            # Run img_to_pdf.py on the temporary directory
            cmd = [
                sys.executable,
                str(img_to_pdf_path),
                "-i", str(temp_path),
                "-o", str(output_dir),
                "--log", "INFO"
            ]
            logger.info(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Find the merged PDF and text files
            merged_pdf = output_dir / f"{temp_path.name}.pdf"
            merged_text = output_dir / f"{temp_path.name}.txt"
            
            # Copy to final output locations with proper names
            final_pdf = output_dir / f"{output_dir.name}.pdf"
            final_text = output_dir / f"{output_dir.name}.txt"
            
            if merged_pdf.exists() and merged_text.exists():
                shutil.copy(merged_pdf, final_pdf)
                shutil.copy(merged_text, final_text)
                logger.info(f"Created merged PDF: {final_pdf}")
                logger.info(f"Created merged text: {final_text}")
                return final_pdf, final_text
            else:
                raise FileNotFoundError(f"OCR processing failed to produce merged files")
    
    def process_file(self, input_path: Path, output_path: Path, prompt="") -> None:
        """Process a single file and extract raw text"""

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        logger.info(f"Processing file: {input_path}")

        mime_type = self._get_mime_type(input_path)
        logger.info(f"MIME type: {mime_type}")
        
        # Special handling for PDF files
        if mime_type == 'application/pdf':
            # Create output directory based on PDF name
            pdf_name = input_path.stem
            output_dir = Path("output") / pdf_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract pages as images
            image_paths = self.extract_pdf_pages(input_path, output_dir)
            
            # Run OCR on the extracted images
            merged_pdf, merged_text = self.run_ocr_on_images(image_paths, output_dir)
            
            # Use the OCR text as input for Gemini API
            with open(merged_text, 'r', encoding='utf-8') as f:
                ocr_text = f.read()
                
            # Create a temporary text file with the OCR text
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as temp_file:
                temp_file.write(ocr_text)
                temp_path = Path(temp_file.name)
            
            try:
                # Process the OCR text with Gemini API
                with open(temp_path, 'rb') as f:
                    uploaded_file = self.client.files.upload(
                        file=f,
                        config=dict(mime_type='text/plain')
                    )
                logger.info(f"Uploaded OCR text: {uploaded_file}")
                
                # Process with Gemini API
                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[prompt, uploaded_file],
                )
                logger.info(f"Response: {response}")
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
        else:
            # Standard processing for non-PDF files
            # Open file in binary mode and upload
            with open(input_path, 'rb') as f:
                uploaded_file = self.client.files.upload(
                    file=f,
                    config=dict(mime_type=mime_type)
                )
            logger.info(f"File uploaded: {uploaded_file}")

            # Process with Gemini API
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=[prompt, uploaded_file],
            )
            logger.info(f"Response: {response}")
        # Write to file as we receive chunks
        with open(output_path, 'w', encoding='utf-8') as f_out:
            content_saved = False
            try:
                # First attempt: process as a normal stream
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text is not None:
                        f_out.write(chunk.text)
                        f_out.flush()
                        print(chunk.text, end='', flush=True)
                        content_saved = True
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error in response: {json_err}")
                # If we got some content before the error, keep it
                if content_saved:
                    logger.info("Partial content was saved before the JSON error occurred")
                else:
                    # Try alternative approach: access the raw response data
                    logger.info("Attempting to recover from JSON error by processing raw response...")
                    try:
                        # Try to access the raw response data if available
                        if hasattr(response, '_raw_response') and hasattr(response._raw_response, 'text'):
                            raw_text = response._raw_response.text
                            # Try to extract content from raw response
                            # Look for text content between quotes after "text": pattern
                            import re
                            text_matches = re.findall(r'"text"\s*:\s*"([^"]+)"', raw_text)
                            if text_matches:
                                for match in text_matches:
                                    # Unescape any escaped characters
                                    clean_text = bytes(match, 'utf-8').decode('unicode_escape')
                                    f_out.write(clean_text)
                                    f_out.flush()
                                    print(clean_text, end='', flush=True)
                                    content_saved = True
                            else:
                                logger.warning("Could not extract text content from raw response")
                        else:
                            logger.warning("Raw response data not available")
                    except Exception as raw_err:
                        logger.error(f"Error processing raw response: {raw_err}")
            except Exception as e:
                logger.error(f"Error processing response chunks: {e}")
                
            # If no content was saved through any method, write an error message
            if not content_saved:
                f_out.write(f"Error processing document. The API response could not be parsed correctly.\n")
                f_out.flush()
        # Clean up the uploaded file
        try:
            if hasattr(uploaded_file, 'id'):
                self.client.files.delete(file_id=uploaded_file.id)
        except Exception as e:
            logger.warning(f"Failed to clean up uploaded file: {e}")
    
    @staticmethod
    def _get_mime_type(file_path: Path) -> str:
        """Get MIME type based on file extension"""
        ext = file_path.suffix.lower()
        if ext == '.txt':
            return 'text/plain'
        elif ext == '.md':
            return 'text/markdown'
        elif ext == '.pdf':
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
    parser.add_argument('-p', '--prompt', default='', help='Prompt file path')
    parser.add_argument('--model', default=MODEL_NAME, help='Model name')
    parser.add_argument('--log', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Log level (default: INFO)')
    parser.add_argument('--skip-ocr', action='store_true', 
                      help='Skip OCR processing for PDFs and use direct API upload')
    args = parser.parse_args()
    
    # Set log level
    logging.basicConfig(level=getattr(logging, args.log.upper()),
                      format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create output directory if needed
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read prompt from file if provided
    prompt = ""
    if args.prompt:
        prompt_path = Path(args.prompt)
        if prompt_path.exists():
            try:
                prompt = prompt_path.read_text(encoding='utf-8')
                logger.info(f"Loaded prompt from {prompt_path}")
            except Exception as e:
                logger.warning(f"Failed to read prompt file: {e}")
                prompt = ""
    
    # Process the file
    extractor = TextExtractor(api_key=api_key, model_name=args.model)
    
    try:
        # For PDF files, ensure output directory exists
        if input_path.suffix.lower() == '.pdf' and not args.skip_ocr:
            # Create output directory structure
            pdf_name = input_path.stem
            output_dir = Path("output") / pdf_name
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # Process the file
        extractor.process_file(
            input_path=input_path,
            output_path=output_path,
            prompt=prompt
        )
        logger.info(f"Successfully processed {input_path} -> {output_path}")
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)