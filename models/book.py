from datetime import datetime
from models.user import db

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, epub, docx
    original_filename = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Book {self.title}>'

class ReadingProgress(db.Model):
    __tablename__ = 'reading_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    position = db.Column(db.Float, default=0)  # 进度百分比或位置
    voice_name = db.Column(db.String(50), default='default')  # 默认语音
    current_page = db.Column(db.Integer, default=0)  # 当前页面
    last_read = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系定义
    user = db.relationship('User')
    book = db.relationship('Book')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'book_id', name='uix_user_book'),
    ) 