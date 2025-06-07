#!/usr/bin/env python3
"""
img_to_pdf.py: Image to Searchable PDF Conversion using Tesseract OCR

이 모듈은 이미지 파일(PNG, JPG 등)을 Tesseract OCR을 사용하여 검색 가능한 PDF로 변환하고,
여러 PDF 파일을 하나로 병합하는 기능을 제공합니다.

Provides functionality to convert images to searchable PDFs using Tesseract OCR
and merge multiple PDFs into a single file.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tesseract(input_path, output_path, lang, tess_path):
    """
    Tesseract를 사용하여 PNG 이미지를 검색 가능한 PDF로 변환합니다.
    
    Args:
        input_path (Path): 입력 PNG 파일 경로
        output_path (Path): 출력 PDF 파일 경로
        lang (str): Tesseract 언어 설정 (예: 'kor+eng')
        tess_path (str): Tesseract 실행 파일 경로
        
    Returns:
        Path: 생성된 PDF 파일 경로
        
    Converts PNG image to searchable PDF using Tesseract OCR.
    """
    cmd = [tess_path, str(input_path), str(output_path.with_suffix('')), '-l', lang, 'pdf']
    logger.info(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return output_path

def merge_pdfs(pdf_files, merged_path):
    """
    여러 PDF 파일을 하나로 병합합니다.
    
    Args:
        pdf_files (List[Path]): 병합할 PDF 파일 경로 목록
        merged_path (Path): 병합된 PDF 저장 경로
        
    Merge multiple PDF files into a single PDF.
    """
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        logger.error("PyPDF2가 필요합니다. pip install PyPDF2")
        sys.exit(1)
    merger = PdfMerger()
    for pdf in sorted(pdf_files, key=lambda x: str(x)):
        with open(pdf, 'rb') as f:
            merger.append(f)
    merger.write(str(merged_path))
    merger.close()
    logger.info(f"병합 PDF 저장: {merged_path}")

def main():
    # Supported input formats
    supported_input = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif']
    supported_output = ['pdf']
    
    parser = argparse.ArgumentParser(
        description='이미지 → 검색 가능한 PDF 변환 (Image to Searchable PDF Conversion)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
지원하는 입력 형식 (Supported input formats): {', '.join(supported_input)}
지원하는 출력 형식 (Supported output formats): {', '.join(supported_output)}

예시 (Examples):
  # 단일 파일 변환 (Single file conversion)
  {os.path.basename(__file__)} -i input.png -o output.pdf
  
  # 디렉토리 내 모든 이미지 변환 (Convert all images in directory)
  {os.path.basename(__file__)} -i ./input_dir -o ./output_dir
  
  # 병합 옵션 사용 (With merge option)
  {os.path.basename(__file__)} -i ./input_dir -o output.pdf --merge
'''
    )
    
    # Required arguments
    parser.add_argument('-i', '--input', required=True,
                      help='입력 파일 또는 디렉토리 (Input file or directory)')
    
    # Optional arguments
    parser.add_argument('-o', '--output',
                      help='출력 파일 또는 디렉토리 (Output file or directory)')
    
    parser.add_argument('-l', '--log', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='로그 레벨 (Log level, default: INFO)')
    
    args = parser.parse_args()
    
    # Set log level
    log_level = getattr(logging, args.log.upper())
    logger.setLevel(log_level)
    ch.setLevel(log_level)

    input_path = Path(args.input)
    
    # Determine if input is file or directory
    if input_path.is_file():
        # Single file processing
        if not input_path.suffix.lower().lstrip('.') in supported_input:
            logger.error(f"지원하지 않는 파일 형식: {input_path.suffix}")
            logger.error(f"지원 형식: {', '.join(supported_input)}")
            sys.exit(1)
            
        output_path = Path(args.output) if args.output else input_path.with_suffix('.pdf')
        run_tesseract(input_path, output_path, 'kor+eng+chi_tra', 'tesseract')
        logger.info(f"PDF 저장: {output_path}")
        return
    elif input_path.is_dir():
        # Directory processing
        output_dir = Path(args.output) if args.output else input_path
        output_dir.mkdir(exist_ok=True)
        
        # Get all supported image files
        png_files = []
        for ext in supported_input:
            png_files.extend(input_path.glob(f'*.{ext}'))
            png_files.extend(input_path.glob(f'*.{ext.upper()}'))
        png_files = sorted(list(set(png_files)))  # Remove duplicates
        for png in png_files:
            pdf_path = output_dir / (png.stem + '.pdf')
            if pdf_path.exists():
                logger.info(f"이미 존재: {pdf_path} → 건너뜀")
            else:
                run_tesseract(png, pdf_path, 'kor+eng+chi_tra', 'tesseract')
                logger.info(f"PDF 저장: {pdf_path}")
        all_pdfs = sorted(list(output_dir.glob('*.pdf')) + list(output_dir.glob('*.PDF')), key=lambda x: str(x))
        if not all_pdfs:
            logger.warning(f"병합할 PDF 파일이 없습니다: {output_dir}")
        else:
            merged_path = output_dir / f"{input_path.name}.pdf"
            merge_pdfs(all_pdfs, merged_path)
        return
    logger.error("--input-file/-if 또는 --input-dir/-id 중 하나를 지정하세요.")
    sys.exit(1)

if __name__ == '__main__':
    main()