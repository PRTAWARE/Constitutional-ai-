#!/usr/bin/env python3
"""
Constitution AI LAN Server
Share Constitution AI across local network without internet
"""

import flask
from flask import Flask, request, jsonify, render_template_string
import threading
import socket
import json
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import ConstitutionDataProcessor
from vector_database import ConstitutionVectorDB, ConstitutionRAG
from llm_interface import LocalLLMInterface

app = Flask(__name__)

class ConstitutionAILANServer:
    def __init__(self):
        self.data_processor = None
        self.vector_db = None
        self.rag_system = None
        self.llm_interface = None
        self.is_ready = False
        
        self.load_models()
        
    def load_models(self):
        """Load AI models"""
        def load():
            try:
                print("Loading Constitution AI models for LAN sharing...")
                
                self.data_processor = ConstitutionDataProcessor()
                chunks = self.data_processor.load_chunks("real_constitution_chunks.json")
                if not chunks:
                    chunks = self.data_processor.load_chunks("constitution_chunks.json")
                if not chunks:
                    chunks = self.data_processor.process_all(use_sample=False)
                
                self.vector_db = ConstitutionVectorDB()
                self.vector_db.build_database(chunks)
                self.vector_db.load_embedding_model()
                
                self.rag_system = ConstitutionRAG(self.vector_db)
                
                try:
                    self.llm_interface = LocalLLMInterface()
                    if self.llm_interface.setup_model(auto_pull=False):
                        print(f"[OK] Ollama model ready for LAN sharing: {self.llm_interface.model_name}")
                    else:
                        self.llm_interface = None
                        print("[ERROR] Ollama unavailable. Start Ollama and install a model.")
                except Exception as e:
                    self.llm_interface = None
                    print(f"[ERROR] Ollama unavailable: {e}")
                
                self.is_ready = self.llm_interface is not None
                if self.is_ready:
                    print("[OK] Constitution AI ready for LAN access!")
                
            except Exception as e:
                print(f"[ERROR] Error loading models: {e}")
                self.is_ready = False
        
        threading.Thread(target=load, daemon=True).start()
    
    def process_query(self, question):
        """Process a query and return response"""
        if not self.is_ready:
            return {"error": "Ollama is not ready. Start Ollama and install at least one model."}
        
        try:
            # Process query using RAG
            rag_result = self.rag_system.process_query(question)
            
            if rag_result.get('trusted_answer'):
                answer = rag_result['trusted_answer']
            else:
                # Generate LLM response
                answer = self.llm_interface.generate_response(rag_result['prompt'], max_tokens=450)
            
            result = {
                "question": question,
                "answer": answer,
                "model": self.llm_interface.model_name
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Error processing query: {str(e)}"}

# Initialize server
ai_server = ConstitutionAILANServer()

# HTML Template for Web Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Constitution AI - LAN Access</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            display: flex;
            min-height: 600px;
        }
        
        .sidebar {
            width: 350px;
            background: #f8f9fa;
            padding: 30px;
            border-right: 1px solid #e9ecef;
        }
        
        .content {
            flex: 1;
            padding: 30px;
        }
        
        .question-section {
            margin-bottom: 30px;
        }
        
        .question-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        #questionInput {
            width: 100%;
            height: 120px;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
            font-family: inherit;
        }
        
        #questionInput:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .quick-questions {
            margin-top: 30px;
        }
        
        .quick-questions h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .quick-question {
            display: block;
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: left;
            font-size: 14px;
        }
        
        .quick-question:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .answer-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            min-height: 300px;
        }
        
        .answer-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        #answerDisplay {
            background: white;
            padding: 20px;
            border-radius: 8px;
            min-height: 200px;
            line-height: 1.6;
            font-size: 16px;
            white-space: pre-wrap;
        }
        
        .sources {
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 8px;
        }
        
        .sources h4 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .source-item {
            margin-bottom: 8px;
            padding: 8px;
            background: white;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .loading {
            text-align: center;
            color: #667eea;
            font-style: italic;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #f5c6cb;
        }
        
        .status {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #c3e6cb;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e9ecef;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇮🇳 Constitution AI</h1>
            <p>Indian Constitution Q&A - LAN Access</p>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <div class="server-info">
                    <strong>🌐 LAN Access Active</strong><br>
                    Share this URL with other devices on your network:<br>
                    <code id="serverUrl"></code>
                </div>
                
                <div class="status" id="status">
                    🔄 Loading AI models...
                </div>
                
                <div class="question-section">
                    <h3>Ask Your Question</h3>
                    <textarea id="questionInput" placeholder="Type your question about the Indian Constitution here..."></textarea>
                    <div class="button-group">
                        <button class="btn btn-primary" onclick="askQuestion()">🤖 Ask AI</button>
                        <button class="btn btn-secondary" onclick="clearAnswer()">Clear</button>
                    </div>
                </div>
                
                <div class="quick-questions">
                    <h3>⚡ Quick Questions</h3>
                    <button class="quick-question" onclick="setQuestion('What is Article 21?')">What is Article 21?</button>
                    <button class="quick-question" onclick="setQuestion('What are Fundamental Rights?')">What are Fundamental Rights?</button>
                    <button class="quick-question" onclick="setQuestion('Explain Right to Equality')">Explain Right to Equality</button>
                    <button class="quick-question" onclick="setQuestion('What is the Preamble?')">What is the Preamble?</button>
                    <button class="quick-question" onclick="setQuestion('Emergency provisions')">Emergency provisions</button>
                </div>
            </div>
            
            <div class="content">
                <div class="answer-section">
                    <h3>🤖 AI Answer</h3>
                    <div id="answerDisplay">Ask a question about the Indian Constitution to get started...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Get server URL
        document.getElementById('serverUrl').textContent = window.location.href;
        
        // Check server status
        function checkStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    
                    if (data.ready) {
                        statusEl.innerHTML = '✅ Constitution AI Ready<br>Model: ' + data.model;
                        statusEl.className = 'status';
                    } else {
                        statusEl.innerHTML = '🔄 Loading AI models...';
                        statusEl.className = 'status';
                    }
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '❌ Server Error';
                    document.getElementById('status').className = 'error';
                });
        }
        
        // Set question in input
        function setQuestion(question) {
            document.getElementById('questionInput').value = question;
        }
        
        // Clear answer
        function clearAnswer() {
            document.getElementById('answerDisplay').innerHTML = 'Ask a question about the Indian Constitution to get started...';
        }
        
        // Ask question
        function askQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) {
                alert('Please enter a question!');
                return;
            }
            
            const answerDisplay = document.getElementById('answerDisplay');
            answerDisplay.innerHTML = '<div class="loading">🤖 Processing... Please wait...</div>';
            
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    answerDisplay.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                } else {
                    answerDisplay.textContent = data.answer;
                }
            })
            .catch(error => {
                answerDisplay.innerHTML = `<div class="error">❌ Network Error: ${error.message}</div>`;
            });
        }
        
        // Check status on load and every 5 seconds
        checkStatus();
        setInterval(checkStatus, 5000);
        
        // Allow Enter key to submit (with Shift+Enter for new line)
        document.getElementById('questionInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """Check server status"""
    return jsonify({
        'ready': ai_server.is_ready,
        'model': ai_server.llm_interface.model_name if ai_server.llm_interface else 'Loading...'
    })

@app.route('/ask', methods=['POST'])
def ask():
    """Process a question"""
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    question = data['question'].strip()
    if not question:
        return jsonify({'error': 'Empty question'}), 400
    
    result = ai_server.process_query(question)
    return jsonify(result)

def get_local_ip():
    """Get local IP address for LAN access"""
    try:
        # Connect to an external host to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    """Start the LAN server"""
    import sys
    
    # Fix Unicode encoding for Windows console
    if sys.platform == 'win32':
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    
    local_ip = get_local_ip()
    port = 5000
    
    print("=" * 60)
    print("CONSTITUTION AI LAN SERVER")
    print("=" * 60)
    print(f"Server starting on: http://{local_ip}:{port}")
    print(f"Local access: http://localhost:{port}")
    print(f"Network access: http://{local_ip}:{port}")
    print(f"Share the Network URL with other devices on your LAN")
    print("=" * 60)
    print("Loading AI models...")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    main()
