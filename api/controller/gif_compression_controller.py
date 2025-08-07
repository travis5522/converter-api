from flask import Blueprint, request, jsonify
from api.services.gif_compression_service import compress_gif
import os

gif_compression_bp = Blueprint('gif_compression', __name__)

@gif_compression_bp.route('/compress-gif', methods=['POST'])
def compress_gif_endpoint():
    """
    Compress GIF files with advanced options
    
    Request:
    - file: GIF file to compress
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
                "input_format": "gif",
                "output_format": "gif",
                "options": {
                    "gif_undo_optimization": false,
                    "gif_compression_level": 75,
                    "gif_compress_reduce_frames": "no-change",
                    "gif_optimize_transparency": false,
                    "gif_color": "reduce",
                    "gif_compress_number_of_colors": 256
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
        
        # Check if file is GIF
        if not file.filename.lower().endswith('.gif'):
            return jsonify({'success': False, 'error': 'Only GIF files are supported'}), 400
        
        # Get input_body from form data
        input_body_str = request.form.get('input_body', '{}')
        import json
        input_body = json.loads(input_body_str)
        
        # Call the compression service
        result = compress_gif(file, input_body)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compress_gif_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 