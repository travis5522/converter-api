from flask import Blueprint, request, jsonify
from api.services.png_compression_service import compress_png
import os

png_compression_bp = Blueprint('png_compression', __name__)

@png_compression_bp.route('/compress-png', methods=['POST'])
def compress_png_endpoint():
    """
    Compress PNG image files with advanced options
    
    Request:
    - file: PNG file to compress
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
        result = compress_png(file, input_body)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compress_png_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 