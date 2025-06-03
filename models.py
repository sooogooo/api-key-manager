from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')  # active, disabled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    api_keys = db.relationship('ApiKey', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ApiKey(db.Model):
    """API密钥模型"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, disabled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    daily_limit = db.Column(db.Integer, default=1000)
    total_calls = db.Column(db.Integer, default=0)
    
    # 关系
    logs = db.relationship('ApiLog', backref='api_key', lazy=True)
    stats = db.relationship('ApiStat', backref='api_key', lazy=True)
    
    @property
    def is_expired(self):
        """检查密钥是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def update_usage(self):
        """更新使用情况"""
        self.last_used_at = datetime.utcnow()
        self.total_calls += 1
        db.session.commit()

class ApiLog(db.Model):
    """API调用日志模型"""
    __tablename__ = 'api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client_ip = db.Column(db.String(45))
    provider = db.Column(db.String(20))  # openai, anthropic, google
    model = db.Column(db.String(50))
    request_path = db.Column(db.String(200))
    request_method = db.Column(db.String(10))
    response_code = db.Column(db.Integer)
    response_time = db.Column(db.Float)  # 响应时间（秒）
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    @classmethod
    def create(cls, **kwargs):
        """创建新的日志记录"""
        log = cls(**kwargs)
        db.session.add(log)
        db.session.commit()
        return log

class ApiStat(db.Model):
    """API使用统计模型"""
    __tablename__ = 'api_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    total_calls = db.Column(db.Integer, default=0)
    success_calls = db.Column(db.Integer, default=0)
    average_latency = db.Column(db.Float, default=0.0)
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    
    __table_args__ = (
        db.UniqueConstraint('api_key_id', 'date', 'provider', name='unique_daily_stats'),
    )
    
    @classmethod
    def update_stats(cls, api_key_id, provider, success, latency=0, tokens=0, cost=0):
        """更新统计信息"""
        today = datetime.utcnow().date()
        stat = cls.query.filter_by(
            api_key_id=api_key_id,
            date=today,
            provider=provider
        ).first()
        
        if not stat:
            stat = cls(
                api_key_id=api_key_id,
                date=today,
                provider=provider
            )
            db.session.add(stat)
        
        stat.total_calls += 1
        if success:
            stat.success_calls += 1
            if stat.average_latency == 0:
                stat.average_latency = latency
            else:
                stat.average_latency = (stat.average_latency * (stat.success_calls - 1) + latency) / stat.success_calls
        
        stat.total_tokens += tokens
        stat.total_cost += cost
        
        db.session.commit()
        return stat

class SystemLog(db.Model):
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20))  # INFO, WARNING, ERROR
    message = db.Column(db.Text)
    source = db.Column(db.String(100))
    
    @classmethod
    def log(cls, message, level='INFO', source=None):
        """记录系统日志"""
        log = cls(
            message=message,
            level=level,
            source=source
        )
        db.session.add(log)
        db.session.commit()
        return log