import os
import requests
from src.config import DOC_IDS, DOC_EXPORT_URL, DATA_DIR

def fetch_document(doc_key: str) -> str:
    if doc_key not in DOC_IDS:
        raise ValueError(f"Unknown document key: {doc_key}")
    
    doc_id = DOC_IDS[doc_key]
    url = DOC_EXPORT_URL.format(doc_id=doc_id)
    
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch doc '{doc_key}' (Status Code: {response.status_code})")
    
    content = response.text
    
    file_path = os.path.join(DATA_DIR, f"{doc_key}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return content

def fetch_all() -> dict:
    docs = {}
    for key in DOC_IDS:
        print(f"📥 Fetching latest state for '{key}'...")
        docs[key] = fetch_document(key)
        print(f"✓ Saved to data/{key}.md")
    return docs

if __name__ == "__main__":
    fetch_all()
