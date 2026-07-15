"""
Constitution Data Processor
Handles downloading, cleaning, and chunking of Indian Constitution data
"""

import os
import json
import re
import requests
import PyPDF2
from typing import List, Dict, Any
import pandas as pd

class ConstitutionDataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.create_data_directory()
        
    def create_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def download_constitution_pdf(self, url: str = None) -> str:
        """Get Indian Constitution PDF - use existing file in project root"""
        # First check if PDF exists in project root
        root_pdf_path = "constitution_of_india.pdf"
        if os.path.exists(root_pdf_path):
            print(f"Using existing PDF at {root_pdf_path}")
            return root_pdf_path
        
        # Check if PDF exists in data directory
        pdf_path = os.path.join(self.data_dir, "constitution_of_india.pdf")
        if os.path.exists(pdf_path):
            print(f"PDF already exists at {pdf_path}")
            return pdf_path
        
        # If not found anywhere, download it
        if url is None:
            # Official Constitution of India PDF URL
            url = "https://legislative.gov.in/sites/default/files/Constitution%20of%20India.pdf"
        
        try:
            print("Downloading Constitution of India PDF...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded successfully to {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Failed to download PDF: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            print("Extracting text from PDF...")
            text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            print(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'CONSTITUTION OF INDIA', '', text)
        
        # Fix common OCR errors
        text = text.replace('â€"', '"')
        text = text.replace('â€"', '"')
        text = text.replace('â€"', "'")
        
        return text.strip()
    
    def extract_articles(self, text: str) -> List[Dict[str, Any]]:
        """Extract individual articles from the constitution text"""
        articles = []
        
        # The official PDF uses headings like:
        # "21. Protection of life and personal liberty. -No person shall..."
        # Older versions of this app looked for "Article 21", which mostly
        # captured the table of contents instead of the article body.
        article_pattern = (
            r'(?:\d+\[)?'
            r'(\d+[A-Z]?)\.\s+'
            r'([A-Z][^.]{3,180}?\.)\s*'
            r'(?:—|-)'
            r'(.*?)'
            r'(?=(?:\s+\d+\[)?\d+[A-Z]?\.\s+[A-Z][^.]{3,180}?\.\s*(?:—|-)|$)'
        )
        
        matches = re.findall(article_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for article_num, article_title, article_text in matches:
            # Clean article text
            article_text = re.sub(r'\s+', ' ', f"{article_title} {article_text}").strip()
            
            if len(article_text) > 50:  # Filter out very short matches
                articles.append({
                    'article_number': article_num.upper(),
                    'text': article_text,
                    'type': 'article',
                    'source': 'constitution_of_india'
                })
        
        print(f"Extracted {len(articles)} articles")
        return articles
    
    def extract_preamble(self, text: str) -> Dict[str, Any]:
        """Extract the Preamble"""
        preamble_pattern = r'PREAMBLE\s*(.*?)(?=Article\s+\d+|$)'
        match = re.search(preamble_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            preamble_text = re.sub(r'\s+', ' ', match.group(1)).strip()
            return {
                'article_number': 'PREAMBLE',
                'text': preamble_text,
                'type': 'preamble',
                'source': 'constitution_of_india'
            }
        
        return None
    
    def create_sample_data(self) -> List[Dict[str, Any]]:
        """Create sample constitution data for testing"""
        sample_articles = [
            {
                'article_number': 'PREAMBLE',
                'text': 'WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC and to secure to all its citizens: JUSTICE, social, economic and political; LIBERTY of thought, expression, belief, faith and worship; EQUALITY of status and of opportunity; and to promote among them all FRATERNITY assuring the dignity of the individual and the unity and integrity of the Nation;',
                'type': 'preamble',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '14',
                'text': 'Equality before law. The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India.',
                'type': 'article',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '15',
                'text': 'Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth. The State shall not discriminate against any citizen on grounds only of religion, race, caste, sex, place of birth or any of them.',
                'type': 'article',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '19',
                'text': 'Protection of certain rights regarding freedom of speech, etc. All citizens shall have the right to freedom of speech and expression; to assemble peaceably and without arms; to form associations or unions; to move freely throughout the territory of India; to reside and settle in any part of the territory of India; to practice any profession, or to carry on any occupation, trade or business.',
                'type': 'article',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '21',
                'text': 'Protection of life and personal liberty. No person shall be deprived of his life or personal liberty except according to procedure established by law.',
                'type': 'article',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '21A',
                'text': 'Right to education. The State shall provide free and compulsory education to all children of the age of six to fourteen years in such manner as the State may, by law, determine.',
                'type': 'article',
                'source': 'constitution_of_india'
            },
            {
                'article_number': '51A',
                'text': 'Fundamental duties. It shall be the duty of every citizen of India to abide by the Constitution and respect its ideals and institutions; to cherish and follow the noble ideals which inspired our national struggle for freedom; to uphold and protect the sovereignty, unity and integrity of India; to defend the country and render national service when called upon to do so.',
                'type': 'article',
                'source': 'constitution_of_india'
            }
        ]
        
        return sample_articles
    
    def chunk_articles(self, articles: List[Dict[str, Any]], chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Split long articles into smaller chunks"""
        chunks = []
        
        for article in articles:
            text = article['text']
            
            if len(text) <= chunk_size:
                chunks.append(article)
            else:
                # Split long text into chunks
                words = text.split()
                current_chunk = ""
                chunk_num = 1
                
                for word in words:
                    if len(current_chunk + " " + word) <= chunk_size:
                        current_chunk += " " + word if current_chunk else word
                    else:
                        if current_chunk:
                            chunk = article.copy()
                            chunk['text'] = current_chunk
                            chunk['chunk_number'] = chunk_num
                            chunks.append(chunk)
                            chunk_num += 1
                            current_chunk = word
                
                # Add remaining text
                if current_chunk:
                    chunk = article.copy()
                    chunk['text'] = current_chunk
                    chunk['chunk_number'] = chunk_num
                    chunks.append(chunk)
        
        print(f"Created {len(chunks)} chunks from {len(articles)} articles")
        return chunks
    
    def save_chunks(self, chunks: List[Dict[str, Any]], filename: str = "constitution_chunks.json"):
        """Save chunks to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(chunks)} chunks to {filepath}")
        return filepath
    
    def load_chunks(self, filename: str = "constitution_chunks.json") -> List[Dict[str, Any]]:
        """Load chunks from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"Loaded {len(chunks)} chunks from {filepath}")
        return chunks
    
    def process_all(self, use_sample: bool = True) -> List[Dict[str, Any]]:
        """Complete processing pipeline"""
        if use_sample:
            print("Using sample constitution data...")
            articles = self.create_sample_data()
        else:
            # Download and process actual PDF
            pdf_path = self.download_constitution_pdf()
            if not pdf_path:
                print("Failed to download PDF, using sample data...")
                articles = self.create_sample_data()
            else:
                text = self.extract_text_from_pdf(pdf_path)
                if not text:
                    print("Failed to extract text, using sample data...")
                    articles = self.create_sample_data()
                else:
                    clean_text = self.clean_text(text)
                    articles = []
                    
                    # Extract preamble
                    preamble = self.extract_preamble(clean_text)
                    if preamble:
                        articles.append(preamble)
                    
                    # Extract articles
                    extracted_articles = self.extract_articles(clean_text)
                    articles.extend(extracted_articles)
                    
                    if not articles:
                        print("No articles found, using sample data...")
                        articles = self.create_sample_data()
        
        # Chunk the articles
        chunks = self.chunk_articles(articles)
        
        # Save chunks
        self.save_chunks(chunks)
        
        return chunks

if __name__ == "__main__":
    processor = ConstitutionDataProcessor()
    chunks = processor.process_all(use_sample=True)
    print(f"Processing complete. Generated {len(chunks)} chunks.")
