import os
import uuid
import tempfile
import json
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import zipfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'documents')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
PREVIEW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'previews')

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

SUPPORTED_PDF_FORMATS = ['pdf']

def upload_pdf_file(file):
    """Upload PDF file and return file_id for processing"""
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        
        # Validate PDF by opening it
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF uploaded successfully',
            'file_id': file_id,
            'filename': file.filename,
            'total_pages': total_pages
        }
        
    except Exception as e:
        # Clean up file if upload failed
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass
        raise Exception(f"PDF upload failed: {str(e)}")

def get_pdf_pages(file_id):
    """Get PDF pages information with previews"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        pages = []
        
        for page_num in range(total_pages):
            page = pdf_doc[page_num]
            
            # Create preview image
            mat = fitz.Matrix(0.5, 0.5)  # Scale down for preview
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save preview image
            preview_filename = f"{file_id}_page_{page_num + 1}.png"
            preview_path = os.path.join(PREVIEW_DIR, preview_filename)
            img.save(preview_path, "PNG")
            
            # Create preview URL
            preview_url = f"/static/previews/{preview_filename}"
            
            pages.append({
                'page_number': page_num + 1,
                'preview_url': preview_url,
                'width': pix.width,
                'height': pix.height
            })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF pages retrieved successfully',
            'total_pages': total_pages,
            'pages': pages
        }
        
    except Exception as e:
        raise Exception(f"Failed to get PDF pages: {str(e)}")

def split_pdf_by_file_id(input_body):
    """Split PDF using file_id"""
    try:
        file_id = input_body['file_id']
        split_task = input_body['tasks']['split']
        options = split_task.get('options', {})
        
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Get split parameters
        split_method = options.get('split_method', 'individual')
        page_ranges = options.get('page_ranges', '')
        every_n_pages = options.get('every_n_pages', 2)
        output_filename = options.get('output_filename', 'split')
        selected_pages = options.get('selected_pages', [])
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        output_files = []
        
        if split_method == 'range':
            # Split by page ranges
            if page_ranges:
                # Parse page ranges (e.g., "1-3,5,7-9")
                ranges = parse_page_ranges(page_ranges, total_pages)
                for i, page_range in enumerate(ranges):
                    start_page, end_page = page_range
                    new_doc = fitz.open()
                    new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                    
                    output_filename_gen = f"{output_filename}_part_{i+1}.pdf"
                    output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                    new_doc.save(output_path)
                    new_doc.close()
                    
                    output_files.append({
                        'filename': output_filename_gen,
                        'download_url': f'/static/documents/{output_filename_gen}',
                        'pages': f'{start_page}-{end_page}'
                    })
            else:
                # Use selected pages
                if selected_pages:
                    for i, page_num in enumerate(selected_pages):
                        if 1 <= page_num <= total_pages:
                            new_doc = fitz.open()
                            new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                            
                            output_filename_gen = f"{output_filename}_page_{page_num}.pdf"
                            output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                            new_doc.save(output_path)
                            new_doc.close()
                            
                            output_files.append({
                                'filename': output_filename_gen,
                                'download_url': f'/static/documents/{output_filename_gen}',
                                'pages': f'{page_num}'
                            })
        
        elif split_method == 'individual':
            # Split each selected page into individual files
            if selected_pages:
                for page_num in selected_pages:
                    if 1 <= page_num <= total_pages:
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                        
                        output_filename_gen = f"{output_filename}_page_{page_num}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{page_num}'
                        })
        
        elif split_method == 'every':
            # Split every N pages
            for i in range(0, total_pages, every_n_pages):
                end_page = min(i + every_n_pages, total_pages)
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=i, to_page=end_page-1)
                
                output_filename_gen = f"{output_filename}_part_{i//every_n_pages + 1}.pdf"
                output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                new_doc.save(output_path)
                new_doc.close()
                
                output_files.append({
                    'filename': output_filename_gen,
                    'download_url': f'/static/documents/{output_filename_gen}',
                    'pages': f'{i+1}-{end_page}'
                })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF split successfully',
            'output_files': output_files,
            'download_urls': [f['download_url'] for f in output_files]
        }
        
    except Exception as e:
        raise Exception(f"PDF split failed: {str(e)}")

def parse_page_ranges(ranges_str, total_pages):
    """Parse page ranges string into list of tuples"""
    ranges = []
    parts = ranges_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Range like "1-3"
            start, end = part.split('-')
            try:
                start_page = int(start.strip())
                end_page = int(end.strip())
                if 1 <= start_page <= end_page <= total_pages:
                    ranges.append((start_page, end_page))
            except ValueError:
                continue
        else:
            # Single page like "5"
            try:
                page_num = int(part)
                if 1 <= page_num <= total_pages:
                    ranges.append((page_num, page_num))
            except ValueError:
                continue
    
    return ranges

def merge_pdfs(files, input_body):
    """Merge multiple PDF files into one"""
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'merge' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'merge'")
        
        merge_task = input_body['tasks']['merge']
        options = merge_task.get('options', {})
        
        # Get PDF files
        pdf_files = [f for f in files if f.filename.lower().endswith('.pdf')]
        if len(pdf_files) < 2:
            raise Exception("At least 2 PDF files are required for merging")
        
        # Create output PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Merge PDFs
        merger = fitz.open()
        
        for pdf_file in pdf_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
                pdf_file.save(temp_input.name)
                pdf_doc = fitz.open(temp_input.name)
                merger.insert_pdf(pdf_doc)
                pdf_doc.close()
                os.unlink(temp_input.name)
        
        merger.save(output_path)
        merger.close()
        
        return {
            'success': True,
            'message': 'PDFs merged successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF merge failed: {str(e)}")

def split_pdf(file, input_body):
    """Split PDF into multiple files"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'split' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'split'")
        
        split_task = input_body['tasks']['split']
        options = split_task.get('options', {})
        
        # Get split parameters
        split_type = options.get('split_type', 'pages')  # 'pages' or 'ranges'
        pages_per_file = options.get('pages_per_file', 1)
        page_ranges = options.get('page_ranges', [])  # List of page ranges like [[1,3], [5,7]]
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        output_files = []
        
        if split_type == 'pages':
            # Split by number of pages per file
            for i in range(0, total_pages, pages_per_file):
                end_page = min(i + pages_per_file, total_pages)
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=i, to_page=end_page-1)
                
                output_filename = str(uuid.uuid4()) + '.pdf'
                output_path = os.path.join(EXPORT_DIR, output_filename)
                new_doc.save(output_path)
                new_doc.close()
                
                output_files.append({
                    'filename': output_filename,
                    'download_url': f'/download/documents/{output_filename}',
                    'pages': f'{i+1}-{end_page}'
                })
        
        elif split_type == 'ranges':
            # Split by specified page ranges
            for i, page_range in enumerate(page_ranges):
                if len(page_range) == 2:
                    start_page, end_page = page_range
                    new_doc = fitz.open()
                    new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                    
                    output_filename = str(uuid.uuid4()) + '.pdf'
                    output_path = os.path.join(EXPORT_DIR, output_filename)
                    new_doc.save(output_path)
                    new_doc.close()
                    
                    output_files.append({
                        'filename': output_filename,
                        'download_url': f'/download/documents/{output_filename}',
                        'pages': f'{start_page}-{end_page}'
                    })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF split successfully',
            'output_files': output_files
        }
        
    except Exception as e:
        raise Exception(f"PDF split failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def flatten_pdf(file, input_body):
    """Flatten PDF (convert annotations and form fields to content)"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'flatten' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'flatten'")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Flatten annotations and form fields
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            page.apply_redactions()
            page.flatten_annotations()
        
        # Save flattened PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF flattened successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF flatten failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def resize_pdf(file, input_body):
    """Resize PDF pages to specified dimensions"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'resize' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'resize'")
        
        resize_task = input_body['tasks']['resize']
        options = resize_task.get('options', {})
        
        # Get resize parameters
        width = options.get('width')
        height = options.get('height')
        scale = options.get('scale', 1.0)
        
        if not width and not height and scale == 1.0:
            raise Exception("Either width/height or scale must be specified")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Create new PDF with resized pages
        new_doc = fitz.open()
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Calculate new dimensions
            if width and height:
                new_width, new_height = width, height
            else:
                new_width = page.rect.width * scale
                new_height = page.rect.height * scale
            
            # Create new page with new dimensions
            new_page = new_doc.new_page(width=new_width, height=new_height)
            
            # Copy content with scaling
            mat = fitz.Matrix(scale, scale)
            new_page.show_pdf_page(new_page.rect, pdf_doc, page_num, matrix=mat)
        
        # Save resized PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF resized successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF resize failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def unlock_pdf(file, input_body):
    """Remove password protection from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'unlock' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'unlock'")
        
        unlock_task = input_body['tasks']['unlock']
        options = unlock_task.get('options', {})
        
        # Get password if provided
        password = options.get('password', '')
        
        # Open PDF
        try:
            pdf_doc = fitz.open(input_path)
        except:
            # Try with password
            pdf_doc = fitz.open(input_path, password=password)
        
        # Create new unprotected PDF
        new_doc = fitz.open()
        new_doc.insert_pdf(pdf_doc)
        
        # Save unprotected PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF unlocked successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF unlock failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def rotate_pdf(file, input_body):
    """Rotate PDF pages"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'rotate' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'rotate'")
        
        rotate_task = input_body['tasks']['rotate']
        options = rotate_task.get('options', {})
        
        # Get rotation parameters
        angle = options.get('angle', 90)  # 90, 180, 270
        page_range = options.get('page_range', 'all')  # 'all' or specific pages
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Apply rotation
        if page_range == 'all':
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page.set_rotation(angle)
        else:
            # Apply to specific pages
            for page_num in page_range:
                if 0 <= page_num < len(pdf_doc):
                    page = pdf_doc[page_num]
                    page.set_rotation(angle)
        
        # Save rotated PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF rotated successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF rotate failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def protect_pdf(file, input_body):
    """Add password protection to PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'protect' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'protect'")
        
        protect_task = input_body['tasks']['protect']
        options = protect_task.get('options', {})
        
        # Get protection parameters
        user_password = options.get('user_password', '')
        owner_password = options.get('owner_password', '')
        permissions = options.get('permissions', 0)  # PDF permissions
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Set encryption
        if user_password or owner_password:
            pdf_doc.save(
                input_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=user_password,
                owner_pw=owner_password,
                permissions=permissions
            )
        
        # Save protected PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF protected successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF protection failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_image_from_pdf(file, input_body):
    """Extract images from PDF pages"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'extract_image' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'extract_image'")
        
        extract_task = input_body['tasks']['extract_image']
        options = extract_task.get('options', {})
        
        # Get extraction parameters
        page_number = options.get('page_number', 0)  # 0-based
        image_format = options.get('image_format', 'png')
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        if page_number >= len(pdf_doc):
            raise Exception(f"Page number {page_number} is out of range")
        
        # Get page
        page = pdf_doc[page_number]
        
        # Extract images
        image_list = page.get_images()
        extracted_images = []
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            pix = fitz.Pixmap(pdf_doc, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_data = pix.tobytes("png")
            else:  # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix1.tobytes("png")
                pix1 = None
            
            # Save image
            output_filename = str(uuid.uuid4()) + f'.{image_format}'
            output_path = os.path.join(EXPORT_DIR, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            extracted_images.append({
                'filename': output_filename,
                'download_url': f'/download/images/{output_filename}',
                'index': img_index
            })
            
            pix = None
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Extracted {len(extracted_images)} images from page {page_number + 1}',
            'extracted_images': extracted_images
        }
        
    except Exception as e:
        raise Exception(f"Image extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_all_images_from_pdf(file):
    """Extract all images from all pages of PDF and return as ZIP file"""
    print(f"[DEBUG] Starting image extraction for file: {file.filename}")
    
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name
        print(f"[DEBUG] File saved to temporary path: {input_path}")

    try:
        # Open PDF
        print("[DEBUG] Opening PDF document...")
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        print(f"[DEBUG] PDF opened successfully. Total pages: {total_pages}")
        
        # Create ZIP file
        zip_filename = str(uuid.uuid4()) + '.zip'
        zip_path = os.path.join(EXPORT_DIR, zip_filename)
        print(f"[DEBUG] Creating ZIP file: {zip_path}")
        
        extracted_count = 0
        total_images_found = 0
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Extract images from each page
            for page_num in range(total_pages):
                print(f"[DEBUG] Processing page {page_num + 1}/{total_pages}")
                page = pdf_doc[page_num]
                
                # Get images from page
                image_list = page.get_images()
                page_image_count = len(image_list)
                print(f"[DEBUG] Found {page_image_count} images on page {page_num + 1}")
                total_images_found += page_image_count
                
                for img_index, img in enumerate(image_list):
                    print(f"[DEBUG] Processing image {img_index + 1}/{page_image_count} on page {page_num + 1}")
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_doc, xref)
                    
                    try:
                        # Handle different image formats with robust alpha channel removal
                        print(f"[DEBUG] Image format: n={pix.n}, alpha={pix.alpha}")
                        
                        if pix.n == 1:  # GRAY
                            print(f"[DEBUG] Image is GRAY format")
                            img_data = pix.tobytes("jpeg")
                        elif pix.n == 3:  # RGB
                            print(f"[DEBUG] Image is RGB format")
                            img_data = pix.tobytes("jpeg")
                        elif pix.n == 4:  # RGBA or CMYK
                            if pix.alpha:  # RGBA
                                print(f"[DEBUG] Image is RGBA format, removing alpha channel")
                                # Create RGB version without alpha - more robust approach
                                try:
                                    # First try direct RGB conversion
                                    rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                                    img_data = rgb_pix.tobytes("jpeg")
                                    rgb_pix = None
                                except Exception as rgb_error:
                                    print(f"[DEBUG] Direct RGB conversion failed: {rgb_error}")
                                    # Fallback: convert to PIL Image and back to remove alpha
                                    import io
                                    from PIL import Image
                                    
                                    # Convert to PIL Image
                                    img_bytes = pix.tobytes("png")
                                    pil_img = Image.open(io.BytesIO(img_bytes))
                                    
                                    # Convert to RGB (removes alpha)
                                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                                        pil_img = pil_img.convert('RGB')
                                    
                                    # Convert back to bytes
                                    img_buffer = io.BytesIO()
                                    pil_img.save(img_buffer, format='JPEG', quality=95)
                                    img_data = img_buffer.getvalue()
                                    img_buffer.close()
                            else:  # CMYK
                                print(f"[DEBUG] Image is CMYK format, converting to RGB")
                                rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                                img_data = rgb_pix.tobytes("jpeg")
                                rgb_pix = None
                        else:
                            print(f"[DEBUG] Unknown image format (n={pix.n}), converting to RGB")
                            # Convert to RGB as fallback
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = rgb_pix.tobytes("jpeg")
                            rgb_pix = None
                        
                        # Create filename for ZIP
                        img_filename = f"page_{page_num + 1}_image_{img_index + 1}.jpg"
                        print(f"[DEBUG] Adding to ZIP: {img_filename}")
                        
                        # Add to ZIP file
                        zip_file.writestr(img_filename, img_data)
                        extracted_count += 1
                        
                        print(f"[DEBUG] Image {img_index + 1} on page {page_num + 1} processed successfully")
                        
                    except Exception as img_error:
                        print(f"[DEBUG] Error processing image {img_index + 1} on page {page_num + 1}: {img_error}")
                        # Continue with next image instead of failing completely
                        continue
                    finally:
                        pix = None
        
        pdf_doc.close()
        print(f"[DEBUG] PDF document closed")
        print(f"[DEBUG] Total images found: {total_images_found}")
        print(f"[DEBUG] Total images extracted: {extracted_count}")
        
        if extracted_count == 0:
            print("[DEBUG] No images found in the PDF")
            raise Exception("No images found in the PDF")
        
        print(f"[DEBUG] ZIP file created successfully: {zip_path}")
        print(f"[DEBUG] Extraction completed successfully")
        
        return {
            'success': True,
            'message': f'Extracted {extracted_count} images from {total_pages} pages',
            'zip_filename': zip_filename,
            'download_url': f'/download/documents/{zip_filename}',
            'extracted_count': extracted_count,
            'total_pages': total_pages
        }
        
    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        raise Exception(f"Image extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
                print(f"[DEBUG] Temporary file cleaned up: {input_path}")
            except:
                print(f"[DEBUG] Failed to clean up temporary file: {input_path}")
                pass

def remove_pdf_pages(file, input_body):
    """Remove specific pages from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'remove_pages' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'remove_pages'")
        
        remove_task = input_body['tasks']['remove_pages']
        options = remove_task.get('options', {})
        
        # Get removal parameters
        pages_to_remove = options.get('pages_to_remove', [])  # List of page numbers (1-based)
        
        if not pages_to_remove:
            raise Exception("No pages specified for removal")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        # Convert to 0-based indexing
        pages_to_remove = [p - 1 for p in pages_to_remove if 1 <= p <= total_pages]
        
        if not pages_to_remove:
            raise Exception("No valid pages to remove")
        
        # Create new PDF without specified pages
        new_doc = fitz.open()
        
        for page_num in range(total_pages):
            if page_num not in pages_to_remove:
                new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        
        # Save modified PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Removed {len(pages_to_remove)} pages from PDF',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF page removal failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def remove_pages_by_file_id(file_id, page_ids):
    """Remove specific pages from PDF using file_id and page_ids"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        # Convert page_ids to 0-based indexing and validate
        pages_to_remove = []
        for page_id in page_ids:
            if isinstance(page_id, int) and 1 <= page_id <= total_pages:
                pages_to_remove.append(page_id - 1)
        
        if not pages_to_remove:
            raise Exception("No valid pages to remove")
        
        # Create new PDF without specified pages
        new_doc = fitz.open()
        
        for page_num in range(total_pages):
            if page_num not in pages_to_remove:
                new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        
        # Save modified PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Removed {len(pages_to_remove)} pages from PDF',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF page removal failed: {str(e)}")

def extract_pdf_pages(file, input_body):
    """Extract specific pages from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'extract_pages' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'extract_pages'")
        
        extract_task = input_body['tasks']['extract_pages']
        options = extract_task.get('options', {})
        
        # Get extraction parameters
        page_ranges = options.get('page_ranges', [])  # List of page ranges like [[1,3], [5,7]]
        
        if not page_ranges:
            raise Exception("No page ranges specified for extraction")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        extracted_files = []
        
        # Extract each page range
        for i, page_range in enumerate(page_ranges):
            if len(page_range) == 2:
                start_page, end_page = page_range
                
                # Validate page range
                if start_page < 1 or end_page > total_pages or start_page > end_page:
                    continue
                
                # Create new PDF with extracted pages
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                
                # Save extracted PDF
                output_filename = str(uuid.uuid4()) + '.pdf'
                output_path = os.path.join(EXPORT_DIR, output_filename)
                new_doc.save(output_path)
                new_doc.close()
                
                extracted_files.append({
                    'filename': output_filename,
                    'download_url': f'/download/documents/{output_filename}',
                    'pages': f'{start_page}-{end_page}'
                })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Extracted {len(extracted_files)} page ranges from PDF',
            'extracted_files': extracted_files
        }
        
    except Exception as e:
        raise Exception(f"PDF page extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_pages_by_file_id(file_id, page_ranges, merge_output=False, compression_level='none', password=''):
    """Extract pages from PDF using file_id"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        try:
            if password:
                pdf_doc = fitz.open(file_path, password=password)
            else:
                pdf_doc = fitz.open(file_path)
        except:
            raise Exception("Failed to open PDF. Check if password is correct.")
        
        total_pages = len(pdf_doc)
        
        # Validate page ranges
        valid_pages = []
        for page_num in page_ranges:
            if isinstance(page_num, int) and 1 <= page_num <= total_pages:
                valid_pages.append(page_num - 1)  # Convert to 0-based index
            else:
                raise Exception(f"Invalid page number: {page_num}. Must be between 1 and {total_pages}")
        
        if not valid_pages:
            raise Exception("No valid pages to extract")
        
        # Remove duplicates and sort
        valid_pages = sorted(list(set(valid_pages)))
        
        if merge_output:
            # Extract all selected pages into one PDF
            new_doc = fitz.open()
            for page_index in valid_pages:
                new_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
            
            # Save merged PDF with compression if specified
            output_filename = str(uuid.uuid4()) + '.pdf'
            output_path = os.path.join(EXPORT_DIR, output_filename)
            
            if compression_level != 'none':
                # Apply compression based on level
                if compression_level == 'low':
                    new_doc.save(output_path, garbage=1, deflate=True)
                elif compression_level == 'medium':
                    new_doc.save(output_path, garbage=2, deflate=True)
                elif compression_level == 'high':
                    new_doc.save(output_path, garbage=3, deflate=True, clean=True)
                else:
                    new_doc.save(output_path)
            else:
                new_doc.save(output_path)
            new_doc.close()
            
            pdf_doc.close()
            
            return {
                'success': True,
                'message': f'Extracted {len(valid_pages)} pages into single PDF',
                'output_filename': output_filename,
                'download_url': f'/download/documents/{output_filename}'
            }
        else:
            # Extract each page as separate PDF and create a ZIP file
            extracted_files = []
            temp_files = []  # Track temporary files for cleanup
            
            try:
                for page_index in valid_pages:
                    new_doc = fitz.open()
                    new_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                    
                    # Save individual PDF with compression if specified
                    output_filename = str(uuid.uuid4()) + '.pdf'
                    output_path = os.path.join(EXPORT_DIR, output_filename)
                    
                    if compression_level != 'none':
                        # Apply compression based on level
                        if compression_level == 'low':
                            new_doc.save(output_path, garbage=1, deflate=True)
                        elif compression_level == 'medium':
                            new_doc.save(output_path, garbage=2, deflate=True)
                        elif compression_level == 'high':
                            new_doc.save(output_path, garbage=3, deflate=True, clean=True)
                        else:
                            new_doc.save(output_path)
                    else:
                        new_doc.save(output_path)
                    new_doc.close()
                    
                    temp_files.append(output_path)
                    
                    extracted_files.append({
                        'filename': output_filename,
                        'download_url': f'/download/documents/{output_filename}',
                        'page': page_index + 1
                    })
                
                # Create ZIP file containing all extracted PDFs
                zip_filename = str(uuid.uuid4()) + '.zip'
                zip_path = os.path.join(EXPORT_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for i, file_path in enumerate(temp_files):
                        # Add file to ZIP with descriptive name
                        page_num = valid_pages[i] + 1
                        zip_name = f'page_{page_num}.pdf'
                        zipf.write(file_path, zip_name)
                
                pdf_doc.close()
                
                return {
                    'success': True,
                    'message': f'Extracted {len(extracted_files)} pages as separate PDFs in ZIP file',
                    'download_url': f'/download/documents/{zip_filename}',
                    'extracted_files': extracted_files,
                    'zip_filename': zip_filename
                }
                
            finally:
                # Clean up individual PDF files after creating ZIP
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except:
                        pass
        
    except Exception as e:
        raise Exception(f"PDF page extraction failed: {str(e)}")