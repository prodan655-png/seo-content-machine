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
        # We'll sanitize the brand name.
        safe_name = "".join(c if c.isalnum() else "_" for c in brand_name).lower()
        # Ensure it starts with a letter and is not too long
        if not safe_name[0].isalpha():
            safe_name = "p_" + safe_name
        safe_name = safe_name[:63]
        
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
