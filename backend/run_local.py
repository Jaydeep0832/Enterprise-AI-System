import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Local Enterprise AI Backend Server on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
