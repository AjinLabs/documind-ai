"""
DocuMind AI — Vercel Python WSGI Entrypoint
Serves the Eliza-themed DocuMind AI Document Intelligence Platform.
Exports top-level 'app' and 'handler' variables required by Vercel Serverless.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def app(environ, start_response):
    """WSGI application callable for Vercel Python runtime."""
    raw_path = environ.get('PATH_INFO', '/').lstrip('/')
    target_file = ROOT_DIR / raw_path if raw_path else ROOT_DIR / "index.html"

    # Serve static assets if requested
    if target_file.is_file() and not target_file.name.endswith(('.py', '.db', '.key', '.env', '.toml')):
        if target_file.suffix == '.html':
            content_type = 'text/html; charset=utf-8'
        elif target_file.suffix == '.css':
            content_type = 'text/css; charset=utf-8'
        elif target_file.suffix == '.js':
            content_type = 'application/javascript; charset=utf-8'
        elif target_file.suffix == '.json':
            content_type = 'application/json; charset=utf-8'
        elif target_file.suffix == '.svg':
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'

        status = '200 OK'
        headers = [
            ('Content-Type', content_type),
            ('Cache-Control', 'public, max-age=3600')
        ]
        start_response(status, headers)
        return [target_file.read_bytes()]

    # Default fallback to index.html (SPA routing)
    index_file = ROOT_DIR / "index.html"
    status = '200 OK'
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Cache-Control', 'public, max-age=0, must-revalidate')
    ]
    start_response(status, headers)
    return [index_file.read_bytes()]

# Top-level exports required by Vercel Python runtime
handler = app
application = app
