from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Blueprint, render_template, request, jsonify, 
    redirect, url_for, session, g, current_app
)
import logging

from models import db, ApiKey, ApiLog, ApiStat, SystemLog, User

logger = logging.getLogger(__name__)
bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
            
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': '需要管理员权限'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/api-keys')
@require_admin
def list_api_keys():
    """列出所有API密钥"""
    try:
        api_keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
        return render_template(
            'admin/api_keys.html',
            api_keys=api_keys,
            message=session.pop('message', None),
            error=session.pop('error', None)
        )
    except Exception as e:
        logger.error(f"获取API密钥列表失败: {e}")
        session['error'] = '获取API密钥列表失败'
        return redirect(url_for('admin.dashboard'))

@bp.route('/api-keys/new', methods=['GET', 'POST'])
@require_admin
def create_api_key():
    """创建新的API密钥"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            validity_days = int(request.form.get('validity_days', 365))
            daily_limit = int(request.form.get('daily_limit', 1000))
            
            # 创建新的API密钥
            import secrets
            key = ApiKey(
                key=secrets.token_hex(16),
                name=name,
                created_by=session['user_id'],
                expires_at=datetime.utcnow() + timedelta(days=validity_days) if validity_days > 0 else None,
                daily_limit=daily_limit
            )
            
            db.session.add(key)
            db.session.commit()
            
            SystemLog.log(f"创建新API密钥: {name}", level="INFO", source="create_api_key")
            session['message'] = 'API密钥创建成功'
            return redirect(url_for('admin.list_api_keys'))
            
        except Exception as e:
            logger.error(f"创建API密钥失败: {e}")
            session['error'] = f'创建API密钥失败: {str(e)}'
            return redirect(url_for('admin.create_api_key'))
    
    return render_template(
        'admin/create_api_key.html',
        error=session.pop('error', None)
    )

@bp.route('/api-keys/<int:key_id>/toggle', methods=['POST'])
@require_admin
def toggle_api_key(key_id):
    """启用/禁用API密钥"""
    try:
        key = ApiKey.query.get_or_404(key_id)
        key.status = 'disabled' if key.status == 'active' else 'active'
        key.updated_at = datetime.utcnow()
        db.session.commit()
        
        SystemLog.log(
            f"切换API密钥状态: {key.name} -> {key.status}",
            level="INFO",
            source="toggle_api_key"
        )
        return jsonify({'status': 'success', 'new_status': key.status})
        
    except Exception as e:
        logger.error(f"切换API密钥状态失败: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api-keys/<int:key_id>/delete', methods=['POST'])
@require_admin
def delete_api_key(key_id):
    """删除API密钥"""
    try:
        key = ApiKey.query.get_or_404(key_id)
        name = key.name
        db.session.delete(key)
        db.session.commit()
        
        SystemLog.log(f"删除API密钥: {name}", level="INFO", source="delete_api_key")
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"删除API密钥失败: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api-keys/<int:key_id>')
@require_admin
def view_api_key(key_id):
    """查看API密钥详情"""
    try:
        key = ApiKey.query.get_or_404(key_id)
        
        # 获取最近的调用日志
        recent_logs = ApiLog.query.filter_by(api_key_id=key_id)\
            .order_by(ApiLog.timestamp.desc())\
            .limit(100)\
            .all()
            
        # 获取使用统计
        stats = ApiStat.query.filter_by(api_key_id=key_id)\
            .order_by(ApiStat.date.desc())\
            .limit(30)\
            .all()
            
        return render_template(
            'admin/view_api_key.html',
            key=key,
            recent_logs=recent_logs,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"获取API密钥详情失败: {e}")
        session['error'] = '获取API密钥详情失败'
        return redirect(url_for('admin.list_api_keys'))

@bp.route('/stats')
@require_admin
def view_stats():
    """查看API使用统计"""
    try:
        provider = request.args.get('provider', 'all')
        days = int(request.args.get('days', 7))
        
        # 构建查询
        query = db.session.query(
            ApiStat.date,
            ApiStat.provider,
            db.func.sum(ApiStat.total_calls).label('total_calls'),
            db.func.sum(ApiStat.success_calls).label('success_calls'),
            db.func.avg(ApiStat.average_latency).label('avg_latency'),
            db.func.sum(ApiStat.total_tokens).label('total_tokens'),
            db.func.sum(ApiStat.total_cost).label('total_cost')
        )\
        .filter(ApiStat.date >= datetime.utcnow().date() - timedelta(days=days))
        
        if provider != 'all':
            query = query.filter(ApiStat.provider == provider)
            
        stats = query.group_by(ApiStat.date, ApiStat.provider)\
            .order_by(ApiStat.date.desc(), ApiStat.provider)\
            .all()
            
        return render_template(
            'admin/stats.html',
            stats=stats,
            provider=provider,
            days=days
        )
        
    except Exception as e:
        logger.error(f"获取API统计信息失败: {e}")
        session['error'] = '获取API统计信息失败'
        return redirect(url_for('admin.dashboard'))

@bp.route('/logs')
@require_admin
def view_logs():
    """查看系统日志"""
    try:
        page = request.args.get('page', 1, type=int)
        level = request.args.get('level', 'all')
        source = request.args.get('source', 'all')
        
        # 构建查询
        query = SystemLog.query
        
        if level != 'all':
            query = query.filter(SystemLog.level == level)
        if source != 'all':
            query = query.filter(SystemLog.source == source)
            
        # 分页
        pagination = query.order_by(SystemLog.timestamp.desc())\
            .paginate(page=page, per_page=50, error_out=False)
            
        return render_template(
            'admin/logs.html',
            logs=pagination.items,
            pagination=pagination,
            level=level,
            source=source
        )
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        session['error'] = '获取系统日志失败'
        return redirect(url_for('admin.dashboard'))

def init_app(app):
    """初始化路由"""
    app.register_blueprint(bp)