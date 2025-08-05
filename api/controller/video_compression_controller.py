from flask import Blueprint, request, jsonify
from api.services.video_compression_service import compress_video
import json

video_compression_bp = Blueprint('video_compression', __name__)

@video_compression_bp.route('/compress-video', methods=['POST'])
def compress_video_endpoint():
    """
    Video compression endpoint.
    Supports compression-specific options like:
    - Video bitrate control
    - Compression level (CRF)
    - Resolution scaling
    - Frame rate adjustment
    - Audio compression settings
    - Two-pass encoding
    - Web optimization
    """
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({
            'error': 'Missing file',
            'message': 'No file was uploaded',
            'example': {
                'file': 'video file to compress',
                'input_body': {
                    'tasks': {
                        'compress': {
                            'options': {
                                'videoCodec': 'h264',
                                'videoBitrate': 2000,
                                'compressionLevel': 23,
                                'resolution': '1920x1080',
                                'frameRate': 'original',
                                'removeAudio': False,
                                'audioCodec': 'aac',
                                'audioBitrate': 128,
                                'twoPassEncoding': False,
                                'optimizeForWeb': True
                            }
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
        
        result = compress_video(file, input_body)
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