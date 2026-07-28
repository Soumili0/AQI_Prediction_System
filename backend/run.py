"""
Application Entry Point
=======================
Starts the Flask development server or is referenced by WSGI servers
like Gunicorn in production: `gunicorn run:app`
"""

import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
