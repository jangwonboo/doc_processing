from google import genai
from google.genai import types
import pathlib
import os
import time
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

client = genai.Client(api_key=GOOGLE_API_KEY)

filepath = pathlib.Path('test.pdf')

uploaded_file = client.files.upload(file=filepath)
file_info = client.files.get(name=uploaded_file.name)
print(file_info.model_dump_json(indent=4))

prompt = "Summarize this document"

response = client.models.generate_content_stream(
    model="gemini-2.5-flash-preview-05-20",
    contents=[uploaded_file, prompt])

for chunk in response:
    if hasattr(chunk, 'text'):
        print(chunk.text, end='', flush=True)