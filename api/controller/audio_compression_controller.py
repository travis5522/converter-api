from flask import Blueprint, request, jsonify
from api.services.audio_compression_service import compress_audio
import json

audio_compression_bp = Blueprint('audio_compression', __name__)

@audio_compression_bp.route('/compress-audio', methods=['POST'])
def compress_audio_endpoint():
    """
    Audio compression endpoint.
    Supports compression-specific options like:
    - Target file size (percentage)
    - Target file size (MB)
    - Target audio quality
    """
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({
            'error': 'Missing file',
            'message': 'No file was uploaded',
            'example': {
                'file': 'MP3 file to compress',
                'input_body': {
                    'tasks': {
                        'import': {
                            'operation': 'import/upload'
                        },
                        'compress': {
                            'operation': 'compress',
                            'input': 'import',
                            'input_format': 'mp3',
                            'output_format': 'mp3',
                            'options': {
                                'compression_method': 'percentage',
                                'target_size_percentage': 40
                            }
                        },
                        'export-url': {
                            'operation': 'export/url',
                            'input': ['compress']
                        }
                    }
                }
            }
        }), 400
    
    if not input_body_raw:
        return jsonify({
            'error': 'Missing input data',
            'message': 'No input_body provided'
        }), 400
    
    try:
        input_body = json.loads(input_body_raw)
        
        # Validate input structure
        if not isinstance(input_body, dict):
            return jsonify({
                'error': 'Invalid input format',
                'message': 'input_body must be a valid JSON object'
            }), 400
        
        if 'tasks' not in input_body:
            return jsonify({
                'error': 'Missing tasks',
                'message': 'input_body must contain a "tasks" object'
            }), 400
        
        if 'compress' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing compress task',
                'message': 'tasks must contain a "compress" object'
            }), 400
        
        result = compress_audio(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Compression failed',
            'message': str(e)
        }), 500 