import json
import os
import random
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ================= 配置区域 =================

# 管理员密码
ADMIN_PASSWORD = "admin888"

# 数据存储文件
DATA_FILE = "lottery_data.json"

# 用户名单及次数配置
ALLOWED_USERS_CONFIG = {
    "123456": 1,
    "888888": 5,
    "10001": 2,
    "admin": 30
}

# 奖品池
PRIZE_POOL = [
    "小代哥的茶叶",
    "仁之剑", "义之剑",
    "自刎归天", "自刎归天", "自刎归天",
    "牛魔", "牛魔", "牛魔", "牛魔",
    "猪", "猪", "猪", "猪", "猪",
    "猪", "猪", "猪", "猪", "猪",
    "猪", "猪", "猪", "猪", "猪",
    "猪", "猪", "猪", "猪", "猪"
]

# 全局变量
game_state = {}

# ================= 核心逻辑 =================

def init_new_game():
    """初始化新游戏"""
    print("正在初始化新游戏...")
    prizes = PRIZE_POOL[:30]
    random.shuffle(prizes)
    
    new_state = {
        'slots': {},
        'is_revealed': False,
        'taken_count': 0,
        'user_remaining': ALLOWED_USERS_CONFIG.copy()
    }
    
    for i in range(30):
        # 注意：JSON的key必须是字符串
        new_state['slots'][str(i)] = {
            'id': i,
            'taken': False,
            'user': '',
            'prize': prizes[i]
        }
    return new_state

def save_data():
    """保存数据到硬盘"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(game_state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存失败: {e}")

def load_data():
    """加载数据"""
    global game_state
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                game_state = json.load(f)
            print("成功加载存档！")
        except:
            print("存档损坏，重新初始化...")
            game_state = init_new_game()
            save_data()
    else:
        game_state = init_new_game()
        save_data()

# 启动时加载
load_data()

# ================= 路由接口 =================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    qq = str(data.get('qq', '')).strip()
    
    user_counts = game_state.get('user_remaining', {})
    
    if qq not in user_counts:
        return jsonify({'success': False, 'message': '❌ 该QQ号不在邀请名单中！'})
    
    remaining = user_counts[qq]
    if remaining <= 0:
        return jsonify({'success': False, 'message': '⚠️ 您的抽奖次数已用完！'})
        
    return jsonify({
        'success': True, 
        'remaining': remaining,
        'message': f'验证成功！您还有 {remaining} 次机会'
    })

@app.route('/api/status')
def get_status():
    # 如果全部抽完，自动触发揭晓
    if game_state['taken_count'] >= 30 and not game_state['is_revealed']:
        game_state['is_revealed'] = True
        save_data()
        
    safe_slots = {}
    for k, v in game_state['slots'].items():
        safe_slots[k] = v.copy()
        if not game_state['is_revealed']:
             safe_slots[k]['prize'] = "???" # 隐藏奖品

    return jsonify({
        'slots': safe_slots,
        'is_revealed': game_state['is_revealed'],
        'taken_count': game_state['taken_count']
    })

@app.route('/api/pick', methods=['POST'])
def pick_slot():
    if game_state['is_revealed']:
         return jsonify({'success': False, 'message': '抽奖已结束'})

    data = request.json
    slot_id = str(data.get('slot_id'))
    qq = str(data.get('qq', '')).strip()
    
    user_counts = game_state['user_remaining']

    if qq not in user_counts:
        return jsonify({'success': False, 'message': '非法用户'})
    
    if user_counts[qq] <= 0:
        return jsonify({'success': False, 'message': '您的次数已用完'})

    if game_state['slots'][slot_id]['taken']:
        return jsonify({'success': False, 'message': '手慢了，位置被抢了！'})

    # 更新状态
    game_state['user_remaining'][qq] -= 1
    game_state['slots'][slot_id]['taken'] = True
    game_state['slots'][slot_id]['user'] = f"QQ:{qq}"
    game_state['taken_count'] += 1
    
    save_data() # 立即保存

    return jsonify({
        'success': True, 
        'remaining': game_state['user_remaining'][qq]
    })

@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    data = request.json
    password = data.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': '密码错误！'})
    
    global game_state
    game_state = init_new_game()
    save_data()
    
    return jsonify({'success': True, 'message': '系统已重置，所有数据已清除！'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
