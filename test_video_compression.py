#!/usr/bin/env python3
"""
Simple test script for video compression endpoint
Run this to test if the video compression backend is working
"""

import requests
import json
import os

# Configuration
BASE_URL = 'http://localhost:5000'  # Adjust if your server runs on different port
ENDPOINT = '/api/video_compression/compress-video'

def test_video_compression():
    """Test the video compression endpoint"""
    
    # Test payload
    test_payload = {
        "tasks": {
            "compress": {
                "options": {
                    "videoCodec": "h264",
                    "videoBitrate": 1000,
                    "compressionLevel": 28,
                    "resolution": "1280x720",
                    "frameRate": "24",
                    "removeAudio": False,
                    "audioCodec": "aac",
                    "audioBitrate": 128,
                    "twoPassEncoding": False,
                    "optimizeForWeb": True
                }
            }
        }
    }
    
    print("🧪 Testing Video Compression Endpoint")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("=" * 50)
    
    # Test without file (should return error with example)
    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            data={'input_body': json.dumps(test_payload)},
            headers={'ngrok-skip-browser-warning': 'true'}
        )
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 400:
            result = response.json()
            if 'example' in result:
                print("✅ Endpoint properly returns example structure when no file provided")
                print(f"Example structure: {json.dumps(result['example'], indent=2)}")
            else:
                print(f"❌ Missing example in error response: {result}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask server is running")
        print("   Run: python app.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    print("\n🎯 Next Steps:")
    print("1. Start the Flask server: python app.py")
    print("2. Test with a real video file through the frontend")
    print("3. Check the /static/videos/ directory for output files")
    
    return True

def test_health_check():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health/ffmpeg")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ FFmpeg Status: {result.get('status', 'unknown')}")
            print(f"   Version: {result.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ FFmpeg health check failed: {response.status_code}")
            return False
    except:
        print("❌ Server not responding")
        return False

if __name__ == "__main__":
    print("🚀 Video Compression Backend Test")
    print("=" * 50)
    
    # Test server health first
    if test_health_check():
        print()
        test_video_compression()
    else:
        print("\n💡 Make sure to:")
        print("1. Install FFmpeg on your system")
        print("2. Start the Flask server: python app.py")
        print("3. Install required Python packages: pip install -r requirements.txt") 