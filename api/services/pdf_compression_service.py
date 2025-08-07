import os
import tempfile
import shutil
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
import io

def compress_pdf(file, input_body):
    """
    Compress PDF files using PyMuPDF with advanced options
    
    Args:
        file: Uploaded PDF file
        input_body: JSON with compression options
    
    Returns:
        dict: Result with success status and download URL
    """
    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, file.filename)
        output_filename = f"compressed_{file.filename}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Save uploaded file
        file.save(input_path)
        
        # Get original file size
        original_size = os.path.getsize(input_path)
        
        # Get compression options from input_body
        tasks = input_body.get('tasks', {})
        compress_task = tasks.get('compress', {})
        options = compress_task.get('options', {})
        
        # Get PDF compression options
        compression_level = options.get('compression_level', 'medium')
        convert_to_gray = options.get('convert_to_gray', False)
        
        # Map compression levels to quality settings
        compression_settings = {
            'no_compression': {
                'image_quality': 100,
                'image_resolution': None,  # Keep original
                'deflate_images': False
            },
            'high': {
                'image_quality': 50,
                'image_resolution': 150,
                'deflate_images': True
            },
            'medium': {
                'image_quality': 70,
                'image_resolution': 200,
                'deflate_images': True
            },
            'low': {
                'image_quality': 90,
                'image_resolution': 300,
                'deflate_images': True
            }
        }
        
        settings = compression_settings.get(compression_level, compression_settings['medium'])
        
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(input_path)
        
        # Create a new PDF document for output
        output_pdf = fitz.open()
        
        # Process each page
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # Convert page to pixmap (image)
            if settings['image_resolution']:
                # Calculate zoom factor for target resolution
                mat = fitz.Matrix(settings['image_resolution'] / 72, settings['image_resolution'] / 72)
                pix = page.get_pixmap(matrix=mat)
            else:
                pix = page.get_pixmap()
            
            # Convert to grayscale if requested
            if convert_to_gray:
                # Convert pixmap to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Convert to grayscale
                img = img.convert('L')
                
                # Convert back to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_data = img_byte_arr.getvalue()
                
                # Create new pixmap from processed image
                pix = fitz.Pixmap(img_data)
            
            # Create a new page in output PDF
            new_page = output_pdf.new_page(width=page.rect.width, height=page.rect.height)
            
            # Insert the processed image
            new_page.insert_image(new_page.rect, pixmap=pix)
            
            # Clean up
            pix = None
        
        # Save with compression settings
        if compression_level != 'no_compression':
            # Apply additional compression options
            save_options = {
                'garbage': 4,  # Remove unused objects
                'clean': True,  # Clean up content streams
                'deflate': settings['deflate_images']  # Compress streams
            }
        else:
            save_options = {}
        
        # Save the compressed PDF
        output_pdf.save(output_path, **save_options)
        
        # Close documents
        pdf_document.close()
        output_pdf.close()
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'documents')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"pdf_compressed_{timestamp}_{output_filename}"
        final_path = os.path.join(static_dir, unique_filename)
        
        # Move compressed file to static directory
        shutil.move(output_path, final_path)
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create download URL (use absolute URL for cross-domain requests)
        # Try to get the base URL from the request context
        try:
            from flask import request
            base_url = request.url_root.rstrip('/')
            # Force HTTPS for ngrok URLs to avoid CORS redirect issues
            if 'ngrok' in base_url and base_url.startswith('http://'):
                base_url = base_url.replace('http://', 'https://')
            download_url = f"{base_url}/static/documents/{unique_filename}"
        except:
            # Fallback to relative URL if request context is not available
            download_url = f"/static/documents/{unique_filename}"
        
        # Calculate compression stats
        compression_ratio = (1 - (file_size / original_size)) * 100
        size_reduction = original_size - file_size
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'PDF compressed successfully using {compression_level} compression',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': 'pdf',
            'input_format': 'pdf',
            'compression_stats': {
                'original_size': original_size,
                'compressed_size': file_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{size_reduction} bytes"
            },
            'settings_used': {
                'compression_level': compression_level,
                'convert_to_gray': convert_to_gray,
                'image_quality': settings['image_quality'],
                'image_resolution': settings['image_resolution']
            }
        }
        
        print(f"PDF compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"PDF compression failed: {str(e)}") 