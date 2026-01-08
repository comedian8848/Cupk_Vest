from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import glob
from operator import itemgetter
import datetime
import json
import subprocess
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

# Track running analysis tasks
analysis_status = {}

def run_analysis_task(code, task_id):
    """Background task to run stock analysis"""
    try:
        analysis_status[task_id] = {'status': 'running', 'progress': 0, 'message': 'Starting analysis...'}
        
        script_path = os.path.join(WORKING_DIR, 'stock_analysis_v2.py')
        result = subprocess.run(
            ['python', script_path, code],
            cwd=WORKING_DIR,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            analysis_status[task_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Analysis completed successfully',
                'code': code
            }
        else:
            analysis_status[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Analysis failed: {result.stderr[:200]}'
            }
    except subprocess.TimeoutExpired:
        analysis_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': 'Analysis timeout (>1 hour)'
        }
    except Exception as e:
        analysis_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Start a new stock analysis"""
    data = request.json
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'Stock code is required'}), 400
    
    # Generate task ID
    task_id = f"{code}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Start background task
    thread = threading.Thread(target=run_analysis_task, args=(code, task_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'started',
        'message': f'Analysis started for {code}'
    })

@app.route('/api/analyze/<task_id>', methods=['GET'])
def get_analysis_status(task_id):
    """Get status of an analysis task"""
    if task_id not in analysis_status:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(analysis_status[task_id])

@app.route('/api/reports', methods=['GET'])
def list_reports():
    reports = []
    
    # 1. Scan for Stock Analysis folders
    # Pattern: 分析报告_{code}_{datetime}
    stock_dirs = glob.glob(os.path.join(WORKING_DIR, "分析报告_*"))
    for d in stock_dirs:
        if os.path.isdir(d):
            dirname = os.path.basename(d)
            # Try to parse
            parts = dirname.split('_')
            # Format: 分析报告_600519_20260107_1648
            if len(parts) >= 4:
                code = parts[1]
                date_str = parts[2]
                time_str = parts[3]
                try:
                    dt = datetime.datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
                    
                    # Try to get stock name from analysis_data.json
                    stock_name = None
                    json_path = os.path.join(d, 'analysis_data.json')
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                stock_name = data.get('meta', {}).get('stock_name')
                        except:
                            pass
                    
                    reports.append({
                        "id": dirname,
                        "type": "stock",
                        "code": code,
                        "name": stock_name,  # Add stock name
                        "date": dt.strftime("%Y-%m-%d %H:%M"),
                        "timestamp": dt.timestamp(),
                        "path": dirname
                    })
                except:
                    pass

    # 2. Scan for Futures Analysis files
    # Pattern: 期货报告_{symbol}_{date}.png
    futures_files = glob.glob(os.path.join(WORKING_DIR, "期货报告_*.png"))
    for f in futures_files:
        filename = os.path.basename(f)
        # Format: 期货报告_RB_20260108.png
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
            except:
                pass
                
    # Sort by date desc
    reports.sort(key=itemgetter('timestamp'), reverse=True)
    return jsonify(reports)

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report_details(report_id):
    # Determine type by ID
    path = os.path.join(WORKING_DIR, report_id)
    
    if report_id.endswith(".png"):
        # Futures single file report
        if not os.path.exists(path):
            return jsonify({"error": "Report not found"}), 404
            
        return jsonify({
            "id": report_id,
            "type": "futures",
            "images": [f"/api/images/{report_id}"]
        })
    else:
        # Stock folder report
        if not os.path.exists(path) or not os.path.isdir(path):
            return jsonify({"error": "Report not found"}), 404
            
        # List all png images in the folder recursively
        images = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.png'):
                    # Create a relative path accessible via API
                    # We need to construct a way to serve this. 
                    # Simpler is to use the direct filename if flat, or construct a special path
                    rel_path = os.path.relpath(os.path.join(root, file), WORKING_DIR)
                    images.append(f"/api/images/{rel_path}")
        
        # Sort images to ensure order (optional)
        images.sort()
        return jsonify({
            "id": report_id,
            "type": "stock",
            "images": images
        })

@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    file_path = os.path.join(WORKING_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/reports/<report_id>/summary', methods=['GET'])
def get_report_summary(report_id):
    path = os.path.join(WORKING_DIR, report_id)
    json_path = os.path.join(path, 'analysis_data.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract and map fields for frontend
            meta = data.get('meta', {})
            valuation = data.get('valuation', {})
            fundamentals = data.get('fundamentals', {})
            
            summary = {
                # Meta info
                'stock_name': meta.get('stock_name'),
                'industry': meta.get('industry'),
                'total_shares': meta.get('total_shares_yi', 0) * 1e8,  # Convert to actual shares
                'analysis_date': meta.get('analysis_date'),
                
                # Valuation
                'market_cap': valuation.get('total_mv_yi', 0) * 1e8,  # Convert to actual value
                'pe_ttm': valuation.get('pe_ttm'),
                'pb': valuation.get('pb'),
                'dividend_yield': valuation.get('dividend_yield'),
                'price': valuation.get('price'),
                
                # Fundamentals (convert percentages)
                'roe': fundamentals.get('roe_pct'),
                'gross_margin': fundamentals.get('gross_margin_pct'),
                'net_margin': fundamentals.get('net_margin_pct'),
                'debt_ratio': fundamentals.get('debt_ratio_pct'),
                'revenue': fundamentals.get('revenue_yi'),
                'net_profit': fundamentals.get('net_profit_yi'),
                
                # Full data for reference
                'full_data': data
            }
            
            return jsonify(summary)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Try parsing text report if json missing
    txt_path = os.path.join(path, '分析报告.txt')
    if os.path.exists(txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"raw_text": content})
        except:
            pass

    return jsonify({"error": "No summary data found"}), 404

if __name__ == '__main__':
    print("🚀 Report Server running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
