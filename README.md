# HomeCam API

A simple, containerized FastAPI application to stream your USB webcam over the network. Turn any computer with a USB camera into a network camera.

The web interface provides a live feed with controls to refresh the stream or take a snapshot.

## ✨ Features

- **Live Video Streaming**: Real-time MJPEG stream accessible from any web browser on your network.
- **High-Quality Snapshots**: Grab a full-resolution JPEG snapshot anytime.
- **Dockerized**: Built for cross-platform deployment (linux/amd64, linux/arm64) for easy setup on servers, Raspberry Pi, etc.
- **Configurable**: Easily change camera device, resolution, and FPS using environment variables.
- **Robust Camera Detection**: Automatically finds a working camera if the specified one isn't available.
- **Helper Scripts**: Includes scripts for camera detection, building multi-arch images, and one-command server deployment.

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Camera Handling**: OpenCV
- **Containerization**: Docker & Docker Compose
- **Dependency Management**: `uv`

---

## 🚀 Getting Started (Docker Compose)

This is the recommended method for local development or simple deployments.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
- A USB Webcam connected to your machine.

### 1. Clone the Repository

```bash
git clone https://github.com/ptt3199/homecam-api.git
cd homecam-api
```

### 2. Find Your Camera Device

Before running the application, you need to know which device index your camera is using (e.g., `0`, `1`, etc.).

Run the provided helper script on the **host machine (not in Docker)**:

```bash
python3 find_camera.py
```

This will test camera indices and show you which ones are working, along with their resolutions. Note the recommended index.

### 3. Configure the Application

The application is configured via `docker-compose.yml`.

1.  Open `docker-compose.yml`.
2.  **Update Camera Device**:
    - In the `devices` section, make sure the correct `/dev/videoX` device is listed, where `X` is the index you found in the previous step.
    - In the `environment` section, set `CAMERA_DEVICE_ID` to the same index `X`.

    ```yaml
    services:
      homecam-api:
        # ...
        devices:
          - /dev/video0:/dev/video0 # <-- Change if your camera is not video0
          - /dev/video1:/dev/video1
          - /dev/video2:/dev/video2
        environment:
          - CAMERA_DEVICE_ID=0 # <-- Change to your camera's index
          - CAMERA_WIDTH=1280
          - CAMERA_HEIGHT=720
          - CAMERA_FPS=10
    ```

### 4. Build and Run

From the project root, run:

```bash
docker-compose up --build
```

To run it in the background, use `docker-compose up -d --build`.

### 5. Access Your Webcam

- **Web Interface**: Open your browser and go to `http://localhost:8020`
- **Direct Video Stream**: `http://localhost:8020/video_feed`

---

## ☁️ Deployment

This application is designed for easy deployment on a server (e.g., an Ubuntu server or a Raspberry Pi).

For detailed instructions, see:
- **[Server Deployment Guide](./SERVER_DEPLOYMENT.md)**: A guide for quick deployment using the `deploy-server.sh` script.
- **[Ubuntu Deployment Guide](./UBUNTU_DEPLOYMENT.md)**: A more detailed guide for setting up a fresh Ubuntu server.

---

## 🔌 API Endpoints

- `GET /`: Displays the main HTML page with the video stream.
- `GET /video_feed`: The MJPEG video stream.
- `GET /snapshot`: Returns a single high-quality JPEG image from the camera.
- `GET /camera/status`: Returns a JSON object with the current camera status.
- `GET /camera/debug`: Scans for available cameras and returns a JSON report.

---

## 📜 Helper Scripts

This project includes several scripts to simplify development and deployment.

- **`find_camera.py`**: Helps you identify the correct camera device index on your host machine.
- **`build-and-push.sh`**: Builds and pushes multi-platform (amd64, arm64) Docker images to Docker Hub. Useful for CI/CD.
- **`deploy-server.sh`**: A simple shell script to pull the latest image and deploy it on a remote server.
