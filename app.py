from flask import Flask, render_template, request, jsonify, session
from config import Config
from xiaohongshu_bot import XiaohongshuBot
import threading
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

bots = {}
tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    data = request.json
    headless = data.get('headless', False)
    
    try:
        bot = XiaohongshuBot(headless=headless)
        bot.init_driver()
        bot.open_xiaohongshu()
        
        session_id = session.get('session_id') or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session['session_id'] = session_id
        bots[session_id] = bot
        
        return jsonify({
            'success': True,
            'message': '浏览器已启动，请在打开的窗口中登录小红书',
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动失败: {str(e)}'
        })

@app.route('/api/check_login', methods=['GET'])
def check_login():
    session_id = session.get('session_id')
    bot = bots.get(session_id)
    
    if not bot:
        return jsonify({
            'success': False,
            'message': '请先启动浏览器'
        })
    
    try:
        # 确保浏览器在小红书首页，这样可以更准确地检查登录状态
        current_url = bot.driver.current_url
        if 'xiaohongshu.com' not in current_url:
            bot.open_xiaohongshu()
        
        is_logged_in = bot.check_login_status()
        return jsonify({
            'success': True,
            'is_logged_in': is_logged_in,
            'message': '已登录' if is_logged_in else '未登录，请完成登录'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查登录状态失败: {str(e)}'
        })

@app.route('/api/search', methods=['POST'])
def search():
    session_id = session.get('session_id')
    bot = bots.get(session_id)
    
    if not bot:
        return jsonify({
            'success': False,
            'message': '请先启动浏览器并登录'
        })
    
    keyword = request.json.get('keyword', '')
    if not keyword:
        return jsonify({
            'success': False,
            'message': '请输入搜索关键词'
        })
    
    try:
        notes = bot.search_by_keyword(keyword)
        return jsonify({
            'success': True,
            'notes': notes,
            'count': len(notes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        })

@app.route('/api/get_comments', methods=['POST'])
def get_comments():
    session_id = session.get('session_id')
    bot = bots.get(session_id)
    
    if not bot:
        return jsonify({
            'success': False,
            'message': '请先启动浏览器并登录'
        })
    
    note_url = request.json.get('note_url', '')
    if not note_url:
        return jsonify({
            'success': False,
            'message': '请输入笔记链接'
        })
    
    try:
        comments = bot.get_note_comments(note_url)
        return jsonify({
            'success': True,
            'comments': comments,
            'count': len(comments)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取评论失败: {str(e)}'
        })

@app.route('/api/auto_reply', methods=['POST'])
def auto_reply():
    session_id = session.get('session_id')
    bot = bots.get(session_id)
    
    if not bot:
        return jsonify({
            'success': False,
            'message': '请先启动浏览器并登录'
        })
    
    data = request.json
    note_url = data.get('note_url', '')
    reply_template = data.get('reply_template', Config.DEFAULT_REPLY_TEMPLATE)
    keywords_filter = data.get('keywords_filter', '').split(',') if data.get('keywords_filter') else None
    max_replies = int(data.get('max_replies', Config.MAX_REPLIES_PER_NOTE))
    
    if not note_url:
        return jsonify({
            'success': False,
            'message': '请输入笔记链接'
        })
    
    def reply_task():
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        tasks[task_id] = {
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'replied_comments': []
        }
        
        try:
            replied = bot.auto_reply_comments(
                note_url=note_url,
                reply_template=reply_template,
                keywords_filter=keywords_filter,
                max_replies=max_replies
            )
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['replied_comments'] = replied
            tasks[task_id]['end_time'] = datetime.now().isoformat()
        except Exception as e:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = str(e)
            tasks[task_id]['end_time'] = datetime.now().isoformat()
        
        return task_id
    
    task_id = reply_task()
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '自动回复任务已启动'
    })

@app.route('/api/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        })
    
    return jsonify({
        'success': True,
        'task': task
    })

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    session_id = session.get('session_id')
    bot = bots.get(session_id)
    
    if bot:
        bot.close()
        del bots[session_id]
    
    return jsonify({
        'success': True,
        'message': '浏览器已关闭'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
