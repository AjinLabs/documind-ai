# DocuMind AI — Installation & Setup Guide

## System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python Version**: Python 3.10 – 3.14.
- **RAM**: Minimum 4 GB (8 GB recommended for local vector embeddings).

## Quick Start (Windows PowerShell)

### 1. Clone the Repository
```powershell
git clone https://github.com/AjinLabs/documind-ai.git
cd documind-ai
```

### 2. Create and Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Automated Test Suite
Verify that all unit and integration tests pass without errors:
```powershell
python -m pytest tests/ -v
```

### 5. Launch the Application
```powershell
streamlit run app.py
```
The browser interface will open automatically at `http://localhost:8501`.

---

## Configuration & Environment Variables (Optional)

DocuMind runs out of the box in **100% Offline Extractive Mode** with zero external API keys required. If you wish to use commercial LLM models, configure them in your environment or via the in-app **Settings and Model Configuration** screen:

```powershell
# Optional: Set in PowerShell
$env:OPENAI_API_KEY="sk-..."
$env:GEMINI_API_KEY="AIzaSy..."
```

---

## Deployment Options

### Option 1: Streamlit Community Cloud (Free 1-Click Hosting)
1. Fork or push this repository to your GitHub account: `https://github.com/AjinLabs/documind-ai`.
2. Visit [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account and select `documind-ai`.
4. Set Main file path to `app.py`.
5. Click **Deploy!**

### Option 2: Render.com (1-Click Web Service)
This repository includes a `render.yaml` blueprint. Connect the repository in Render to deploy as a Python Web Service.

### Option 3: Docker Container
```powershell
docker build -t documind-ai .
docker run -p 8501:8501 documind-ai
```
