"""Camera-specific exception classes."""

from app.exceptions.base import HomeCamException, NotFoundError
from fastapi import status


class CameraError(HomeCamException):
    """Base camera error."""
    
    def __init__(self, detail: str = "Camera error occurred"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CameraNotFoundError(NotFoundError):
    """Camera not found or not accessible."""
    
    def __init__(self, camera_id: int = None):
        detail = f"Camera {camera_id} not found" if camera_id else "Camera not found"
        super().__init__(detail=detail)


class CameraNotAvailableError(CameraError):
    """Camera is not available for streaming."""
    
    def __init__(self, detail: str = "Camera is not available"):
        super().__init__(detail=detail)


class StreamingError(CameraError):
    """Error occurred during streaming."""
    
    def __init__(self, detail: str = "Streaming error occurred"):
        super().__init__(detail=detail) 