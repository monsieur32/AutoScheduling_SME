"""
Startup script for the backend server.
Run with:  python -m backend.run
"""

import uvicorn
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )
