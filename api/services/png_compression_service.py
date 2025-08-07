import os
import tempfile
import shutil
from datetime import datetime
from PIL import Image
import math

def resize_image(img, resize_output, target_width, target_height, resize_percentage):
    """
    Resize image based on resize options
    """
    original_width, original_height = img.size
    
    if resize_output == 'keep_original':
        return img
    
    elif resize_output == 'by_width' and target_width > 0:
        # Calculate height maintaining aspect ratio
        aspect_ratio = original_width / original_height
        new_height = int(target_width / aspect_ratio)
        return img.resize((target_width, new_height), Image.Resampling.LANCZOS)
    
    elif resize_output == 'by_height' and target_height > 0:
        # Calculate width maintaining aspect ratio
        aspect_ratio = original_width / original_height
        new_width = int(target_height * aspect_ratio)
        return img.resize((new_width, target_height), Image.Resampling.LANCZOS)
    
    elif resize_output == 'by_width_height' and target_width > 0 and target_height > 0:
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    elif resize_output == 'by_percentage' and resize_percentage != 100:
        new_width = int(original_width * (resize_percentage / 100))
        new_height = int(original_height * (resize_percentage / 100))
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return img

def compress_png(file, input_body):
    """
    Compress PNG image files using Pillow with advanced options
    
    Args:
        file: Uploaded PNG file
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
        
        # Get PNG compression options
        png_compression_quality = options.get('png_compression_quality', 60)
        png_compression_speed = options.get('png_compression_speed', 4)
        png_colors = options.get('png_colors', 256)
        compress_png_resize_output = options.get('compress_png_resize_output', 'keep_original')
        target_width = options.get('target_width', 0)
        target_height = options.get('target_height', 0)
        resize_percentage = options.get('resize_percentage', 100)
        
        # Open image with Pillow
        with Image.open(input_path) as img:
            # Convert to RGBA if not already
            if img.mode not in ('RGBA', 'RGB', 'L'):
                img = img.convert('RGBA')
            
            # Resize image if requested
            img = resize_image(img, compress_png_resize_output, target_width, target_height, resize_percentage)
            
            # Prepare save options for PNG compression
            save_kwargs = {
                'format': 'PNG',
                'optimize': True
            }
            
            # Set compression level (0-9, higher = better compression but slower)
            # Map quality (1-100) to compression level (0-9)
            compression_level = max(0, min(9, int((100 - png_compression_quality) / 11)))
            save_kwargs['compress_level'] = compression_level
            
            # If colors are specified and less than 256, convert to palette mode
            if png_colors < 256:
                # Convert to palette mode with specified number of colors
                if img.mode in ('RGBA', 'RGB'):
                    # Create a palette with the specified number of colors
                    img = img.quantize(colors=png_colors, method=2)  # method=2 for median cut
                elif img.mode == 'L':
                    # For grayscale, we can still reduce colors
                    img = img.quantize(colors=png_colors, method=2)
            
            # Save compressed image
            img.save(output_path, **save_kwargs)
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"png_compressed_{timestamp}_{output_filename}"
        final_path = os.path.join(static_dir, unique_filename)
        
        # Move compressed file to static directory
        shutil.move(output_path, final_path)
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create download URL
        download_url = f"/static/images/{unique_filename}"
        
        # Calculate compression stats
        compression_ratio = (1 - (file_size / original_size)) * 100
        size_reduction = original_size - file_size
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'PNG compressed successfully using palette mode with {png_colors} colors',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': 'png',
            'input_format': 'png',
            'compression_stats': {
                'original_size': original_size,
                'compressed_size': file_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{size_reduction} bytes"
            },
            'settings_used': {
                'png_compression_quality': png_compression_quality,
                'png_compression_speed': png_compression_speed,
                'png_colors': png_colors,
                'compress_png_resize_output': compress_png_resize_output,
                'compression_level': compression_level
            }
        }
        
        print(f"PNG compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"PNG compression failed: {str(e)}") 