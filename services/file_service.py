import os
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def process_uploaded_file(file_path, file_type):
    """处理上传的文件，返回处理后的文件路径"""
    # 这里可以添加文件处理逻辑，如格式转换、优化等
    return file_path

def extract_text_from_pdf(file_path):
    """从PDF文件中提取文本，保留格式并识别标题和目录"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            # 处理每一页
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                # 添加页码标记
                text += f"<div class='pdf-page' data-page='{page_num+1}'>\n"
                
                # 处理段落
                paragraphs = page_text.split('\n')
                
                # 检测目录
                in_toc = False
                toc_items = []
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue
                    
                    # 检测是否为标题（简单启发式方法）
                    is_title = False
                    if len(paragraph) < 100 and (
                        paragraph.isupper() or 
                        paragraph.endswith(':') or
                        (paragraph.strip().startswith('第') and ('章' in paragraph or '节' in paragraph)) or
                        any(word in paragraph for word in ['目录', '章节', 'CHAPTER', 'SECTION'])
                    ):
                        is_title = True
                    
                    # 检测是否为目录项
                    is_toc_item = False
                    if '...' in paragraph or paragraph.strip().endswith('...'):
                        is_toc_item = True
                        in_toc = True
                        toc_items.append(paragraph)
                        continue
                    elif in_toc and (
                        (paragraph.strip().isdigit() or 
                         (len(paragraph) < 50 and any(c.isdigit() for c in paragraph)))
                    ):
                        is_toc_item = True
                        toc_items.append(paragraph)
                        continue
                    else:
                        in_toc = False
                    
                    if is_toc_item:
                        continue  # 跳过目录项，稍后一起处理
                    
                    if is_title:
                        # 处理标题
                        text += f"<h3 class='pdf-title'>{paragraph}</h3>\n"
                    else:
                        # 处理普通段落，分割成句子
                        sentences = []
                        current_sentence = ""
                        
                        # 简单的句子分割（可以根据需要改进）
                        for char in paragraph:
                            current_sentence += char
                            if char in ['。', '！', '？', '.', '!', '?'] and current_sentence.strip():
                                sentences.append(current_sentence.strip())
                                current_sentence = ""
                        
                        # 添加最后一个句子（如果有）
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        
                        # 将句子包装在span中，以便于朗读时高亮
                        formatted_paragraph = ""
                        for i, sentence in enumerate(sentences):
                            formatted_paragraph += f"<span class='sentence' data-sentence-id='{page_num}-{i}'>{sentence}</span> "
                        
                        text += f"<p>{formatted_paragraph}</p>\n"
                
                # 如果有目录项，添加到页面末尾
                if toc_items:
                    text += "<div class='pdf-toc'>\n"
                    text += "<h4>目录</h4>\n"
                    text += "<ul>\n"
                    for item in toc_items:
                        text += f"<li>{item}</li>\n"
                    text += "</ul>\n"
                    text += "</div>\n"
                
                text += "</div>\n"
            
            return text
    except Exception as e:
        raise Exception(f"PDF提取错误: {str(e)}")

def extract_text_from_docx(file_path):
    """从DOCX文件中提取文本，保留格式"""
    try:
        doc = docx.Document(file_path)
        text = "<div class='docx-document'>\n"
        
        # 处理段落
        has_content = False
        para_index = 0  # 使用手动索引而不是列表索引
        
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
                
            has_content = True
            # 检测是否为标题
            if para.style.name.startswith('Heading'):
                heading_level = int(para.style.name.replace('Heading', '')) if para.style.name != 'Heading' else 1
                if heading_level > 6:
                    heading_level = 6  # HTML只支持h1-h6
                text += f"<h{heading_level} class='docx-heading'>{para.text}</h{heading_level}>\n"
            else:
                # 处理普通段落，分割成句子
                sentences = []
                current_sentence = ""
                
                # 简单的句子分割
                for char in para.text:
                    current_sentence += char
                    if char in ['。', '！', '？', '.', '!', '?'] and current_sentence.strip():
                        sentences.append(current_sentence.strip())
                        current_sentence = ""
                
                # 添加最后一个句子（如果有）
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                
                # 将句子包装在span中，使用手动索引
                formatted_paragraph = ""
                for i, sentence in enumerate(sentences):
                    formatted_paragraph += f"<span class='sentence' data-sentence-id='p{para_index}-{i}'>{sentence}</span> "
                
                text += f"<p>{formatted_paragraph}</p>\n"
            
            para_index += 1  # 增加段落索引
        
        text += "</div>"
        
        # 如果没有内容，添加一个提示
        if not has_content:
            text = "<div class='docx-document'><p>此文档没有可读取的文本内容。</p></div>"
            
        return text
    except Exception as e:
        raise Exception(f"DOCX提取错误: {str(e)}")

def extract_text_from_epub(file_path):
    """从EPUB文件中提取文本，保留格式"""
    try:
        book = epub.read_epub(file_path)
        text = "<div class='epub-document'>\n"
        
        chapter_count = 0
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapter_count += 1
                content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # 添加章节标记
                text += f"<div class='epub-chapter' data-chapter='{chapter_count}'>\n"
                
                # 处理标题
                title_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_tags:
                    for title in title_tags:
                        text += f"<{title.name} class='epub-heading'>{title.get_text()}</{title.name}>\n"
                
                # 处理段落
                paragraphs = soup.find_all('p')
                para_index = 0  # 使用手动索引
                
                for para in paragraphs:
                    para_text = para.get_text().strip()
                    if not para_text:
                        continue
                    
                    # 分割成句子
                    sentences = []
                    current_sentence = ""
                    
                    for char in para_text:
                        current_sentence += char
                        if char in ['。', '！', '？', '.', '!', '?'] and current_sentence.strip():
                            sentences.append(current_sentence.strip())
                            current_sentence = ""
                    
                    # 添加最后一个句子（如果有）
                    if current_sentence.strip():
                        sentences.append(current_sentence.strip())
                    
                    # 将句子包装在span中，使用手动索引
                    formatted_paragraph = ""
                    for i, sentence in enumerate(sentences):
                        formatted_paragraph += f"<span class='sentence' data-sentence-id='c{chapter_count}-p{para_index}-{i}'>{sentence}</span> "
                    
                    text += f"<p>{formatted_paragraph}</p>\n"
                    para_index += 1  # 增加段落索引
                
                text += "</div>\n"
        
        text += "</div>"
        return text
    except Exception as e:
        raise Exception(f"EPUB提取错误: {str(e)}")

def extract_text_from_txt(file_path):
    """从TXT文件中提取文本，保留格式"""
    try:
        # 尝试不同编码读取文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        text_content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    text_content = file.read()
                break  # 如果成功读取，跳出循环
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            raise Exception("无法识别文件编码")
        
        # 将文本包装在HTML中
        text = "<div class='txt-document'>\n"
        
        # 处理段落
        paragraphs = text_content.split('\n\n')
        has_content = False
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            has_content = True
            
            # 检测是否为标题（简单启发式方法）
            is_title = False
            if len(paragraph) < 100 and (
                paragraph.isupper() or 
                paragraph.endswith(':') or
                (paragraph.strip().startswith('第') and ('章' in paragraph or '节' in paragraph)) or
                any(word in paragraph for word in ['目录', '章节', 'CHAPTER', 'SECTION'])
            ):
                is_title = True
            
            if is_title:
                # 处理标题
                text += f"<h3 class='txt-title'>{paragraph}</h3>\n"
            else:
                # 处理普通段落，分割成句子
                sentences = []
                current_sentence = ""
                
                # 简单的句子分割
                for char in paragraph:
                    current_sentence += char
                    if char in ['。', '！', '？', '.', '!', '?'] and current_sentence.strip():
                        sentences.append(current_sentence.strip())
                        current_sentence = ""
                
                # 添加最后一个句子（如果有）
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                
                # 将句子包装在span中
                formatted_paragraph = ""
                for i, sentence in enumerate(sentences):
                    formatted_paragraph += f"<span class='sentence' data-sentence-id='txt-{i}'>{sentence}</span> "
                
                text += f"<p>{formatted_paragraph}</p>\n"
        
        text += "</div>"
        
        # 如果没有内容，添加一个提示
        if not has_content:
            text = "<div class='txt-document'><p>此文档没有可读取的文本内容。</p></div>"
            
        return text
    except Exception as e:
        raise Exception(f"TXT提取错误: {str(e)}")

def extract_text_from_file(file_path, file_type):
    """根据文件类型提取文本"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
        
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'docx':
        return extract_text_from_docx(file_path)
    elif file_type == 'epub':
        return extract_text_from_epub(file_path)
    elif file_type == 'txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

def paginate_text(text, max_chars_per_page=1000):
    """将文本分成多个页面，每页不超过指定字符数"""
    if not text:
        return []
        
    # 如果文本已经包含HTML标记，需要特殊处理
    if '<span class=' in text or '<div class=' in text:
        # 处理HTML格式的文本
        soup = BeautifulSoup(text, 'html.parser')
        
        pages = []
        current_page = ""
        current_length = 0
        
        # 获取所有需要处理的元素
        elements = []
        
        # 首先找到所有顶级元素
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div']):
            # 只处理直接子元素，避免重复处理嵌套元素
            if element.parent.name in ['body', '[document]'] or element.parent.name == 'div' and 'class' in element.parent.attrs and (
                'docx-document' in element.parent['class'] or 
                'epub-document' in element.parent['class'] or
                'pdf-page' in element.parent['class'] or
                'txt-document' in element.parent['class']):
                elements.append(element)
        
        # 处理每个元素
        for element in elements:
            # 跳过空元素
            if not element.text.strip():
                continue
                
            # 跳过已经被处理过的嵌套元素
            if element.find_parent('div', class_=('epub-chapter', 'pdf-page', 'txt-document')) and element.name != 'div':
                continue
                
            # 获取元素的HTML字符串
            element_html = str(element)
            element_text = element.text.strip()
            
            # 如果当前元素会使页面超出限制，开始新页面
            if current_length + len(element_text) > max_chars_per_page and current_length > 0:
                pages.append(current_page)
                current_page = ""
                current_length = 0
            
            # 添加元素到当前页面
            current_page += element_html
            current_length += len(element_text)
        
        # 添加最后一页
        if current_page:
            pages.append(current_page)
            
        return pages
    else:
        # 处理纯文本
        pages = []
        paragraphs = text.split('\n\n')
        
        current_page = ""
        current_length = 0
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # 如果当前段落会使页面超出限制，开始新页面
            if current_length + len(paragraph) > max_chars_per_page and current_length > 0:
                pages.append(current_page)
                current_page = ""
                current_length = 0
            
            # 添加段落到当前页面
            if current_page:
                current_page += "\n\n"
            current_page += paragraph
            current_length += len(paragraph)
        
        # 添加最后一页
        if current_page:
            pages.append(current_page)
            
        return pages 