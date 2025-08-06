from flask import Blueprint, request, jsonify
from api.services.jpeg_compression_service import compress_jpeg
import os

jpeg_compression_bp = Blueprint('jpeg_compression', __name__)

@jpeg_compression_bp.route('/compress-jpeg', methods=['POST'])
def compress_jpeg_endpoint():
    """
    Compress JPEG image files with advanced options
    
    Request:
    - file: JPEG file to compress
    - input_body: JSON with compression options
    
    Example input_body:
    {
        "tasks": {
            "import": {
                "operation": "import/upload"
            },
            "compress": {
                "operation": "compress",
                "input": "import",
                "input_format": "jpeg",
                "output_format": "jpeg",
                "options": {
                    "jpeg_compression_method": "lossless",
                    "compress_jpeg_resize_output": "by_width_keep_ar",
                    "jpeg_compress_target_width": 0,
                    "jpeg_compression_type": "progressive",
                    "jpeg_compress_use_grayscale": false,
                    "jpeg_compress_reduce_chroma_sampling": true
                }
            },
            "export-url": {
                "operation": "export/url",
                "input": ["compress"]
            }
        }
    }
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get input_body from form data
        input_body_str = request.form.get('input_body', '{}')
        import json
        input_body = json.loads(input_body_str)
        
        # Call the compression service
        result = compress_jpeg(file, input_body)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compress_jpeg_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 