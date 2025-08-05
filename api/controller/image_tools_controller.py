from flask import Blueprint, request, jsonify
from api.services.image_tools_service import (
    create_gif, resize_image, crop_image, get_image_colors,
    rotate_image, flip_image, enlarge_image
)
import json

image_tools_bp = Blueprint('image_tools', __name__)

@image_tools_bp.route('/create-gif', methods=['POST'])
def create_gif_endpoint():
    files = request.files.getlist('images')
    input_body_raw = request.form.get('input_body')
    
    if not files:
        return jsonify({
            'error': 'Missing files',
            'message': 'No images were uploaded'
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
        
        if 'gif_maker' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing gif_maker task',
                'message': 'tasks must contain a "gif_maker" object'
            }), 400
        
        result = create_gif(files, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'GIF creation failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/resize-image', methods=['POST'])
def resize_image_endpoint():
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
        
        if 'resize' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing resize task',
                'message': 'tasks must contain a "resize" object'
            }), 400
        
        result = resize_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Resize image failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/crop-image', methods=['POST'])
def crop_image_endpoint():
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
        
        result = crop_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Crop image failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/get-image-colors', methods=['POST'])
def get_image_colors_endpoint():
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body', '{}')
    
    if not file:
        return jsonify({
            'error': 'Missing file',
            'message': 'No file was uploaded'
        }), 400
    
    try:
        input_body = json.loads(input_body_raw)
        
        # Validate input structure
        if not isinstance(input_body, dict):
            return jsonify({
                'error': 'Invalid input format',
                'message': 'input_body must be a valid JSON object'
            }), 400
        
        result = get_image_colors(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Color extraction failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/rotate-image', methods=['POST'])
def rotate_image_endpoint():
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
        
        if 'rotate' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing rotate task',
                'message': 'tasks must contain a "rotate" object'
            }), 400
        
        result = rotate_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Rotate image failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/flip-image', methods=['POST'])
def flip_image_endpoint():
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
        
        if 'flip' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing flip task',
                'message': 'tasks must contain a "flip" object'
            }), 400
        
        result = flip_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Flip image failed',
            'message': str(e)
        }), 500

@image_tools_bp.route('/enlarge-image', methods=['POST'])
def enlarge_image_endpoint():
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
        
        if 'enlarge' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing enlarge task',
                'message': 'tasks must contain an "enlarge" object'
            }), 400
        
        result = enlarge_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Enlarge image failed',
            'message': str(e)
        }), 500 