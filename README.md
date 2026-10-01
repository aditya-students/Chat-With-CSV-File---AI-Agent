# 📊 AI Agent - Chat with Your CSV File

An interactive, full-stack AI-powered CSV data analyst application. Built with **Flask**, **LangChain**, **LangGraph**, **Groq LLM (`llama-3.3-70b-versatile`)**, and a sleek modern HTML5/CSS3 frontend featuring Markdown tables, dynamic data visualizations, and session history management.

---

## 🌟 Key Features

- 🤖 **Natural Language Data Analysis**: Ask questions in plain English to summarize, filter, aggregate, or visualize your CSV datasets.
- 📈 **Custom LangChain Tools**:
  - `get_data_info`: Analyzes dataset shape, column names, data types, and sample records.
  - `filter_data`: Executes safe pandas queries (e.g., `age > 30 and loan_status == 'Default'`).
  - `analyze_data`: Runs whitelisted, secure pandas statistics and grouping expressions (`df.describe()`, `df.groupby()`, etc.).
- 🎨 **Modern Dark-Themed UI**: Premium glassmorphism interface with smooth micro-animations, customizable column badges, typing indicators, and markdown table rendering.
- 🔒 **Sandboxed Execution**: Custom `SAFE_BUILTINS` whitelist prevents code injection (`__`, `import`, `open`, `exec`, `os.`, `sys.`, `subprocess`).
- ⚡ **Thread-Safe Architecture**: Uses `threading.Lock` across shared session states for seamless Gunicorn deployment.
- 📁 **Instant Pre-loaded & Custom Datasets**: Automatically pre-loads `credit_risk_dataset.csv` out-of-the-box while supporting drag-and-drop CSV uploads.
- 🚀 **Production-Ready**: Configured for instant deployment to platforms like **Render** via Gunicorn, Docker, or `Procfile`.

---

## 🛠️ Tech Stack & Architecture

### Backend
- **Framework**: Python 3.12, Flask, Flask-CORS, Werkzeug
- **Orchestration**: LangChain, LangGraph, LangChain-Groq (`llama-3.3-70b-versatile`)
- **Data Manipulation**: Pandas
- **WSGI Server**: Gunicorn

### Frontend
- **Interface**: HTML5, Vanilla CSS3 (CSS Variables, Flexbox/Grid, Animations), ES6+ JavaScript
- **Markdown & Tables**: Custom regex-based Markdown parser supporting interactive HTML table generation.

### Project Architecture

```
📁 AI-Agent- Chat with your CSV file/
├── 📄 app.py                  # AI Agent core (LangChain tools, prompt, thread locking, query runner)
├── 📄 main.py                 # Flask API routes (/health, /, /api/upload, /api/chat, /api/status, etc.)
├── 📄 index.html              # Modern single-page web UI (HTML/CSS/JS)
├── 📄 credit_risk_dataset.csv # Default sample dataset (32,581 rows x 12 columns)
├── 📄 requirements.txt        # Pinned Python package dependencies
├── 📄 Procfile                # Gunicorn startup command for Render / Heroku
├── 📄 Dockerfile              # Docker container definition (Python 3.12-slim)
├── 📄 .dockerignore           # Docker build exclusions
├── 📄 .gitignore              # Git exclusions (.env, uploads/, __pycache__/)
└── 📄 .env.example            # Environment variable template
```

---

## 🔄 How It Works

1. **Dataset Initialization**: Upon server startup or new CSV upload, `main.py` loads the CSV into Pandas and triggers `app.build_agent(df)`.
2. **User Query**: The user types a question in the chat input (e.g., *"What is the average loan amount for defaulted loans?"*).
3. **Agent Reasoning Loop**:
   - The **LangGraph Agent** receives the prompt and decides which tool to call based on system instructions.
   - If column names are unknown, it invokes `get_data_info`.
   - To compute statistics, it constructs a Pandas expression and executes it securely through `analyze_data`.
4. **Markdown Table Generation**: Tool outputs are formatted back to the user as plain text, list items, or Markdown tables.
5. **UI Rendering**: The frontend receives the response via `/api/chat` and dynamically renders Markdown into HTML tables, formatted lists, and styled text.

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.10+
- A free [Groq API Key](https://console.groq.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/aditya-students/Chat-With-CSV-File---AI-Agent.git
cd Chat-With-CSV-File---AI-Agent
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the Application
```bash
python main.py
```
Open your browser and navigate to **`http://localhost:8000`**.

---

## 🐳 Docker Setup

Build and run using Docker:

```bash
# Build the Docker image
docker build -t csv-ai-agent .

# Run the container
docker run -p 8000:8000 -e GROQ_API_KEY=your_groq_api_key_here csv-ai-agent
```
Access the application at `http://localhost:8000`.

---

## 🌐 Deploying to Render

This project is pre-configured for **Render.com**.

1. Create a new **Web Service** on Render and link this repository.
2. Set the **Build Command**: `pip install -r requirements.txt`
3. Set the **Start Command**: `gunicorn main:flask_app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`
4. Add an **Environment Variable**: `GROQ_API_KEY` = `your_groq_api_key`
5. Render will automatically build and deploy the web service!

---

## 🔒 Security Measures

- **No Remote Code Execution**: `eval()` runs with restricted `__builtins__` (`SAFE_BUILTINS`) and blocks dangerous keywords like `import`, `exec`, `open`, `os.`, `sys.`, and `subprocess`.
- **File Upload Protection**: Uploaded files are sanitized via `werkzeug.utils.secure_filename` to protect against path traversal attacks.
- **Request Size Limiting**: `MAX_CONTENT_LENGTH` is capped at 20 MB.
- **Thread Synchronization**: Global states are guarded with Python's `threading.Lock` to ensure concurrency safety.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more details.
