听书网 (BookTTS)
网址: http://hi.20241122.xyz

项目简介
基于纯 JavaScript 前端与 Python/SQLite 的听书平台，支持用户注册登录后上传书籍、分页及 TTS 音频朗读。所有核心功能需登录访问。

核心功能
用户认证系统
强制登录：上传文件、查看书库等功能仅限已登录用户使用。
账户安全：
密码加密存储（bcrypt 哈希算法）
单次会话有效期默认为 2 小时
用户数据与账号强关联，书籍仅对本人可见。
核心功能
注册 & 登录 → 管理个人书库。
支持 Word/TXT/PDF/EPUB 文件上传并自动分页。
浏览器 TTS 朗读（支持自定义语音角色与语速）。
手动跳转至指定页码或章节开始播放。
技术栈
模块	技术/工具
后端	Flask (路由 + API) + SQLite
前端	纯 JavaScript + HTML/CSS
用户认证	自定义 Session 验证机制
文件解析	python-docx、PyPDF2
快速启动
开发环境准备
# 安装依赖（确保 Python 3.8+）
pip install -r requirements.txt  
# 包含 Flask, flask-sqlalchemy 等基础库

# 初始化数据库表结构（首次运行必做！）
python init_db.py
运行服务
python app.py  
# 默认访问地址：http://localhost:5000 （重定向到登录页）
用户指南
1. 注册与登录
创建新账户：
访问网站根路径 → 点击 **"注册"**。
填写用户名、密码后提交 → 自动跳转至书库页面。
登录现有账号：
在登录页输入用户名和密码 → 成功后进入书库主页。
如忘记密码，需通过邮箱重置（暂未实现）。
2. 使用核心功能
已登录用户可操作：

上传书籍：

导航至书库页面 → 点击 "选择文件" 按钮。
文件解析完成自动展示分页内容，仅保存于当前账号下。
TTS 朗读：

// 前端调用示例（需登录状态）
function startReading(pageNumber) {
    const audio = new SpeechSynthesisUtterance(getPageContent(pageNumber));
    window.speechSynthesis.speak(audio);
}
API 文档 (Flask 后端)
路径	方法	描述
/api/register	POST	创建新用户账号
/api/login	POST	登录并返回 Session Cookie
/api/logout	GET	注销当前会话
/api/check-auth	GET	检查登录状态（前端用）
安全与部署注意事项
用户数据隔离
书籍表设计：
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100))
    # 其他字段如分页内容...
部署建议
# 生产环境推荐设置 HTTPS（部署指南另附）
# 启动正式服务时绑定域名：
python app.py --host=0.0.0.0 --port=80  
FAQ
Q: 登录失败如何排查？ A:

检查用户名或密码是否正确。
清除浏览器 Cookie 后重试。
Q: 如何查看书籍分页数据？ A: 上传成功后，在书库页面选择书籍 → 进入章节列表即可查看分页内容。

联系我们
技术支持：support@hi.20241122.xyz
提交问题：GitHub 仓库（如有公开代码库）
特别说明：
登录状态检查：所有需要认证的路由均被 @login_required 装饰器保护，未登录用户会被重定向到 /login。
会话机制：通过 Flask 的 Session 管理 Cookie，存储用户 ID 以确保权限控制。
