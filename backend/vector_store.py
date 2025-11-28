"""
Vector Store Module
Handles document storage and retrieval using ChromaDB
"""

import chromadb
from chromadb.utils import embedding_functions
import os
import hashlib

class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize the vector store with ChromaDB"""
        self.persist_directory = persist_directory
        
        # Create embedding function using sentence-transformers
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="qa_documents",
            embedding_function=self.embedding_function,
            metadata={"description": "QA Agent Knowledge Base"}
        )
    
    def generate_doc_id(self, text, source):
        """Generate a unique ID for a document chunk"""
        content = f"{source}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_documents(self, chunks, source_name):
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of text chunks
            source_name: Name of the source document
        """
        if not chunks:
            return 0
        
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            doc_id = self.generate_doc_id(chunk, f"{source_name}_{i}")
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "source": source_name,
                "chunk_index": i
            })
        
        # Add to collection (upsert to avoid duplicates)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def search(self, query, n_results=5):
        """
        Search for relevant documents
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def get_all_documents(self):
        """Get all documents in the collection"""
        return self.collection.get()
    
    def get_document_count(self):
        """Get the number of documents in the collection"""
        return self.collection.count()
    
    def clear(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        self.client.delete_collection("qa_documents")
        self.collection = self.client.get_or_create_collection(
            name="qa_documents",
            embedding_function=self.embedding_function,
            metadata={"description": "QA Agent Knowledge Base"}
        )
    
    def get_sources(self):
        """Get list of unique source documents"""
        all_docs = self.collection.get()
        sources = set()
        if all_docs and all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])
        return list(sources)