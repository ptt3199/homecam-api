"""Camera API routes."""

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from app.operations.camera_ops import get_camera, generate_stream_frames
from app.models.api.base import BaseResponse
from app.exceptions.camera import CameraNotAvailableError, StreamingError
from app.operations.auth_ops import get_current_user, get_current_user_stream, generate_streaming_token

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/feed")
async def video_feed(user: Dict[str, Any] = Depends(get_current_user_stream)):
    """Stream camera video feed. Accepts token via ?token=xxx query parameter."""
    try:
        camera = get_camera()
        if not camera.is_streaming:
            camera.start_streaming()
        
        return StreamingResponse(
            generate_stream_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        raise StreamingError(f"Failed to start video stream: {str(e)}")


@router.post("/start")
async def start_stream(user: Dict[str, Any] = Depends(get_current_user)):
    """Start camera streaming."""
    try:
        camera = get_camera()
        if not camera.is_streaming:
            camera.start_streaming()
            return BaseResponse(message="Streaming started successfully")
        else:
            return BaseResponse(message="Streaming is already active")
    except Exception as e:
        raise StreamingError(f"Failed to start streaming: {str(e)}")


@router.post("/stop")
async def stop_stream(user: Dict[str, Any] = Depends(get_current_user)):
    """Stop camera streaming and release camera resources."""
    try:
        camera = get_camera()
        if camera.is_streaming:
            camera.stop_streaming()
            # Also release camera to turn off the camera light
            camera.release()
            return BaseResponse(message="Streaming stopped and camera released successfully")
        else:
            # Even if not streaming, try to release camera resources
            camera.release()
            return BaseResponse(message="Streaming was already inactive, camera released")
    except Exception as e:
        raise StreamingError(f"Failed to stop streaming: {str(e)}")


@router.get("/snapshot")
async def snapshot(user: Dict[str, Any] = Depends(get_current_user_stream)):
    """Take a camera snapshot. Requires streaming to be active."""
    try:
        camera = get_camera()
        
        # Check if streaming is active
        if not camera.is_streaming:
            raise StreamingError("Camera streaming must be started before taking snapshots. Use /camera/start first.")
        
        frame_bytes, format_type = camera.get_frame()
        
        media_type = f"image/{format_type}"
        return Response(content=frame_bytes, media_type=media_type)
    except Exception as e:
        raise StreamingError(f"Failed to capture snapshot: {str(e)}")


@router.get("/status")
async def camera_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get camera status and current user information."""
    try:
        # Get camera info
        from app.operations.camera_ops import _camera_instance
        
        if _camera_instance is None:
            camera_info = {
                "camera_id": 0,  # Default device ID
                "status": "uninitialized",
                "is_streaming": False,
                "frame_rate": None,
                "resolution": None
            }
        else:
            camera_status_obj = _camera_instance.get_status()
            camera_info = {
                "camera_id": camera_status_obj.camera_id,
                "status": camera_status_obj.status,
                "is_streaming": camera_status_obj.is_streaming,
                "frame_rate": camera_status_obj.frame_rate,
                "resolution": camera_status_obj.resolution
            }
        
        # Add user info from decoded token
        return {
            "camera": camera_info,
            "user": {
                "user_id": user.get("user_id"),
                "email": user.get("email"),
                "username": user.get("username")
            },
            "container_status": "running"  # Container is running if we can respond
        }
        
    except Exception as e:
        raise CameraNotAvailableError(f"Failed to get camera status: {str(e)}")



@router.post("/streaming-token")
async def get_streaming_token(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Generate a short-lived token for streaming endpoints.
    This token expires in 5 minutes and is only valid for video streaming.
    """
    user_id = user.get("user_id")
    streaming_token = generate_streaming_token(user_id, expires_minutes=5)
    
    return {
        "streaming_token": streaming_token,
        "expires_in_minutes": 5,
        "usage": "Use this token for /feed endpoint: /camera/feed?token=STREAMING_TOKEN",
        "security_note": "This token expires quickly to reduce security risks"
    } 