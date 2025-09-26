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
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def natural_sort_key(path):
    """
    자연스러운 정렬을 위한 키 함수 (숫자 순서 고려)
    Natural sorting key function that considers numeric order
    
    Args:
        path: Path 객체 또는 문자열
        
    Returns:
        list: 정렬을 위한 키 리스트
    """
    if isinstance(path, Path):
        text = path.name
    else:
        text = str(path)
    
    # 숫자와 문자를 분리하여 정렬 키 생성
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', text)]

def run_tesseract(input_path, output_path, lang, tess_path):
    """
    Tesseract를 사용하여 PNG 이미지를 검색 가능한 PDF로 변환하고 텍스트 파일도 생성합니다.
    
    Args:
        input_path (Path): 입력 PNG 파일 경로
        output_path (Path): 출력 PDF 파일 경로
        lang (str): Tesseract 언어 설정 (예: 'kor+eng')
        tess_path (str): Tesseract 실행 파일 경로
        
    Returns:
        tuple: (생성된 PDF 파일 경로, 생성된 텍스트 파일 경로)
        
    Converts PNG image to searchable PDF using Tesseract OCR and also saves text output.
    """
    # Tesseract 출력 파일의 기본 경로 (확장자 없음)
    base_output = output_path.with_suffix('')
    
    # PDF와 텍스트 파일 생성
    cmd = [tess_path, str(input_path), str(base_output), '-l', lang, 'pdf', 'txt']
    logger.info(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # 생성된 텍스트 파일 경로
    text_path = base_output.with_suffix('.txt')
    
    logger.info(f"Generated PDF: {output_path}")
    logger.info(f"Generated text: {text_path}")
    
    return output_path, text_path

def check_pdf_integrity(pdf_path):
    """PDF 파일의 무결성을 검사합니다."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        logger.error("PyPDF2가 필요합니다. pip install PyPDF2")
        sys.exit(1)
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            num_pages = len(reader.pages)
            if num_pages > 0:
                first_page = reader.pages[0]
                _ = first_page.extract_text()
        return True, f"정상 ({num_pages}페이지)"
    except Exception as e:
        return False, str(e)

def find_corresponding_image(pdf_path):
    """PDF 파일에 대응하는 이미지 파일을 찾습니다."""
    base_name = pdf_path.stem
    image_extensions = ['.png', '.jpg', '.jpeg']
    
    for ext in image_extensions:
        image_path = pdf_path.parent / (base_name + ext)
        if image_path.exists():
            return image_path
    return None

def repair_corrupted_pdf(pdf_path):
    """손상된 PDF 파일을 이미지에서 다시 생성합니다."""
    image_path = find_corresponding_image(pdf_path)
    
    if not image_path:
        logger.warning(f"이미지 파일을 찾을 수 없어 복구 불가: {pdf_path.stem}")
        return False
    
    logger.info(f"손상된 PDF 복구 시도: {pdf_path.name} <- {image_path.name}")
    
    backup_pdf = pdf_path.with_suffix('.pdf.backup')
    backup_txt = pdf_path.with_suffix('.txt.backup')
    
    try:
        if pdf_path.exists():
            pdf_path.rename(backup_pdf)
        
        txt_path = pdf_path.with_suffix('.txt')
        if txt_path.exists():
            txt_path.rename(backup_txt)
        
        new_pdf, new_txt = run_tesseract(image_path, pdf_path, 'kor+eng+chi_tra', 'tesseract')
        
        if new_pdf.exists() and new_txt.exists():
            is_valid, message = check_pdf_integrity(new_pdf)
            if is_valid:
                logger.info(f"PDF 복구 성공: {pdf_path.name} - {message}")
                if backup_pdf.exists():
                    backup_pdf.unlink()
                if backup_txt.exists():
                    backup_txt.unlink()
                return True
            else:
                logger.error(f"복구된 PDF도 손상됨: {message}")
                return False
        else:
            logger.error(f"파일 생성 실패")
            return False
            
    except Exception as e:
        logger.error(f"PDF 복구 중 오류: {e}")
        try:
            if backup_pdf.exists() and not pdf_path.exists():
                backup_pdf.rename(pdf_path)
            if backup_txt.exists() and not txt_path.exists():
                backup_txt.rename(txt_path)
        except Exception as restore_error:
            logger.error(f"백업 복원 실패: {restore_error}")
        return False

def merge_pdfs(pdf_files, merged_path):
    """
    여러 PDF 파일을 하나로 병합합니다.
    
    Args:
        pdf_files (List[Path]): 병합할 PDF 파일 경로 목록
        merged_path (Path): 병합된 PDF 저장 경로
        
    Returns:
        Path: 병합된 PDF 파일 경로
        
    Merge multiple PDF files into a single PDF.
    """
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        logger.error("PyPDF2가 필요합니다. pip install PyPDF2")
        sys.exit(1)
    
    merger = PdfMerger()
    successful_merges = 0
    failed_files = []
    repaired_files = []
    
    for pdf in sorted(pdf_files, key=natural_sort_key):
        try:
            with open(pdf, 'rb') as f:
                merger.append(f)
                successful_merges += 1
        except Exception as e:
            logger.warning(f"PDF 병합 실패: {pdf} - {e}")
            
            # 손상된 PDF 복구 시도
            if repair_corrupted_pdf(pdf):
                try:
                    with open(pdf, 'rb') as f:
                        merger.append(f)
                        successful_merges += 1
                        repaired_files.append(pdf)
                        logger.info(f"복구 후 병합 성공: {pdf.name}")
                except Exception as retry_error:
                    logger.error(f"복구 후에도 병합 실패: {pdf} - {retry_error}")
                    failed_files.append(pdf)
            else:
                failed_files.append(pdf)
            continue
    
    if successful_merges == 0:
        logger.error("병합할 수 있는 PDF 파일이 없습니다.")
        return None
    
    try:
        merger.write(str(merged_path))
        merger.close()
        logger.info(f"병합 PDF 저장: {merged_path} ({successful_merges}개 파일 병합)")
        
        if repaired_files:
            logger.info(f"복구된 파일 {len(repaired_files)}개: {[f.name for f in repaired_files[:5]]}")
        
        if failed_files:
            logger.warning(f"병합 실패한 파일 {len(failed_files)}개: {[f.name for f in failed_files[:5]]}")
            
        return merged_path
    except Exception as e:
        logger.error(f"PDF 병합 저장 실패: {e}")
        merger.close()
        return None


def merge_text_files(text_files, merged_path):
    """
    여러 텍스트 파일을 하나로 병합합니다.
    
    Args:
        text_files (List[Path]): 병합할 텍스트 파일 경로 목록
        merged_path (Path): 병합된 텍스트 파일 저장 경로
        
    Returns:
        Path: 병합된 텍스트 파일 경로
        
    Merge multiple text files into a single text file.
    """
    with open(merged_path, 'w', encoding='utf-8') as outfile:
        for i, text_file in enumerate(sorted(text_files, key=natural_sort_key)):

            # 파일 내용 추가
            try:
                with open(text_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
            except UnicodeDecodeError:
                # UTF-8로 읽기 실패 시 다른 인코딩 시도
                try:
                    with open(text_file, 'r', encoding='cp949') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    logger.warning(f"텍스트 파일 읽기 실패: {text_file} - {e}")
                    outfile.write(f"[파일 읽기 오류: {text_file}]\n")
    
    logger.info(f"병합 텍스트 파일 저장: {merged_path}")
    return merged_path

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
    
    parser.add_argument('--ocr', action='store_true',
                      help='OCR 변환 (OCR conversion)') 
    
    args = parser.parse_args()
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=getattr(logging, args.log.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    input_path = Path(args.input)
    
    # Determine if input is file or directory
    if input_path.is_file():
        # Single file processing
        if not input_path.suffix.lower().lstrip('.') in supported_input:
            logger.error(f"지원하지 않는 파일 형식: {input_path.suffix}")
            logger.error(f"지원 형식: {', '.join(supported_input)}")
            sys.exit(1)
            
        output_path = Path(args.output) if args.output else input_path.with_suffix('.pdf')
        text_path = output_path.with_suffix('.txt')
        
        # 이미 PDF와 텍스트 파일이 모두 존재하는지 확인
        if output_path.exists() and text_path.exists():
            logger.info(f"이미 존재하는 파일입니다: {output_path} 및 {text_path} → 건너뜀")
            return
            
        pdf_path, text_path = run_tesseract(input_path, output_path, 'kor+eng+chi_tra', 'tesseract')
        logger.info(f"PDF 저장: {pdf_path}")
        logger.info(f"텍스트 저장: {text_path}")
        return
    elif input_path.is_dir():
        # Directory processing
        output_dir = Path(args.output) if args.output else input_path
        output_dir.mkdir(exist_ok=True)
        
        # Get all supported image files
        image_files = []
        for ext in supported_input:
            image_files.extend(input_path.glob(f'*.{ext}'))
            image_files.extend(input_path.glob(f'*.{ext.upper()}'))
        
        # Remove duplicates and sort naturally (considering numeric order)
        image_files = list(set(image_files))
        image_files = sorted(image_files, key=natural_sort_key)
        
        logger.info(f"발견된 이미지 파일 수: {len(image_files)}")
        if image_files:
            logger.info(f"처리 순서: {[f.name for f in image_files[:5]]}" + 
                       (f" ... (총 {len(image_files)}개)" if len(image_files) > 5 else ""))
        # 생성된 PDF와 텍스트 파일 경로를 저장할 리스트
        generated_pdfs = []
        generated_texts = []
        
        # 병합된 파일의 경로 미리 계산
        merged_pdf_path = output_dir / f"{input_path.name}.pdf"
        merged_text_path = output_dir / f"{input_path.name}.txt"
        
        # 병합된 파일이 이미 존재하는지 확인
        if merged_pdf_path.exists() and merged_text_path.exists():
            logger.info(f"이미 병합된 파일이 존재합니다: {merged_pdf_path} 및 {merged_text_path} → 건너뜀")
            return
        
        for image_file in image_files:
            pdf_path = output_dir / (image_file.stem + '.pdf')
            text_path = output_dir / (image_file.stem + '.txt')
            
            if pdf_path.exists() and text_path.exists():
                logger.info(f"이미 존재: {pdf_path} 및 {text_path} → 건너뜀")
                generated_pdfs.append(pdf_path)
                generated_texts.append(text_path)
            else:
                pdf_result, text_result = run_tesseract(image_file, pdf_path, 'kor+eng+chi_tra', 'tesseract')
                generated_pdfs.append(pdf_result)
                generated_texts.append(text_result)
        
        # PDF 파일 병합 (자연스러운 정렬 적용)
        all_pdfs = sorted(generated_pdfs, key=natural_sort_key)
        if not all_pdfs:
            logger.warning(f"병합할 PDF 파일이 없습니다: {output_dir}")
        else:
            # PDF 병합
            merged_pdf_path = output_dir / f"{input_path.name}.pdf"
            merge_pdfs(all_pdfs, merged_pdf_path)
            
            # 텍스트 파일 병합 (자연스러운 정렬 적용)
            all_texts = sorted(generated_texts, key=natural_sort_key)
            if all_texts:
                merged_text_path = output_dir / f"{input_path.name}.txt"
                merge_text_files(all_texts, merged_text_path)
                logger.info(f"모든 텍스트 파일이 {merged_text_path}로 병합되었습니다.")
        return
    logger.error("--input-file/-if 또는 --input-dir/-id 중 하나를 지정하세요.")
    sys.exit(1)

if __name__ == '__main__':
    main()