"""
DocuMind AI — Vercel Gateway & Architectural Portal
Provides a serverless landing page explaining DocuMind deployment and hosting options.
"""
from http.server import BaseHTTPRequestHandler

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuMind AI — Enterprise Intelligence Edition</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #151618;
            color: #CED3D6;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .container {
            max-width: 640px;
            background-color: #1E2124;
            border: 1px solid #3C4449;
            border-radius: 14px;
            padding: 36px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }
        h1 {
            color: #FFFFFF;
            font-size: 26px;
            margin-top: 0;
            letter-spacing: -0.02em;
        }
        .tagline {
            color: #8D9295;
            font-size: 15px;
            margin-bottom: 24px;
        }
        .badge {
            background-color: rgba(53, 199, 208, 0.12);
            color: #35C7D0;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .btn {
            display: inline-block;
            background-color: #3C4449;
            color: #FFFFFF;
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            margin-top: 18px;
            transition: background-color 0.2s;
        }
        .btn:hover {
            background-color: #62676B;
        }
        hr {
            border: 0;
            height: 1px;
            background-color: #3C4449;
            margin: 22px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">Enterprise Edition</span>
        <h1>DocuMind AI</h1>
        <div class="tagline">"From Documents to Decisions."</div>
        <p>DocuMind AI is an enterprise document intelligence and agentic RAG platform built with Python, PyMuPDF, FAISS, ChromaDB, and SQLite.</p>
        <p>To run the interactive 13-page platform with multi-turn chat, evidence lab, and knowledge graphs:</p>
        <ul>
            <li><b>Local execution:</b> <code>streamlit run app.py</code></li>
            <li><b>Streamlit Community Cloud:</b> 1-click deploy from GitHub (free, full WebSocket support)</li>
            <li><b>Render / Docker:</b> Deploy using <code>render.yaml</code> or <code>Dockerfile</code></li>
        </ul>
        <hr>
        <a href="https://github.com/AjinLabs/documind-ai" class="btn" target="_blank">View GitHub Repository →</a>
    </div>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode('utf-8'))
        return
