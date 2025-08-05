from flask import Blueprint, request, jsonify
from api.services.archive_converter_service import convert_archive, check_dependencies
import json

archive_converter_bp = Blueprint('archive_converter', __name__)

@archive_converter_bp.route('/convert', methods=['POST'])
def archive_convert():
    """Convert archive files between different formats"""
    try:
        # Get uploaded file
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Get input body (conversion parameters)
        input_body_raw = request.form.get('input_body')
        if not input_body_raw:
            return jsonify({'error': 'No conversion parameters provided'}), 400
        
        try:
            input_body = json.loads(input_body_raw)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in input_body'}), 400
        
        # Validate input body structure
        if 'tasks' not in input_body or 'convert' not in input_body['tasks']:
            return jsonify({'error': 'Invalid input body structure'}), 400
        
        convert_config = input_body['tasks']['convert']
        if 'output_format' not in convert_config:
            return jsonify({'error': 'No output format specified'}), 400
        
        # Perform conversion
        result = convert_archive(file, input_body)
        return jsonify(result)
        
    except Exception as e:
        print(f"Archive conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@archive_converter_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported archive formats"""
    return jsonify({
        'supported_formats': ['7z', 'gz', 'rar', 'tar', 'targz', 'tgz', 'zip'],
        'dependencies': check_dependencies()
    })

@archive_converter_bp.route('/health', methods=['GET'])
def health_check():
    """Check if archive conversion service is available and dependencies are installed"""
    try:
        dependencies = check_dependencies()
        
        # Calculate overall health status
        rarfile_available = dependencies.get('rarfile', False)
        external_tools_available = dependencies.get('7z', False) or dependencies.get('rar', False)
        
        if rarfile_available and external_tools_available:
            status = 'healthy'
            message = 'All archive conversion tools are available'
        elif rarfile_available or external_tools_available:
            status = 'partial'
            message = 'Some archive conversion tools are available'
        else:
            status = 'degraded'
            message = 'Only basic archive formats supported (ZIP, TAR, GZ)'
        
        # Detailed capability information
        capabilities = {
            'zip': True,  # Always available (built-in Python)
            'tar': True,  # Always available (built-in Python)
            'gz': True,   # Always available (built-in Python)
            'targz': True,  # Always available (built-in Python)
            'tgz': True,    # Always available (built-in Python)
            '7z': dependencies.get('7z', False),
            'rar_extract': rarfile_available or dependencies.get('rar', False),
            'rar_create': dependencies.get('rar', False)  # RAR creation requires WinRAR
        }
        
        # Installation instructions for missing tools
        installation_instructions = {}
        if not dependencies.get('7z', False):
            installation_instructions['7z'] = {
                'tool': '7-Zip',
                'url': 'https://www.7-zip.org/',
                'description': 'Required for 7z format support'
            }
        if not rarfile_available:
            installation_instructions['rarfile'] = {
                'tool': 'rarfile Python library',
                'command': 'pip install rarfile',
                'description': 'Recommended for RAR extraction support'
            }
        if not dependencies.get('rar', False):
            installation_instructions['rar'] = {
                'tool': 'WinRAR',
                'url': 'https://www.rarlab.com/',
                'description': 'Required for RAR creation and enhanced RAR extraction'
            }
        
        # Provide detailed dependency status
        detailed_status = {
            'python_libraries': {
                'rarfile': {
                    'available': rarfile_available,
                    'purpose': 'RAR extraction support',
                    'install_command': 'pip install rarfile' if not rarfile_available else None
                }
            },
            'external_tools': {
                '7z': {
                    'available': dependencies.get('7z', False),
                    'purpose': '7z format support',
                    'install_url': 'https://www.7-zip.org/' if not dependencies.get('7z', False) else None
                },
                'rar/unrar': {
                    'available': dependencies.get('rar', False),
                    'purpose': 'Enhanced RAR support and RAR creation',
                    'install_url': 'https://www.rarlab.com/' if not dependencies.get('rar', False) else None
                }
            }
        }
        
        return jsonify({
            'status': status,
            'message': message,
            'dependencies': dependencies,
            'capabilities': capabilities,
            'supported_formats': {
                'extract': [fmt for fmt, supported in capabilities.items() if supported and fmt != 'rar_create'],
                'create': [fmt for fmt, supported in capabilities.items() if supported and fmt not in ['rar_extract']]
            },
            'detailed_status': detailed_status,
            'installation_instructions': installation_instructions
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'dependencies': {},
            'capabilities': {}
        }), 500

@archive_converter_bp.route('/check-dependencies', methods=['GET'])
def check_archive_dependencies():
    """Check if required external tools are available"""
    try:
        dependencies = check_dependencies()
        return jsonify({
            'success': True,
            'dependencies': dependencies,
            'message': 'Dependency check completed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@archive_converter_bp.route('/zip-to-rar', methods=['POST'])
def zip_to_rar():
    """Convert ZIP to RAR - specific endpoint"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        input_body_raw = request.form.get('input_body')
        if input_body_raw:
            try:
                input_body = json.loads(input_body_raw)
            except json.JSONDecodeError:
                input_body = {}
        else:
            input_body = {}
        
        # Set up conversion for ZIP to RAR
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'rar',
                    'options': input_body.get('options', {
                        'compression_level': 5
                    })
                }
            }
        }
        
        result = convert_archive(file, input_body)
        return jsonify(result)
        
    except Exception as e:
        print(f"ZIP to RAR conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@archive_converter_bp.route('/rar-to-zip', methods=['POST'])
def rar_to_zip():
    """Convert RAR to ZIP - specific endpoint"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        input_body_raw = request.form.get('input_body')
        if input_body_raw:
            try:
                input_body = json.loads(input_body_raw)
            except json.JSONDecodeError:
                input_body = {}
        else:
            input_body = {}
        
        # Set up conversion for RAR to ZIP
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'zip',
                    'options': input_body.get('options', {
                        'compression_level': 6
                    })
                }
            }
        }
        
        result = convert_archive(file, input_body)
        return jsonify(result)
        
    except Exception as e:
        print(f"RAR to ZIP conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@archive_converter_bp.route('/7z-to-zip', methods=['POST'])
def sevenzip_to_zip():
    """Convert 7Z to ZIP - specific endpoint"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        input_body_raw = request.form.get('input_body')
        if input_body_raw:
            try:
                input_body = json.loads(input_body_raw)
            except json.JSONDecodeError:
                input_body = {}
        else:
            input_body = {}
        
        # Set up conversion for 7Z to ZIP
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'zip',
                    'options': input_body.get('options', {
                        'compression_level': 6
                    })
                }
            }
        }
        
        result = convert_archive(file, input_body)
        return jsonify(result)
        
    except Exception as e:
        print(f"7Z to ZIP conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@archive_converter_bp.route('/tar-gz-to-zip', methods=['POST'])
def targz_to_zip():
    """Convert TARGZ to ZIP - specific endpoint"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        input_body_raw = request.form.get('input_body')
        if input_body_raw:
            try:
                input_body = json.loads(input_body_raw)
            except json.JSONDecodeError:
                input_body = {}
        else:
            input_body = {}
        
        # Set up conversion for TARGZ to ZIP
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'zip',
                    'options': input_body.get('options', {
                        'compression_level': 6
                    })
                }
            }
        }
        
        result = convert_archive(file, input_body)
        return jsonify(result)
        
    except Exception as e:
        print(f"TARGZ to ZIP conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500 