import os
import tempfile
import shutil
from datetime import datetime
from PIL import Image
import math

def get_jpeg_quality_from_target_size(original_size_bytes, target_size_kb):
    """
    Calculate JPEG quality based on target file size
    """
    target_size_bytes = target_size_kb * 1024
    if target_size_bytes >= original_size_bytes:
        return 95  # High quality if target is larger than original
    
    # Estimate quality based on size ratio
    size_ratio = target_size_bytes / original_size_bytes
    quality = int(size_ratio * 100)
    
    # Clamp quality between 1 and 95
    return max(1, min(95, quality))

def get_jpeg_quality_from_percentage(original_size_bytes, target_percentage):
    """
    Calculate JPEG quality based on target percentage
    """
    target_size_bytes = original_size_bytes * (target_percentage / 100)
    return get_jpeg_quality_from_target_size(original_size_bytes, target_size_bytes / 1024)

def resize_image(img, resize_output, target_width, target_height, resize_percentage):
    """
    Resize image based on resize options
    """
    original_width, original_height = img.size
    
    if resize_output == 'keep_original_size':
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

def compress_jpeg(file, input_body):
    """
    Compress JPEG image files using Pillow with advanced options
    
    Args:
        file: Uploaded JPEG file
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
        
        # Get JPEG compression options
        compression_method = options.get('jpeg_compression_method', 'by_quality')
        image_quality = options.get('jpeg_image_quality', 66)
        target_file_size = options.get('jpeg_target_file_size', 100)
        target_file_size_percentage = options.get('jpeg_target_file_size_percentage', 20)
        compression_type = options.get('jpeg_compression_type', 'progressive')
        resize_output = options.get('jpeg_resize_output', 'keep_original_size')
        target_width = options.get('jpeg_target_width', 0)
        target_height = options.get('jpeg_target_height', 0)
        resize_percentage = options.get('jpeg_resize_percentage', 100)
        use_grayscale = options.get('jpeg_use_grayscale', False)
        reduce_chroma_sampling = options.get('jpeg_reduce_chroma_sampling', True)
        
        # Open image with Pillow
        with Image.open(input_path) as img:
            # Convert to grayscale if requested
            if use_grayscale:
                img = img.convert('L')
            
            # Resize image if requested
            img = resize_image(img, resize_output, target_width, target_height, resize_percentage)
            
            # Determine quality based on compression method
            if compression_method == 'by_quality':
                quality = image_quality
            elif compression_method == 'target_file_size':
                quality = get_jpeg_quality_from_target_size(original_size, target_file_size)
            elif compression_method == 'target_file_size_percentage':
                quality = get_jpeg_quality_from_target_size(original_size, target_file_size_percentage)
            elif compression_method == 'lossless':
                quality = 95  # High quality for lossless-like compression
            else:
                quality = 66  # Default quality
            
            # Prepare save options
            save_kwargs = {
                'quality': quality,
                'optimize': True
            }
            
            # Add progressive option
            if compression_type == 'progressive':
                save_kwargs['progressive'] = True
            
            # Add chroma sampling option
            if reduce_chroma_sampling:
                save_kwargs['subsampling'] = 2  # 4:2:0 chroma sampling
            
            # Save compressed image
            img.save(output_path, format='JPEG', **save_kwargs)
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"jpeg_compressed_{timestamp}_{output_filename}"
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
            'message': f'JPEG compressed successfully using {compression_method} method',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': 'jpeg',
            'input_format': 'jpeg',
            'compression_stats': {
                'original_size': original_size,
                'compressed_size': file_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{size_reduction} bytes"
            },
            'settings_used': {
                'compression_method': compression_method,
                'quality': quality,
                'compression_type': compression_type,
                'resize_output': resize_output,
                'use_grayscale': use_grayscale,
                'reduce_chroma_sampling': reduce_chroma_sampling
            }
        }
        
        print(f"JPEG compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"JPEG compression failed: {str(e)}") 