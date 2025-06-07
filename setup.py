from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="capture-mac",
    version="0.1.0",
    author="jangwonboo",
    author_email="your.email@example.com",  # Update with your email
    description="A tool for screen capture, OCR, and document generation on macOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/capture_mac",  # Update with your repo URL
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: Capture",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "filelock>=3.12.0",
        "PyPDF2>=3.0.0",
        "numpy>=1.24.0",
        "opencv-python-headless>=4.7.0",
        "pyautogui>=0.9.54",
        "Pillow>=10.0.0",
        "google-generativeai>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "capture=scr_to_img:main",
            "img2pdf=img_to_pdf:main",
            "textract=input_to_txt:main",
            "docgen=txt_to_doc:main",
            "llm-ocr=llm_ocr:main",
        ],
    },
    include_package_data=True,
)
