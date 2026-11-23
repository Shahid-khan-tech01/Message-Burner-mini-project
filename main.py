from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import sqlite3
import secrets

app = FastAPI(title="Message Burner")

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "messages.db"
STATIC_DIR = BASE_DIR / "static"

# Create the database table when the app starts.
def setup_database():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                token TEXT PRIMARY KEY,
                message TEXT NOT NULL
            )
        """)
        conn.commit()

setup_database()

# Display the home page :
@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")

class MessageRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/create")
def create_message(data: MessageRequest):
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a message.")

    token = secrets.token_urlsafe(16)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO messages (token, message) VALUES (?, ?)",
            (token, message)
        )
        conn.commit()

    return {"link": f"/read/{token}"}

@app.get("/read/{token}")
def read_page(token: str):
    return FileResponse(STATIC_DIR / "read.html")

@app.get("/message/{token}")
def burn_message(token: str):
    # Read and delete the message in one database transaction.
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT message FROM messages WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Message not found or already opened.")
        conn.execute("DELETE FROM messages WHERE token = ?", (token,))
        conn.commit()

    return {"message": row[0]}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")