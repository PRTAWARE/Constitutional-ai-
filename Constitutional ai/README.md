# Constitution AI

Constitution AI is a local Python application for asking questions about the Constitution of India. It combines extracted Constitution text, semantic search with FAISS, and a local Ollama model to answer questions offline. The project includes both a desktop Tkinter app and a Flask LAN server for sharing the app on a local network.

## Features

- Offline Constitution Q&A using local data
- FAISS semantic search over Constitution chunks
- Ollama-based local LLM responses
- Desktop GUI with question history, favorites, export, and learning tools
- LAN web server for access from phones or other computers on the same network
- PDF processing script for rebuilding Constitution data

## Project Structure

```text
.
├── main.py                    # Main desktop GUI
├── lan_server.py              # Flask LAN/web server
├── data_processor.py          # PDF extraction and chunking
├── vector_database.py         # FAISS search and RAG prompt builder
├── llm_interface.py           # Ollama integration
├── process_real_pdf.py        # Rebuild data from the Constitution PDF
├── constitution_of_india.pdf  # Source document
├── data/                      # JSON chunks kept; indexes are generated locally
├── requirements.txt
└── docs/guides in markdown
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install Python dependencies.

```bash
pip install -r requirements.txt
```

3. Install Ollama from <https://ollama.com> and pull a model.

```bash
ollama pull llama3:8b
```

The app can also use other local Ollama models if configured in `llm_interface.py`.

## Run The Desktop App

```bash
python main.py
```

## Run The LAN Server

```bash
python lan_server.py
```

Then open:

```text
http://localhost:5000
```

Other devices on the same network can open the LAN URL printed by the server, for example:

```text
http://192.168.x.x:5000
```

## Rebuild Data

The repository keeps JSON Constitution chunks for convenience. FAISS indexes and embedding cache files are ignored because they are generated locally.

To rebuild the processed data:

```bash
python process_real_pdf.py
```

If indexes are missing, the app can rebuild them from the JSON chunks.

## GitHub Notes

The following files are intentionally ignored:

- `__pycache__/` and Python bytecode
- `*.log`
- `user_data.json`, because it stores local history and favorites
- `data/*.pkl` and `data/*.bin`, because they are generated vector indexes and embeddings

## Disclaimer

This project is for educational use. Verify important constitutional or legal information with official sources or qualified professionals.
