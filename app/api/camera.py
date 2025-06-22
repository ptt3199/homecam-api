"""Camera API routes."""

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from app.operations.auth_ops import require_auth
from app.operations.camera_ops import get_camera, generate_stream_frames
from app.models.api.camera import (
    CameraStatusResponse, 
    StreamStatusResponse, 
    CameraFormatsResponse
)
from app.models.api.base import BaseResponse
from app.exceptions.camera import CameraNotAvailableError, StreamingError

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/video_feed")
async def video_feed(user: Dict[str, Any] = Depends(require_auth)):
    """Stream camera video feed."""
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


@router.get("/snapshot")
async def snapshot(user: Dict[str, Any] = Depends(require_auth)):
    """Take a camera snapshot. Requires streaming to be active."""
    try:
        camera = get_camera()
        
        # Check if streaming is active
        if not camera.is_streaming:
            raise StreamingError("Camera streaming must be started before taking snapshots. Use /camera/stream/start first.")
        
        frame_bytes, format_type = camera.get_frame()
        
        media_type = f"image/{format_type}"
        return Response(content=frame_bytes, media_type=media_type)
    except Exception as e:
        raise StreamingError(f"Failed to capture snapshot: {str(e)}")


@router.get("/snapshot/{format_type}")
async def snapshot_with_format(
    format_type: str, 
    user: Dict[str, Any] = Depends(require_auth)
):
    """Take a camera snapshot with specific format. Requires streaming to be active."""
    if format_type not in ["jpeg", "webp", "png"]:
        raise StreamingError("Unsupported format. Use: jpeg, webp, or png")
    
    try:
        camera = get_camera()
        
        # Check if streaming is active
        if not camera.is_streaming:
            raise StreamingError("Camera streaming must be started before taking snapshots. Use /camera/stream/start first.")
        
        frame_bytes, actual_format = camera.get_frame(format_type=format_type)
        
        media_type = f"image/{actual_format}"
        return Response(content=frame_bytes, media_type=media_type)
    except Exception as e:
        raise StreamingError(f"Failed to capture snapshot: {str(e)}")


@router.get("/status", response_model=CameraStatusResponse)
async def camera_status(user: Dict[str, Any] = Depends(require_auth)):
    """Get camera status information."""
    try:
        # Check if camera instance exists without initializing it
        from app.operations.camera_ops import _camera_instance
        
        if _camera_instance is None:
            # Return status for uninitialized camera
            return CameraStatusResponse(
                camera_id=0,  # Default device ID
                status="uninitialized",
                is_streaming=False,
                frame_rate=None,
                resolution=None
            )
        
        return _camera_instance.get_status()
    except Exception as e:
        raise CameraNotAvailableError(f"Failed to get camera status: {str(e)}")


@router.get("/stream/status", response_model=StreamStatusResponse)
async def stream_status(user: Dict[str, Any] = Depends(require_auth)):
    """Get streaming status information."""
    try:
        camera = get_camera()
        return camera.get_stream_status()
    except Exception as e:
        raise CameraNotAvailableError(f"Failed to get stream status: {str(e)}")


@router.post("/stream/start", response_model=BaseResponse)
async def start_stream(user: Dict[str, Any] = Depends(require_auth)):
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


@router.post("/stream/stop", response_model=BaseResponse)
async def stop_stream(user: Dict[str, Any] = Depends(require_auth)):
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


@router.get("/formats", response_model=CameraFormatsResponse)
async def supported_formats(user: Dict[str, Any] = Depends(require_auth)):
    """Get supported camera formats."""
    return CameraFormatsResponse(
        formats=["jpeg", "webp", "png"],
        default_format="webp"
    ) 