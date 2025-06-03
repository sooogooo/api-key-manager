from datetime import datetime, timedelta
import secrets
from functools import wraps
from flask import request, jsonify, g, current_app
import logging

logger = logging.getLogger(__name__)

class ApiKeyManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def create_key(self, name, created_by, validity_days=365, daily_limit=1000):
        """创建新的API密钥"""
        try:
            # 生成随机密钥
            api_key = secrets.token_hex(16)
            
            # 计算过期时间
            expires_at = datetime.now() + timedelta(days=validity_days) if validity_days > 0 else None
            
            # 保存到数据库
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_keys (
                        key, name, created_by, created_at, 
                        expires_at, status, daily_limit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    api_key,
                    name,
                    created_by,
                    datetime.now(),
                    expires_at,
                    'active',
                    daily_limit
                ))
                conn.commit()
                key_id = cursor.lastrowid
                
            logger.info(f"创建新API密钥: name={name}, id={key_id}")
            return {'id': key_id, 'key': api_key}
            
        except Exception as e:
            logger.error(f"创建API密钥失败: {e}")
            raise

    def validate_key(self, api_key):
        """验证API密钥并返回密钥对象"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM api_keys 
                    WHERE key = ? AND status = 'active'
                """, (api_key,))
                key_obj = cursor.fetchone()
                
                if not key_obj:
                    return None
                    
                # 检查是否过期
                if key_obj['expires_at'] and datetime.now() > key_obj['expires_at']:
                    return None
                    
                return key_obj
                
        except Exception as e:
            logger.error(f"验证API密钥时出错: {e}")
            return None

    def check_rate_limit(self, api_key_id):
        """检查API密钥的使用频率限制"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取今日使用次数
                cursor.execute("""
                    SELECT COUNT(*) FROM api_logs 
                    WHERE api_key_id = ? AND DATE(timestamp) = DATE('now')
                """, (api_key_id,))
                today_usage = cursor.fetchone()[0]
                
                # 获取密钥的每日限制
                cursor.execute("""
                    SELECT daily_limit FROM api_keys WHERE id = ?
                """, (api_key_id,))
                daily_limit = cursor.fetchone()[0]
                
                return today_usage < daily_limit
                
        except Exception as e:
            logger.error(f"检查使用频率限制时出错: {e}")
            return False

    def update_key_status(self, key_id, new_status):
        """更新API密钥状态"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE api_keys 
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (new_status, datetime.now(), key_id))
                conn.commit()
                
            logger.info(f"更新API密钥状态: id={key_id}, new_status={new_status}")
            return True
            
        except Exception as e:
            logger.error(f"更新API密钥状态失败: {e}")
            return False

    def delete_key(self, key_id):
        """删除API密钥"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
                conn.commit()
                
            logger.info(f"删除API密钥: id={key_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除API密钥失败: {e}")
            return False

    def get_key_list(self):
        """获取API密钥列表"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ak.*, u.username as created_by_name
                    FROM api_keys ak
                    LEFT JOIN users u ON ak.created_by = u.id
                    ORDER BY ak.created_at DESC
                """)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取API密钥列表失败: {e}")
            return []

    def log_api_call(self, client_ip, provider, model, api_key_id, success, 
                     error_message=None, response_time=0):
        """记录API调用日志"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_logs (
                        client_ip, provider, model, api_key_id, 
                        success, error_message, response_time,
                        request_path, request_method, response_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    client_ip, provider, model, api_key_id,
                    success, error_message, response_time,
                    request.path, request.method,
                    200 if success else 500
                ))
                conn.commit()
                
                # 更新API统计信息
                if success:
                    cursor.execute("""
                        INSERT INTO api_stats (
                            api_key_id, provider, date, total_calls, 
                            success_calls, average_latency
                        ) VALUES (?, ?, DATE('now'), 1, 1, ?)
                        ON CONFLICT(api_key_id, provider, date) DO UPDATE SET
                            total_calls = total_calls + 1,
                            success_calls = success_calls + 1,
                            average_latency = (average_latency * success_calls + ?) / (success_calls + 1)
                    """, (api_key_id, provider, response_time, response_time))
                else:
                    cursor.execute("""
                        INSERT INTO api_stats (
                            api_key_id, provider, date, total_calls
                        ) VALUES (?, ?, DATE('now'), 1)
                        ON CONFLICT(api_key_id, provider, date) DO UPDATE SET
                            total_calls = total_calls + 1
                    """, (api_key_id, provider))
                conn.commit()
                
        except Exception as e:
            logger.error(f"记录API调用日志时出错: {e}")

    def get_api_stats(self, api_key_id=None, provider=None, days=7):
        """获取API使用统计信息"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        date,
                        provider,
                        SUM(total_calls) as total_calls,
                        SUM(success_calls) as success_calls,
                        AVG(average_latency) as avg_latency
                    FROM api_stats
                    WHERE date >= DATE('now', ?)
                """
                params = [f'-{days} days']
                
                if api_key_id:
                    query += " AND api_key_id = ?"
                    params.append(api_key_id)
                if provider and provider != 'all':
                    query += " AND provider = ?"
                    params.append(provider)
                    
                query += " GROUP BY date, provider ORDER BY date DESC, provider"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取API统计信息时出错: {e}")
            return []

def get_api_key_from_request():
    """从请求中获取API密钥"""
    # 尝试从请求头获取
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        # 尝试从查询参数获取
        api_key = request.args.get('api_key')
    if not api_key:
        # 尝试从表单数据获取
        api_key = request.form.get('api_key')
    if not api_key and request.is_json:
        # 尝试从JSON数据获取
        api_key = request.json.get('api_key')
    return api_key

def require_api_key(f):
    """验证API密钥的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key_from_request()
        
        if not api_key:
            return jsonify({'error': 'API密钥缺失'}), 401
            
        api_key_manager = current_app.api_key_manager
        key_obj = api_key_manager.validate_key(api_key)
            
        if not key_obj:
            return jsonify({'error': '无效的API密钥'}), 401
            
        # 检查使用限制
        if not api_key_manager.check_rate_limit(key_obj['id']):
            return jsonify({'error': 'API密钥已达到使用限制或已过期'}), 429
            
        # 将API密钥对象添加到g对象中，以便在路由处理函数中使用
        g.api_key = key_obj
        
        return f(*args, **kwargs)
    return decorated_function