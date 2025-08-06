from flask import Blueprint, request, jsonify
from api.services.wav_compression_service import compress_wav
import os

wav_compression_bp = Blueprint('wav_compression', __name__)

@wav_compression_bp.route('/compress-wav', methods=['POST'])
def compress_wav_endpoint():
    """
    Compress WAV audio files
    
    Request:
    - file: WAV file to compress
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
                "input_format": "wav",
                "output_format": "wav",
                "options": {
                    "wav_compression_level": "medium"
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
        result = compress_wav(file, input_body)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compress_wav_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 