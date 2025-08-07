from flask import Blueprint, request, jsonify
from api.services.pdf_tools_service import (
    merge_pdfs, split_pdf, flatten_pdf, resize_pdf, unlock_pdf,
    rotate_pdf, protect_pdf, extract_image_from_pdf, remove_pdf_pages,
    extract_pdf_pages, upload_pdf_file, get_pdf_pages, split_pdf_by_file_id,
    remove_pages_by_file_id, extract_all_images_from_pdf, extract_pages_by_file_id
)
import json
import os

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

@pdf_tools_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf_endpoint():
    """Upload PDF file and return file_id for processing"""
    file = request.files.get('file')
    
    if not file:
        return jsonify({
            'success': False,
            'error': 'Missing file',
            'message': 'No PDF file was uploaded'
        }), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Invalid file type',
            'message': 'Only PDF files are supported'
        }), 400
    
    try:
        result = upload_pdf_file(file)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/get-pdf-pages/<file_id>', methods=['GET'])
def get_pdf_pages_endpoint(file_id):
    """Get PDF pages information with previews"""
    try:
        result = get_pdf_pages(file_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get PDF pages',
            'message': str(e)
        }), 500

@pdf_tools_bp.route('/split-pdf', methods=['POST'])
def split_pdf_endpoint():
    """Split PDF using file_id (updated for new workflow)"""
    try:
        # Check if this is a file upload (old method) or file_id (new method)
        file = request.files.get('file')
        input_body_raw = request.form.get('input_body')
        
        if file and input_body_raw:
            # Old method - file upload with form data
            if not input_body_raw:
                return jsonify({
                    'success': False,
                    'error': 'Missing input data',
                    'message': 'No input_body provided'
                }), 400
            
            try:
                input_body = json.loads(input_body_raw)
                
                # Validate input structure
                if not isinstance(input_body, dict):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid input format',
                        'message': 'input_body must be a valid JSON object'
                    }), 400
                
                if 'tasks' not in input_body:
                    return jsonify({
                        'success': False,
                        'error': 'Missing tasks',
                        'message': 'input_body must contain a "tasks" object'
                    }), 400
                
                if 'split' not in input_body['tasks']:
                    return jsonify({
                        'success': False,
                        'error': 'Missing split task',
                        'message': 'tasks must contain a "split" object'
                    }), 400
                
                result = split_pdf(file, input_body)
                return jsonify(result)
                
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON',
                    'message': f'Failed to parse input_body: {str(e)}'
                }), 400
                
        else:
            # New method - JSON body with file_id
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Invalid content type',
                    'message': 'Request must be JSON for file_id method'
                }), 400
            
            input_body = request.get_json()
            
            if not input_body:
                return jsonify({
                    'success': False,
                    'error': 'Missing input data',
                    'message': 'No JSON body provided'
                }), 400
            
            if 'file_id' not in input_body:
                return jsonify({
                    'success': False,
                    'error': 'Missing file_id',
                    'message': 'file_id is required'
                }), 400
            
            if 'tasks' not in input_body:
                return jsonify({
                    'success': False,
                    'error': 'Missing tasks',
                    'message': 'input_body must contain a "tasks" object'
                }), 400
            
            if 'split' not in input_body['tasks']:
                return jsonify({
                    'success': False,
                    'error': 'Missing split task',
                    'message': 'tasks must contain a "split" object'
                }), 400
            
            result = split_pdf_by_file_id(input_body)
            return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
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

@pdf_tools_bp.route('/rotate-pdf/<file_id>', methods=['POST'])
def rotate_pdf_endpoint(file_id):
    input_body_raw = request.form.get('input_body')
    
    if not file_id:
        return jsonify({
            'error': 'Missing file_id',
            'message': 'No file_id provided'
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
        
        result = rotate_pdf(file_id, input_body)
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

@pdf_tools_bp.route('/download-pdf/<file_id>', methods=['GET'])
def download_pdf_endpoint(file_id):
    """Download PDF file by file_id"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found',
                'message': 'PDF file not found'
            }), 404
        
        # Return file as response
        from flask import send_file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Download failed',
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

@pdf_tools_bp.route('/extract-all-images', methods=['POST'])
def extract_all_images_endpoint():
    """Extract all images from PDF and return as ZIP file"""
    file = request.files.get('file')
    
    if not file:
        return jsonify({
            'error': 'Missing file',
            'message': 'No file was uploaded'
        }), 400
    
    try:
        result = extract_all_images_from_pdf(file)
        return jsonify(result)
        
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

@pdf_tools_bp.route('/remove-pages', methods=['POST'])
def remove_pages_endpoint():
    """Remove pages from PDF using file_id and page_ids"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'message': 'No JSON data provided'
            }), 400
        
        file_id = data.get('file_id')
        page_ids = data.get('page_ids', [])
        
        if not file_id:
            return jsonify({
                'error': 'Missing file_id',
                'message': 'file_id is required'
            }), 400
        
        if not page_ids:
            return jsonify({
                'error': 'Missing page_ids',
                'message': 'page_ids array is required'
            }), 400
        
        if not isinstance(page_ids, list):
            return jsonify({
                'error': 'Invalid page_ids format',
                'message': 'page_ids must be an array'
            }), 400
        
        result = remove_pages_by_file_id(file_id, page_ids)
        return jsonify(result)
        
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

@pdf_tools_bp.route('/extract-pages', methods=['POST'])
def extract_pages_endpoint():
    """Extract pages from PDF using file_id and page ranges"""
    try:
        file_id = request.form.get('file_id')
        page_ranges_raw = request.form.get('page_ranges')
        merge_output = request.form.get('merge_output', 'false').lower() == 'true'
        compression_level = request.form.get('compression_level', 'none')
        password = request.form.get('password', '')
        
        if not file_id:
            return jsonify({
                'error': 'Missing file_id',
                'message': 'file_id is required'
            }), 400
        
        if not page_ranges_raw:
            return jsonify({
                'error': 'Missing page_ranges',
                'message': 'page_ranges is required'
            }), 400
        
        try:
            page_ranges = json.loads(page_ranges_raw)
        except json.JSONDecodeError:
            return jsonify({
                'error': 'Invalid page_ranges format',
                'message': 'page_ranges must be a valid JSON array'
            }), 400
        
        # Call the service function
        result = extract_pages_by_file_id(file_id, page_ranges, merge_output, compression_level, password)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'PDF page extraction failed',
            'message': str(e)
        }), 500