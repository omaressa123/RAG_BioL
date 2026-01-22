# 🧬 BioLens

**BioLens** is an AI-powered educational web application that helps students understand Biology concepts by combining **computer vision**, **3D visualization**, and **RAG (Retrieval-Augmented Generation)**.

The idea is simple:

* 📸 Upload an image from a biology textbook (cell diagram, organelle, etc.)
* 🧠 The system understands what the image represents (using CLIP or OCR)
* 📚 It retrieves explanations directly from *school biology books*
* 🧊 Displays an interactive 3D model with a clear explanation

This project is designed for **hackathons**, **education platforms**, and **AI learning demos**.

---

## 🚀 Core Features

* ✅ Image understanding (without training a model)
* ✅ Biology-focused knowledge base (school textbooks)
* ✅ RAG system for accurate explanations from books
* ✅ Interactive 3D models (Three.js)
* ✅ Flask backend + HTML/CSS/JS frontend

---

## 🏗️ System Architecture

```
HTML / CSS / JS (Frontend)
        ↓
Image Upload (Camera / File)
        ↓
Flask API (/analyze-image)
        ↓
CLIP or OCR
        ↓
Concept Mapping (Organelle / Cell Type)
        ↓
RAG System (Books → Chunks → Vector DB)
        ↓
JSON Response
        ↓
Three.js 3D Viewer + Explanation
```

---

## 🧠 AI Components Explained

### 1️⃣ CLIP (Image Understanding)

CLIP (Contrastive Language–Image Pretraining) understands images by comparing them to **text concepts**.

* No training required
* Uses pre-written biology concepts
* Matches image → best concept

Example:

> Image of mitochondria → "mitochondrion" → explanation

---

### 2️⃣ RAG (Retrieval-Augmented Generation)

Instead of letting AI hallucinate answers, BioLens:

* Reads **real biology textbooks (PDF)**
* Splits them into chunks
* Stores them in a vector database
* Retrieves the *exact* explanation from the book

This ensures:

* ✔ Accurate
* ✔ Curriculum-aligned
* ✔ Student-safe answers

---

## 📚 Supported Educational Content

Designed for:

* Middle School Biology
* High School Biology
* IGCSE / American / National Curricula

### Common Topics

* Cell Structure
* Plant vs Animal Cells
* Organelles and Functions
* Photosynthesis
* Respiration

---

## 📁 Project Structure

```
BioLens/
│   ├── app.py
│   ├── rag/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── vector_store.py
│
├── Templates/
│   ├── index.html
│── static/
    ├── style.css
│   └── script.js
├── books/
│   └── biology_books.pdf
│
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Tech Stack

### Backend

* Flask
* LangChain
* FAISS (Vector DB)
* CLIP (HuggingFace)
* Sentence Transformers

### Frontend

* HTML
* CSS
* JavaScript
* Three.js

### AI & ML

* CLIP (Image ↔ Text)
* RAG (Book-based QA)

---

## 📦 Installation

### 1️⃣ Create Virtual Environment

```bash
python -m venv env
```

### 2️⃣ Activate Environment

**Windows (VS Code Terminal)**

```bash
env\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📚 Preparing Books for RAG

1. Put biology PDFs inside `books/`
2. Extract text from PDFs
3. Chunk the text
4. Generate embeddings
5. Store in FAISS

This is done once and reused.

---

## 🧪 Example Use Case

1. Student uploads a picture of a plant cell
2. BioLens detects **chloroplast**
3. Retrieves explanation from school book
4. Displays:

   * 3D chloroplast model
   * Function & description

---

## 🌟 Hackathon Value

* 🎯 Clear problem → solution
* 🤖 Real AI usage (CLIP + RAG)
* 📚 Education impact
* 🎥 Strong live demo

---

## 🛣️ Future Roadmap

* 🔍 Visual object detection (no labels)
* 🗣️ Voice explanation
* 🧠 Quiz mode
* 📱 Mobile version
* 🌐 Multi-language support

---

## 👨‍🎓 Target Users

* Students
* Teachers
* EdTech platforms
* Hackathon judges 😉

---

## 📌 Final Note

BioLens focuses on **clarity over complexity**.

Instead of training huge models, it smartly combines:

* Vision models
* Book-based knowledge
* 3D visualization

To make biology **easy, visual, and engaging** 🧬✨

---

**Built for learning. Powered by AI.**
