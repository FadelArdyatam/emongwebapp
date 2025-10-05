"""
User Management Service untuk advanced user operations
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from models import db, User, Student, StudentParent
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

class UserManagementService:
    def __init__(self):
        pass
    
    def get_user_activity_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user activity summary"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get user statistics
            total_users = User.query.count()
            active_users = User.query.filter(User.is_active == True).count()
            inactive_users = total_users - active_users
            
            # Get role distribution
            role_stats = db.session.query(
                User.role, 
                func.count(User.id).label('count')
            ).group_by(User.role).all()
            
            role_distribution = {role: count for role, count in role_stats}
            
            # Get recent registrations
            recent_registrations = User.query.filter(
                User.created_at >= start_date
            ).order_by(User.created_at.desc()).limit(10).all()
            
            # Get user activity (login attempts, etc.)
            # This would need to be implemented based on your login tracking
            recent_activity = self._get_recent_user_activity(days)
            
            return {
                'status': 'success',
                'summary': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': inactive_users,
                    'role_distribution': role_distribution,
                    'period_days': days
                },
                'recent_registrations': [
                    {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'created_at': user.created_at.isoformat(),
                        'is_active': user.is_active
                    }
                    for user in recent_registrations
                ],
                'recent_activity': recent_activity,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_recent_user_activity(self, days: int) -> List[Dict[str, Any]]:
        """Get recent user activity (placeholder implementation)"""
        # This would need to be implemented based on your activity tracking
        # For now, return empty list
        return []
    
    def bulk_user_operations(self, operation: str, user_ids: List[int], **kwargs) -> Dict[str, Any]:
        """Perform bulk operations on users"""
        try:
            if not user_ids:
                return {'status': 'error', 'message': 'No users selected'}
            
            users = User.query.filter(User.id.in_(user_ids)).all()
            if not users:
                return {'status': 'error', 'message': 'No users found'}
            
            results = {
                'success_count': 0,
                'error_count': 0,
                'errors': []
            }
            
            for user in users:
                try:
                    if operation == 'activate':
                        user.is_active = True
                        user.updated_at = datetime.utcnow()
                    elif operation == 'deactivate':
                        user.is_active = False
                        user.updated_at = datetime.utcnow()
                    elif operation == 'delete':
                        # Soft delete - mark as inactive instead of hard delete
                        user.is_active = False
                        user.updated_at = datetime.utcnow()
                        user.deleted_at = datetime.utcnow()
                    elif operation == 'change_role':
                        new_role = kwargs.get('new_role')
                        if new_role in ['admin', 'guru', 'orang_tua']:
                            user.role = new_role
                            user.updated_at = datetime.utcnow()
                        else:
                            raise ValueError(f"Invalid role: {new_role}")
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                    
                    results['success_count'] += 1
                    
                except Exception as e:
                    results['error_count'] += 1
                    results['errors'].append({
                        'user_id': user.id,
                        'username': user.username,
                        'error': str(e)
                    })
            
            # Commit all changes
            db.session.commit()
            
            return {
                'status': 'success',
                'operation': operation,
                'results': results,
                'message': f"Operation completed: {results['success_count']} success, {results['error_count']} errors"
            }
            
        except Exception as e:
            logger.error(f"Error in bulk user operations: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_user_detailed_info(self, user_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            # Get related data based on role
            related_data = {}
            
            if user.role == 'orang_tua':
                # Get children
                children = db.session.query(Student).join(StudentParent).filter(
                    StudentParent.parent_id == user_id
                ).all()
                
                related_data['children'] = [
                    {
                        'id': child.id,
                        'student_code': child.student_code,
                        'full_name': child.full_name,
                        'class_name': child.class_name,
                        'is_active': child.is_active
                    }
                    for child in children
                ]
            
            elif user.role == 'guru':
                # Get students in their class (if class-based system)
                # This would need to be implemented based on your class structure
                related_data['students'] = []
            
            # Get user statistics
            stats = {
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
                'login_count': 0  # This would need to be tracked
            }
            
            return {
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'related_data': related_data,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user detailed info: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_users(self, query: str, role: Optional[str] = None, 
                    is_active: Optional[bool] = None, limit: int = 50) -> Dict[str, Any]:
        """Advanced user search with filters"""
        try:
            # Build query
            search_query = User.query
            
            # Text search
            if query:
                search_query = search_query.filter(
                    or_(
                        User.username.ilike(f'%{query}%'),
                        User.email.ilike(f'%{query}%'),
                        User.full_name.ilike(f'%{query}%')
                    )
                )
            
            # Role filter
            if role:
                search_query = search_query.filter(User.role == role)
            
            # Active status filter
            if is_active is not None:
                search_query = search_query.filter(User.is_active == is_active)
            
            # Execute query
            users = search_query.order_by(User.created_at.desc()).limit(limit).all()
            
            return {
                'status': 'success',
                'users': [
                    {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role,
                        'is_active': user.is_active,
                        'created_at': user.created_at.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    }
                    for user in users
                ],
                'total_found': len(users),
                'query': query,
                'filters': {
                    'role': role,
                    'is_active': is_active
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def export_users(self, format: str = 'json', filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Export users data in specified format"""
        try:
            # Build query with filters
            query = User.query
            
            if filters:
                if filters.get('role'):
                    query = query.filter(User.role == filters['role'])
                if filters.get('is_active') is not None:
                    query = query.filter(User.is_active == filters['is_active'])
                if filters.get('created_after'):
                    query = query.filter(User.created_at >= filters['created_after'])
                if filters.get('created_before'):
                    query = query.filter(User.created_at <= filters['created_before'])
            
            users = query.all()
            
            # Prepare data
            user_data = [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ]
            
            if format == 'json':
                return {
                    'status': 'success',
                    'format': 'json',
                    'data': user_data,
                    'total_records': len(user_data),
                    'exported_at': datetime.utcnow().isoformat()
                }
            elif format == 'csv':
                # Convert to CSV format
                csv_data = self._convert_to_csv(user_data)
                return {
                    'status': 'success',
                    'format': 'csv',
                    'data': csv_data,
                    'total_records': len(user_data),
                    'exported_at': datetime.utcnow().isoformat()
                }
            else:
                return {'status': 'error', 'message': f'Unsupported format: {format}'}
                
        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _convert_to_csv(self, data: List[Dict]) -> str:
        """Convert data to CSV format"""
        if not data:
            return ""
        
        # Get headers
        headers = list(data[0].keys())
        
        # Create CSV
        csv_lines = [','.join(headers)]
        for row in data:
            csv_lines.append(','.join([str(row.get(header, '')) for header in headers]))
        
        return '\n'.join(csv_lines)
    
    def get_user_roles_permissions(self) -> Dict[str, Any]:
        """Get available roles and their permissions"""
        return {
            'status': 'success',
            'roles': {
                'admin': {
                    'name': 'Administrator',
                    'description': 'Full system access',
                    'permissions': [
                        'user_management',
                        'student_management',
                        'system_monitoring',
                        'data_export',
                        'system_configuration'
                    ]
                },
                'guru': {
                    'name': 'Guru',
                    'description': 'Teacher access',
                    'permissions': [
                        'student_management',
                        'emotion_detection',
                        'reports_view',
                        'session_management'
                    ]
                },
                'orang_tua': {
                    'name': 'Orang Tua',
                    'description': 'Parent access',
                    'permissions': [
                        'child_monitoring',
                        'reports_view',
                        'mental_health_view'
                    ]
                }
            }
        }

# Global instance
user_management_service = UserManagementService()