# --- preprocess.py ---
import os
import fitz  # PyMuPDF
import json
import re

def approximate_token_count(text):
    return int(len(text.split()) / 0.75)

def simple_sent_tokenize(text):
    return re.split(r'(?<=[.!?])\s+', text)

def chunk_text(text, max_tokens=800):
    sentences = simple_sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if approximate_token_count(current_chunk + sentence) <= max_tokens:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def extract_text_pdf(filepath):
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def preprocess_pdfs(source_dir, output_file):
    knowledge_chunks = []
    for filename in os.listdir(source_dir):
        if filename.endswith(".pdf"):
            full_path = os.path.join(source_dir, filename)
            content = extract_text_pdf(full_path)
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                knowledge_chunks.append({
                    "id": f"{filename.replace(' ', '_').replace('.pdf', '')}_{i+1}",
                    "source": filename,
                    "category": "menu" if "menu" in filename.lower() else "location",
                    "content": chunk,
                    "tokens": approximate_token_count(chunk)
                })
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(knowledge_chunks, f, indent=2)
    print(f"Processed {len(knowledge_chunks)} knowledge chunks.")

# Example usage
if __name__ == "__main__":
    preprocess_pdfs("./Knowledge Base", "./data/knowledge_chunks.json")
