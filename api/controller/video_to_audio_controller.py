from flask import Blueprint, request, jsonify
from api.services.video_to_audio_service import convert_video_to_audio
import json

video_to_audio_bp = Blueprint('video_to_audio', __name__)

@video_to_audio_bp.route('/video-to-audio', methods=['POST'])
def video_to_audio():
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({
            'error': 'Missing file',
            'message': 'No file was uploaded'
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
        
        if 'convert' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing convert task',
                'message': 'tasks must contain a "convert" object'
            }), 400
        
        result = convert_video_to_audio(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Conversion failed',
            'message': str(e)
        }), 500