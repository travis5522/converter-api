#!/usr/bin/env python3
"""
Test script for PNG compression functionality
"""

import requests
import json
import os

def test_png_compression():
    """Test PNG compression endpoint"""
    
    # Test URL (adjust if needed)
    url = "http://localhost:5000/api/png_compression/compress-png"
    
    # Create a simple test PNG file (you would need a real PNG file for testing)
    print("PNG Compression Test")
    print("=" * 50)
    
    # Test input body
    input_body = {
        "tasks": {
            "import": {
                "operation": "import/upload"
            },
            "compress": {
                "operation": "compress",
                "input": "import",
                "input_format": "png",
                "output_format": "png",
                "options": {
                    "png_compression_quality": 60,
                    "png_compression_speed": 4,
                    "png_colors": 256,
                    "compress_png_resize_output": "keep_original",
                    "target_width": 0,
                    "target_height": 0,
                    "resize_percentage": 100
                }
            },
            "export-url": {
                "operation": "export/url",
                "input": ["compress"]
            }
        }
    }
    
    print("Input body structure:")
    print(json.dumps(input_body, indent=2))
    print()
    
    print("To test this endpoint:")
    print("1. Start the Flask server: python app.py")
    print("2. Use a tool like Postman or curl to send a POST request to:")
    print(f"   {url}")
    print("3. Include a PNG file in the 'file' field")
    print("4. Include the input_body as form data")
    print()
    
    print("Expected response structure:")
    expected_response = {
        "success": True,
        "message": "PNG compressed successfully using palette mode with 256 colors",
        "download_url": "/static/images/png_compressed_YYYYMMDD_HHMMSS_compressed_filename.png",
        "export_url": "/static/images/png_compressed_YYYYMMDD_HHMMSS_compressed_filename.png",
        "file_size": 12345,
        "output_format": "png",
        "input_format": "png",
        "compression_stats": {
            "original_size": 50000,
            "compressed_size": 12345,
            "compression_ratio": "75.3%",
            "size_reduction": "37655 bytes"
        },
        "settings_used": {
            "png_compression_quality": 60,
            "png_compression_speed": 4,
            "png_colors": 256,
            "compress_png_resize_output": "keep_original",
            "compression_level": 4
        }
    }
    print(json.dumps(expected_response, indent=2))

if __name__ == "__main__":
    test_png_compression() 