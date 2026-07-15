#!/usr/bin/env python3
"""
Process Real Constitution PDF
Extract and process the actual Constitution of India PDF for local AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import ConstitutionDataProcessor
from vector_database import ConstitutionVectorDB, ConstitutionRAG
import json

def process_real_constitution():
    """Process the actual Constitution of India PDF"""
    
    print("=" * 80)
    print("PROCESSING REAL CONSTITUTION OF INDIA PDF")
    print("=" * 80)
    
    # Initialize data processor
    processor = ConstitutionDataProcessor()
    
    # Check if PDF exists
    pdf_path = "constitution_of_india.pdf"
    if os.path.exists(pdf_path):
        print(f"[OK] Found Constitution PDF: {pdf_path}")
    else:
        print(f"[ERROR] PDF not found: {pdf_path}")
        print("Please ensure constitution_of_india.pdf is in the current directory")
        return False
    
    # Process the PDF
    print("\n1. Extracting text from PDF...")
    try:
        text = processor.extract_text_from_pdf(pdf_path)
        if not text:
            print("[ERROR] Failed to extract text from PDF")
            return False
        print(f"[OK] Extracted {len(text)} characters from PDF")
    except Exception as e:
        print(f"[ERROR] Error extracting PDF: {e}")
        return False
    
    # Clean the text
    print("\n2. Cleaning extracted text...")
    try:
        clean_text = processor.clean_text(text)
        print(f"[OK] Cleaned text to {len(clean_text)} characters")
    except Exception as e:
        print(f"[ERROR] Error cleaning text: {e}")
        return False
    
    # Extract articles
    print("\n3. Extracting constitutional articles...")
    try:
        articles = []
        
        # Extract preamble
        preamble = processor.extract_preamble(clean_text)
        if preamble:
            articles.append(preamble)
            print(f"[OK] Found Preamble")
        
        # Extract articles
        extracted_articles = processor.extract_articles(clean_text)
        articles.extend(extracted_articles)
        print(f"[OK] Extracted {len(extracted_articles)} articles")
        
        if not articles:
            print("[ERROR] No articles found in the text")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error extracting articles: {e}")
        return False
    
    # Create chunks
    print("\n4. Creating chunks for vector database...")
    try:
        chunks = processor.chunk_articles(articles, chunk_size=800)
        print(f"[OK] Created {len(chunks)} chunks")
        
        # Save chunks
        chunk_file = processor.save_chunks(chunks, "real_constitution_chunks.json")
        print(f"[OK] Saved chunks to {chunk_file}")
        
    except Exception as e:
        print(f"[ERROR] Error creating chunks: {e}")
        return False
    
    # Build vector database
    print("\n5. Building vector database...")
    try:
        vector_db = ConstitutionVectorDB()
        vector_db.build_database(chunks, force_rebuild=True)
        
        stats = vector_db.get_statistics()
        print(f"[OK] Built vector database:")
        print(f"   - Total chunks: {stats['total_chunks']}")
        print(f"   - Total articles: {stats['total_articles']}")
        print(f"   - Article types: {stats['article_types']}")
        print(f"   - Embedding dimension: {stats['embedding_dimension']}")
        
    except Exception as e:
        print(f"[ERROR] Error building vector database: {e}")
        return False
    
    # Test search functionality
    print("\n6. Testing search functionality...")
    try:
        test_queries = [
            "Article 21",
            "Fundamental Rights",
            "Right to Equality",
            "Preamble",
            "Emergency provisions"
        ]
        
        for query in test_queries:
            results = vector_db.search(query, k=3)
            print(f"   Query: '{query}' -> Found {len(results)} results")
            
    except Exception as e:
        print(f"[ERROR] Error testing search: {e}")
        return False
    
    # Initialize RAG system
    print("\n7. Initializing RAG system...")
    try:
        rag = ConstitutionRAG(vector_db)
        print("[OK] RAG system ready")
        
        # Test query
        test_result = rag.process_query("What is Article 21?")
        print(f"[OK] Query test successful")
        print(f"   - Context sources: {len(test_result['search_results'])}")
        
    except Exception as e:
        print(f"[ERROR] Error with RAG: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("[OK] REAL CONSTITUTION PDF PROCESSING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nYour system is now ready with:")
    print("• Real Constitution of India data")
    print("• Vector database with semantic search")
    print("• RAG system for constitutional analysis")
    print("• Complete offline capability")
    print("\nYou can now run: python main.py")
    
    return True

if __name__ == "__main__":
    success = process_real_constitution()
    if not success:
        print("\n[ERROR] Processing failed. Please check the error messages above.")
        sys.exit(1)
