from flask import Blueprint, request, jsonify
from api.services.pdf_compression_service import compress_pdf
import os

pdf_compression_bp = Blueprint('pdf_compression', __name__)

@pdf_compression_bp.route('/compress-pdf', methods=['POST'])
def compress_pdf_endpoint():
    """
    Compress PDF files with advanced options
    
    Request:
    - file: PDF file to compress
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
                "input_format": "pdf",
                "output_format": "pdf",
                "options": {
                    "compression_level": "medium",
                    "convert_to_gray": false
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
        
        # Check if file is PDF
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400
        
        # Get input_body from form data
        input_body_str = request.form.get('input_body', '{}')
        import json
        input_body = json.loads(input_body_str)
        
        # Call the compression service
        result = compress_pdf(file, input_body)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compress_pdf_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 