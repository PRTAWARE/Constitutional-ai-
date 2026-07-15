#!/usr/bin/env python3
"""
Constitution AI - Offline Indian Constitution Q&A App
Author: Prathamesh
VIT Pune Software Engineering
"""

import html
import json
import os
import random
import re
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ImportError:
    letter = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None

from data_processor import ConstitutionDataProcessor
from llm_interface import LocalLLMInterface
from vector_database import ConstitutionRAG, ConstitutionVectorDB


class ConstitutionAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Constitution AI - Enhanced Version")
        self.root.geometry("1180x760")

        self.themes = {
            "light": {
                "bg": "#f6f8fc",
                "title_bg": "#ffffff",
                "title_fg": "#111827",
                "nav_bg": "#ffffff",
                "card_bg": "#ffffff",
                "border": "#d9e2ef",
                "muted_fg": "#566176",
                "text_bg": "white",
                "fg": "#17202a",
                "label_fg": "#17202a",
                "button_bg": "#1f5fd0",
                "button_fg": "white",
                "active_bg": "#eaf2ff",
                "accent_bg": "#f59e0b",
                "danger_bg": "#b42318",
                "quick_button_bg": "#f8fafc",
                "quick_button_fg": "#1f2937",
                "status_bg": "#edf4ff",
            },
            "dark": {
                "bg": "#111827",
                "title_bg": "#0b1220",
                "title_fg": "#eef5ff",
                "nav_bg": "#0b1220",
                "card_bg": "#151f2f",
                "border": "#2f3b52",
                "muted_fg": "#aab5c6",
                "text_bg": "#0f172a",
                "fg": "#e5e7eb",
                "label_fg": "#e5e7eb",
                "button_bg": "#2563eb",
                "button_fg": "white",
                "active_bg": "#182a4a",
                "accent_bg": "#f59e0b",
                "danger_bg": "#b91c1c",
                "quick_button_bg": "#1f2937",
                "quick_button_fg": "#e5e7eb",
                "status_bg": "#111827",
            },
        }

        self.translations = {
            "en": {
                "language": "Language:",
                "question": "Ask your question:",
                "answer": "AI Answer:",
                "ask": "Ask Question",
                "theme_light": "Light",
                "theme_dark": "Dark",
                "export": "Export PDF",
                "favorites": "Favorites",
                "compare": "Compare",
                "progress": "Progress",
                "practice": "Practice",
                "quiz": "Quiz",
                "add_favorite": "Add to Favorites",
                "quick": "Quick Questions:",
                "ready_loading": "Ready - Loading models...",
                "ready": "Ready",
                "thinking": "Thinking...",
                "question_required": "Please enter a question!",
                "no_answer": "No answer to export.",
                "no_qa": "No Q&A to add to favorites.",
            },
            "hi": {
                "language": "भाषा:",
                "question": "अपना प्रश्न पूछिए:",
                "answer": "AI उत्तर:",
                "ask": "प्रश्न पूछें",
                "theme_light": "Light",
                "theme_dark": "Dark",
                "export": "PDF Export",
                "favorites": "पसंदीदा",
                "compare": "तुलना",
                "progress": "प्रगति",
                "practice": "Practice",
                "quiz": "Quiz",
                "add_favorite": "पसंदीदा में जोड़ें",
                "quick": "त्वरित प्रश्न:",
                "ready_loading": "तैयार - मॉडल लोड हो रहे हैं...",
                "ready": "तैयार",
                "thinking": "सोच रहा है...",
                "question_required": "कृपया प्रश्न लिखिए!",
                "no_answer": "Export करने के लिए कोई उत्तर नहीं है.",
                "no_qa": "पसंदीदा में जोड़ने के लिए Q&A नहीं है.",
            },
        }

        self.data_processor = None
        self.vector_db = None
        self.rag_system = None
        self.llm_interface = None
        self.quick_question_buttons = []
        self.quick_questions = {
            "en": [
                "What is Article 21?",
                "What are Fundamental Rights?",
                "Explain Right to Equality",
                "What is Preamble?",
                "Fundamental Duties",
            ],
            "hi": [
                "Article 21 क्या है?",
                "Fundamental Rights क्या हैं?",
                "Right to Equality समझाइए",
                "Preamble क्या है?",
                "Fundamental Duties",
            ],
        }
        self.practice_questions = [
            "Explain the importance of Article 14.",
            "What protections are given under Article 21?",
            "Compare Fundamental Rights and Directive Principles.",
            "Why is the Preamble important?",
            "Explain the Right to Freedom under Article 19.",
            "What are the Fundamental Duties under Article 51A?",
            "What is the role of Article 32?",
            "Explain the idea of secularism in the Constitution.",
            "What does equality before law mean?",
            "How does the Constitution protect minorities?",
            "What is the difference between Lok Sabha and Rajya Sabha?",
            "Explain the federal structure of India.",
            "What are Directive Principles of State Policy?",
            "How is the President of India elected?",
            "What is judicial review?",
            "Explain emergency provisions in simple words.",
        ]
        self.quiz_bank = [
            {
                "question": "Which Article protects life and personal liberty?",
                "options": ["Article 14", "Article 19", "Article 21", "Article 32"],
                "answer": "Article 21",
            },
            {
                "question": "Fundamental Rights are mainly found in which part of the Constitution?",
                "options": ["Part II", "Part III", "Part IV", "Part IVA"],
                "answer": "Part III",
            },
            {
                "question": "Which Article is known for constitutional remedies?",
                "options": ["Article 15", "Article 21", "Article 32", "Article 51A"],
                "answer": "Article 32",
            },
            {
                "question": "Fundamental Duties are mentioned in which Article?",
                "options": ["Article 14", "Article 19", "Article 21A", "Article 51A"],
                "answer": "Article 51A",
            },
            {
                "question": "Which Article provides equality before law?",
                "options": ["Article 14", "Article 15", "Article 16", "Article 17"],
                "answer": "Article 14",
            },
            {
                "question": "Right to Education is provided under which Article?",
                "options": ["Article 19", "Article 21", "Article 21A", "Article 32"],
                "answer": "Article 21A",
            },
            {
                "question": "Directive Principles of State Policy are mainly in which part?",
                "options": ["Part III", "Part IV", "Part IVA", "Part V"],
                "answer": "Part IV",
            },
            {
                "question": "Which word in the Preamble shows India has no official state religion?",
                "options": ["Sovereign", "Socialist", "Secular", "Republic"],
                "answer": "Secular",
            },
            {
                "question": "Which Article abolishes untouchability?",
                "options": ["Article 15", "Article 16", "Article 17", "Article 18"],
                "answer": "Article 17",
            },
            {
                "question": "Who is the head of the Indian Union executive?",
                "options": ["Prime Minister", "President", "Chief Justice", "Speaker"],
                "answer": "President",
            },
            {
                "question": "Which house is known as the Council of States?",
                "options": ["Lok Sabha", "Rajya Sabha", "Vidhan Sabha", "Gram Sabha"],
                "answer": "Rajya Sabha",
            },
            {
                "question": "The Constitution of India came into force on which date?",
                "options": ["15 August 1947", "26 November 1949", "26 January 1950", "2 October 1950"],
                "answer": "26 January 1950",
            },
            {
                "question": "Which body interprets the Constitution at the national level?",
                "options": ["Election Commission", "Supreme Court", "Parliament Secretariat", "NITI Aayog"],
                "answer": "Supreme Court",
            },
            {
                "question": "Which Article prohibits discrimination on certain grounds?",
                "options": ["Article 14", "Article 15", "Article 18", "Article 20"],
                "answer": "Article 15",
            },
            {
                "question": "India is described as what type of state in the Preamble?",
                "options": ["Monarchy", "Sovereign socialist secular democratic republic", "Military state", "Confederation"],
                "answer": "Sovereign socialist secular democratic republic",
            },
        ]
        self.theme_widgets = []
        self.last_answer = ""

        self.user_data = {
            "favorites": [],
            "history": [],
            "quiz_results": [],
            "preferences": {"language": "en", "theme": "light"},
        }
        self.load_user_data()

        self.language = self.user_data.get("preferences", {}).get("language", "en")
        self.theme_name = self.user_data.get("preferences", {}).get("theme", "light")
        if self.language not in self.translations:
            self.language = "en"
        if self.theme_name not in self.themes:
            self.theme_name = "light"
        self.current_theme = self.themes[self.theme_name]
        self.root.configure(bg=self.current_theme["bg"])

        self.setup_ui()
        self.apply_language()
        self.load_models()

    def t(self, key):
        return self.translations.get(self.language, self.translations["en"]).get(key, key)

    def load_user_data(self):
        try:
            if os.path.exists("user_data.json"):
                with open("user_data.json", "r", encoding="utf-8") as file:
                    saved = json.load(file)
                self.user_data.update(saved)
                self.user_data.setdefault("favorites", [])
                self.user_data.setdefault("history", [])
                self.user_data.setdefault("quiz_results", [])
                self.user_data.setdefault("preferences", {})
        except Exception:
            self.user_data = {"favorites": [], "history": [], "quiz_results": [], "preferences": {}}

    def save_user_data(self):
        self.user_data.setdefault("preferences", {})
        self.user_data["preferences"]["language"] = self.language
        self.user_data["preferences"]["theme"] = self.theme_name
        try:
            with open("user_data.json", "w", encoding="utf-8") as file:
                json.dump(self.user_data, file, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.status_var.set(f"Could not save user data: {exc}")

    def setup_ui(self):
        self.nav_buttons = []
        self.title_frame = tk.Frame(self.root, bg=self.current_theme["nav_bg"], bd=0, highlightthickness=1, highlightbackground=self.current_theme["border"])
        self.title_frame.pack(fill=tk.X)

        self.title_label = tk.Label(
            self.title_frame,
            text="Constitution AI",
            font=("Arial", 12, "bold"),
            bg=self.current_theme["nav_bg"],
            fg=self.current_theme["title_fg"],
        )
        self.title_label.pack(side=tk.LEFT, padx=(18, 24), pady=14)

        self.ask_button = self.create_nav_button(self.title_frame, "Ask Question", "?", self.ask_question, active=True)
        self.favorites_button = self.create_nav_button(self.title_frame, "Favorites", "*", self.show_favorites)
        self.compare_button = self.create_nav_button(self.title_frame, "Compare", "=", self.compare_articles)
        self.progress_button = self.create_nav_button(self.title_frame, "Progress", "|", self.show_progress)
        self.practice_button = self.create_nav_button(self.title_frame, "Practice", "P", self.show_practice)
        self.quiz_button = self.create_nav_button(self.title_frame, "Quiz", "Q", self.show_quiz)
        self.export_button = self.create_nav_button(self.title_frame, "Export PDF", "PDF", self.export_to_pdf)

        self.theme_button = tk.Button(
            self.title_frame,
            command=self.toggle_theme,
            font=("Arial", 18, "bold"),
            bg=self.current_theme["nav_bg"],
            fg=self.current_theme["accent_bg"],
            activebackground=self.current_theme["active_bg"],
            activeforeground=self.current_theme["accent_bg"],
            bd=0,
            cursor="hand2",
            width=4,
        )
        self.theme_button.pack(side=tk.RIGHT, padx=18, pady=8)

        self.main_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        self.left_frame = tk.Frame(
            self.main_frame,
            bg=self.current_theme["card_bg"],
            width=370,
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground=self.current_theme["border"],
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        self.left_frame.pack_propagate(False)

        self.language_frame = tk.Frame(self.left_frame, bg=self.current_theme["card_bg"])
        self.language_frame.pack(fill=tk.X, padx=18, pady=(18, 12))

        self.language_label = tk.Label(
            self.language_frame,
            font=("Arial", 10, "bold"),
            bg=self.current_theme["card_bg"],
            fg=self.current_theme["label_fg"],
        )
        self.language_label.pack(side=tk.LEFT)

        self.language_var = tk.StringVar(value="Hindi" if self.language == "hi" else "English")
        self.language_menu = ttk.Combobox(
            self.language_frame,
            textvariable=self.language_var,
            values=["English", "Hindi"],
            state="readonly",
            width=12,
        )
        self.language_menu.pack(side=tk.LEFT, padx=8)
        self.language_menu.bind("<<ComboboxSelected>>", self.change_language)

        self.question_label = tk.Label(
            self.left_frame,
            font=("Arial", 13, "bold"),
            bg=self.current_theme["card_bg"],
            fg=self.current_theme["label_fg"],
        )
        self.question_label.pack(anchor=tk.W, padx=18, pady=(0, 7))

        self.question_entry = scrolledtext.ScrolledText(
            self.left_frame,
            height=6,
            width=42,
            font=("Arial", 11),
            wrap=tk.WORD,
            bg=self.current_theme["text_bg"],
            fg=self.current_theme["fg"],
            insertbackground=self.current_theme["fg"],
            relief=tk.FLAT,
            bd=8,
        )
        self.question_entry.pack(fill=tk.X, padx=18, pady=(0, 12))

        self.button_frame = tk.Frame(self.left_frame, bg=self.current_theme["bg"])
        self.button_frame.pack(fill=tk.X, padx=18, pady=(0, 8))

        self.voice_button = tk.Button(
            self.button_frame,
            text="Voice",
            command=self.voice_input,
            font=("Arial", 10),
            bg=self.current_theme["danger_bg"],
            fg=self.current_theme["button_fg"],
            cursor="hand2",
            relief=tk.FLAT,
            width=12,
        )
        self.voice_button.pack(side=tk.LEFT)

        self.quick_questions_label = tk.Label(
            self.left_frame,
            font=("Arial", 11, "bold"),
            bg=self.current_theme["card_bg"],
            fg=self.current_theme["label_fg"],
        )
        self.quick_questions_label.pack(anchor=tk.W, padx=18, pady=(12, 7))

        for index, question in enumerate(self.quick_questions["en"]):
            button = tk.Button(
                self.left_frame,
                text=question,
                command=lambda i=index: self.set_question(self.quick_questions[self.language][i]),
                font=("Arial", 9),
                bg=self.current_theme["quick_button_bg"],
                fg=self.current_theme["quick_button_fg"],
                cursor="hand2",
                anchor=tk.W,
                relief=tk.FLAT,
                padx=12,
                pady=7,
            )
            button.pack(fill=tk.X, padx=18, pady=3)
            self.quick_question_buttons.append(button)

        self.right_frame = tk.Frame(
            self.main_frame,
            bg=self.current_theme["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground=self.current_theme["border"],
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.answer_label = tk.Label(
            self.right_frame,
            font=("Arial", 13, "bold"),
            bg=self.current_theme["card_bg"],
            fg=self.current_theme["label_fg"],
        )
        self.answer_label.pack(anchor=tk.W, padx=18, pady=(18, 7))

        self.answer_text = scrolledtext.ScrolledText(
            self.right_frame,
            height=15,
            font=("Arial", 11),
            wrap=tk.WORD,
            bg=self.current_theme["text_bg"],
            fg=self.current_theme["fg"],
            insertbackground=self.current_theme["fg"],
            relief=tk.FLAT,
            bd=10,
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        self.favorite_frame = tk.Frame(self.right_frame, bg=self.current_theme["card_bg"])
        self.favorite_frame.pack(fill=tk.X, padx=18, pady=(0, 14))
        self.add_favorite_button = tk.Button(
            self.favorite_frame,
            command=self.add_to_favorites,
            font=("Arial", 10, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            cursor="hand2",
            relief=tk.FLAT,
            padx=12,
            pady=7,
        )
        self.add_favorite_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value=self.t("ready_loading"))
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Arial", 9),
            bg=self.current_theme["status_bg"],
            fg=self.current_theme["fg"],
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.theme_widgets = [
            self.main_frame,
            self.left_frame,
            self.language_frame,
            self.button_frame,
            self.right_frame,
            self.favorite_frame,
        ]

    def create_nav_button(self, parent, label, icon, command, active=False):
        button = tk.Button(
            parent,
            text=f"{icon}\n{label}",
            command=command,
            font=("Arial", 9, "bold"),
            bg=self.current_theme["active_bg"] if active else self.current_theme["nav_bg"],
            fg=self.current_theme["button_bg"] if active else self.current_theme["fg"],
            activebackground=self.current_theme["active_bg"],
            activeforeground=self.current_theme["button_bg"],
            bd=0,
            cursor="hand2",
            width=12,
            pady=6,
        )
        button.pack(side=tk.LEFT, padx=2, pady=5)
        self.nav_buttons.append((button, icon, label, active))
        return button

    def create_action_button(self, parent, command, column):
        button = tk.Button(
            parent,
            command=command,
            font=("Arial", 9),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            cursor="hand2",
            width=13,
        )
        button.grid(row=0, column=column, padx=(0, 5), sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        return button

    def apply_language(self):
        self.language_label.config(text=self.t("language"))
        self.question_label.config(text=self.t("question"))
        self.answer_label.config(text=self.t("answer"))
        self.ask_button.config(text=f"?\n{self.t('ask')}")
        self.favorites_button.config(text=f"*\n{self.t('favorites')}")
        self.compare_button.config(text=f"=\n{self.t('compare')}")
        self.progress_button.config(text=f"|\n{self.t('progress')}")
        self.practice_button.config(text=f"P\n{self.t('practice')}")
        self.quiz_button.config(text=f"Q\n{self.t('quiz')}")
        self.export_button.config(text=f"PDF\n{self.t('export')}")
        self.add_favorite_button.config(text=self.t("add_favorite"))
        self.quick_questions_label.config(text=self.t("quick"))
        self.theme_button.config(text="☀" if self.theme_name == "light" else "☾")
        for index, button in enumerate(self.quick_question_buttons):
            button.config(text=self.quick_questions[self.language][index])
        self.status_var.set(self.t("ready_loading") if not self.rag_system else self.t("ready"))

    def apply_theme(self):
        self.current_theme = self.themes[self.theme_name]
        self.root.configure(bg=self.current_theme["bg"])
        self.title_frame.configure(bg=self.current_theme["nav_bg"], highlightbackground=self.current_theme["border"])
        self.title_label.configure(bg=self.current_theme["nav_bg"], fg=self.current_theme["title_fg"])

        for widget in [self.main_frame, self.button_frame]:
            widget.configure(bg=self.current_theme["bg"])
        for widget in [self.left_frame, self.language_frame, self.right_frame, self.favorite_frame]:
            widget.configure(bg=self.current_theme["card_bg"])
            if hasattr(widget, "configure"):
                try:
                    widget.configure(highlightbackground=self.current_theme["border"])
                except tk.TclError:
                    pass

        for label in [self.language_label, self.question_label, self.quick_questions_label, self.answer_label]:
            label.configure(bg=self.current_theme["card_bg"], fg=self.current_theme["label_fg"])

        for text_widget in [self.question_entry, self.answer_text]:
            text_widget.configure(
                bg=self.current_theme["text_bg"],
                fg=self.current_theme["fg"],
                insertbackground=self.current_theme["fg"],
            )

        nav_states = {
            self.ask_button: True,
            self.favorites_button: False,
            self.compare_button: False,
            self.progress_button: False,
            self.practice_button: False,
            self.quiz_button: False,
            self.export_button: False,
        }
        for button, active in nav_states.items():
            button.configure(
                bg=self.current_theme["active_bg"] if active else self.current_theme["nav_bg"],
                fg=self.current_theme["button_bg"] if active else self.current_theme["fg"],
                activebackground=self.current_theme["active_bg"],
                activeforeground=self.current_theme["button_bg"],
            )

        self.theme_button.configure(
            bg=self.current_theme["nav_bg"],
            fg=self.current_theme["accent_bg"],
            activebackground=self.current_theme["active_bg"],
            activeforeground=self.current_theme["accent_bg"],
        )
        self.add_favorite_button.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"])
        self.voice_button.configure(bg=self.current_theme["danger_bg"], fg=self.current_theme["button_fg"])
        for button in self.quick_question_buttons:
            button.configure(bg=self.current_theme["quick_button_bg"], fg=self.current_theme["quick_button_fg"])

        self.status_bar.configure(bg=self.current_theme["status_bg"], fg=self.current_theme["fg"])
        self.apply_language()

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()
        self.save_user_data()

    def change_language(self, _event=None):
        self.language = "hi" if self.language_var.get() == "Hindi" else "en"
        self.apply_language()
        self.save_user_data()
        messagebox.showinfo("Language", f"Language changed to {self.language_var.get()}")

    def load_models(self):
        def load():
            try:
                self.status_var.set("Initializing data processor...")
                self.data_processor = ConstitutionDataProcessor()

                self.status_var.set("Loading cached constitution data...")
                chunks = self.data_processor.load_chunks("real_constitution_chunks.json")
                if not chunks:
                    chunks = self.data_processor.load_chunks("constitution_chunks.json")
                if not chunks:
                    self.status_var.set("Processing constitution data once...")
                    chunks = self.data_processor.process_all(use_sample=False)

                self.status_var.set("Building vector database...")
                self.vector_db = ConstitutionVectorDB()
                self.vector_db.build_database(chunks)
                self.status_var.set("Loading search model...")
                self.vector_db.load_embedding_model()

                self.status_var.set("Initializing RAG system...")
                self.rag_system = ConstitutionRAG(self.vector_db)

                self.status_var.set("Setting up local LLM...")
                try:
                    self.llm_interface = LocalLLMInterface()
                    if not self.llm_interface.setup_model(auto_pull=False):
                        self.llm_interface = None
                        self.status_var.set("Ollama unavailable - start Ollama and install a model")
                except Exception as exc:
                    print(f"Failed to setup local LLM: {exc}")
                    self.llm_interface = None
                    self.status_var.set("Ollama unavailable - start Ollama and install a model")

                if self.llm_interface:
                    self.status_var.set(f"Ready - using Ollama model: {self.llm_interface.model_name}")
                    self.ask_button.config(state=tk.NORMAL)
                else:
                    self.ask_button.config(state=tk.DISABLED)

                print(f"Database loaded: {self.vector_db.get_statistics()}")
            except Exception as exc:
                self.status_var.set(f"Error: {exc}")
                messagebox.showerror("Error", f"Failed to load models: {exc}")

        self.ask_button.config(state=tk.DISABLED)
        threading.Thread(target=load, daemon=True).start()

    def set_question(self, question):
        self.question_entry.delete(1.0, tk.END)
        self.question_entry.insert(1.0, question)

    def language_instruction(self):
        if self.language == "hi":
            return "\nAnswer in simple Hindi. Use Devanagari Hindi where possible."
        return "\nAnswer in clear English."

    def ask_question(self):
        question = self.question_entry.get(1.0, tk.END).strip()
        if not question:
            messagebox.showwarning("Warning", self.t("question_required"))
            return

        if not self.rag_system or not self.llm_interface:
            messagebox.showerror("Error", "Ollama is not ready. Start Ollama and install at least one model, then restart the app.")
            return

        def process():
            try:
                self.status_var.set("Processing question...")
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(1.0, self.t("thinking"))

                rag_result = self.rag_system.process_query(question)
                if rag_result.get("trusted_answer"):
                    answer = rag_result["trusted_answer"]
                    if self.language == "hi":
                        answer = self.llm_interface.generate_response(
                            f"Translate this answer into simple Hindi:\n\n{answer}",
                            max_tokens=350,
                        )
                else:
                    prompt = rag_result["prompt"] + self.language_instruction()
                    self.status_var.set("Generating answer with Ollama...")
                    answer = self.llm_interface.generate_response(prompt, max_tokens=550)

                self.last_answer = answer
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(1.0, answer)
                self.status_var.set(f"Ready - using Ollama model: {self.llm_interface.model_name}")

                self.user_data["history"].append(
                    {
                        "question": question,
                        "answer": answer,
                        "language": self.language,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                self.save_user_data()
            except Exception as exc:
                self.status_var.set(f"Error: {exc}")
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(1.0, f"Error: {exc}")

        threading.Thread(target=process, daemon=True).start()

    def require_reportlab(self):
        if SimpleDocTemplate is None:
            messagebox.showerror("Missing Dependency", "ReportLab is required. Install it with: pip install reportlab")
            return False
        return True

    def export_to_pdf(self):
        if not self.require_reportlab():
            return

        answer = self.answer_text.get(1.0, tk.END).strip()
        question = self.question_entry.get(1.0, tk.END).strip()
        if not answer:
            messagebox.showwarning("Warning", self.t("no_answer"))
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Answer as PDF",
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = [Paragraph("Constitution AI - Q&A Export", styles["Title"]), Spacer(1, 12)]
            if question:
                story.append(Paragraph(f"<b>Question:</b> {html.escape(question)}", styles["Heading2"]))
                story.append(Spacer(1, 8))
            for paragraph in answer.splitlines():
                if paragraph.strip():
                    story.append(Paragraph(html.escape(paragraph.strip()), styles["Normal"]))
                    story.append(Spacer(1, 6))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", styles["Normal"]))
            doc.build(story)
            messagebox.showinfo("Success", f"PDF exported to {file_path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to export PDF: {exc}")

    def add_to_favorites(self):
        question = self.question_entry.get(1.0, tk.END).strip()
        answer = self.answer_text.get(1.0, tk.END).strip()
        if not question or not answer:
            messagebox.showwarning("Warning", self.t("no_qa"))
            return

        for favorite in self.user_data["favorites"]:
            if favorite.get("question", "").strip().lower() == question.lower():
                messagebox.showinfo("Info", "This question is already in favorites.")
                return

        self.user_data["favorites"].append(
            {
                "question": question,
                "answer": answer,
                "language": self.language,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.save_user_data()
        messagebox.showinfo("Success", "Added to favorites!")

    def show_favorites(self):
        if not self.user_data["favorites"]:
            messagebox.showinfo("Favorites", "No favorites saved yet.")
            return

        window = self.create_text_window("Favorites", "900x620")
        text = window["text"]
        favorites = self.user_data["favorites"]
        for index, favorite in enumerate(favorites, 1):
            text.insert(tk.END, f"--- Favorite {index} ---\n")
            text.insert(tk.END, f"Question: {favorite.get('question', '')}\n")
            text.insert(tk.END, f"Answer: {favorite.get('answer', '')}\n")
            text.insert(tk.END, f"Saved: {favorite.get('timestamp', '')}\n\n")

        def load_selected():
            try:
                selected_text = text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                messagebox.showwarning("Warning", "Select one favorite block first.")
                return
            match = re.search(r"--- Favorite (\d+) ---", selected_text)
            if not match:
                messagebox.showwarning("Warning", "Select from a favorite heading through its answer.")
                return
            favorite = favorites[int(match.group(1)) - 1]
            self.set_question(favorite.get("question", ""))
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(1.0, favorite.get("answer", ""))
            window["top"].destroy()

        tk.Button(
            window["top"],
            text="Load Selected",
            command=load_selected,
            font=("Arial", 10),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=6)

    def compare_articles(self):
        if not self.vector_db or not self.vector_db.chunks:
            messagebox.showwarning("Warning", "Database not loaded yet.")
            return

        window = tk.Toplevel(self.root)
        window.title("Compare Articles")
        window.geometry("980x700")
        window.configure(bg=self.current_theme["bg"])

        article_numbers = sorted(
            {chunk.get("article_number", "") for chunk in self.vector_db.chunks if chunk.get("article_number", "")},
            key=self.article_sort_key,
        )

        controls = tk.Frame(window, bg=self.current_theme["bg"])
        controls.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(controls, text="Article 1:", bg=self.current_theme["bg"], fg=self.current_theme["label_fg"]).pack(side=tk.LEFT)
        article1_var = tk.StringVar()
        ttk.Combobox(controls, textvariable=article1_var, values=article_numbers, state="readonly", width=18).pack(side=tk.LEFT, padx=6)

        tk.Label(controls, text="Article 2:", bg=self.current_theme["bg"], fg=self.current_theme["label_fg"]).pack(side=tk.LEFT, padx=(16, 0))
        article2_var = tk.StringVar()
        ttk.Combobox(controls, textvariable=article2_var, values=article_numbers, state="readonly", width=18).pack(side=tk.LEFT, padx=6)

        comparison_frame = tk.Frame(window, bg=self.current_theme["bg"])
        comparison_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        article1_text = self.article_text_area(comparison_frame)
        article2_text = self.article_text_area(comparison_frame)

        def display_article(article_number, text_widget):
            text_widget.delete(1.0, tk.END)
            chunks = self.vector_db.get_articles_by_number(article_number)
            if chunks:
                text_widget.insert(tk.END, f"Article {article_number}\n\n")
                for chunk in chunks:
                    text_widget.insert(tk.END, f"{chunk.get('text', '')}\n\n")
            else:
                text_widget.insert(tk.END, f"Article {article_number} not found.")

        def do_compare():
            if not article1_var.get() or not article2_var.get():
                messagebox.showwarning("Warning", "Please select both articles.")
                return
            display_article(article1_var.get(), article1_text)
            display_article(article2_var.get(), article2_text)

        tk.Button(
            window,
            text="Compare",
            command=do_compare,
            font=("Arial", 11, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(pady=8)

    def article_text_area(self, parent):
        frame = tk.Frame(parent, bg=self.current_theme["bg"])
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        text = scrolledtext.ScrolledText(
            frame,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=self.current_theme["text_bg"],
            fg=self.current_theme["fg"],
            insertbackground=self.current_theme["fg"],
        )
        text.pack(fill=tk.BOTH, expand=True)
        return text

    def article_sort_key(self, value):
        match = re.match(r"(\d+)([A-Z]*)", str(value).upper())
        if not match:
            return (9999, str(value))
        return (int(match.group(1)), match.group(2))

    def show_progress(self):
        window = self.create_text_window("Learning Progress", "760x540")
        text = window["text"]
        history = self.user_data["history"]
        favorites = self.user_data["favorites"]
        quiz_results = self.user_data.get("quiz_results", [])
        articles = set()
        for item in history:
            match = re.search(r"article\s+(\d+[a-z]?)", item.get("question", ""), re.IGNORECASE)
            if match:
                articles.add(match.group(1).upper())

        text.insert(tk.END, "=== Learning Progress Report ===\n\n")
        text.insert(tk.END, f"Total Questions Asked: {len(history)}\n")
        text.insert(tk.END, f"Total Favorites Saved: {len(favorites)}\n")
        text.insert(tk.END, f"Quizzes Completed: {len(quiz_results)}\n")
        if quiz_results:
            latest = quiz_results[-1]
            text.insert(tk.END, f"Latest Quiz Score: {latest.get('score', 0)}/{latest.get('total', 5)}\n")
        text.insert(tk.END, f"Unique Articles Explored: {len(articles)}\n\n")
        if articles:
            text.insert(tk.END, "Articles Explored:\n")
            for article in sorted(articles, key=self.article_sort_key):
                text.insert(tk.END, f"  - Article {article}\n")
        text.insert(tk.END, "\n=== Recent Activity ===\n\n")
        for index, item in enumerate(history[-5:], 1):
            text.insert(tk.END, f"{index}. {item.get('question', '')[:80]}\n")
            text.insert(tk.END, f"   {item.get('timestamp', '')[:19]}\n\n")
        if not history:
            text.insert(tk.END, "No recent activity.\n")

    def show_practice(self):
        window = tk.Toplevel(self.root)
        window.title("Practice - 5 Fresh Questions")
        window.geometry("760x520")
        window.configure(bg=self.current_theme["bg"])

        header = tk.Frame(window, bg=self.current_theme["bg"])
        header.pack(fill=tk.X, padx=18, pady=(18, 8))

        tk.Label(
            header,
            text="Practice Questions",
            font=("Arial", 16, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["label_fg"],
        ).pack(side=tk.LEFT)

        content = tk.Frame(window, bg=self.current_theme["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=8)

        def load_question(question):
            self.set_question(question)
            self.status_var.set("Practice question loaded. Press Ask Question when ready.")
            window.destroy()

        def render_new_set():
            for child in content.winfo_children():
                child.destroy()

            questions = random.sample(self.practice_questions, k=5)
            for index, question in enumerate(questions, 1):
                row = tk.Frame(
                    content,
                    bg=self.current_theme["card_bg"],
                    bd=1,
                    relief=tk.SOLID,
                    highlightthickness=1,
                    highlightbackground=self.current_theme["border"],
                )
                row.pack(fill=tk.X, pady=6)

                tk.Label(
                    row,
                    text=f"{index}. {question}",
                    font=("Arial", 11, "bold"),
                    bg=self.current_theme["card_bg"],
                    fg=self.current_theme["fg"],
                    anchor=tk.W,
                    wraplength=560,
                    justify=tk.LEFT,
                ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=12)

                tk.Button(
                    row,
                    text="Ask",
                    command=lambda q=question: load_question(q),
                    font=("Arial", 10, "bold"),
                    bg=self.current_theme["button_bg"],
                    fg=self.current_theme["button_fg"],
                    relief=tk.FLAT,
                    cursor="hand2",
                    width=8,
                ).pack(side=tk.RIGHT, padx=12, pady=10)

        tk.Button(
            header,
            text="New 5 Questions",
            command=render_new_set,
            font=("Arial", 10, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=7,
        ).pack(side=tk.RIGHT)

        render_new_set()

    def show_quiz(self):
        window = tk.Toplevel(self.root)
        window.title("Quiz - 5 Random Questions")
        window.geometry("860x680")
        window.configure(bg=self.current_theme["bg"])

        questions = random.sample(self.quiz_bank, k=5)
        answers = []

        header = tk.Frame(window, bg=self.current_theme["bg"])
        header.pack(fill=tk.X, padx=18, pady=(18, 8))
        tk.Label(
            header,
            text="Constitution Quiz",
            font=("Arial", 16, "bold"),
            bg=self.current_theme["bg"],
            fg=self.current_theme["label_fg"],
        ).pack(side=tk.LEFT)

        result_var = tk.StringVar(value="Choose one option for each question, then submit.")
        result_label = tk.Label(
            window,
            textvariable=result_var,
            font=("Arial", 11, "bold"),
            bg=self.current_theme["status_bg"],
            fg=self.current_theme["fg"],
            anchor=tk.W,
            padx=12,
            pady=8,
        )
        result_label.pack(fill=tk.X, padx=18, pady=(0, 10))

        quiz_frame = tk.Frame(window, bg=self.current_theme["bg"])
        quiz_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=4)

        for index, item in enumerate(questions, 1):
            selected = tk.StringVar(value="")
            answers.append(selected)

            card = tk.Frame(
                quiz_frame,
                bg=self.current_theme["card_bg"],
                bd=1,
                relief=tk.SOLID,
                highlightthickness=1,
                highlightbackground=self.current_theme["border"],
            )
            card.pack(fill=tk.X, pady=6)

            tk.Label(
                card,
                text=f"{index}. {item['question']}",
                font=("Arial", 11, "bold"),
                bg=self.current_theme["card_bg"],
                fg=self.current_theme["fg"],
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=780,
            ).pack(fill=tk.X, padx=12, pady=(10, 4))

            options_frame = tk.Frame(card, bg=self.current_theme["card_bg"])
            options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            for option in item["options"]:
                tk.Radiobutton(
                    options_frame,
                    text=option,
                    variable=selected,
                    value=option,
                    font=("Arial", 10),
                    bg=self.current_theme["card_bg"],
                    fg=self.current_theme["fg"],
                    activebackground=self.current_theme["card_bg"],
                    activeforeground=self.current_theme["button_bg"],
                    selectcolor=self.current_theme["text_bg"],
                    anchor=tk.W,
                ).pack(side=tk.LEFT, padx=8, pady=3)

        footer = tk.Frame(window, bg=self.current_theme["bg"])
        footer.pack(fill=tk.X, padx=18, pady=14)

        review_text = scrolledtext.ScrolledText(
            window,
            height=5,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=self.current_theme["text_bg"],
            fg=self.current_theme["fg"],
            insertbackground=self.current_theme["fg"],
            relief=tk.FLAT,
            bd=8,
        )
        review_text.pack(fill=tk.X, padx=18, pady=(0, 14))
        review_text.insert(tk.END, "Result details will appear here after submit.")
        review_text.configure(state=tk.DISABLED)

        def submit_quiz():
            unanswered = [str(index + 1) for index, answer in enumerate(answers) if not answer.get()]
            if unanswered:
                messagebox.showwarning("Quiz", f"Please answer question(s): {', '.join(unanswered)}")
                return

            score = 0
            review_lines = []
            for index, item in enumerate(questions, 1):
                selected_answer = answers[index - 1].get()
                correct = item["answer"]
                if selected_answer == correct:
                    score += 1
                    review_lines.append(f"{index}. Correct - {correct}")
                else:
                    review_lines.append(f"{index}. Wrong - Your answer: {selected_answer}; Correct answer: {correct}")

            percent = int((score / len(questions)) * 100)
            result_var.set(f"Result: {score}/{len(questions)} correct ({percent}%)")
            review_text.configure(state=tk.NORMAL)
            review_text.delete(1.0, tk.END)
            review_text.insert(tk.END, "\n".join(review_lines))
            review_text.configure(state=tk.DISABLED)

            self.user_data.setdefault("quiz_results", []).append(
                {
                    "score": score,
                    "total": len(questions),
                    "percent": percent,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self.save_user_data()

        def new_quiz():
            window.destroy()
            self.show_quiz()

        tk.Button(
            footer,
            text="Submit Quiz",
            command=submit_quiz,
            font=("Arial", 10, "bold"),
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT)

        tk.Button(
            footer,
            text="New Quiz",
            command=new_quiz,
            font=("Arial", 10, "bold"),
            bg=self.current_theme["accent_bg"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT, padx=8)

    def create_text_window(self, title, geometry):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry(geometry)
        top.configure(bg=self.current_theme["bg"])
        text = scrolledtext.ScrolledText(
            top,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=self.current_theme["text_bg"],
            fg=self.current_theme["fg"],
            insertbackground=self.current_theme["fg"],
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return {"top": top, "text": text}

    def voice_input(self):
        messagebox.showinfo("Voice Input", "Voice input feature coming soon!")


def main():
    root = tk.Tk()
    ConstitutionAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

