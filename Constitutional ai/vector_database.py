"""
Vector Database using FAISS
Handles embedding generation and similarity search for Constitution articles
"""

import os
import json
import numpy as np
import faiss
import re
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
import pickle
import threading

TRUSTED_QA = {
    "what is the constitution of india": "The Constitution of India is the supreme law of the country.",
    "when was the constitution adopted": "The Constitution was adopted on 26 November 1949.",
    "when did the constitution come into force": "It came into force on 26 January 1950.",
    "who is known as the father of the indian constitution": "B. R. Ambedkar is known as the Father of the Indian Constitution.",
    "what is the preamble": "The Preamble is the introduction to the Constitution stating its ideals and objectives.",
    "what is secularism": "Secularism means the State treats all religions equally.",
    "what is democracy": "Democracy is a form of government where people elect their representatives.",
    "what are fundamental rights": "Fundamental Rights are basic rights guaranteed under Part III (Articles 12-35) of the Constitution.",
    "which article deals with constitutional remedies": "Article 32 deals with Constitutional Remedies.",
    "what are fundamental duties": "Fundamental Duties are duties of citizens mentioned in Article 51A.",
    "what are directive principles of state policy": "Directive Principles of State Policy are guidelines for the government to establish social and economic justice.",
    "what is federalism": "Federalism is a system where powers are divided between the Centre and States.",
    "how many fundamental rights are there": "There are six Fundamental Rights in India.",
    "what is universal adult franchise": "Universal Adult Franchise gives every citizen aged 18 years or above the right to vote.",
    "who is the head of the indian state": "The President of India is the Head of the State.",
    "what is the role of the prime minister": "The Prime Minister is the head of the government.",
    "what is parliament": "Parliament is the law-making body of India consisting of the President, Lok Sabha, and Rajya Sabha.",
    "difference between lok sabha and rajya sabha": "Lok Sabha is the lower house elected by the people, while Rajya Sabha is the upper house representing the states.",
    "what is judicial review": "Judicial Review is the power of courts to examine laws and declare them unconstitutional.",
    "what is a writ": "A writ is an order issued by a court to protect Fundamental Rights.",
    "what is the importance of article 32": "Article 32 allows citizens to approach the Supreme Court of India for protection of Fundamental Rights.",
    "what is the emergency provision": "Emergency provisions allow the government to take special powers during crises.",
    "what is meant by equality before law": "Equality before Law means all persons are equal in the eyes of law.",
    "what is meant by right to freedom": "Right to Freedom guarantees freedoms such as speech, expression, movement, residence, association, and profession.",
    "why is the indian constitution called the longest written constitution": "The Indian Constitution is called the longest written Constitution because it contains detailed provisions for governance and administration.",
}


def normalize_question(question: str) -> str:
    """Normalize a question so common punctuation/casing still matches."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    return re.sub(r"\s+", " ", normalized).strip()


class ConstitutionVectorDB:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", data_dir: str = "data"):
        self.model_name = model_name
        self.data_dir = data_dir
        self.model = None
        self.index = None
        self.chunks = []
        self.embeddings = None
        
        # Thread safety locks
        self._model_lock = threading.RLock()
        self._search_lock = threading.RLock()
        
        # File paths
        self.index_path = os.path.join(data_dir, "faiss_index.bin")
        self.chunks_path = os.path.join(data_dir, "constitution_chunks.json")
        self.embeddings_path = os.path.join(data_dir, "embeddings.pkl")
        
        self.create_data_directory()
    
    def create_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_embedding_model(self):
        """Load the sentence transformer model (thread-safe)"""
        with self._model_lock:
            if self.model is None:
                try:
                    print(f"Loading embedding model: {self.model_name}")
                    self.model = SentenceTransformer(self.model_name, local_files_only=True)
                    print("Embedding model loaded successfully")
                except Exception as e:
                    self.model = None
                    print(f"Embedding model unavailable; using fast keyword search. Reason: {e}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts (thread-safe)"""
        with self._model_lock:
            if self.model is None:
                self.load_embedding_model()
            
            print(f"Generating embeddings for {len(texts)} texts...")
            embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
            
            print(f"Generated embeddings with shape: {embeddings.shape}")
            return embeddings
    
    def create_faiss_index(self, embeddings: np.ndarray) -> faiss.IndexFlatL2:
        """Create FAISS index from embeddings"""
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        
        print(f"Creating FAISS index with dimension {dimension}")
        index.add(embeddings.astype('float32'))
        
        print(f"FAISS index created with {index.ntotal} vectors")
        return index
    
    def save_index(self, index: faiss.IndexFlatL2):
        """Save FAISS index to disk"""
        faiss.write_index(index, self.index_path)
        print(f"FAISS index saved to {self.index_path}")
    
    def load_index(self) -> faiss.IndexFlatL2:
        """Load FAISS index from disk"""
        if os.path.exists(self.index_path):
            print(f"Loading FAISS index from {self.index_path}")
            index = faiss.read_index(self.index_path)
            print(f"FAISS index loaded with {index.ntotal} vectors")
            return index
        else:
            print("FAISS index not found")
            return None
    
    def save_embeddings(self, embeddings: np.ndarray):
        """Save embeddings to disk"""
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump(embeddings, f)
        print(f"Embeddings saved to {self.embeddings_path}")
    
    def load_embeddings(self) -> np.ndarray:
        """Load embeddings from disk"""
        if os.path.exists(self.embeddings_path):
            print(f"Loading embeddings from {self.embeddings_path}")
            with open(self.embeddings_path, 'rb') as f:
                embeddings = pickle.load(f)
            print(f"Embeddings loaded with shape: {embeddings.shape}")
            return embeddings
        else:
            print("Embeddings not found")
            return None
    
    def build_database(self, chunks: List[Dict[str, Any]], force_rebuild: bool = False):
        """Build the vector database from chunks"""
        self.chunks = chunks
        
        # Check if we can load existing database
        if not force_rebuild and os.path.exists(self.index_path):
            print("Loading existing vector database...")
            self.index = self.load_index()
            
            if self.index is not None and self.index.ntotal == len(chunks):
                print("Vector database loaded successfully")
                return
            print("Cached FAISS index does not match current chunks; rebuilding...")
        
        print("Building new vector database...")
        
        # Extract text from chunks
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        self.embeddings = self.generate_embeddings(texts)
        
        # Create FAISS index
        self.index = self.create_faiss_index(self.embeddings)
        
        # Save to disk
        self.save_index(self.index)
        self.save_embeddings(self.embeddings)
        
        print("Vector database built and saved successfully")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar chunks (thread-safe)"""
        with self._search_lock:
            with self._model_lock:
                if self.model is None:
                    self.load_embedding_model()
                use_embeddings = self.model is not None
            
            if self.index is None:
                print("Vector database not initialized")
                return []
            
            if not use_embeddings:
                return self.keyword_search(query, k=k)
            
            # Generate query embedding
            with self._model_lock:
                query_embedding = self.model.encode([query])
            query_embedding = query_embedding.astype('float32')
            
            # Search in FAISS index
            distances, indices = self.index.search(query_embedding, k)
            
            # Get results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx].copy()
                    chunk['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    results.append((chunk, chunk['similarity_score']))
            
            return results
    
    def keyword_search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Fast offline fallback when the embedding model is not available."""
        query_lower = query.lower()
        tokens = [
            token for token in re.findall(r"[a-z0-9]+", query_lower)
            if len(token) > 2 and token not in {"what", "are", "the", "and", "for", "with", "this", "that", "explain"}
        ]
        article_match = re.search(r"\barticle\s+(\d+[a-z]?)\b", query_lower)
        article_number = article_match.group(1).upper() if article_match else ""
        
        scored = []
        for chunk in self.chunks:
            article = str(chunk.get("article_number", "")).upper()
            text = chunk.get("text", "")
            haystack = f"{article} {text}".lower()
            
            score = 0
            if article_number:
                if article == article_number:
                    score += 100
                if re.search(rf"(^|\s){re.escape(article_number.lower())}\s*[\.\-]", haystack):
                    score += 80
            
            for token in tokens:
                score += haystack.count(token)
            
            if score > 0:
                scored.append((score, chunk))
        
        scored.sort(key=lambda item: item[0], reverse=True)
        return [(chunk.copy(), float(score)) for score, chunk in scored[:k]]
    
    def get_chunk_by_id(self, chunk_id: int) -> Dict[str, Any]:
        """Get a specific chunk by ID"""
        if 0 <= chunk_id < len(self.chunks):
            return self.chunks[chunk_id]
        return None
    
    def get_articles_by_number(self, article_number: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific article number"""
        results = []
        for chunk in self.chunks:
            if chunk.get('article_number', '').upper() == article_number.upper():
                results.append(chunk)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.chunks:
            return {}
        
        # Count different types
        article_types = {}
        for chunk in self.chunks:
            chunk_type = chunk.get('type', 'unknown')
            article_types[chunk_type] = article_types.get(chunk_type, 0) + 1
        
        # Get article numbers
        article_numbers = set()
        for chunk in self.chunks:
            if 'article_number' in chunk:
                article_numbers.add(chunk['article_number'])
        
        return {
            'total_chunks': len(self.chunks),
            'total_articles': len(article_numbers),
            'article_types': article_types,
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else (self.index.d if self.index is not None else None),
            'index_size': self.index.ntotal if self.index is not None else 0
        }

class ConstitutionRAG:
    """Retrieval-Augmented Generation for Constitution Q&A"""
    
    def __init__(self, vector_db: ConstitutionVectorDB):
        self.vector_db = vector_db
        self.context_template = """You are Constitution AI. Give a direct, concise answer to the user's question.
Use the constitutional text below when it is relevant. Do not show your reasoning process. Do not add a sources section.

Constitutional text:
{context}

User question: {question}

Direct answer:
"""
    
    def _article_number_from_query(self, query: str) -> str:
        """Return an exact article number if the user asks for one."""
        match = re.search(r"\barticle\s+(\d+[a-z]?)\b", query, re.IGNORECASE)
        return match.group(1).upper() if match else ""
    
    def get_trusted_answer(self, query: str) -> str:
        """Return a short verified answer for common classroom-style questions."""
        normalized = normalize_question(query)
        if normalized in TRUSTED_QA:
            return TRUSTED_QA[normalized]
        
        # Allow small variants such as "explain democracy" or "define secularism".
        for question, answer in TRUSTED_QA.items():
            topic = question
            for prefix in ("what is ", "what are ", "what is meant by ", "which article deals with "):
                if topic.startswith(prefix):
                    topic = topic[len(prefix):]
                    break
            if topic and topic in normalized and len(normalized.split()) <= len(question.split()) + 3:
                return answer
        
        return ""
    
    def search_relevant_chunks(self, query: str, max_chunks: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """Find relevant chunks, using direct article lookup for common article questions."""
        article_number = self._article_number_from_query(query)
        if article_number:
            article_chunks = []
            found_article = False
            for chunk in self.vector_db.chunks:
                if chunk.get("article_number", "").upper() == article_number:
                    article_chunks.append(chunk)
                    found_article = True
                    if len(article_chunks) >= max_chunks:
                        break
                elif found_article:
                    break
            if article_chunks:
                return [(chunk, 1.0) for chunk in article_chunks]
        
        return self.vector_db.search(query, k=max_chunks)
    
    def retrieve_context(self, query: str, max_chunks: int = 3, search_results: List[Tuple[Dict[str, Any], float]] = None) -> str:
        """Retrieve relevant context for the query"""
        results = search_results or self.search_relevant_chunks(query, max_chunks=max_chunks)
        
        context_parts = []
        for chunk, score in results:
            article_info = f"Article {chunk['article_number']}"
            if 'chunk_number' in chunk:
                article_info += f" (Part {chunk['chunk_number']})"
            
            context_part = f"{article_info}:\n{chunk['text']}"
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def generate_answer_prompt(self, query: str, context: str) -> str:
        """Generate prompt for the LLM"""
        return self.context_template.format(
            context=context,
            question=query
        )
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a complete query"""
        trusted_answer = self.get_trusted_answer(query)
        if trusted_answer:
            return {
                'query': query,
                'context': '',
                'prompt': '',
                'search_results': [],
                'trusted_answer': trusted_answer
            }
        
        search_results = self.search_relevant_chunks(query, max_chunks=3)
        
        # Retrieve relevant context
        context = self.retrieve_context(query, search_results=search_results)
        
        # Generate prompt for LLM
        prompt = self.generate_answer_prompt(query, context)

        return {
            'query': query,
            'context': context,
            'prompt': prompt,
            'search_results': search_results,
            'trusted_answer': ''
        }

if __name__ == "__main__":
    # Test the vector database
    from data_processor import ConstitutionDataProcessor
    
    print("Testing Constitution Vector Database...")
    
    # Process data
    processor = ConstitutionDataProcessor()
    chunks = processor.process_all(use_sample=True)
    
    # Build vector database
    vector_db = ConstitutionVectorDB()
    vector_db.build_database(chunks)
    
    # Test search
    test_queries = [
        "What is Article 21?",
        "What are Fundamental Rights?",
        "Explain Right to Equality",
        "What is the Preamble?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_db.search(query, k=3)
        
        for i, (chunk, score) in enumerate(results):
            print(f"Result {i+1} (Score: {score:.3f}): Article {chunk['article_number']}")
            print(f"Text: {chunk['text'][:100]}...")
    
    # Print statistics
    stats = vector_db.get_statistics()
    print(f"\nDatabase Statistics: {stats}")
