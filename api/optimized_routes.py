"""
Optimized API Routes dengan caching dan bulk operations
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.database_service import DatabaseService
from services.websocket_service import websocket_service
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('optimized_api', __name__, url_prefix='/api/v2')

# Initialize services
db_service = None
ws_service = None

def init_services(db, redis_client, socketio):
    """Initialize services"""
    global db_service, ws_service
    db_service = DatabaseService(db, redis_client)
    ws_service = websocket_service


@api_bp.route('/debug/stream/publish', methods=['POST'])
def debug_stream_publish():
    """Publish a test emotion event into the stream."""
    if not db_service or not db_service.redis:
        return jsonify({'error': 'Redis not available'}), 503
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id', 0)
    emotion = data.get('emotion', 'neutral')
    confidence = data.get('confidence')
    detected_at = data.get('detected_at') or datetime.utcnow().isoformat()

    try:
        from services.redis_streams import publish_emotion_event
        publish_emotion_event(
            db_service.redis,
            student_id=int(student_id),
            emotion=emotion,
            confidence=confidence,
            detected_at_iso=detected_at,
            extra={'source': 'debug-api'}
        )
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/debug/stream/health', methods=['GET'])
def debug_stream_health():
    if not db_service or not db_service.redis:
        return jsonify({'status': 'redis_unavailable'}), 503
    try:
        stream = os.environ.get('EMOTION_STREAM', 'emotion-events')
        group = os.environ.get('EMOTION_GROUP', 'emotion-workers')
        
        # Check if stream exists
        try:
            info = db_service.redis.xinfo_stream(stream)
            stream_exists = True
        except Exception:
            info = None
            stream_exists = False
        
        # Check groups if stream exists
        groups = []
        group_info = None
        if stream_exists:
            try:
                groups = db_service.redis.xinfo_groups(stream)
                for g in groups:
                    if g.get('name') == group:
                        group_info = g
                        break
            except Exception:
                groups = []
        
        payload = {
            'stream': stream,
            'stream_exists': stream_exists,
            'length': info.get('length') if info and isinstance(info, dict) else 0,
            'groups': groups,
            'group_info': group_info,
        }
        
        # pending metrics
        if stream_exists and group_info:
            try:
                pend = db_service.redis.xpending(stream, group)
                if isinstance(pend, dict):
                    payload['pending'] = pend.get('pending')
                else:
                    payload['pending'] = pend[0] if isinstance(pend, (list, tuple)) and pend else 0
            except Exception:
                payload['pending'] = 0
        else:
            payload['pending'] = 0
            
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"Stream health error: {e}")
        return jsonify({'error': str(e)}), 500

def require_role(roles):
    """Role-based access control decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                user = db_service.get_user_with_relations(user_id)
                if not user or user['user']['role'] not in roles:
                    return jsonify({'error': 'Access denied'}), 403
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return decorated_function
    return decorator

@api_bp.route('/dashboard/stats')
@jwt_required()
def get_optimized_dashboard_stats():
    """Optimized dashboard stats dengan caching"""
    try:
        user_id = get_jwt_identity()
        user_data = db_service.get_user_with_relations(user_id)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        user_role = user_data['user']['role']
        stats = db_service.get_dashboard_stats_optimized(user_id, user_role)
        
        # Add real-time data
        if ws_service:
            connection_stats = ws_service.get_connection_stats()
            stats['real_time'] = connection_stats
            
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/students/bulk', methods=['POST'])
@jwt_required()
@require_role(['guru', 'admin'])
def bulk_create_students():
    """Bulk create students untuk efisiensi"""
    try:
        data = request.get_json()
        students_data = data.get('students', [])
        
        if not students_data:
            return jsonify({'error': 'No students data provided'}), 400
            
        # Validate all students first
        for student_data in students_data:
            required_fields = ['student_code', 'full_name', 'class_name']
            for field in required_fields:
                if field not in student_data or not student_data[field]:
                    return jsonify({'error': f'Field {field} is required for all students'}), 400
        
        # Bulk create
        from models import Student, StudentTeacher
        user_id = get_jwt_identity()
        
        created_students = []
        for student_data in students_data:
            student = Student(
                student_code=student_data['student_code'],
                full_name=student_data['full_name'],
                class_name=student_data['class_name'],
                birth_date=student_data.get('birth_date'),
                photo_path=student_data.get('photo_path')
            )
            db_service.db.session.add(student)
            db_service.db.session.flush()  # Get ID without commit
            
            # Create teacher-student relationship
            if user_id:
                relation = StudentTeacher(
                    teacher_id=user_id,
                    student_id=student.id
                )
                db_service.db.session.add(relation)
            
            created_students.append(student.to_dict())
        
        db_service.db.session.commit()
        
        # Clear cache
        if db_service.redis:
            pattern = f"user:{user_id}:*"
            keys = db_service.redis.keys(pattern)
            if keys:
                db_service.redis.delete(*keys)
        
        return jsonify({
            'message': f'Successfully created {len(created_students)} students',
            'students': created_students
        }), 201
        
    except Exception as e:
        db_service.db.session.rollback()
        logger.error(f"Bulk create students error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/emotions/bulk', methods=['POST'])
@jwt_required()
@require_role(['guru', 'admin'])
def bulk_create_emotion_logs():
    """Bulk create emotion logs untuk performa"""
    try:
        data = request.get_json()
        logs_data = data.get('logs', [])
        
        if not logs_data:
            return jsonify({'error': 'No logs data provided'}), 400
        
        # Validate logs
        for log_data in logs_data:
            required_fields = ['session_id', 'student_id', 'emotion']
            for field in required_fields:
                if field not in log_data:
                    return jsonify({'error': f'Field {field} is required for all logs'}), 400
        
        # Bulk insert
        success = db_service.bulk_create_emotion_logs(logs_data)
        
        if success:
            # Broadcast updates via WebSocket
            if ws_service:
                for log_data in logs_data:
                    ws_service.broadcast_emotion_update(
                        log_data['student_id'],
                        log_data['emotion'],
                        log_data.get('detected_at', '')
                    )
            
            return jsonify({
                'message': f'Successfully created {len(logs_data)} emotion logs'
            }), 201
        else:
            return jsonify({'error': 'Failed to create emotion logs'}), 500
            
    except Exception as e:
        logger.error(f"Bulk create emotion logs error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analytics/emotions')
@jwt_required()
@require_role(['guru', 'admin'])
def get_emotion_analytics():
    """Optimized emotion analytics dengan caching"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 7, type=int)
        
        analytics = db_service.get_emotion_analytics_optimized(user_id, days)
        
        return jsonify(analytics), 200
        
    except Exception as e:
        logger.error(f"Emotion analytics error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/mental/score')
@jwt_required()
@require_role(['guru', 'admin'])
def get_mental_score():
    """Get daily risk score trend for a student."""
    try:
        student_id = request.args.get('student_id', type=int)
        days = request.args.get('days', 7, type=int)
        if not student_id:
            return jsonify({'error': 'student_id is required'}), 400

        if not db_service or not db_service.redis:
            return jsonify({'error': 'Redis not available'}), 503

        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        out = []
        for i in range(days):
            day = today - timedelta(days=i)
            key = f"risk:student:{student_id}:{day.isoformat()}"
            r = db_service.redis.hgetall(key)
            if r:
                try:
                    out.append({
                        'date': day.isoformat(),
                        'score': float(r.get('score', 0)),
                        'band': r.get('band', 'low'),
                        'ratio_negative': float(r.get('ratio_negative', 0)),
                        'ratio_neutral': float(r.get('ratio_neutral', 0)),
                        'ratio_positive': float(r.get('ratio_positive', 0)),
                        'total': int(r.get('total', 0)),
                    })
                except Exception:
                    pass

        # sort ascending by date
        out.sort(key=lambda x: x['date'])
        return jsonify({'student_id': student_id, 'days': days, 'trend': out}), 200
    except Exception as e:
        logger.error(f"Mental score error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/system/health')
@jwt_required()
@require_role(['admin'])
def get_system_health():
    """System health check dengan real-time stats"""
    try:
        health_data = {
            'database': 'healthy',
            'redis': 'healthy' if db_service.redis else 'unavailable',
            'websocket': 'healthy' if ws_service else 'unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add connection stats
        if ws_service:
            health_data['connections'] = ws_service.get_connection_stats()
        
        # Add cache stats
        if db_service.redis:
            try:
                cache_info = db_service.redis.info('memory')
                health_data['cache'] = {
                    'used_memory': cache_info.get('used_memory_human'),
                    'connected_clients': cache_info.get('connected_clients')
                }
            except Exception:
                health_data['cache'] = 'unavailable'
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"System health error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cache/clear')
@jwt_required()
@require_role(['admin'])
def clear_cache():
    """Clear all cache"""
    try:
        if db_service.redis:
            db_service.redis.flushdb()
            return jsonify({'message': 'Cache cleared successfully'}), 200
        else:
            return jsonify({'error': 'Redis not available'}), 503
            
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/debug/worker/status', methods=['GET'])
def get_worker_status():
    """Get worker status"""
    try:
        # Check if worker thread exists and is alive
        from app import worker_thread
        if worker_thread and worker_thread.is_alive():
            status = 'running'
        else:
            status = 'stopped'
        
        return jsonify({
            'status': status,
            'thread_alive': worker_thread.is_alive() if worker_thread else False
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/debug/worker/restart', methods=['POST'])
@jwt_required()
@require_role(['admin'])
def restart_worker():
    """Restart worker (admin only)"""
    try:
        import threading
        from workers.emotion_stream_worker import main as worker_main
        from app import worker_thread, worker_stop_event
        
        def run_worker():
            try:
                worker_main()
            except Exception as e:
                logger.error(f"Worker error: {e}")
        
        # Start new worker thread
        new_thread = threading.Thread(target=run_worker, daemon=True)
        new_thread.start()
        
        return jsonify({'message': 'Worker restarted successfully'}), 200
    except Exception as e:
        logger.error(f"Worker restart error: {e}")
        return jsonify({'error': str(e)}), 500