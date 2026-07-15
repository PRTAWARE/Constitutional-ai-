"""
Local LLM Interface
Handles communication with local LLM (Ollama) for answer generation
"""

import os
import requests
import json
import subprocess
import time
from typing import Dict, Any, Optional
import threading

class LocalLLMInterface:
    def __init__(self, model_name: str = "llama3:8b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.is_available = False
        self.available_models = []
        self.check_ollama_status()
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=1.5)
            if response.status_code == 200:
                self.is_available = True
                print(f"Ollama is available at {self.ollama_url}")
                
                # Check if model is available
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                self.available_models = model_names
                
                if self.model_name in model_names:
                    print(f"Model '{self.model_name}' is available")
                    return True
                else:
                    print(f"Model '{self.model_name}' not found. Available models: {model_names}")
                    return False
            else:
                self.is_available = False
                return False
                
        except requests.exceptions.RequestException:
            self.is_available = False
            print("Ollama is not running or not accessible")
            return False
    
    def install_ollama(self) -> bool:
        """Install Ollama (platform-specific)"""
        try:
            print("Installing Ollama...")
            
            # For Windows
            if os.name == 'nt':
                # Download and install Ollama for Windows
                install_url = "https://ollama.ai/download/OllamaSetup.exe"
                print(f"Please download and install Ollama from: {install_url}")
                print("After installation, restart this application.")
                return False
            else:
                # For Linux/Mac
                subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], check=True)
                return True
                
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            return False
    
    def pull_model(self, model_name: str = None) -> bool:
        """Pull a model from Ollama"""
        if not self.is_available:
            if not self.check_ollama_status():
                print("Ollama is not available. Please install and start Ollama first.")
                return False
        
        model = model_name or self.model_name
        
        try:
            print(f"Pulling model '{model}' from Ollama...")
            
            # Run ollama pull command
            process = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Check if pull was successful
            if process.returncode == 0:
                print(f"Model '{model}' pulled successfully")
                return True
            else:
                error = process.stderr.read()
                print(f"Failed to pull model: {error}")
                return False
                
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
    
    def start_ollama(self) -> bool:
        """Start Ollama service"""
        try:
            print("Starting Ollama service...")
            
            # Start ollama serve in background
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for Ollama to start
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                if self.check_ollama_status():
                    print("Ollama service started successfully")
                    return True
            
            print("Failed to start Ollama service")
            return False
            
        except Exception as e:
            print(f"Error starting Ollama: {e}")
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 450, temperature: float = 0.2) -> str:
        """Generate response from local LLM"""
        if not self.is_available:
            if not self.check_ollama_status():
                return "Error: Ollama is not available. Please install and start Ollama first."
        
        try:
            url = f"{self.ollama_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 2048
                }
            }
            
            response = requests.post(url, json=payload, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"Error: Ollama returned status {response.status_code}. {response.text[:300]}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model might be processing a large request."
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_response_stream(self, prompt: str, max_tokens: int = 450, temperature: float = 0.2):
        """Generate streaming response from local LLM"""
        if not self.is_available:
            if not self.check_ollama_status():
                yield "Error: Ollama is not available. Please install and start Ollama first."
                return
        
        try:
            url = f"{self.ollama_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True,
                "keep_alive": "10m",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 2048
                }
            }
            
            response = requests.post(url, json=payload, stream=True, timeout=60)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"Error: LLM API returned status {response.status_code}"
                
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def setup_model(self, model_name: str = None, auto_pull: bool = True) -> bool:
        """Setup the model (check availability, pull if needed)"""
        if model_name:
            self.model_name = model_name
        model = self.model_name
        
        # Check if Ollama is running
        if not self.check_ollama_status():
            print("Attempting to start Ollama...")
            if not self.start_ollama():
                print("Please start Ollama manually by running: ollama serve")
                return False
        
        # Check if model is available. If the preferred model is missing,
        # use the first installed Ollama model so answers still come from Ollama.
        if not self.check_ollama_status():
            if self.is_available and self.available_models:
                self.model_name = self.available_models[0]
                print(f"Using installed Ollama model: {self.model_name}")
                return True
            return False
        
        # Pull model if needed
        if auto_pull:
            print(f"Checking model availability: {model}")
            if not self.pull_model(model):
                return False
        
        return True

class MockLLMInterface:
    """Mock LLM interface for testing without Ollama"""
    
    def __init__(self):
        self.is_available = True
        self.model_name = "mock"
    
    def generate_response(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate mock response"""
        
        # Extract question from prompt
        if "question:" in prompt.lower():
            question_start = prompt.lower().find("question:") + 9
            question = prompt[question_start:].strip().strip('"')
        else:
            question = "the constitutional question"
        
        # Generate contextual response based on common patterns
        responses = {
            "article 21": "Article 21 of the Indian Constitution states that 'No person shall be deprived of his life or personal liberty except according to procedure established by law.' This is a fundamental right that protects the right to life and personal liberty of all individuals.",
            "fundamental rights": "Fundamental Rights are enshrined in Part III of the Indian Constitution (Articles 12-35). These include Right to Equality, Right to Freedom, Right against Exploitation, Right to Freedom of Religion, Cultural and Educational Rights, and Right to Constitutional Remedies.",
            "equality": "The Right to Equality is guaranteed under Articles 14-18 of the Indian Constitution. Article 14 ensures equality before law and equal protection of laws, while Article 15 prohibits discrimination on grounds of religion, race, caste, sex, or place of birth.",
            "preamble": "The Preamble of the Indian Constitution declares India as a 'SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC' and outlines the objectives of securing JUSTICE, LIBERTY, EQUALITY, and FRATERNITY for all citizens.",
            "education": "Article 21A of the Indian Constitution provides for the Right to Education, stating that 'The State shall provide free and compulsory education to all children of the age of six to fourteen years.'"
        }
        
        # Check for keywords in the question
        question_lower = question.lower()
        for keyword, response in responses.items():
            if keyword in question_lower:
                return f"""Answer to: {question}

{response}

Related Constitutional Provisions:
- This right is enforceable under Article 32 and 226 of the Constitution
- The Supreme Court has expanded its interpretation through various judgments
- It forms part of the basic structure of the Constitution

Source: Constitution of India

This answer is based on constitutional provisions and judicial interpretations. For legal matters, please consult with qualified legal professionals.
"""
        
        # Default response
        return f"""Book Answer to: {question}

Based on the Indian Constitution, this question relates to important constitutional provisions. The specific answer would depend on the exact constitutional article or principle being referenced.

Key Points:
- The Constitution provides comprehensive framework for governance
- Fundamental Rights are enforceable in courts of law
- Directive Principles guide state policy
- The Preamble outlines the basic philosophy

Recommendation:
Please refer to the specific article or section of the Constitution for detailed information. You may also consult legal commentaries or seek professional legal advice for specific cases.

Search Strategy:
Look for relevant articles in Parts III (Fundamental Rights), IV (Directive Principles), or other relevant sections based on your specific question.

This is a general response. For specific legal queries, please consult constitutional experts or legal professionals.
"""
    
    def generate_response_fast(self, prompt: str) -> str:
        """Generate fast response (alias for generate_response)"""
        return self.generate_response(prompt)
    
    def generate_response_stream(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7):
        """Generate streaming mock response"""
        response = self.generate_response(prompt, max_tokens, temperature)
        for word in response.split():
            yield word + " "
            time.sleep(0.05)  # Simulate streaming delay
    
    def setup_model(self, model_name: str = None, auto_pull: bool = True) -> bool:
        """Setup mock model"""
        return True

if __name__ == "__main__":
    # Test the LLM interface
    print("Testing Local LLM Interface...")
    
    # Try to use real LLM first, fall back to mock
    try:
        llm = LocalLLMInterface()
        if not llm.setup_model():
            print("Using mock LLM for testing...")
            llm = MockLLMInterface()
    except:
        print("Using mock LLM for testing...")
        llm = MockLLMInterface()
    
    # Test response generation
    test_prompt = """Based on the Indian Constitution, here are the relevant articles:

Article 21: Protection of life and personal liberty. No person shall be deprived of his life or personal liberty except according to procedure established by law.

Please answer the question: "What is Article 21?"

Provide a clear, informative answer based on the constitutional text above."""
    
    print("Generating response...")
    response = llm.generate_response(test_prompt)
    print(f"Response: {response}")
