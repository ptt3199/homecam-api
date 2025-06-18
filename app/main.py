import cv2
import time
from fastapi import FastAPI, Request, Response  
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import threading
from contextlib import asynccontextmanager
from app.settings import settings

class Camera:
  def __init__(self, device_id=0):
    self.device_id = device_id
    self.cap = None
    self.lock = threading.Lock()
    self._initialize_camera()
  
  def _initialize_camera(self):
    # Try multiple camera devices to find a working one
    for device in [self.device_id, 0, 1, 2]:
      try:
        print(f"Trying camera device: {device}")
        cap = cv2.VideoCapture(device)
        if cap.isOpened():
          ret, frame = cap.read()
          if ret:
            print(f"Successfully initialized camera on device: {device}")
            self.cap = cap
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, settings.camera_fps)
            return
          else:
            cap.release()
        else:
          cap.release()
      except Exception as e:
        print(f"Error with camera device {device}: {e}")
    
    print("No working camera found!")
    self.cap = None

  def get_frame(self):
    with self.lock:
      if self.cap is None or not self.cap.isOpened():
        return b''
        
      ret, frame = self.cap.read()
      if not ret:
        return b''
      
      ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
      if not ret:
        return b''
        
      return jpeg.tobytes()

  def release(self):
    with self.lock:
      if self.cap and self.cap.isOpened():
        self.cap.release()

# Global camera instance
camera = None

@asynccontextmanager
async def lifespan(app: FastAPI):
  global camera
  # Print current settings for debugging
  print("=== PTT Home Configuration ===")
  print(f"Camera Device ID: {settings.camera_device_id}")
  print(f"Camera Resolution: {settings.camera_width}x{settings.camera_height}")
  print(f"Camera FPS: {settings.camera_fps}")
  print("=" * 30)
  
  camera = Camera(device_id=settings.camera_device_id)
  try:
    yield
  finally:
    if camera:
      camera.release()
      print("Camera resource released.")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

def gen_frames():
  while True:
    frame = camera.get_frame()
    if frame:
      yield (
        b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
      )
    else:
      break
    time.sleep(0.1)  # 10 FPS to match your camera

@app.get('/')
async def index(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get('/video_feed')
def video_feed():
  return StreamingResponse(
    gen_frames(), 
    media_type='multipart/x-mixed-replace; boundary=frame'
  )

@app.get('/snapshot')
def snapshot():
  frame = camera.get_frame()
  if frame:
    return Response(content=frame, media_type="image/jpeg")
  else:
    return Response(status_code=404, content="Camera not available")

@app.get('/camera/status')
def camera_status():
  return {
    "camera_available": camera.cap is not None and camera.cap.isOpened(),
    "device_id": camera.device_id if camera else None,
    "camera_initialized": camera is not None
  }

@app.get('/camera/debug')
def camera_debug():
  available_cameras = []
  for i in range(10):  # Check first 10 camera indices
    try:
      cap = cv2.VideoCapture(i)
      if cap.isOpened():
        ret, frame = cap.read()
        if ret:
          available_cameras.append({
            "device_id": i,
            "working": True,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
          })
        else:
          available_cameras.append({"device_id": i, "working": False})
        cap.release()
    except Exception as e:
      available_cameras.append({"device_id": i, "error": str(e)})
  
  return {"available_cameras": available_cameras}
