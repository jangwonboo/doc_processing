# Document Processing Application

A powerful document processing application with OCR, PDF conversion, and text extraction capabilities. Built with Python and PyQt6 for a user-friendly GUI experience.

## ✨ Features

- **Screen Capture**: Capture screen content with customizable settings
- **OCR Processing**: Extract text from images and PDFs using Tesseract OCR
- **PDF Conversion**: Convert images to searchable PDFs
- **Document Generation**: Create and edit documents from extracted text
- **User-friendly GUI**: Intuitive interface for all operations
- **Multi-language Support**: Supports multiple languages for OCR (English, Korean, Chinese, etc.)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Tesseract OCR (for OCR functionality)
- Required Python packages (install via `pip install -r requirements.txt`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jangwonboo/doc_processing.git
   cd doc_processing
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - On macOS: `brew install tesseract tesseract-lang`
   - On Linux: `sudo apt install tesseract-ocr` (Ubuntu/Debian)
   - On Windows: Download installer from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Running the Application

Start the application with:

```bash
python gui.py
```

## 📝 Usage

1. **Capture Settings**:
   - Set the application window to capture from
   - Configure capture area (x, y, width, height)
   - Set page range for batch processing

2. **OCR Settings**:
   - Select languages for OCR
   - Configure output format (PDF, text, or both)
   - Set output directory

3. **Processing**:
   - Click "Run" to start the capture and processing
   - Monitor progress in the log window
   - Pause or stop the process as needed

## 🛠️ Project Structure

```
doc_processing/
├── gui.py              # Main GUI application
├── gui.ui              # UI definition file
├── gui_elements.py     # Custom UI elements
├── scr_to_img.py       # Screen capture functionality
├── img_to_pdf.py       # Image to PDF conversion
├── input_to_txt.py     # Text extraction from various inputs
├── txt_to_doc.py       # Document generation from text
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## ❓ FAQ

### Q: Is this application cross-platform?
A: The core functionality works on all platforms, but the screen capture feature is currently optimized for macOS.

### Q: Do I need Tesseract OCR installed?
A: Yes, Tesseract is required for OCR functionality. See installation instructions above.

### Q: How do I add support for more languages?
A: Install the appropriate Tesseract language packs and select them in the language settings.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
