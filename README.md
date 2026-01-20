# Enhanced Video Streaming Server

A production-ready video streaming server built with FastAPI, designed for Raspberry Pi and other platforms. Features include user authentication, video upload with chunked streaming, background processing, and a modern web interface.

## Key Features

- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Video Upload**: Chunked file upload for memory efficiency
- **Video Streaming**: HTTP range request support for video seeking and progressive download
- **Background Processing**: Async video processing (ready for FFmpeg integration)
- **Modern UI**: Responsive web interface with drag-and-drop upload
- **Database Support**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Production Ready**: Proper error handling, CORS configuration, and security measures

## What's Improved

### From Original Version
1. **Proper Async Operations**: Uses `aiofiles` for non-blocking file I/O
2. **Chunked Streaming**: Memory-efficient video streaming with range request support
3. **Background Processing**: Async video processing framework (ready for FFmpeg)
4. **Better Database Design**: Enhanced models with video metadata and processing status
5. **Modern Frontend**: Clean, responsive UI with real-time updates
6. **Security Enhancements**: Proper JWT implementation, password hashing, and input validation
7. **Error Handling**: Comprehensive error handling and user feedback
8. **File Management**: Unique filenames, file type validation, and organized storage

## Prerequisites

- **Raspberry Pi**: Model 3B+ or later (or any Linux/Windows/Mac system)
- **Python**: 3.8 or higher
- **Database**: PostgreSQL (recommended) or SQLite (for development)
- **FFmpeg** (optional): For advanced video processing
  ```bash
  # Install FFmpeg on Raspberry Pi/Debian/Ubuntu
  sudo apt update
  sudo apt install ffmpeg
  ```

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd video-streaming-server
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Database

**Option A: PostgreSQL (Production)**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb video_streaming
sudo -u postgres createuser video_user
sudo -u postgres psql -c "ALTER USER video_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE video_streaming TO video_user;"
```

**Option B: SQLite (Development)**
```bash
# Database will be created automatically as videos.db
```

### 5. Configure Environment
Create `.env` file:
```bash
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=postgresql://video_user:your_password@localhost/video_streaming
# Or for SQLite: DATABASE_URL=sqlite:///./videos.db
```

### 6. Create Required Directories
```bash
mkdir -p uploads processed thumbnails static templates
```

## Usage

### Start the Server
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the Application
- **Web Interface**: `http://<your-ip>:8000`
- **API Documentation**: `http://<your-ip>:8000/docs`
- **Alternative Docs**: `http://<your-ip>:8000/redoc`

### Using the Interface
1. **Register**: Create a new account
2. **Login**: Authenticate with your credentials
3. **Upload**: Drag and drop videos or click to browse
4. **Stream**: Click on any video to play it
5. **Manage**: View your uploaded videos and their processing status

## Adding FFmpeg Video Processing

To enable actual video processing (transcoding, thumbnail generation), uncomment the FFmpeg sections and add:

```python
import subprocess
import ffmpeg

async def process_video(video_path: Path, video_id: int, db: Session):
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        video.processing_status = "processing"
        db.commit()
        
        # Get video duration
        probe = ffmpeg.probe(str(video_path))
        duration = float(probe['streams'][0]['duration'])
        
        # Generate thumbnail
        thumbnail_path = THUMBNAIL_DIR / f"{video.filename}.jpg"
        (
            ffmpeg
            .input(str(video_path), ss=duration/2)
            .filter('scale', 320, -1)
            .output(str(thumbnail_path), vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Transcode to web-friendly format
        output_path = PROCESSED_DIR / f"{video.filename}.mp4"
        (
            ffmpeg
            .input(str(video_path))
            .output(str(output_path), 
                   vcodec='libx264',
                   acodec='aac',
                   video_bitrate='2M',
                   preset='fast')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        video.duration = int(duration)
        video.thumbnail_path = str(thumbnail_path)
        video.processed = True
        video.processing_status = "completed"
        db.commit()
        
    except Exception as e:
        video.processing_status = f"failed: {str(e)}"
        db.commit()
```

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login and receive JWT token

### Videos
- `POST /api/upload` - Upload video (multipart/form-data)
- `GET /api/videos` - List user's videos
- `GET /api/video/{id}` - Get video metadata
- `GET /api/stream/{id}` - Stream video with range support
- `DELETE /api/video/{id}` - Delete video

## Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Bcrypt for password storage
- **Input Validation**: File type checking and size limits
- **CORS Protection**: Configurable cross-origin policies
- **SQL Injection Prevention**: ORM-based queries
- **Unique File Storage**: UUID-based filenames prevent overwrites

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email
- `hashed_password`: Bcrypt hashed password
- `created_at`: Account creation timestamp

### Videos Table
- `id`: Primary key
- `title`: Video title
- `description`: Optional description
- `filename`: Unique storage filename
- `original_filename`: Original upload name
- `file_size`: File size in bytes
- `duration`: Video duration (seconds)
- `thumbnail_path`: Path to thumbnail image
- `processed`: Boolean processing status
- `processing_status`: Status string (pending/processing/completed/failed)
- `upload_date`: Upload timestamp
- `views`: View counter
- `user_id`: Foreign key to users

## Performance Tips

1. **Use PostgreSQL** for production deployments
2. **Enable caching** for frequently accessed videos
3. **Use reverse proxy** (nginx) for static file serving
4. **Implement CDN** for video delivery at scale
5. **Add Redis** for session management and caching
6. **Configure workers** based on CPU cores (usually CPU cores × 2 + 1)

## Troubleshooting

**Videos won't play:**
- Check file permissions in `uploads/` directory
- Ensure video codec is web-compatible (H.264 + AAC recommended)
- Verify server URL is accessible from client

**Upload fails:**
- Check disk space
- Verify write permissions
- Confirm file size doesn't exceed server limits

**Slow streaming:**
- Implement video transcoding to lower bitrates
- Use CDN for content delivery
- Enable HTTP/2 on your server

## License

MIT License - Feel free to use and modify

## Contributing

Feel free to fork this repo, make changes and open a PR

## Future Enhancements

- [ ] Building my own free streaming platform using the [Vidking API](https://www.vidking.net/)
- [ ] HLS/DASH adaptive streaming
- [ ] Subtitle support
- [ ] Live streaming capability
