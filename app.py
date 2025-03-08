from flask import Flask, render_template, redirect, url_for
from models.user import db
from controllers.auth_controller import auth_bp
from controllers.book_controller import book_bp
from config.config import Config
import os
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    # 只在开发环境或明确指定时重置数据库
    if os.environ.get('RESET_DB') == '1':
        with app.app_context():
            print("重置数据库...")
            db.drop_all()  # 删除所有表
            db.create_all()  # 重新创建所有表
    else:
        # 确保数据库表存在
        with app.app_context():
            db.create_all()
    
    # 在应用启动时检查并添加缺失的列
    with app.app_context():
        # 检查current_page列是否存在
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('reading_progress')]
        
        if 'current_page' not in columns:
            print("添加current_page列到reading_progress表")
            db.engine.execute('ALTER TABLE reading_progress ADD COLUMN current_page INTEGER DEFAULT 0')
    
    # 注册蓝图 - 确保路由前缀正确
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(book_bp, url_prefix='/book')
    
    # 单独注册 API 路由
    from controllers.book_controller import get_book_text, save_progress
    app.add_url_rule('/api/text/<int:book_id>', 'api_text', get_book_text)
    app.add_url_rule('/api/save-progress', 'api_save_progress', save_progress, methods=['POST'])
    
    # 确保上传目录存在
    upload_dir = Config.UPLOAD_FOLDER
    os.makedirs(upload_dir, exist_ok=True)
    print(f"上传目录: {upload_dir}")  # 添加日志以便调试
    
    # 创建音频目录
    audio_dir = os.path.join(os.path.dirname(__file__), 'static/audio')
    os.makedirs(audio_dir, exist_ok=True)
    print(f"音频目录: {audio_dir}")  # 添加日志以便调试
    
    # 添加全局上下文处理器
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    
    @app.route('/')
    def index():
        return redirect(url_for('book.library'))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 