"""Camera operations and streaming logic."""

import cv2
import time
import threading
import queue
from typing import Optional, Tuple
from app.settings import settings
from app.exceptions.camera import CameraNotAvailableError, StreamingError
from app.models.api.camera import CameraStatusResponse
from app.log import get_logger

logger = get_logger(__name__)


class Camera:
    """Camera handler with background streaming support."""
    
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.cap = None
        self.lock = threading.Lock()
        self.frame_queue = queue.Queue(maxsize=2)  # Small buffer to prevent memory issues
        self.is_streaming = False
        self.stream_thread = None
        self._initialize_camera()
    
    def _initialize_camera(self) -> None:
        """Initialize camera with fallback device detection."""
        # Try multiple camera devices to find a working one
        for device in [self.device_id, 0, 1, 2]:
            try:
                logger.info("Trying camera device: %s", device)
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        logger.info("Successfully initialized camera on device: %s", device)
                        self.cap = cap
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)
                        self.cap.set(cv2.CAP_PROP_FPS, settings.camera_fps)
                        # Optimize camera for streaming
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize latency
                        return
                    else:
                        cap.release()
                else:
                    cap.release()
            except Exception as e:
                logger.error("Error with camera device %s: %s", device, e)
        
        logger.error("No working camera found!")
        self.cap = None

    def start_streaming(self) -> None:
        """Start background frame capture for streaming."""
        # Reinitialize camera if it was released
        if not self.cap or not self.cap.isOpened():
            logger.info("Camera was released, reinitializing...")
            self._initialize_camera()
        
        if self.is_streaming or not self.cap:
            return
        
        self.is_streaming = True
        self.stream_thread = threading.Thread(target=self._capture_frames)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        logger.info("Camera streaming started")
        
    def stop_streaming(self) -> None:
        """Stop background frame capture."""
        self.is_streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1.0)
        logger.info("Camera streaming stopped")
    
    def _encode_frame(self, frame, quality: int = 85, format_type: str = "webp") -> Optional[bytes]:
        """Encode frame with specified format and quality."""
        if format_type.lower() == "webp":
            ret, encoded = cv2.imencode('.webp', frame, [cv2.IMWRITE_WEBP_QUALITY, quality])
        else:  # Default to JPEG
            ret, encoded = cv2.imencode('.jpg', frame, [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1
            ])
        
        if ret:
            return encoded.tobytes()
        return None

    def _capture_frames(self) -> None:
        """Background thread to capture frames."""
        target_fps = settings.camera_fps
        frame_time = 1.0 / target_fps
        
        while self.is_streaming and self.cap and self.cap.isOpened():
            start_time = time.time()
            
            with self.lock:
                ret, frame = self.cap.read()
                
            if ret:
                # Encode frame to WebP for better compression
                frame_bytes = self._encode_frame(frame, quality=85, format_type="webp")
                
                if frame_bytes:
                    # Add to queue, remove old frame if queue is full
                    try:
                        self.frame_queue.put_nowait(frame_bytes)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()  # Remove oldest frame
                            self.frame_queue.put_nowait(frame_bytes)  # Add new frame
                        except queue.Empty:
                            pass
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self, format_type: str = "webp") -> Tuple[bytes, str]:
        """Get single frame for snapshot."""
        with self.lock:
            if self.cap is None or not self.cap.isOpened():
                raise CameraNotAvailableError("Camera is not available")
                
            ret, frame = self.cap.read()
            if not ret:
                raise StreamingError("Failed to capture frame")
            
            # Try WebP first, fallback to JPEG if WebP fails
            frame_bytes = self._encode_frame(frame, quality=90, format_type=format_type)
            if frame_bytes is None and format_type == "webp":
                frame_bytes = self._encode_frame(frame, quality=90, format_type="jpeg")
                format_type = "jpeg"
            
            if frame_bytes is None:
                raise StreamingError("Failed to encode frame")
                
            return frame_bytes, format_type
    
    def get_stream_frame(self) -> Optional[bytes]:
        """Get frame from streaming buffer."""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def get_status(self) -> CameraStatusResponse:
        """Get camera status information."""
        # Handle released camera
        if not self.cap:
            return CameraStatusResponse(
                camera_id=self.device_id,
                status="released",
                is_streaming=False,
                frame_rate=None,
                resolution=None
            )
            
        is_opened = self.cap.isOpened()
        status = "active" if is_opened else "inactive"
        
        return CameraStatusResponse(
            camera_id=self.device_id,
            status=status,
            is_streaming=self.is_streaming,
            frame_rate=settings.camera_fps if is_opened else None,
            resolution="%sx%s" % (settings.camera_width, settings.camera_height) if is_opened else None
        )
    
    def release(self) -> None:
        """Release camera resources."""
        self.stop_streaming()
        with self.lock:
            if self.cap and self.cap.isOpened():
                self.cap.release()
                self.cap = None  # Set to None so we know it needs reinitialization
        logger.info("Camera resources released")


# Global camera instance
_camera_instance: Optional[Camera] = None


def get_camera() -> Camera:
    """Get the global camera instance, initializing if needed."""
    global _camera_instance
    if _camera_instance is None:
        logger.info("Initializing camera on first use")
        _camera_instance = Camera(device_id=settings.camera_device_id)
    return _camera_instance


def initialize_camera(device_id: int = None) -> Camera:
    """Initialize the global camera instance."""
    global _camera_instance
    device_id = device_id or settings.camera_device_id
    logger.info("Explicitly initializing camera with device_id: %s", device_id)
    _camera_instance = Camera(device_id=device_id)
    return _camera_instance


def release_camera() -> None:
    """Release the global camera instance."""
    global _camera_instance
    if _camera_instance:
        _camera_instance.release()
        _camera_instance = None  # Reset to None so it gets reinitialized next time
        logger.info("Global camera instance released")


def generate_stream_frames():
    """Generator for streaming frames."""
    camera = get_camera()
    while camera.is_streaming:
        frame = camera.get_stream_frame()
        if frame:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/webp\r\n\r\n' + frame + b'\r\n'
            )
        else:
            # If no frame available, wait a bit and try again
            time.sleep(0.01)  # 10ms wait 