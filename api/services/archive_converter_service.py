import os
import tempfile
import zipfile
import tarfile
import gzip
import shutil
import subprocess
import uuid
from pathlib import Path

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'archives')
SUPPORTED_FORMATS = ['7z', 'gz', 'rar', 'tar', 'targz', 'tgz', 'zip']

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def convert_archive(file, input_body):
    """Convert between different archive formats"""
    if not file or not file.filename:
        raise Exception("No file provided")
    
    # Get file extension and detect input format
    input_filename = file.filename
    input_format = detect_archive_format(input_filename)
    
    if input_format not in SUPPORTED_FORMATS:
        raise Exception(f"Unsupported input format: {input_format}")
    
    # Extract conversion parameters
    convert_config = input_body['tasks']['convert']
    output_format = convert_config['output_format']
    options = convert_config.get('options', {})
    
    if output_format not in SUPPORTED_FORMATS:
        raise Exception(f"Unsupported output format: {output_format}")
    
    # Check if required tools are available for this conversion
    dependency_check = check_format_dependencies(input_format, output_format)
    if not dependency_check['available']:
        raise Exception(f"Required tools not available: {dependency_check['message']}")
    
    # Save uploaded file
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_format}")
    file.seek(0)
    temp_input.write(file.read())
    temp_input.close()
    input_path = temp_input.name
    
    try:
        # Generate output filename
        output_filename = f"{uuid.uuid4()}.{output_format}"
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Convert the archive
        success = perform_archive_conversion(input_path, output_path, input_format, output_format, options)
        
        if not success:
            raise Exception("Archive conversion failed")
        
        # Check if output file was created
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output file was not created or is empty")
        
        file_size = os.path.getsize(output_path)
        download_path = f'/download/archives/{output_filename}'
        
        return {
            'success': True,
            'message': f'Successfully converted {input_format} to {output_format}',
            'output_file': output_filename,
            'download_url': download_path,
            'export_url': download_path,
            'file_size': file_size,
            'output_format': output_format
        }
        
    except Exception as e:
        raise Exception(f"Archive conversion error: {str(e)}")
    finally:
        # Clean up input file
        if os.path.exists(input_path):
            os.unlink(input_path)

def detect_archive_format(filename):
    """Detect archive format from filename"""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.tar.gz'):
        return 'targz'  # Map .tar.gz files to internal 'targz' format
    elif filename_lower.endswith('.tgz'):
        return 'tgz'
    elif filename_lower.endswith('.tar'):
        return 'tar'
    elif filename_lower.endswith('.zip'):
        return 'zip'
    elif filename_lower.endswith('.7z'):
        return '7z'
    elif filename_lower.endswith('.rar'):
        return 'rar'
    elif filename_lower.endswith('.gz'):
        return 'gz'
    else:
        raise Exception(f"Unknown archive format: {filename}")

def perform_archive_conversion(input_path, output_path, input_format, output_format, options):
    """Perform the actual archive conversion"""
    
    # If formats are the same, just copy
    if input_format == output_format:
        shutil.copy2(input_path, output_path)
        return True
    
    # Create temporary directory for extraction
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract input archive
        extract_success = extract_archive(input_path, temp_dir, input_format)
        if not extract_success:
            return False
        
        # Create output archive
        create_success = create_archive(temp_dir, output_path, output_format, options)
        return create_success
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def extract_archive(archive_path, extract_dir, format_type):
    """Extract archive based on format"""
    try:
        if format_type == 'zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        
        elif format_type in ['tar', 'targz', 'tgz']:
            mode = 'r:gz' if format_type in ['targz', 'tgz'] else 'r'
            with tarfile.open(archive_path, mode) as tar_ref:
                tar_ref.extractall(extract_dir)
        
        elif format_type == 'gz':
            # Handle single file gzip
            output_file = os.path.join(extract_dir, 'extracted_file')
            with gzip.open(archive_path, 'rb') as gz_file:
                with open(output_file, 'wb') as out_file:
                    shutil.copyfileobj(gz_file, out_file)
        
        elif format_type == '7z':
            # Check if 7z tools are available
            if not _is_tool_available('7z') and not _is_tool_available('7za'):
                raise Exception("7z extraction requires 7-Zip or p7zip to be installed. Please install 7-Zip (https://www.7-zip.org/) or p7zip.")
            
            # Use 7z command line tool
            result = subprocess.run(['7z', 'x', archive_path, f'-o{extract_dir}', '-y'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                # Try p7zip if 7z is not available
                result = subprocess.run(['7za', 'x', archive_path, f'-o{extract_dir}', '-y'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"7z extraction failed: {result.stderr}")
        
        elif format_type == 'rar':
            # Try Python rarfile library first
            try:
                import rarfile
                
                # Try to extract using rarfile library
                with rarfile.RarFile(archive_path) as rar_ref:
                    rar_ref.extractall(extract_dir)
                print("RAR extracted successfully using rarfile library")
                
            except ImportError:
                raise Exception("rarfile library not available. Please install: pip install rarfile")
            except rarfile.RarCannotExec:
                # rarfile library available but needs external tool
                if _is_tool_available('unrar'):
                    # Set the unrar tool path for rarfile
                    rarfile.UNRAR_TOOL = 'unrar'
                    with rarfile.RarFile(archive_path) as rar_ref:
                        rar_ref.extractall(extract_dir)
                    print("RAR extracted successfully using rarfile with unrar")
                else:
                    raise Exception("RAR extraction requires unrar to be installed. Please install WinRAR (https://www.rarlab.com/) or unrar command-line tool.")
            except Exception as e:
                # If rarfile fails, try external unrar as fallback
                if _is_tool_available('unrar'):
                    result = subprocess.run(['unrar', 'x', archive_path, extract_dir, '-y'], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"RAR extraction failed: {result.stderr}")
                    print("RAR extracted successfully using external unrar")
                else:
                    raise Exception(f"RAR extraction failed: {str(e)}. Please install WinRAR (https://www.rarlab.com/) or unrar command-line tool.")
        
        else:
            raise Exception(f"Unsupported extraction format: {format_type}")
        
        return True
        
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return False

def create_archive(source_dir, output_path, format_type, options):
    """Create archive based on format"""
    try:
        compression_level = options.get('compression_level', 6)
        
        if format_type == 'zip':
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=compression_level) as zip_ref:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zip_ref.write(file_path, arcname)
        
        elif format_type == 'tar':
            with tarfile.open(output_path, 'w') as tar_ref:
                tar_ref.add(source_dir, arcname=os.path.basename(source_dir))
        
        elif format_type in ['targz', 'tgz']:
            with tarfile.open(output_path, 'w:gz') as tar_ref:
                tar_ref.add(source_dir, arcname=os.path.basename(source_dir))
        
        elif format_type == 'gz':
            # Handle single file gzip
            files = []
            for root, dirs, filenames in os.walk(source_dir):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            if len(files) == 1:
                with open(files[0], 'rb') as input_file:
                    with gzip.open(output_path, 'wb', compresslevel=compression_level) as gz_file:
                        shutil.copyfileobj(input_file, gz_file)
            else:
                raise Exception("GZ format only supports single files")
        
        elif format_type == '7z':
            # Check if 7z tools are available
            if not _is_tool_available('7z') and not _is_tool_available('7za'):
                raise Exception("7z creation requires 7-Zip or p7zip to be installed. Please install 7-Zip (https://www.7-zip.org/) or p7zip.")
            
            # Use 7z command line tool
            compression_args = ['-mx=' + str(compression_level)]
            result = subprocess.run(['7z', 'a'] + compression_args + [output_path, source_dir + '/*'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                # Try p7zip if 7z is not available
                result = subprocess.run(['7za', 'a'] + compression_args + [output_path, source_dir + '/*'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"7z creation failed: {result.stderr}")
        
        elif format_type == 'rar':
            # RAR creation still requires external WinRAR tool
            # Python libraries don't support RAR creation due to licensing
            if not _is_tool_available('rar'):
                raise Exception("RAR creation requires WinRAR to be installed. Please install WinRAR (https://www.rarlab.com/).")
            
            # Use rar command line tool (WinRAR)
            compression_args = [f'-m{compression_level}']
            result = subprocess.run(['rar', 'a'] + compression_args + [output_path, source_dir + '/*'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"RAR creation failed: {result.stderr}")
        
        else:
            raise Exception(f"Unsupported creation format: {format_type}")
        
        return True
        
    except Exception as e:
        print(f"Archive creation error: {str(e)}")
        return False

def _is_tool_available(tool_name):
    """Check if a command-line tool is available"""
    try:
        subprocess.run([tool_name], capture_output=True, timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_format_dependencies(input_format, output_format):
    """Check if required tools are available for specific format conversion"""
    required_tools = set()
    
    # Check input format requirements
    if input_format == '7z':
        required_tools.add('7z_extract')
    elif input_format == 'rar':
        required_tools.add('rar_extract')
    
    # Check output format requirements
    if output_format == '7z':
        required_tools.add('7z_create')
    elif output_format == 'rar':
        required_tools.add('rar_create')
    
    missing_tools = []
    for tool in required_tools:
        if tool == '7z_extract' and not (_is_tool_available('7z') or _is_tool_available('7za')):
            missing_tools.append('7-Zip (7z or 7za)')
        elif tool == '7z_create' and not (_is_tool_available('7z') or _is_tool_available('7za')):
            missing_tools.append('7-Zip (7z or 7za)')
        elif tool == 'rar_extract':
            # Check if we can handle RAR extraction
            try:
                import rarfile
                # rarfile is available, check if it can work
                if not (_is_tool_available('unrar') or _is_tool_available('rar')):
                    # rarfile needs external tools, but we can still try
                    print("Warning: RAR extraction may require external tools for some archives")
            except ImportError:
                missing_tools.append('rarfile library (pip install rarfile) or unrar tool')
        elif tool == 'rar_create' and not _is_tool_available('rar'):
            missing_tools.append('WinRAR (rar) - Python libraries cannot create RAR files due to licensing')
    
    if missing_tools:
        return {
            'available': False,
            'message': f"Missing required tools: {', '.join(missing_tools)}"
        }
    
    return {'available': True, 'message': 'All required tools are available'}

def check_dependencies():
    """Check if required external tools are available"""
    tools = {
        '7z': ['7z', '7za'],
        'rar': ['rar', 'unrar'],
    }
    
    available = {}
    for tool, commands in tools.items():
        available[tool] = False
        for cmd in commands:
            try:
                subprocess.run([cmd], capture_output=True, timeout=5)
                available[tool] = True
                break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    # Check for Python rarfile library
    try:
        import rarfile
        available['rarfile'] = True
    except ImportError:
        available['rarfile'] = False
    
    return available 