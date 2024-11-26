# Raspberry Pi Video Streaming Server

A simple and efficient video streaming server built for Raspberry Pi that allows users to upload and stream videos through a web interface.

## Features

- User authentication and authorization
- Video file upload functionality
- Secure video storage and streaming
- Web-based video playback interface
- RESTful API for video management

## Prerequisites

- Raspberry Pi (Model 3B+ or later recommended)
- Python 3.8+
- PostgreSQL database
- FFmpeg for video processing

## Installation

1. Clone this repository to your Raspberry Pi:
```bash
git clone <repository-url>
cd video-streaming-server
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb video_streaming
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

6. Initialize the database:
```bash
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. Access the web interface:
   - Open a web browser and navigate to `http://<raspberry-pi-ip>:8000`
   - Register a new user account
   - Log in to upload and stream videos

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://<raspberry-pi-ip>:8000/docs`
- ReDoc: `http://<raspberry-pi-ip>:8000/redoc`

## Security Considerations

- The server uses JWT tokens for authentication
- All passwords are hashed using bcrypt
- Video files are stored securely with proper access controls
- CORS is configured to allow specific origins only

## Directory Structure

```
video-streaming-server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── auth.py
├── static/
├── uploads/
├── templates/
├── .env
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

