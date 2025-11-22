import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid


class VectorStore:
    def __init__(self, persist_directory: str = "./data/vectordb"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="clinic_faq",
            metadata={"description": "Clinic FAQ and information"}
        )
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], 
                     embeddings: List[List[float]]) -> None:
        ids = [str(uuid.uuid4()) for _ in texts]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
    
    def query(self, query_embedding: List[float], n_results: int = 3) -> Dict[str, Any]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def clear(self) -> None:
        self.client.delete_collection(name="clinic_faq")
        self.collection = self.client.get_or_create_collection(
            name="clinic_faq",
            metadata={"description": "Clinic FAQ and information"}
        )
    
    def count(self) -> int:
        return self.collection.count()
