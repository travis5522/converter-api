from flask import Blueprint, request, jsonify
from api.services.document_converter_service import convert_document
import json

document_converter_bp = Blueprint('document_converter', __name__)

@document_converter_bp.route('/document-convert', methods=['POST'])
def document_convert():
    """
    Convert document files between different formats.
    
    Supports: PDF, DOCX, EPUB, JPG conversion
    """
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file or not input_body_raw:
        return jsonify({
            'error': 'Missing file or input data',
            'message': 'Both "file" and "input_body" are required',
            'example': {
                'input_body': {
                    'tasks': {
                        'convert': {
                            'output_format': 'pdf',
                            'options': {
                                'page_size': 'A4',
                                'quality': 'high',
                                'preserve_formatting': True
                            }
                        }
                    }
                }
            }
        }), 400
    
    try:
        input_body = json.loads(input_body_raw)
        
        # Validate input structure
        if 'tasks' not in input_body or 'convert' not in input_body['tasks']:
            return jsonify({
                'error': 'Invalid input structure',
                'message': 'Expected structure: {"tasks": {"convert": {"output_format": "pdf", "options": {}}}}'
            }), 400
        
        # Perform the conversion
        result = convert_document(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON in input_body',
            'message': 'The input_body parameter must be valid JSON'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Document conversion failed'
        }), 500

@document_converter_bp.route('/pdf-to-word', methods=['POST'])
def pdf_to_word():
    """Convert PDF to Word (DOCX) - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing PDF file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'docx',
                    'options': {
                        'preserve_formatting': True,
                        'extract_images': True
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/pdf-to-jpg', methods=['POST'])
def pdf_to_jpg():
    """Convert PDF to JPG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing PDF file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'jpg',
                    'options': {
                        'dpi': 300,
                        'quality': 95,
                        'extract_all_pages': True
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/pdf-to-epub', methods=['POST'])
def pdf_to_epub():
    """Convert PDF to EPUB - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing PDF file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'epub',
                    'options': {
                        'extract_text': True,
                        'preserve_structure': True
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/epub-to-pdf', methods=['POST'])
def epub_to_pdf():
    """Convert EPUB to PDF - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing EPUB file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'pdf',
                    'options': {
                        'page_size': 'A4',
                        'margin': '1in',
                        'quality': 'high'
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/heic-to-pdf', methods=['POST'])
def heic_to_pdf():
    """Convert HEIC to PDF - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing HEIC file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'pdf',
                    'options': {
                        'page_size': 'A4',
                        'fit_to_page': True,
                        'quality': 'high'
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/docx-to-pdf', methods=['POST'])
def docx_to_pdf():
    """Convert DOCX to PDF - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing DOCX file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'pdf',
                    'options': {
                        'preserve_formatting': True,
                        'embed_fonts': True,
                        'quality': 'high'
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/jpg-to-pdf', methods=['POST'])
def jpg_to_pdf():
    """Convert JPG to PDF - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing JPG file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'pdf',
                    'options': {
                        'page_size': 'A4',
                        'fit_to_page': True,
                        'orientation': 'auto'
                    }
                }
            }
        }
        result = convert_document(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@document_converter_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported document formats"""
    from api.services.document_converter_service import SUPPORTED_FORMATS, get_format_info
    
    formats_info = {}
    for fmt in SUPPORTED_FORMATS:
        formats_info[fmt] = get_format_info(fmt)
    
    return jsonify({
        'supported_formats': SUPPORTED_FORMATS,
        'format_details': formats_info,
        'special_endpoints': [
            '/pdf-to-word',
            '/pdf-to-jpg',
            '/pdf-to-epub',
            '/epub-to-pdf',
            '/heic-to-pdf',
            '/docx-to-pdf',
            '/jpg-to-pdf'
        ]
    })

@document_converter_bp.route('/health', methods=['GET'])
def health_check():
    """Check if document conversion service is available and dependencies are installed"""
    try:
        import PyPDF2
        pypdf_available = True
    except ImportError:
        pypdf_available = False
    
    try:
        import fitz  # PyMuPDF
        pymupdf_available = True
    except ImportError:
        pymupdf_available = False
    
    try:
        from docx import Document
        python_docx_available = True
    except ImportError:
        python_docx_available = False
    
    try:
        import ebooklib
        ebooklib_available = True
    except ImportError:
        ebooklib_available = False
    
    return jsonify({
        'status': 'healthy' if pypdf_available else 'degraded',
        'dependencies': {
            'pypdf2': pypdf_available,
            'pymupdf': pymupdf_available,
            'python_docx': python_docx_available,
            'ebooklib': ebooklib_available
        },
        'capabilities': {
            'pdf_processing': pypdf_available or pymupdf_available,
            'docx_processing': python_docx_available,
            'epub_processing': ebooklib_available
        }
    })