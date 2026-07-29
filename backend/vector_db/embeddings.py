import os
import base64
import requests
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings

load_dotenv()

class LocalProvider(Embeddings):
    def __init__(self):
        print("Loading local CLIP model (this might take a moment on first run)...")
        from sentence_transformers import SentenceTransformer
        from PIL import Image
        self.Image = Image
        self.model = SentenceTransformer('clip-ViT-B-32')
        print("Local CLIP model loaded successfully.")
        
    def embed_text(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # CLIP has a strict 77 token limit. We truncate strings to ~300 characters to avoid errors.
        truncated_texts = [t[:300] for t in texts]
        embeddings = self.model.encode(truncated_texts)
        return embeddings.tolist()
        
    def embed_images(self, image_paths: list[str]) -> list[list[float]]:
        if not image_paths:
            return []
        images = [self.Image.open(p) for p in image_paths]
        embeddings = self.model.encode(images)
        return embeddings.tolist()
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_text(texts)
        
    def embed_query(self, text: str) -> list[float]:
        res = self.embed_text([text])
        return res[0] if res else []


class JinaProvider(Embeddings):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.jina.ai/v1/embeddings"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
    def embed_text(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        data = {
            "model": "jina-clip-v1",
            "input": [{"text": t} for t in texts]
        }
        response = self.session.post(self.url, json=data)
        if not response.ok:
            raise RuntimeError(f"Jina API error: {response.text}")
        res_json = response.json()
        return [item["embedding"] for item in res_json["data"]]
        
    def embed_images(self, image_paths: list[str]) -> list[list[float]]:
        if not image_paths:
            return []
            
        import io
        import time
        from PIL import Image
        
        all_embeddings = []
        batch_size = 1
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            inputs = []
            for path in batch_paths:
                try:
                    with Image.open(path) as img:
                        img = img.convert("RGB")
                        img.thumbnail((512, 512))
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=85)
                        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                        inputs.append({"image": b64})
                except Exception as e:
                    print(f"Error processing image {path}: {e}")
                    
            if not inputs:
                continue
                
            data = {
                "model": "jina-clip-v1",
                "input": inputs
            }
            
            # Retry mechanism for robust connection handling
            for attempt in range(3):
                try:
                    response = self.session.post(self.url, json=data)
                    if not response.ok:
                        raise RuntimeError(f"Jina API error: {response.text}")
                    break # Success
                except requests.exceptions.ConnectionError as e:
                    if attempt == 2:
                        raise e
                    time.sleep(2) # Wait before retry
                    
            res_json = response.json()
            batch_embeddings = [item["embedding"] for item in res_json["data"]]
            all_embeddings.extend(batch_embeddings)
            
            # Tiny sleep to avoid aggressive rate limiting
            time.sleep(0.2)
            
        return all_embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_text(texts)
        
    def embed_query(self, text: str) -> list[float]:
        res = self.embed_text([text])
        return res[0] if res else []


def get_embedding_model():
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    if provider == "jina":
        api_key = os.getenv("JINA_API_KEY")
        if not api_key:
            raise ValueError("JINA_API_KEY must be set in .env to use 'jina' provider.")
        return JinaProvider(api_key)
    elif provider == "local":
        return LocalProvider()
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")
