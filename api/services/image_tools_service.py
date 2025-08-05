import os
import uuid
import tempfile
import json
from PIL import Image, ImageDraw, ImageFilter
import colorsys
from io import BytesIO

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
os.makedirs(EXPORT_DIR, exist_ok=True)

SUPPORTED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff']

def create_gif(files, input_body):
    """Create GIF from multiple images with specified settings"""
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'gif_maker' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'gif_maker'")
        
        gif_task = input_body['tasks']['gif_maker']
        options = gif_task.get('options', {})
        
        # Get GIF parameters
        delay = options.get('delay', 100)  # milliseconds
        loop = options.get('loop', 0)  # 0 = infinite
        width = options.get('width')
        height = options.get('height')
        
        # Get images from files parameter
        images = files
        if not images:
            raise Exception("No images provided for GIF creation")
        
        # Process images
        processed_images = []
        for img_file in images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img_file.filename)[1]) as temp_input:
                img_file.save(temp_input.name)
                img = Image.open(temp_input.name)
                
                # Resize if specified
                if width and height:
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                processed_images.append(img)
                os.unlink(temp_input.name)
        
        # Create GIF
        output_filename = str(uuid.uuid4()) + '.gif'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if processed_images:
            processed_images[0].save(
                output_path,
                save_all=True,
                append_images=processed_images[1:],
                duration=delay,
                loop=loop,
                optimize=True
            )
        
        return {
            'success': True,
            'message': 'GIF created successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"GIF creation failed: {str(e)}")

def resize_image(file, input_body):
    """Resize image to specified dimensions"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'resize' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'resize'")
        
        resize_task = input_body['tasks']['resize']
        options = resize_task.get('options', {})
        
        # Get resize parameters
        method = options.get('method', 'size')
        width = options.get('width')
        height = options.get('height')
        width_percent = options.get('width_percent', 100)
        height_percent = options.get('height_percent', 100)
        unit = options.get('unit', 'px')
        maintain_aspect = options.get('maintain_aspect', True)
        
        # Get output format
        output_format = options.get('output_format', 'png').lower()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Open image
        img = Image.open(input_path)
        original_width, original_height = img.size
        
        # Calculate new dimensions based on method
        if method == 'percentage':
            # Resize by percentage
            new_width = int(original_width * (width_percent / 100))
            new_height = int(original_height * (height_percent / 100))
            
        elif method == 'preset':
            # Use preset dimensions (already calculated on frontend)
            new_width = width or original_width
            new_height = height or original_height
            
        else:  # method == 'size'
            # Direct size specification
            if not width and not height:
                raise Exception("At least width or height must be specified for size method")
            
            new_width = width or original_width
            new_height = height or original_height
            
            # Handle aspect ratio locking for size method
            if maintain_aspect and width and height:
                # Calculate aspect ratio
                img_ratio = original_width / original_height
                target_ratio = width / height
                
                if img_ratio > target_ratio:
                    # Image is wider, fit to width
                    new_width = width
                    new_height = int(width / img_ratio)
                else:
                    # Image is taller, fit to height
                    new_height = height
                    new_width = int(height * img_ratio)
        
        # Validate dimensions
        if new_width <= 0 or new_height <= 0:
            raise Exception("Invalid dimensions: width and height must be positive")
        
        if new_width > 10000 or new_height > 10000:
            raise Exception("Dimensions too large: maximum 10000x10000 pixels")
        
        # Resize image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save resized image
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if output_format == 'jpg' or output_format == 'jpeg':
            resized_img = resized_img.convert('RGB')
            resized_img.save(output_path, 'JPEG', quality=95)
        else:
            resized_img.save(output_path)
        
        return {
            'success': True,
            'message': 'Image resized successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}',
            'original_size': {'width': original_width, 'height': original_height},
            'new_size': {'width': new_width, 'height': new_height}
        }
        
    except Exception as e:
        raise Exception(f"Resize image failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def crop_image(file, input_body):
    """Crop image to specified dimensions"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'crop' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'crop'")
        
        crop_task = input_body['tasks']['crop']
        options = crop_task.get('options', {})
        
        # Get crop parameters
        x = options.get('x', 0)
        y = options.get('y', 0)
        width = options.get('width')
        height = options.get('height')
        
        if not width or not height:
            raise Exception("Crop dimensions (width and height) are required")
        
        # Get output format
        output_format = options.get('output_format', 'png').lower()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Open and crop image
        img = Image.open(input_path)
        cropped_img = img.crop((x, y, x + width, y + height))
        
        # Save cropped image
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if output_format == 'jpg' or output_format == 'jpeg':
            cropped_img = cropped_img.convert('RGB')
            cropped_img.save(output_path, 'JPEG', quality=95)
        else:
            cropped_img.save(output_path)
        
        return {
            'success': True,
            'message': 'Image cropped successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Crop image failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def get_image_colors(file, input_body):
    """Extract dominant colors from image"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Open image
        img = Image.open(input_path)
        
        # Resize for faster processing
        img_small = img.resize((150, 150))
        
        # Get colors
        colors = img_small.getcolors(maxcolors=10000)
        if not colors:
            # If getcolors fails, convert to RGB and try again
            img_small = img_small.convert('RGB')
            colors = img_small.getcolors(maxcolors=10000)
        
        if not colors:
            raise Exception("Could not extract colors from image")
        
        # Sort by frequency and get top colors
        colors.sort(key=lambda x: x[0], reverse=True)
        dominant_colors = []
        
        for count, color in colors[:10]:  # Get top 10 colors
            if len(color) == 3:  # RGB
                r, g, b = color
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                dominant_colors.append({
                    'rgb': color,
                    'hex': hex_color,
                    'hsv': (h*360, s*100, v*100),
                    'frequency': count
                })
        
        return {
            'success': True,
            'message': 'Colors extracted successfully',
            'colors': dominant_colors
        }
        
    except Exception as e:
        raise Exception(f"Color extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def rotate_image(file, input_body):
    """Rotate image by specified angle"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'rotate' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'rotate'")
        
        rotate_task = input_body['tasks']['rotate']
        options = rotate_task.get('options', {})
        
        # Get rotation parameters
        angle = options.get('angle', 90)
        expand = options.get('expand', True)
        
        # Get output format
        output_format = options.get('output_format', 'png').lower()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Open and rotate image
        img = Image.open(input_path)
        rotated_img = img.rotate(angle, expand=expand)
        
        # Save rotated image
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if output_format == 'jpg' or output_format == 'jpeg':
            rotated_img = rotated_img.convert('RGB')
            rotated_img.save(output_path, 'JPEG', quality=95)
        else:
            rotated_img.save(output_path)
        
        return {
            'success': True,
            'message': 'Image rotated successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Rotate image failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def flip_image(file, input_body):
    """Flip image horizontally or vertically"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'flip' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'flip'")
        
        flip_task = input_body['tasks']['flip']
        options = flip_task.get('options', {})
        
        # Get flip parameters
        direction = options.get('direction', 'horizontal')  # 'horizontal' or 'vertical'
        
        # Get output format
        output_format = options.get('output_format', 'png').lower()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Open and flip image
        img = Image.open(input_path)
        
        if direction == 'horizontal':
            flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif direction == 'vertical':
            flipped_img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        else:
            raise Exception("Invalid direction. Use 'horizontal' or 'vertical'")
        
        # Save flipped image
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if output_format == 'jpg' or output_format == 'jpeg':
            flipped_img = flipped_img.convert('RGB')
            flipped_img.save(output_path, 'JPEG', quality=95)
        else:
            flipped_img.save(output_path)
        
        return {
            'success': True,
            'message': 'Image flipped successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Flip image failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def enlarge_image(file, input_body):
    """Enlarge image using upscaling"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'enlarge' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'enlarge'")
        
        enlarge_task = input_body['tasks']['enlarge']
        options = enlarge_task.get('options', {})
        
        # Get enlargement parameters
        scale_factor = options.get('scale_factor', 2.0)
        method = options.get('method', 'lanczos')  # 'lanczos', 'bicubic', 'bilinear'
        
        if scale_factor <= 1.0:
            raise Exception("Scale factor must be greater than 1.0")
        
        # Get output format
        output_format = options.get('output_format', 'png').lower()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Open image
        img = Image.open(input_path)
        
        # Calculate new dimensions
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        
        # Choose resampling method
        if method == 'lanczos':
            resampling = Image.Resampling.LANCZOS
        elif method == 'bicubic':
            resampling = Image.Resampling.BICUBIC
        elif method == 'bilinear':
            resampling = Image.Resampling.BILINEAR
        else:
            resampling = Image.Resampling.LANCZOS
        
        # Enlarge image
        enlarged_img = img.resize((new_width, new_height), resampling)
        
        # Save enlarged image
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        if output_format == 'jpg' or output_format == 'jpeg':
            enlarged_img = enlarged_img.convert('RGB')
            enlarged_img.save(output_path, 'JPEG', quality=95)
        else:
            enlarged_img.save(output_path)
        
        return {
            'success': True,
            'message': 'Image enlarged successfully',
            'output_filename': output_filename,
            'download_url': f'/download/images/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Enlarge image failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass 