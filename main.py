import asyncio
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles
import jwt
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
THUMBNAIL_DIR = Path("thumbnails")
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming

# Create directories
for directory in [UPLOAD_DIR, PROCESSED_DIR, THUMBNAIL_DIR]:
    directory.mkdir(exist_ok=True)

app = FastAPI(title="Enhanced Video Streaming Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database models (simplified for example)
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./videos.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    videos = relationship("Video", back_populates="owner")


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    filename = Column(String, unique=True)
    original_filename = Column(String)
    file_size = Column(Integer)
    duration = Column(Integer, nullable=True)  # in seconds
    thumbnail_path = Column(String, nullable=True)
    processed = Column(Boolean, default=False)
    processing_status = Column(
        String, default="pending"
    )  # pending, processing, completed, failed
    upload_date = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="videos")


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Authentication utilities
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_current_user(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# Video processing utilities (placeholder - would use FFmpeg in production)
async def process_video(video_path: Path, video_id: int, db: Session):
    """
    Process video: generate thumbnail, get duration, optionally transcode
    In production, this would use FFmpeg via subprocess
    """
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        video.processing_status = "processing"
        db.commit()

        # Simulate processing delay
        await asyncio.sleep(2)

        # ffmpeg -i input.mp4 -ss 00:00:01 -vframes 1 thumbnail.jpg
        # ffmpeg -i input.mp4 -c:v libx264 -preset fast -crf 23 output.mp4

        video.duration = 120  # Mock duration
        video.processed = True
        video.processing_status = "completed"
        video.thumbnail_path = f"thumbnails/{video.filename}.jpg"
        db.commit()

    except Exception as e:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.processing_status = f"failed: {str(e)}"
            db.commit()


# Routes
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/register")
async def register(
    username: str, email: str, password: str, db: Session = Depends(get_db)
):
    # Check if user exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully", "user_id": user.id}


@app.post("/api/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    token: str = None,
    db: Session = Depends(get_db),
):
    # Authenticate user
    user = await get_current_user(token, db)

    # Validate file type
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file in chunks (memory efficient)
    file_size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(CHUNK_SIZE):
            await f.write(chunk)
            file_size += len(chunk)

    # Create database entry
    video = Video(
        title=title or file.filename,
        description=description,
        filename=unique_filename,
        original_filename=file.filename,
        file_size=file_size,
        user_id=user.id,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Start background processing
    asyncio.create_task(process_video(file_path, video.id, db))

    return {
        "message": "Video uploaded successfully",
        "video_id": video.id,
        "status": "processing",
    }


@app.get("/api/videos")
async def list_videos(
    skip: int = 0, limit: int = 20, token: str = None, db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    videos = (
        db.query(Video).filter(Video.user_id == user.id).offset(skip).limit(limit).all()
    )

    return [
        {
            "id": v.id,
            "title": v.title,
            "description": v.description,
            "filename": v.filename,
            "duration": v.duration,
            "views": v.views,
            "upload_date": v.upload_date.isoformat(),
            "processed": v.processed,
            "processing_status": v.processing_status,
        }
        for v in videos
    ]


@app.get("/api/video/{video_id}")
async def get_video_info(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "duration": video.duration,
        "views": video.views,
        "upload_date": video.upload_date.isoformat(),
        "processed": video.processed,
    }


@app.get("/api/stream/{video_id}")
async def stream_video(video_id: int, request: Request, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = UPLOAD_DIR / video.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Increment view count
    video.views += 1
    db.commit()

    # Handle range requests for seeking
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        # Parse range header
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if byte_range[1] else file_size - 1

        async def iterfile():
            async with aiofiles.open(file_path, mode="rb") as f:
                await f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(CHUNK_SIZE, remaining)
                    data = await f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)

    # Full file streaming
    async def iterfile():
        async with aiofiles.open(file_path, mode="rb") as f:
            while chunk := await f.read(CHUNK_SIZE):
                yield chunk

    return StreamingResponse(
        iterfile(), media_type="video/mp4", headers={"Content-Length": str(file_size)}
    )


@app.delete("/api/video/{video_id}")
async def delete_video(video_id: int, token: str, db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    video = (
        db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete file
    file_path = UPLOAD_DIR / video.filename
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
