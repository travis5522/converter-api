import os
import tempfile
import shutil
from datetime import datetime
from PIL import Image
import mimetypes

def get_image_format(filename):
    """
    Get image format from filename
    """
    ext = os.path.splitext(filename)[1].lower()
    format_map = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.webp': 'WEBP',
        '.bmp': 'BMP',
        '.tiff': 'TIFF',
        '.tif': 'TIFF',
        '.gif': 'GIF'
    }
    return format_map.get(ext, 'JPEG')

def compress_image(file, input_body):
    """
    Compress image files using Pillow
    
    Args:
        file: Uploaded image file
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
        
        # Get compression options from input_body
        tasks = input_body.get('tasks', {})
        compress_task = tasks.get('compress', {})
        input_format = compress_task.get('input_format', 'jpeg')
        output_format = compress_task.get('output_format', 'jpeg')
        
        # Open image with Pillow
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for JPEG output)
            if output_format.lower() in ['jpeg', 'jpg'] and img.mode in ['RGBA', 'LA', 'P']:
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Determine output format
            output_format_upper = get_image_format(output_filename)
            
            # Set compression quality (JPEG) or optimize (PNG)
            save_kwargs = {}
            if output_format_upper == 'JPEG':
                save_kwargs['quality'] = 85  # Good balance between quality and size
                save_kwargs['optimize'] = True
            elif output_format_upper == 'PNG':
                save_kwargs['optimize'] = True
            elif output_format_upper == 'WEBP':
                save_kwargs['quality'] = 85
                save_kwargs['method'] = 6  # Best compression method
            
            # Save compressed image
            img.save(output_path, format=output_format_upper, **save_kwargs)
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"image_compressed_{timestamp}_{output_filename}"
        final_path = os.path.join(static_dir, unique_filename)
        
        # Move compressed file to static directory
        shutil.move(output_path, final_path)
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create download URL
        download_url = f"/static/images/{unique_filename}"
        
        # Get output format extension
        output_ext = os.path.splitext(output_filename)[1].lower()
        if not output_ext:
            output_ext = '.jpg'  # Default to jpg
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'Image compressed successfully from {input_format} to {output_format}',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': output_ext[1:],  # Remove the dot
            'input_format': input_format,
            'output_format_full': output_format
        }
        
        print(f"Image compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"Image compression failed: {str(e)}") 