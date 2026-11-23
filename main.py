
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
import sqlite3
import secrets

app = FastAPI(title="Message Burner")

# Project paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_FILE = BASE_DIR / "messages.db"


# Create database table
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


# Validate message length
class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


# Home page
@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


# Create one-time message link
@app.post("/create")
def create_message(data: MessageRequest):

    message = data.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    if len(message) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 1000 characters allowed."
        )

    # Generate unique secret token
    token = secrets.token_urlsafe(16)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO messages (token, message) VALUES (?, ?)",
            (token, message)
        )
        conn.commit()

    return {"link": f"/read/{token}"}


# Open reader page
@app.get("/read/{token}")
def read_page(token: str):
    return FileResponse(STATIC_DIR / "read.html")


# Read and delete message
@app.get("/message/{token}")
def burn_message(token: str):

    with sqlite3.connect(DB_FILE) as conn:

        row = conn.execute(
            "SELECT message FROM messages WHERE token = ?",
            (token,)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Message not found or already opened."
            )

        # Delete message after reading
        conn.execute(
            "DELETE FROM messages WHERE token = ?",
            (token,)
        )

        conn.commit()

    return {"message": row[0]}


# Static files
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)
