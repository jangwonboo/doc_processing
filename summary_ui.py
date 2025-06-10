#!/usr/bin/env python3
"""
summary_ui.py: Streamlit interface for document summarization using LLM

This module provides a user-friendly web interface for summarizing documents
using the TextExtractor class from input_to_txt.py.
"""

import os
import sys
import logging
import streamlit as st
from pathlib import Path
from typing import Optional, Tuple

# Import the TextExtractor class from input_to_txt
from input_to_txt import TextExtractor, MODEL_NAME
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.doc', '.png', '.jpg', '.jpeg']

def save_uploaded_file(uploaded_file, directory: str = "temp") -> Optional[Path]:
    """Save uploaded file to a temporary directory"""
    try:
        # Create temp directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return Path(file_path)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def process_document(extractor: TextExtractor, doc_path: Path, prompt: str, output_path: Path):
    """Process document and yield output chunks"""
    try:
        # Process the document with streaming
        response = extractor.client.models.generate_content_stream(
            model=extractor.model_name,
            contents=[str(doc_path), prompt],
        )
        
        # Yield chunks as they come
        full_text = ""
        for chunk in response:
            if hasattr(chunk, 'text'):
                full_text += chunk.text
                yield chunk.text, None
        
        # Save the full output to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
            
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        yield None, str(e)

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Document Summarizer",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Document Summarizer")
    st.markdown("Upload a document and a prompt to generate a summary using LLM.")
    
    # Initialize session state
    if 'output_text' not in st.session_state:
        st.session_state.output_text = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = ""
    if 'output_dir' not in st.session_state:
        # Set default output directory to the same as the uploaded document
        if 'doc_file' in st.session_state:
            doc_path = Path(st.session_state.doc_file.name)
            st.session_state.output_dir = str(doc_path.parent.absolute())
        else:
            st.session_state.output_dir = str(Path.home() / "Documents" / "summaries")
    
    # Document upload
    st.subheader("1. Upload Document")
    doc_file = st.file_uploader(
        "Choose a document (PDF, TXT, DOCX, or image)",
        type=SUPPORTED_EXTENSIONS,
        key="doc_uploader"
    )
    
    # Prompt upload
    st.subheader("2. Upload or Edit Prompt")
    prompt_file = st.file_uploader(
        "Choose a prompt file (TXT)",
        type=['.txt'],
        key="prompt_uploader"
    )
    
    # Initialize prompt text
    default_prompt = """Please summarize the following document in a clear and concise manner.
Include the main points and key details."""
    
    # If prompt file is uploaded, use its content, otherwise use default
    if prompt_file is not None:
        prompt_text = prompt_file.getvalue().decode("utf-8")
    else:
        prompt_text = default_prompt
    
    # Show prompt in an editable text area
    st.subheader("3. Edit Prompt")
    edited_prompt = st.text_area(
        "Prompt:",
        value=prompt_text,
        height=150,
        help="Modify the prompt as needed"
    )
    
    # Save prompt button
    if st.button("💾 Save Prompt", help="Save the current prompt to a file"):
        # Use file dialog to get save path
        save_path = st.file_uploader(
            "Save prompt as:",
            type=['txt'],
            key="prompt_saver",
            accept_multiple_files=False,
            label_visibility="collapsed"
        )
        
        if save_path:
            try:
                # Get the filename from the file_uploader
                save_filename = save_path.name
                # Ensure the file has .txt extension
                if not save_filename.lower().endswith('.txt'):
                    save_filename += '.txt'
                
                # Save the file
                with open(save_filename, 'w', encoding='utf-8') as f:
                    f.write(edited_prompt)
                st.success(f"Prompt saved to: {os.path.abspath(save_filename)}")
            except Exception as e:
                st.error(f"Error saving prompt: {e}")
        else:
            st.warning("Please select a file to save the prompt")
    
    # Output settings
    st.subheader("4. Output Settings")
    
    # Default output directory
    default_output_dir = str(Path.home() / "Documents" / "summaries")
    output_dir = st.text_input(
        "Output Directory:",
        value=default_output_dir,
        help="Directory where the summary will be saved"
    )
    
    # Default filename based on input document
    default_filename = f"{Path(doc_file.name).stem}_summary.md" if doc_file else "summary.md"
    output_filename = st.text_input(
        "Output Filename:",
        value=default_filename,
        help="Name of the output file"
    )
    
    # Create output containers that are always visible
    st.subheader("5. Processing Output")
    output_container = st.container(border=True, height=200)
    
    with output_container:
        if 'output_text' not in st.session_state:
            st.session_state.output_text = "Results will appear here..."
        st.markdown(
            f'<div style="height: 150px; overflow-y: auto; padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9;">'
            f'{st.session_state.output_text}'
            f'</div>', 
            unsafe_allow_html=True
        )
    
    st.subheader("6. Log Messages")
    log_container = st.container(border=True, height=150)
    
    with log_container:
        if 'log_messages' not in st.session_state:
            st.session_state.log_messages = "Log messages will appear here..."
        st.markdown(
            f'<div style="height: 100px; overflow-y: auto; padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9; font-family: monospace; font-size: 0.9em;">'
            f'{st.session_state.log_messages}'
            f'</div>', 
            unsafe_allow_html=True
        )
    
    # Process button at the bottom
    process_btn = st.button("▶️ Start Processing", type="primary", use_container_width=True)
    
    # Process the document when the button is clicked
    if process_btn and doc_file:
        with st.spinner("Processing document..."):
            try:
                # Save uploaded files
                doc_path = save_uploaded_file(doc_file)
                if not doc_path:
                    st.error("Failed to save the uploaded document.")
                    return
                
                # Initialize output in session state
                st.session_state.output_text = "Starting processing..."
                st.session_state.log_messages = ""
                
                # Force UI update
                st.rerun()
                
                try:
                    # Initialize TextExtractor
                    api_key = os.getenv("GOOGLE_API_KEY")
                    if not api_key:
                        raise ValueError("GOOGLE_API_KEY not found in environment variables")
                    
                    extractor = TextExtractor(api_key=api_key)
                    
                    # Prepare output path
                    output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir_path / output_filename
                    
                    # Process the document and update the UI in real-time
                    output_text = ""
                    for chunk, error in process_document(extractor, doc_path, edited_prompt, output_path):
                        if error:
                            st.session_state.log_messages += f"\n[ERROR] {error}"
                            st.session_state.error_message = error
                        elif chunk:
                            output_text += chunk
                            st.session_state.output_text = output_text
                        
                        # Force UI update after each chunk
                        st.rerun()
                except Exception as e:
                    st.session_state.log_messages += f"\n[FATAL] {str(e)}"
                    st.session_state.error_message = str(e)
                    st.rerun()
                    raise
                
                # Show success message
                st.success(f"Processing complete! Results saved to: {output_path}")
                
                # Add download button for the result
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="Download Summary",
                        data=f,
                        file_name=output_path.name,
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.exception("Error in document processing")
    
    elif process_btn and not doc_file:
        st.warning("Please upload a document first!")

if __name__ == "__main__":
    main()