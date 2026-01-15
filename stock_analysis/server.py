"""
BlackOil 分析服务器 - Flask API
优化版：增强健壮性和性能
"""
from flask import Flask, jsonify, send_file, request, Response
from flask_cors import CORS
import os
import glob
import sys
import platform
from operator import itemgetter
import datetime
import json
import subprocess
import threading
import hashlib
import time
from functools import wraps
from collections import OrderedDict

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 缓存系统 ====================
class LRUCache:
    """线程安全的 LRU 缓存"""
    def __init__(self, maxsize=100, ttl=300):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl  # 秒
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    self.cache.move_to_end(key)
                    return value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            self.cache[key] = (value, time.time())
    
    def invalidate(self, pattern=None):
        """清除缓存，可选按前缀清除"""
        with self.lock:
            if pattern:
                keys_to_delete = [k for k in self.cache if k.startswith(pattern)]
                for k in keys_to_delete:
                    del self.cache[k]
            else:
                self.cache.clear()

# 全局缓存实例
report_cache = LRUCache(maxsize=50, ttl=60)  # 报告列表缓存 60 秒
summary_cache = LRUCache(maxsize=100, ttl=300)  # 摘要数据缓存 5 分钟
file_etag_cache = LRUCache(maxsize=500, ttl=3600)  # 文件 ETag 缓存 1 小时

# ==================== 任务管理 ====================
class TaskManager:
    """线程安全的任务管理器"""
    def __init__(self, max_tasks=100, cleanup_interval=3600):
        self.tasks = {}
        self.lock = threading.Lock()
        self.max_tasks = max_tasks
        self.cleanup_interval = cleanup_interval
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_tasks()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _cleanup_old_tasks(self):
        """清理超过 1 小时的已完成/失败任务"""
        with self.lock:
            now = time.time()
            to_delete = []
            for task_id, task in self.tasks.items():
                if task.get('status') in ('completed', 'error'):
                    if now - task.get('updated_at', 0) > 3600:
                        to_delete.append(task_id)
            for task_id in to_delete:
                del self.tasks[task_id]
            if to_delete:
                print(f"[CLEANUP] Removed {len(to_delete)} old tasks")
    
    def create(self, task_id, initial_status):
        with self.lock:
            # 如果任务数超限，清理最老的已完成任务
            if len(self.tasks) >= self.max_tasks:
                completed = [(k, v.get('updated_at', 0)) for k, v in self.tasks.items() 
                            if v.get('status') in ('completed', 'error')]
                if completed:
                    completed.sort(key=lambda x: x[1])
                    del self.tasks[completed[0][0]]
            
            self.tasks[task_id] = {
                **initial_status,
                'created_at': time.time(),
                'updated_at': time.time()
            }
    
    def update(self, task_id, status_dict):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(status_dict)
                self.tasks[task_id]['updated_at'] = time.time()
    
    def get(self, task_id):
        with self.lock:
            return self.tasks.get(task_id)
    
    def exists(self, task_id):
        with self.lock:
            return task_id in self.tasks

# 全局任务管理器
task_manager = TaskManager()

# ==================== 工具函数 ====================
def get_python_executable():
    """获取当前 Python 解释器的完整路径"""
    return sys.executable

def compute_file_etag(filepath):
    """计算文件 ETag（基于修改时间和大小）"""
    cached = file_etag_cache.get(filepath)
    if cached:
        return cached
    
    try:
        stat = os.stat(filepath)
        etag = hashlib.md5(f"{stat.st_mtime}-{stat.st_size}".encode()).hexdigest()
        file_etag_cache.set(filepath, etag)
        return etag
    except:
        return None

def validate_stock_code(code):
    """验证股票/期货代码格式"""
    if not code:
        return False, "代码不能为空"
    
    code = code.strip().upper()
    
    # 股票代码：6位数字
    if code.isdigit() and len(code) == 6:
        return True, code
    
    # 期货品种：2-4位字母或字母+数字组合
    if len(code) >= 1 and len(code) <= 10:
        # 允许字母、数字和常见的期货品种格式
        if code.isalnum():
            return True, code
    
    # 中文期货名称也允许
    if any('\u4e00' <= c <= '\u9fff' for c in code):
        return True, code
    
    return False, f"无效的代码格式: {code}"

def safe_json_load(filepath, default=None):
    """安全加载 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"[WARN] Failed to load JSON {filepath}: {e}")
        return default

def log_request(func):
    """请求日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        print(f"[API] {request.method} {request.path} - {elapsed:.1f}ms")
        return result
    return wrapper

# ==================== 分析任务 ====================
def run_analysis_task(code, task_id):
    """后台分析任务"""
    try:
        task_manager.update(task_id, {
            'status': 'running',
            'progress': 10,
            'message': '正在初始化分析环境...'
        })
        
        script_path = os.path.join(WORKING_DIR, 'stock_analysis_v2.py')
        python_exe = get_python_executable()
        
        print(f"[TASK] {task_id}: Starting analysis for {code}")
        print(f"[TASK] Python: {python_exe}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'
        
        task_manager.update(task_id, {
            'progress': 20,
            'message': '正在获取数据...'
        })
        
        # 运行分析脚本
        result = subprocess.run(
            [python_exe, script_path, code],
            cwd=WORKING_DIR,
            capture_output=True,
            text=True,
            timeout=3600,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # 清除报告缓存，让新报告能被发现
            report_cache.invalidate()
            
            task_manager.update(task_id, {
                'status': 'completed',
                'progress': 100,
                'message': '分析完成！',
                'code': code
            })
            print(f"[TASK] {task_id}: Completed successfully")
        else:
            error_msg = result.stderr or result.stdout or f'Exit code: {result.returncode}'
            task_manager.update(task_id, {
                'status': 'error',
                'progress': 0,
                'message': f'分析失败: {error_msg[:1500]}'
            })
            print(f"[TASK] {task_id}: Failed - {error_msg[:200]}")
            
    except subprocess.TimeoutExpired:
        task_manager.update(task_id, {
            'status': 'error',
            'progress': 0,
            'message': '分析超时（超过 1 小时）'
        })
        print(f"[TASK] {task_id}: Timeout")
    except Exception as e:
        import traceback
        error_str = f"{str(e)}\n{traceback.format_exc()}"
        task_manager.update(task_id, {
            'status': 'error',
            'progress': 0,
            'message': f'服务器错误: {str(e)[:500]}'
        })
        print(f"[TASK] {task_id}: Exception - {error_str[:500]}")

# ==================== API 路由 ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'python': sys.version,
        'platform': platform.system()
    })

@app.route('/api/analyze', methods=['POST'])
@log_request
def start_analysis():
    """启动股票分析任务"""
    try:
        data = request.get_json(silent=True) or {}
        code = data.get('code', '').strip()
        
        # 验证代码
        valid, result = validate_stock_code(code)
        if not valid:
            return jsonify({'error': result}), 400
        code = result
        
        # 生成任务 ID
        task_id = f"{code}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 初始化任务
        task_manager.create(task_id, {
            'status': 'starting',
            'progress': 0,
            'message': '任务已创建，正在启动...',
            'code': code
        })
        
        # 启动后台线程
        thread = threading.Thread(target=run_analysis_task, args=(code, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'started',
            'message': f'已启动 {code} 的分析任务'
        })
        
    except Exception as e:
        return jsonify({'error': f'启动失败: {str(e)}'}), 500

@app.route('/api/analyze/<task_id>', methods=['GET'])
def get_analysis_status(task_id):
    """获取分析任务状态"""
    task = task_manager.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    # 返回状态（不包含内部时间戳）
    return jsonify({
        'status': task.get('status'),
        'progress': task.get('progress', 0),
        'message': task.get('message', ''),
        'code': task.get('code')
    })

@app.route('/api/reports', methods=['GET'])
@log_request
def list_reports():
    """获取报告列表（带缓存）"""
    # 检查缓存
    cached = report_cache.get('all_reports')
    if cached:
        return jsonify(cached)
    
    reports = []
    
    try:
        # 1. 扫描股票分析文件夹
        stock_dirs = glob.glob(os.path.join(WORKING_DIR, "分析报告_*"))
        for d in stock_dirs:
            if not os.path.isdir(d):
                continue
                
            dirname = os.path.basename(d)
            parts = dirname.split('_')
            
            if len(parts) >= 4:
                code = parts[1]
                date_str = parts[2]
                time_str = parts[3]
                
                try:
                    dt = datetime.datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
                    
                    # 尝试获取股票名称
                    stock_name = None
                    json_path = os.path.join(d, 'analysis_data.json')
                    if os.path.exists(json_path):
                        data = safe_json_load(json_path)
                        if data:
                            stock_name = data.get('meta', {}).get('stock_name')
                    
                    reports.append({
                        "id": dirname,
                        "type": "stock",
                        "code": code,
                        "name": stock_name,
                        "date": dt.strftime("%Y-%m-%d %H:%M"),
                        "timestamp": dt.timestamp(),
                        "path": dirname
                    })
                except ValueError:
                    continue

        # 2. 扫描期货报告
        futures_files = glob.glob(os.path.join(WORKING_DIR, "期货报告_*.png"))
        for f in futures_files:
            filename = os.path.basename(f)
            parts = filename.replace('.png', '').split('_')
            
            if len(parts) >= 3:
                symbol = parts[1]
                date_str = parts[2]
                
                try:
                    dt = datetime.datetime.strptime(date_str, "%Y%m%d")
                    reports.append({
                        "id": filename,
                        "type": "futures",
                        "code": symbol,
                        "name": None,
                        "date": dt.strftime("%Y-%m-%d"),
                        "timestamp": dt.timestamp(),
                        "path": filename
                    })
                except ValueError:
                    continue
        
        # 按时间降序排序
        reports.sort(key=itemgetter('timestamp'), reverse=True)
        
        # 缓存结果
        report_cache.set('all_reports', reports)
        
    except Exception as e:
        print(f"[ERROR] list_reports: {e}")
        return jsonify({'error': '获取报告列表失败'}), 500
    
    return jsonify(reports)

@app.route('/api/reports/<report_id>', methods=['GET'])
@log_request
def get_report_details(report_id):
    """获取报告详情"""
    # 安全检查：防止路径遍历
    if '..' in report_id or report_id.startswith('/'):
        return jsonify({"error": "Invalid report ID"}), 400
    
    path = os.path.join(WORKING_DIR, report_id)
    
    if report_id.endswith(".png"):
        # 期货单文件报告
        if not os.path.exists(path):
            return jsonify({"error": "报告不存在"}), 404
        
        return jsonify({
            "id": report_id,
            "type": "futures",
            "images": [f"/api/images/{report_id}"]
        })
    else:
        # 股票文件夹报告
        if not os.path.exists(path) or not os.path.isdir(path):
            return jsonify({"error": "报告不存在"}), 404
        
        images = []
        try:
            for root, dirs, files in os.walk(path):
                for file in sorted(files):
                    if file.lower().endswith('.png'):
                        rel_path = os.path.relpath(os.path.join(root, file), WORKING_DIR)
                        images.append(f"/api/images/{rel_path}")
        except Exception as e:
            print(f"[ERROR] get_report_details: {e}")
            return jsonify({"error": "读取报告失败"}), 500
        
        return jsonify({
            "id": report_id,
            "type": "stock",
            "images": images
        })

@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """提供图片文件（带缓存控制）"""
    # 安全检查
    if '..' in filename:
        return jsonify({"error": "Invalid path"}), 400
    
    file_path = os.path.join(WORKING_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "文件不存在"}), 404
    
    # 计算 ETag
    etag = compute_file_etag(file_path)
    
    # 检查客户端缓存
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match and if_none_match == etag:
        return Response(status=304)
    
    # 返回文件
    response = send_file(file_path)
    
    # 设置缓存头
    if etag:
        response.headers['ETag'] = etag
    response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 小时缓存
    
    return response

@app.route('/api/reports/<report_id>/summary', methods=['GET'])
@log_request
def get_report_summary(report_id):
    """获取报告摘要数据（带缓存）"""
    # 安全检查
    if '..' in report_id or report_id.startswith('/'):
        return jsonify({"error": "Invalid report ID"}), 400
    
    # 检查缓存
    cache_key = f"summary_{report_id}"
    cached = summary_cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    path = os.path.join(WORKING_DIR, report_id)
    json_path = os.path.join(path, 'analysis_data.json')
    
    if os.path.exists(json_path):
        data = safe_json_load(json_path)
        if data:
            try:
                meta = data.get('meta', {})
                valuation = data.get('valuation', {})
                fundamentals = data.get('fundamentals', {})
                
                summary = {
                    'stock_name': meta.get('stock_name'),
                    'industry': meta.get('industry'),
                    'total_shares': meta.get('total_shares_yi', 0) * 1e8,
                    'analysis_date': meta.get('analysis_date'),
                    'market_cap': valuation.get('total_mv_yi', 0) * 1e8,
                    'pe_ttm': valuation.get('pe_ttm'),
                    'pb': valuation.get('pb'),
                    'dividend_yield': valuation.get('dividend_yield'),
                    'price': valuation.get('price'),
                    'roe': fundamentals.get('roe_pct'),
                    'gross_margin': fundamentals.get('gross_margin_pct'),
                    'net_margin': fundamentals.get('net_margin_pct'),
                    'debt_ratio': fundamentals.get('debt_ratio_pct'),
                    'revenue': fundamentals.get('revenue_yi'),
                    'net_profit': fundamentals.get('net_profit_yi'),
                    'full_data': data
                }
                
                # 缓存结果
                summary_cache.set(cache_key, summary)
                
                return jsonify(summary)
            except Exception as e:
                print(f"[ERROR] get_report_summary: {e}")
                return jsonify({"error": f"解析数据失败: {str(e)}"}), 500
    
    # 尝试读取文本报告
    txt_path = os.path.join(path, '分析报告.txt')
    if os.path.exists(txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"raw_text": content})
        except Exception as e:
            print(f"[ERROR] Reading text report: {e}")
    
    return jsonify({"error": "无摘要数据"}), 404

# ==================== 错误处理 ====================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "资源不存在"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "服务器内部错误"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"[UNHANDLED] {type(e).__name__}: {e}")
    return jsonify({"error": "服务器错误"}), 500

# ==================== 启动 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 BlackOil Report Server")
    print(f"   URL: http://localhost:5001")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Platform: {platform.system()}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
