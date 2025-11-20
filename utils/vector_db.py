import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os

class VectorDB:
    def __init__(self, persist_directory="chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    def get_collection(self, brand_name):
        """Gets or creates a collection for a specific brand."""
        # ChromaDB collection names must be alphanumeric, underscores, hyphens, 3-63 chars.
        # AND must start/end with alphanumeric.
        # IMPORTANT: ChromaDB often requires ASCII.
        
        # Simple transliteration map for common Cyrillic chars to ensure we get ASCII
        # Or just strip non-ascii.
        
        import re
        
        # 1. Transliterate (Simple approach for MVP)
        # If we have 'transliterate' lib, good. If not, let's just use a hash if it's non-ascii
        # or strip non-ascii.
        
        # Let's try to keep it readable if possible, but safe.
        # "Світ Пекаря" -> "Svit_Pekarya" would be nice, but "brand_HASH" is safer without extra libs.
        
        # Let's use a simple approach: 
        # Keep ASCII alphanumeric. If result is too short, append hash of original name.
        
        ascii_name = re.sub(r'[^a-zA-Z0-9_-]', '', brand_name)
        
        # If the name became empty or too short (e.g. purely Cyrillic name), use hash
        import hashlib
        hash_suffix = hashlib.md5(brand_name.encode('utf-8')).hexdigest()[:8]
        
        if len(ascii_name) < 3:
            safe_name = f"brand_{hash_suffix}"
        else:
            safe_name = ascii_name
            
        # Ensure length limits (3-63)
        safe_name = safe_name[:50] # Leave room for suffix if needed
        
        # Ensure starts/ends with alphanumeric
        if not safe_name[0].isalnum():
            safe_name = "p" + safe_name
        if not safe_name[-1].isalnum():
            safe_name = safe_name + "0"
            
        # Lowercase is usually preferred/enforced
        safe_name = safe_name.lower()
        
        return self.client.get_or_create_collection(
            name=safe_name,
            embedding_function=self.embedding_fn
        )

    def add_pages(self, brand_name, pages_df):
        """
        Adds pages from a DataFrame (url, title, h1) to the brand's collection.
        """
        collection = self.get_collection(brand_name)
        
        documents = []
        metadatas = []
        ids = []

        for index, row in pages_df.iterrows():
            # Create a rich context for embedding: Title + H1
            content = f"{row.get('title', '')} {row.get('h1', '')}"
            if not content.strip():
                continue
                
            documents.append(content)
            metadatas.append({"url": row['url'], "title": row.get('title', '')})
            ids.append(str(row['url'])) # URL as ID to prevent duplicates

        if documents:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def query_similar(self, brand_name, query_text, n_results=5):
        """Finds semantically similar pages for internal linking."""
        collection = self.get_collection(brand_name)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        links = []
        if results['metadatas']:
            for meta in results['metadatas'][0]:
                links.append(meta)
        return links

    def get_all_pages(self, brand_name):
        """Retrieves all indexed pages for a brand."""
        collection = self.get_collection(brand_name)
        # Get all items
        results = collection.get()
        
        pages = []
        if results['metadatas']:
            for meta in results['metadatas']:
                pages.append(meta)
        return pages
