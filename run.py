import argparse
import subprocess
import pathlib
import logging

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-T', '--book-title', required=True, help='Input file path')
    parser.add_argument('-S','--start', default=1, type=int, required=True, help='Input file path')
    parser.add_argument('-E','--end', type=int, required=True, help='Input file path')
    args = parser.parse_args()

    title = args.book_title

    output_path = pathlib.Path('output') / title
    basic_prompt_path = pathlib.Path('prompt') / 'basic_prompt.txt'
    newneek_prompt_path = pathlib.Path('prompt') / 'newneek_prompt.txt'

    # capture pages
    logger.info(f"Capturing pages for {title}")

    if len(list(output_path.glob('*.png'))) > 1:
        logger.info(f"Skipping capture for {title} because there are multiple existing PNGs in {output_path}")
    else:
        subprocess.run(['python', 'scr_to_img.py', '-T', title, '-S', str(args.start), '-E', str(args.end)])
        
    # convert images to pdf
    if not (output_path / f"{title}.pdf").exists() or not (output_path / f"{title}.txt").exists():
        logger.info(f"Converting images to pdf for {title}")
        subprocess.run(['python', 'img_to_pdf.py', '-i', output_path])
    else:
        logger.info(f"Skipping conversion for {title} because pdf and txt already exist")
    
    # convert txt to doc
    logger.info(f"Converting txt to doc for {title} with basic prompt")
    if not (output_path / f"{title}_basic.md").exists():
        subprocess.run(['python', 'txt_to_doc.py', '-i', str(output_path / f"{title}.txt"), '-o', str(output_path / f"{title}_basic.md"), '-p', str(basic_prompt_path)])
    else:
        logger.info(f"Skipping conversion for {title} because basic doc already exists")
        
    # convert doc to pdf
    logger.info(f"Converting txt to doc for {title} with newneek prompt")
    if not(output_path / f"{title}_newneek.md").exists():
        subprocess.run(['python', 'txt_to_doc.py', '-i', str(output_path / f"{title}.txt"), '-o', str(output_path / f"{title}_newneek.md"), '-p', str(newneek_prompt_path)])
    else:
        logger.info(f"Skipping conversion for {title} because newneek doc already exists")

if __name__ == '__main__':
    main()
    