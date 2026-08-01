import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# Determine which Vector DB to use
# Default is 'chroma'
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma").lower()

def get_collection_dimension():
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    return 768 if provider == "jina" else 512

class QdrantCollectionWrapper:
    def __init__(self, client, name, dimension):
        self.client = client
        self.name = name
        self.dimension = dimension
        
        # Ensure collection exists in Qdrant
        try:
            if not self.client.collection_exists(self.name):
                from qdrant_client.models import VectorParams, Distance
                self.client.create_collection(
                    collection_name=self.name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                )
        except Exception:
            # Fallback for client versions or environments without collection_exists
            try:
                self.client.get_collection(self.name)
            except Exception:
                from qdrant_client.models import VectorParams, Distance
                self.client.create_collection(
                    collection_name=self.name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                )
                
        # Create payload indexes for filterable fields to satisfy Qdrant Cloud constraints
        try:
            from qdrant_client.models import PayloadSchemaType
            for field in ["category", "district", "trekking_difficulty", "province", "best_season"]:
                self.client.create_payload_index(
                    collection_name=self.name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD
                )
        except Exception:
            pass

    def upsert(self, ids, embeddings, metadatas=None, documents=None):
        from qdrant_client.models import PointStruct
        
        points = []
        for i in range(len(ids)):
            doc_id = ids[i]
            # Convert string ID to UUID to satisfy Qdrant requirements deterministically
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(doc_id)))
            
            payload = {"_original_id": str(doc_id)}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])
            if documents and i < len(documents):
                payload["document"] = documents[i]
                
            points.append(
                PointStruct(
                    id=point_uuid,
                    vector=embeddings[i],
                    payload=payload
                )
            )
            
        self.client.upsert(
            collection_name=self.name,
            points=points
        )

    def count(self):
        res = self.client.count(collection_name=self.name, exact=True)
        return res.count

    def query(self, query_embeddings, n_results=3, where=None):
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Handle single query embedding list
        query_vector = query_embeddings[0] if query_embeddings else []
        
        # Convert metadata filters to Qdrant Filters
        qdrant_filter = None
        if where:
            conditions = []
            for key, val in where.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=val)
                    )
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)
                
        search_res = self.client.query_points(
            collection_name=self.name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=n_results,
            with_payload=True,
            with_vectors=False
        )
        
        ids = []
        distances = []
        metadatas = []
        documents = []
        
        for point in search_res.points:
            ids.append(point.payload.get("_original_id", str(point.id)))
            # Convert cosine similarity to cosine distance (1 - similarity) to match Chroma DB behaviour
            distances.append(1.0 - point.score)
            
            # Extract metadata (exclude system attributes)
            meta = {k: v for k, v in point.payload.items() if k not in ["_original_id", "document"]}
            metadatas.append(meta)
            
            documents.append(point.payload.get("document", ""))
            
        return {
            "ids": [ids],
            "distances": [distances],
            "metadatas": [metadatas],
            "documents": [documents]
        }


# Initialize clients based on selected provider
if VECTOR_DB_TYPE == "qdrant":
    from qdrant_client import QdrantClient
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
    
    if qdrant_url == ":memory:":
        qdrant_client = QdrantClient(":memory:")
    elif qdrant_url.startswith("http://") or qdrant_url.startswith("https://"):
        qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        # Treat as local directory path
        if not os.path.isabs(qdrant_url):
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            qdrant_path = os.path.normpath(os.path.join(backend_dir, qdrant_url))
        else:
            qdrant_path = qdrant_url
        qdrant_client = QdrantClient(path=qdrant_path)
        
    def get_text_collection():
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        dimension = get_collection_dimension()
        return QdrantCollectionWrapper(qdrant_client, f"text_kb_{provider}", dimension)
        
    def get_image_collection():
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        dimension = get_collection_dimension()
        return QdrantCollectionWrapper(qdrant_client, f"image_kb_{provider}", dimension)

else:
    # Default to Chroma DB
    import chromadb
    from chromadb.config import Settings
    
    _env_path = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    if not os.path.isabs(_env_path):
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        CHROMA_PERSIST_DIR = os.path.normpath(os.path.join(backend_dir, _env_path))
    else:
        CHROMA_PERSIST_DIR = _env_path
        
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    
    def get_text_collection():
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        return chroma_client.get_or_create_collection(
            name=f"text_kb_{provider}",
            metadata={"hnsw:space": "cosine"}
        )
        
    def get_image_collection():
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        return chroma_client.get_or_create_collection(
            name=f"image_kb_{provider}",
            metadata={"hnsw:space": "cosine"}
        )
