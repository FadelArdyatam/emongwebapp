#!/usr/bin/env python3
"""
Worker untuk image processing (resize, compress, crop, dll)
"""

import os
import time
import json
import signal
import logging
import redis
from datetime import datetime
from typing import Dict, Any
import cv2
import numpy as np
from PIL import Image
import io
import base64

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("image-worker")

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
IMAGE_STREAM = 'image-processing-events'
GROUP = 'image-workers'
CONSUMER = f"worker-{os.getpid()}"

_stop = False
_processed = 0
_failed = 0

def _handle_stop(signum, frame):
    global _stop
    _stop = True

def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(IMAGE_STREAM, GROUP, id='0', mkstream=True)
        logger.info("Created image processing stream group %s", GROUP)
    except redis.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise

def resize_image(image_data: bytes, width: int, height: int, quality: int = 95) -> bytes:
    """Resize image to specified dimensions"""
    try:
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")
        
        # Resize image
        resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        
        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded_img = cv2.imencode('.jpg', resized, encode_param)
        
        return encoded_img.tobytes()
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        raise

def compress_image(image_data: bytes, quality: int = 80) -> bytes:
    """Compress image with specified quality"""
    try:
        # Use PIL for better compression control
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Compress
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        raise

def crop_face(image_data: bytes, face_coords: Dict[str, int]) -> bytes:
    """Crop face from image using coordinates"""
    try:
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")
        
        # Extract face coordinates
        x = face_coords['x']
        y = face_coords['y']
        w = face_coords['width']
        h = face_coords['height']
        
        # Add some padding
        padding = 20
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2 * padding)
        h = min(img.shape[0] - y, h + 2 * padding)
        
        # Crop face
        face_crop = img[y:y+h, x:x+w]
        
        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        _, encoded_img = cv2.imencode('.jpg', face_crop, encode_param)
        
        return encoded_img.tobytes()
        
    except Exception as e:
        logger.error(f"Error cropping face: {e}")
        raise

def generate_thumbnail(image_data: bytes, size: int = 150) -> bytes:
    """Generate thumbnail of specified size"""
    try:
        # Use PIL for thumbnail generation
        img = Image.open(io.BytesIO(image_data))
        
        # Create thumbnail
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Save as JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        raise

def detect_and_extract_faces(image_data: bytes) -> Dict[str, Any]:
    """Detect and extract faces from image"""
    try:
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")
        
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        face_data = []
        for i, (x, y, w, h) in enumerate(faces):
            # Crop face
            face_crop = img[y:y+h, x:x+w]
            
            # Encode face
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
            _, encoded_face = cv2.imencode('.jpg', face_crop, encode_param)
            
            face_data.append({
                'face_id': i,
                'coordinates': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                'face_image': base64.b64encode(encoded_face.tobytes()).decode('utf-8'),
                'confidence': 1.0  # Basic detection confidence
            })
        
        return {
            'faces_detected': len(faces),
            'faces': face_data,
            'original_size': {'width': img.shape[1], 'height': img.shape[0]}
        }
        
    except Exception as e:
        logger.error(f"Error detecting faces: {e}")
        raise

def _process_image_job(r: redis.Redis, message_id: str, fields: dict) -> None:
    """Process image processing job"""
    global _processed, _failed
    
    try:
        job_type = fields.get('job_type')
        image_data = base64.b64decode(fields.get('image_data', ''))
        job_params = json.loads(fields.get('job_params', '{}'))
        
        logger.info("Processing image job %s: %s", message_id, job_type)
        
        result = None
        
        if job_type == 'resize':
            width = job_params.get('width', 800)
            height = job_params.get('height', 600)
            quality = job_params.get('quality', 95)
            result_data = resize_image(image_data, width, height, quality)
            result = {
                'processed_image': base64.b64encode(result_data).decode('utf-8'),
                'original_size': len(image_data),
                'processed_size': len(result_data),
                'compression_ratio': len(result_data) / len(image_data)
            }
            
        elif job_type == 'compress':
            quality = job_params.get('quality', 80)
            result_data = compress_image(image_data, quality)
            result = {
                'processed_image': base64.b64encode(result_data).decode('utf-8'),
                'original_size': len(image_data),
                'processed_size': len(result_data),
                'compression_ratio': len(result_data) / len(image_data)
            }
            
        elif job_type == 'crop_face':
            face_coords = job_params.get('face_coords', {})
            result_data = crop_face(image_data, face_coords)
            result = {
                'processed_image': base64.b64encode(result_data).decode('utf-8'),
                'face_coords': face_coords
            }
            
        elif job_type == 'thumbnail':
            size = job_params.get('size', 150)
            result_data = generate_thumbnail(image_data, size)
            result = {
                'processed_image': base64.b64encode(result_data).decode('utf-8'),
                'thumbnail_size': size
            }
            
        elif job_type == 'detect_faces':
            face_data = detect_and_extract_faces(image_data)
            result = face_data
        
        if result:
            # Store result in Redis
            result_key = f"image:result:{message_id}"
            r.hset(result_key, mapping=result)
            r.expire(result_key, 24 * 3600)  # 24 hours
            
            _processed += 1
            logger.info("Image job completed: %s", message_id)
        else:
            _failed += 1
            logger.error("Image job failed: %s", message_id)
            
    except Exception as e:
        _failed += 1
        logger.exception("Error processing image job %s: %s", message_id, str(e))

def main() -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    _ensure_group(r)
    
    logger.info("Image processing worker started")
    
    # Process pending jobs
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {IMAGE_STREAM: '0'}, count=50, block=100)
        if not resp:
            break
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_image_job(r, mid, fields)
                    r.xack(IMAGE_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing pending image job %s", mid)
    
    # Process new jobs
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {IMAGE_STREAM: '>'}, count=50, block=5000)
        if not resp:
            continue
            
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_image_job(r, mid, fields)
                    r.xack(IMAGE_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing image job %s", mid)
    
    logger.info("Image processing worker shutting down")

if __name__ == '__main__':
    main()
