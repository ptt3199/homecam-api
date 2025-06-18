#!/usr/bin/env python3
"""
Script to find available camera devices on your system.
Run this OUTSIDE Docker to see what cameras are available.
"""

import cv2
import subprocess
import os

def list_video_devices():
    """List all video devices in /dev/"""
    print("=== Video devices in /dev/ ===")
    video_devices = []
    try:
        for device in os.listdir('/dev/'):
            if device.startswith('video'):
                device_path = f'/dev/{device}'
                video_devices.append(device_path)
                print(f"Found: {device_path}")
    except Exception as e:
        print(f"Error listing /dev/: {e}")
    
    return video_devices

def test_opencv_cameras():
    """Test OpenCV camera access"""
    print("\n=== Testing OpenCV camera access ===")
    working_cameras = []
    
    for i in range(10):
        try:
            print(f"Testing camera index {i}...")
            cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    print(f"  ✅ Camera {i}: Working! Resolution: {width}x{height}, FPS: {fps}")
                    working_cameras.append({
                        'index': i,
                        'width': width,
                        'height': height,
                        'fps': fps
                    })
                else:
                    print(f"  ❌ Camera {i}: Device opened but can't read frames")
                cap.release()
            else:
                print(f"  ❌ Camera {i}: Can't open device")
                
        except Exception as e:
            print(f"  ❌ Camera {i}: Error - {e}")
    
    return working_cameras

def get_v4l2_info():
    """Get detailed info using v4l2-ctl if available"""
    print("\n=== V4L2 device information ===")
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("v4l2-ctl not available or failed")
    except FileNotFoundError:
        print("v4l2-ctl not installed. Install with: sudo apt install v4l-utils")
    except Exception as e:
        print(f"Error running v4l2-ctl: {e}")

def main():
    print("🔍 PTT Home Camera Detection Script")
    print("=" * 50)
    
    # List video devices
    video_devices = list_video_devices()
    
    # Test OpenCV cameras
    working_cameras = test_opencv_cameras()
    
    # Get V4L2 info
    get_v4l2_info()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if video_devices:
        print(f"Video devices found: {', '.join(video_devices)}")
    else:
        print("❌ No video devices found in /dev/")
    
    if working_cameras:
        print("\n✅ Working cameras with OpenCV:")
        for cam in working_cameras:
            print(f"  - Index {cam['index']}: {cam['width']}x{cam['height']} @ {cam['fps']}fps")
        
        recommended = working_cameras[0]['index']
        print("\n💡 RECOMMENDATION:")
        print(f"   Use camera index: {recommended}")
        print("   Update your docker-compose.yml:")
        print("   devices:")
        print(f"     - /dev/video{recommended}:/dev/video{recommended}")
    else:
        print("\n❌ No working cameras found!")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Check if camera is connected and not used by another app")
        print("   2. Try: sudo chmod 666 /dev/video*")
        print("   3. Check if user is in 'video' group: groups $USER")
        print("   4. Add user to video group: sudo usermod -a -G video $USER")

if __name__ == "__main__":
    main() 