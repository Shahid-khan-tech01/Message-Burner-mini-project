
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import closing
import sqlite3
import secrets
import time
import base64   
app = FastAPI() 
BASE = Path(__file__).resolve().parent
DB = BASE / "messages.db"   
# Create database table
with closing(sqlite3.connect(DB)) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS media_messages (
            token TEXT PRIMARY KEY,
            message TEXT,
            image BLOB,
            mime TEXT,
            expires REAL,
            views INTEGER
        )
    """)
    db.commit() 
# Home page
@app.get("/")
def home():
    return FileResponse(BASE / "static/index.html") 
# Create message and image link
@app.post("/create")
async def create_message(
    message: str = Form(""),
    expiration_minutes: int = Form(1440),
    max_reads: int = Form(1),
    image: UploadFile | None = File(None)
):  
    message = message.strip()   
    # Validate message length
    if len(message) > 1000:
        raise HTTPException(
            400, "Maximum 1000 characters allowed"
        )   
    # Validate number of users
    if not 1 <= max_reads <= 20:
        raise HTTPException(
            400, "Enter between 1 and 20 users"
        )   
    # Validate expiration time
    if not 5 <= expiration_minutes <= 10080:
        raise HTTPException(
            400, "Invalid expiration time"
        )   
    content = None
    mime = None 
    # Upload image
    if image and image.filename:    
        content = await image.read(
            5 * 1024 * 1024 + 1
        )   
        await image.close() 
        # Maximum image size
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                400, "Image must be under 5 MB"
            )   
        # Validate image format
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"  
        elif content.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg" 
        elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            mime = "image/webp" 
        else:
            raise HTTPException(
                400,
                "Only PNG, JPEG and WebP images are allowed"
            )   
    # Check empty message
    if not message and not content:
        raise HTTPException(
            400,
            "Enter a message or attach an image"
        )   
    # Generate unique token
    token = secrets.token_urlsafe(24)   
    # Calculate expiry time
    expires = time.time() + expiration_minutes * 60 
    # Store message and image
    with closing(sqlite3.connect(DB)) as db:    
        # Delete expired messages
        db.execute(
            "DELETE FROM media_messages WHERE expires <= ?",
            (time.time(),)
        )   
        db.execute("""
            INSERT INTO media_messages
            (token, message, image, mime, expires, views)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            token,
            message,
            content,
            mime,
            expires,
            max_reads
        ))  
        db.commit() 
    return {
        "link": "/read/" + token,
        "max_reads": max_reads,
        "expires": expires
    }   
# Reading page
@app.get("/read/{token}")
def read_page(token: str):  
    return FileResponse(
        BASE / "static/read.html",
        headers={"Cache-Control": "no-store"}
    )   
# Reveal message and image
@app.post("/message/{token}")
def reveal_message(token: str): 
    with closing(sqlite3.connect(DB)) as db:    
        # Prevent simultaneous extra views
        db.execute("BEGIN IMMEDIATE")   
        row = db.execute("""
            SELECT message, image, mime, expires, views
            FROM media_messages
            WHERE token = ?
        """, (token,)).fetchone()   
        # Check message availability
        if not row:
            raise HTTPException(
                404,
                "Message unavailable or already viewed"
            )   
        message, content, mime, expires, views = row    
        # Check expiration time
        if expires <= time.time():  
            db.execute(
                "DELETE FROM media_messages WHERE token = ?",
                (token,)
            )   
            db.commit() 
            raise HTTPException(
                410, "This message has expired"
            )   
        # Delete after final view
        if views <= 1:  
            db.execute(
                "DELETE FROM media_messages WHERE token = ?",
                (token,)
            )   
        else:   
            db.execute("""
                UPDATE media_messages
                SET views = views - 1
                WHERE token = ?
            """, (token,))  
        db.commit() 
    # Convert image into Base64
    image_data = None   
    if content: 
        image_data = (
            f"data:{mime};base64,"
            + base64.b64encode(content).decode()
        )   
    return JSONResponse(
        {
            "message": message,
            "image": image_data,
            "remaining_reads": views - 1
        },
        headers={"Cache-Control": "no-store"}
    )   
# Connect HTML, CSS and JavaScript
app.mount(
    "/static",
    StaticFiles(directory=BASE / "static"),
    name="static"
)   