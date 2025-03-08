import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from models.user import User, db
from models.book import Book, ReadingProgress
from controllers.auth_controller import login_required
from services.file_service import process_uploaded_file, extract_text_from_file, paginate_text
from services.tts_service import generate_speech
from config.config import Config
import uuid
from datetime import datetime

book_bp = Blueprint('book', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@book_bp.route('/library')
@login_required
def library():
    user_id = session.get('user_id')
    
    # 获取用户的书籍
    user_books = Book.query.filter_by(user_id=user_id).all()
    
    # 获取公开的书籍（不包括用户自己的）
    public_books = Book.query.filter(Book.is_public == True, Book.user_id != user_id).all()
    
    return render_template('book/library.html', user_books=user_books, public_books=public_books)

@book_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # 检查是否有文件
        if 'file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        
        # 先检查原始文件名是否符合要求
        original_filename = file.filename
        if '.' not in original_filename:
            flash('文件名必须包含扩展名', 'danger')
            return redirect(request.url)
            
        # 获取文件类型
        file_type = original_filename.rsplit('.', 1)[1].lower()
        
        # 检查文件类型是否允许
        if file_type not in Config.ALLOWED_EXTENSIONS:
            flash('不支持的文件类型', 'danger')
            return redirect(request.url)
            
        # 安全处理文件名
        filename = secure_filename(original_filename)
        
        # 创建唯一的文件名
        unique_filename = f"{uuid.uuid4().hex}.{file_type}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件
        file.save(file_path)
        
        # 获取书籍标题和作者
        title = request.form.get('title')
        if not title:
            # 使用原始文件名作为标题，去掉扩展名
            title = original_filename.rsplit('.', 1)[0]
            
        author = request.form.get('author') or '未知'
        is_public = True if request.form.get('is_public') else False
        
        # 创建书籍记录
        new_book = Book(
            title=title,
            author=author,
            file_path=unique_filename,
            file_type=file_type,
            original_filename=original_filename,
            is_public=is_public,
            user_id=session.get('user_id')
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        flash('书籍上传成功', 'success')
        return redirect(url_for('book.library'))
            
    return render_template('book/upload.html')

@book_bp.route('/read/<int:book_id>')
@login_required
def read(book_id):
    user_id = session.get('user_id')
    
    # 获取书籍信息
    book = Book.query.get_or_404(book_id)
    
    # 检查权限（用户自己的书或公开的书）
    if book.user_id != user_id and not book.is_public:
        flash('您没有权限访问此书籍', 'danger')
        return redirect(url_for('book.library'))
    
    # 获取或创建阅读进度
    progress = ReadingProgress.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not progress:
        progress = ReadingProgress(user_id=user_id, book_id=book_id)
        db.session.add(progress)
        db.session.commit()
    
    # 更新最后阅读时间
    progress.last_read = datetime.utcnow()
    db.session.commit()
    
    return render_template('book/reader.html', book=book, progress=progress)

@book_bp.route('/api/text/<int:book_id>', endpoint='api_text')
@login_required
def get_book_text(book_id):
    user_id = session.get('user_id')
    
    # 检查用户是否已登录
    if not user_id:
        return jsonify({'error': '用户未登录'}), 401
    
    # 获取书籍信息
    book = Book.query.get_or_404(book_id)
    print(f"获取书籍: ID={book.id}, 标题={book.title}, 文件路径={book.file_path}")
    
    # 检查权限
    if book.user_id != user_id and not book.is_public:
        return jsonify({'error': '没有权限'}), 403
    
    # 获取文件路径
    file_path = os.path.join(Config.UPLOAD_FOLDER, book.file_path)
    print(f"完整文件路径: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({'error': f'文件不存在: {book.original_filename}'}), 404
    
    try:
        # 提取文本
        text = extract_text_from_file(file_path, book.file_type)
        
        # 确保文本不为空
        if not text or text.strip() == "":
            text = "<p>此文档没有可读取的文本内容。</p>"
            return jsonify({'pages': [text], 'total_pages': 1})
        
        # 将文本分页
        pages = paginate_text(text, max_chars_per_page=1000)
        
        print(f"成功提取文本，分为 {len(pages)} 页")
        return jsonify({
            'pages': pages,
            'total_pages': len(pages)
        })
    except Exception as e:
        # 记录错误并返回友好的错误信息
        print(f"提取文本错误: {str(e)}")
        return jsonify({'error': f'无法提取文本: {str(e)}'}), 500

# @book_bp.route('/api/tts', methods=['POST'])
# @login_required
# def text_to_speech():
#     data = request.json
#     text = data.get('text')
#     voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
#     
#     if not text:
#         return jsonify({'error': '没有提供文本'}), 400
#     
#     try:
#         # 生成语音，现在返回URL而不是文件路径
#         audio_url = generate_speech(text, voice)
#         
#         return jsonify({'audio_url': audio_url})
#     except Exception as e:
#         print(f"TTS错误: {str(e)}")
#         return jsonify({'error': f'语音生成失败: {str(e)}'}), 500

@book_bp.route('/api/save-progress', methods=['POST'])
@login_required
def save_progress():
    try:
        data = request.json
        if not data:
            return jsonify({'error': '没有提供数据'}), 400
            
        print(f"接收到的进度数据: {data}")  # 添加调试日志
        
        book_id = data.get('book_id')
        position = data.get('position')
        voice_name = data.get('voice_name', 'default')
        current_page = data.get('current_page', 0)
        
        if not book_id:
            return jsonify({'error': '缺少book_id参数'}), 400
        
        if position is None:  # 允许position为0
            return jsonify({'error': '缺少position参数'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': '用户未登录'}), 401
        
        # 更新阅读进度
        progress = ReadingProgress.query.filter_by(user_id=user_id, book_id=book_id).first()
        
        if progress:
            progress.position = float(position)  # 确保position是浮点数
            progress.voice_name = voice_name
            progress.current_page = int(current_page)  # 确保current_page是整数
            progress.last_read = datetime.utcnow()
        else:
            # 如果记录不存在，创建新记录
            progress = ReadingProgress(
                user_id=user_id,
                book_id=book_id,
                position=float(position),
                voice_name=voice_name,
                current_page=int(current_page)
            )
            db.session.add(progress)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '进度已保存'})
        
    except Exception as e:
        print(f"保存进度错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'保存进度失败: {str(e)}'}), 500 