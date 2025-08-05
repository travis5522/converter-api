from flask import Blueprint, request, jsonify
from api.services.pdf_tools_service import (
    merge_pdfs, split_pdf, flatten_pdf, resize_pdf, unlock_pdf,
    rotate_pdf, protect_pdf, extract_image_from_pdf, remove_pdf_pages,
    extract_pdf_pages
)
import json

pdf_tools_bp = Blueprint('pdf_tools', __name__)

@pdf_tools_bp.route('/merge-pdfs', methods=['POST'])
def merge_pdfs_endpoint():
    files = request.files.getlist('files')
    input_body_raw = request.form.get('input_body')
    
    if not files:
        return jsonify({
            'error': 'Missing files',
            'message': 'No PDF files were uploaded'
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
        
        if 'merge' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing merge task',
                'message': 'tasks must contain a "merge" object'
            }), 400
        
        result = merge_pdfs(files, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF merge failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/split-pdf', methods=['POST'])
def split_pdf_endpoint():
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
        
        if 'split' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing split task',
                'message': 'tasks must contain a "split" object'
            }), 400
        
        result = split_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF split failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/flatten-pdf', methods=['POST'])
def flatten_pdf_endpoint():
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
        
        if 'flatten' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing flatten task',
                'message': 'tasks must contain a "flatten" object'
            }), 400
        
        result = flatten_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF flatten failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/resize-pdf', methods=['POST'])
def resize_pdf_endpoint():
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
        
        result = resize_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF resize failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/unlock-pdf', methods=['POST'])
def unlock_pdf_endpoint():
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
        
        if 'unlock' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing unlock task',
                'message': 'tasks must contain an "unlock" object'
            }), 400
        
        result = unlock_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF unlock failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/rotate-pdf', methods=['POST'])
def rotate_pdf_endpoint():
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
        
        result = rotate_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF rotate failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/protect-pdf', methods=['POST'])
def protect_pdf_endpoint():
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
        
        if 'protect' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing protect task',
                'message': 'tasks must contain a "protect" object'
            }), 400
        
        result = protect_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF protection failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/extract-image-from-pdf', methods=['POST'])
def extract_image_from_pdf_endpoint():
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
        
        if 'extract_image' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing extract_image task',
                'message': 'tasks must contain an "extract_image" object'
            }), 400
        
        result = extract_image_from_pdf(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Image extraction failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/remove-pdf-pages', methods=['POST'])
def remove_pdf_pages_endpoint():
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
        
        if 'remove_pages' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing remove_pages task',
                'message': 'tasks must contain a "remove_pages" object'
            }), 400
        
        result = remove_pdf_pages(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF page removal failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/extract-pdf-pages', methods=['POST'])
def extract_pdf_pages_endpoint():
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
        
        if 'extract_pages' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing extract_pages task',
                'message': 'tasks must contain an "extract_pages" object'
            }), 400
        
        result = extract_pdf_pages(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'PDF page extraction failed',
            'message': str(e)
        }), 500 