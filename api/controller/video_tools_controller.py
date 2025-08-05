from flask import Blueprint, request, jsonify
from api.services.video_tools_service import crop_video, trim_video
import json

video_tools_bp = Blueprint('video_tools', __name__)

@video_tools_bp.route('/crop-video', methods=['POST'])
def crop_video_endpoint():
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
        
        if 'crop' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing crop task',
                'message': 'tasks must contain a "crop" object'
            }), 400
        
        result = crop_video(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Crop video failed',
            'message': str(e)
        }), 500

@video_tools_bp.route('/trim-video', methods=['POST'])
def trim_video_endpoint():
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
        
        if 'trim' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing trim task',
                'message': 'tasks must contain a "trim" object'
            }), 400
        
        result = trim_video(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Trim video failed',
            'message': str(e)
        }), 500 