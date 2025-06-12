#!/usr/bin/env python3
"""
txt_to_doc.py: Text to Document Conversion Tool

이 모듈은 텍스트 파일을 요약하고 문서로 변환하는 기능을 제공합니다.
Google의 Generative AI Python SDK를 사용하여 텍스트를 분석하고 요약합니다.

This module provides functionality to summarize and convert text files into documents.
It uses Google's Generative AI Python SDK for text analysis and summarization.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
from google import genai

# Import configuration
from config import MODEL_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_summary(
    input_file: Path,
    output_file: Path,
    prompt_file: Optional[Path] = None,
    max_chunk_size: Optional[int] = None  # Parameter kept for backward compatibility
) -> None:
    """Generate a summary of the text using Gemini API with streaming.
    
    Args:
        input_file: Path to the input text file
        output_file: Path to save the summary
        prompt_file: Optional path to a file containing the prompt
        max_chunk_size: Ignored parameter, kept for backward compatibility
    """
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Read prompt file if provided
        prompt = "Summarize the following text:"
        if prompt_file and prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
        
        # Generate summary
        success = _generate_text_summary(prompt, text, output_file)
        
        if not success:
            logger.error("Failed to generate summary")
            
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise

def _generate_text_summary(
    prompt: str,
    text: str,
    output_file: Path
) -> bool:
    """Generate a summary for the entire text using Gemini API with streaming.
    
    Args:
        prompt: The prompt to use for summarization
        text: The text to summarize
        output_file: Path to save the summary
        
    Returns:
        bool: True if summary was generated successfully, False otherwise
    """
    logger.info(f"Generating summary for text of length: {len(text)} characters")
    
    # Get API key from environment
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        return False
    
    # Create the full prompt with the text to summarize
    full_prompt = f"{prompt}\n\n{text}"
    
    try:
        # Initialize the client
        client = genai.Client(api_key=api_key)
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate content with streaming using the official API format
        stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": full_prompt}]}]
        )
        
        # Write to file as we receive chunks
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in stream:
                if hasattr(chunk, 'text'):
                    logger.debug(f"Writing chunk: {chunk.text}")
                    f.write(chunk.text)
                    f.flush()  # Ensure content is written immediately
        
        # Verify the output file was created with content
        if output_file.exists() and os.path.getsize(output_file) > 0:
            logger.info("Successfully generated summary")
            return True
        
        logger.warning("Empty response received from API")
        return False
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return False

def setup_logging(log_level: str = 'INFO') -> None:
    """Set up logging configuration with the specified log level.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger.info(f"Logging configured with level: {logging.getLevelName(log_level)}")

if __name__ == '__main__':
    import argparse
    from pathlib import Path
    
    # Define log levels for argument parser
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    # Set up argument parser
    supported_input = ['txt', 'md', 'text', 'log']
    
    parser = argparse.ArgumentParser(
        description='텍스트 요약 및 문서 생성 (Text Summarization and Document Generation)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
지원하는 입력 형식 (Supported input formats): {', '.join(supported_input)}

예시 (Examples):
  # 기본 요약 생성 (Basic summary generation)
  {os.path.basename(__file__)} -i input.txt -o summary.txt
  
  # 커스텀 프롬프트 사용 (With custom prompt)
  {os.path.basename(__file__)} -i input.txt -o summary.txt -p custom_prompt.txt
  
  # 상세 로그 활성화 (Enable debug logging)
  {os.path.basename(__file__)} -i input.txt -o summary.txt -l DEBUG
'''
    )
    
    # Required arguments
    parser.add_argument('-i', '--input', required=True,
                      help='입력 텍스트 파일 (Input text file)')
    
    parser.add_argument('-o', '--output', required=True,
                      help='출력 요약 파일 (Output summary file)')
    
    # Optional arguments
    parser.add_argument('-p', '--prompt',
                      help='사용자 정의 프롬프트 파일 (Custom prompt file)')
    
    parser.add_argument('-l', '--log', default='INFO',
                      choices=LOG_LEVELS,
                      help=f'로그 레벨 (Log level, default: INFO)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log)
    
    # Log startup information
    logger.info(f"Starting summary generation with log level: {args.log}")
    logger.debug(f"Command line arguments: {vars(args)}")
    
    # Generate the summary
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        prompt_path = Path(args.prompt) if args.prompt else None
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
            
        if prompt_path and not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            sys.exit(1)
        
        logger.info(f"Generating summary from {input_path} to {output_path}")
        if prompt_path:
            logger.info(f"Using prompt from: {prompt_path}")
            
        generate_summary(
            input_file=input_path,
            output_file=output_path,
            prompt_file=prompt_path
        )
        
        logger.info("Summary generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during summary generation: {str(e)}", exc_info=True)
        sys.exit(1)
