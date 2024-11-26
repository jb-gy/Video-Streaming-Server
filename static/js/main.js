// Global variables
let token = localStorage.getItem('token');
const API_URL = '';  // Will be set to the appropriate URL when deployed

// DOM Elements
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const logoutBtn = document.getElementById('logout-btn');
const authModal = document.getElementById('auth-modal');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const uploadSection = document.getElementById('upload-section');
const uploadForm = document.getElementById('upload-form');
const videosContainer = document.getElementById('videos-container');

// Event Listeners
loginBtn.addEventListener('click', () => showAuthModal('login'));
registerBtn.addEventListener('click', () => showAuthModal('register'));
logoutBtn.addEventListener('click', logout);
loginForm.addEventListener('submit', handleLogin);
registerForm.addEventListener('submit', handleRegister);
uploadForm.addEventListener('submit', handleUpload);

// Check authentication status on page load
checkAuth();

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
        });

        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            hideAuthModal();
            checkAuth();
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch(`${API_URL}/users/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password }),
        });

        if (response.ok) {
            alert('Registration successful! Please login.');
            showAuthModal('login');
        } else {
            alert('Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed');
    }
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    checkAuth();
}

// UI Functions
function showAuthModal(type) {
    authModal.classList.remove('hidden');
    if (type === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
    }
}

function hideAuthModal() {
    authModal.classList.add('hidden');
}

function checkAuth() {
    if (token) {
        loginBtn.classList.add('hidden');
        registerBtn.classList.add('hidden');
        logoutBtn.classList.remove('hidden');
        uploadSection.classList.remove('hidden');
        loadVideos();
    } else {
        loginBtn.classList.remove('hidden');
        registerBtn.classList.remove('hidden');
        logoutBtn.classList.add('hidden');
        uploadSection.classList.add('hidden');
    }
}

// Video Functions
async function handleUpload(e) {
    e.preventDefault();
    const title = document.getElementById('video-title').value;
    const file = document.getElementById('video-file').files[0];

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    try {
        const response = await fetch(`${API_URL}/upload/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (response.ok) {
            alert('Video uploaded successfully!');
            loadVideos();
            e.target.reset();
        } else {
            alert('Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Upload failed');
    }
}

async function loadVideos() {
    try {
        const response = await fetch(`${API_URL}/videos/`, {
            headers: token ? {
                'Authorization': `Bearer ${token}`,
            } : {},
        });

        if (response.ok) {
            const videos = await response.json();
            displayVideos(videos);
        }
    } catch (error) {
        console.error('Error loading videos:', error);
    }
}

function displayVideos(videos) {
    videosContainer.innerHTML = '';
    videos.forEach(video => {
        const videoCard = document.createElement('div');
        videoCard.className = 'video-card';
        videoCard.innerHTML = `
            <h3>${video.title}</h3>
            <video controls>
                <source src="${API_URL}/uploads/${video.filename}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <p>Uploaded: ${new Date(video.upload_date).toLocaleDateString()}</p>
        `;
        videosContainer.appendChild(videoCard);
    });
}
