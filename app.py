import json
import os
import random
import time
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ================= 配置区域 =================

ADMIN_PASSWORD = "1145141919810"
DATA_FILE = "lottery_data.json"

ADMIN_SECURITY_IP = {} 

# --- 用户名单 (QQ -> 名字 & 次数) ---
ALLOWED_USERS_CONFIG = {
    "11111": {"name": "小A", "count": 10},
    "22222": {"name": "小B", "count": 10},
    "33333": {"name": "小C", "count": 10},

}

# --- 奖品列表 ---
PRIZE_POOL = [
    "曼加利察羊毛猪", "伊比利亚黑蹄猪", "金华两头乌", "匈牙利卷毛猪", "荣昌猪",
    "太湖梅山猪", "宁乡花猪", "东北民猪", "藏香猪", "成华猪",
    "伯克希尔猪", "杜洛克猪", "汉普夏猪", "丹麦长白猪", "约克夏大白猪",
    "皮特兰猪", "波中猪", "塔姆沃思猪", "巴马香猪", "越南大肚猪",
    "酷尼酷尼猪", "哥廷根迷你猪", "尤卡坦缺齿猪", "奥萨巴岛猪", "非洲疣猪",
    "红河猪", "鹿豚", "西貒", "巨林猪", "普通野猪"
]

game_state = {}



def get_client_ip():
    """获取用户真实IP"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def check_ip_lockout(ip):
    """检查IP是否被锁定"""
    if ip not in ADMIN_SECURITY_IP:
        return None 
    
    record = ADMIN_SECURITY_IP[ip]
    
    if time.time() < record['lockout_until']:
        remaining = int(record['lockout_until'] - time.time())
        minutes = remaining // 60
        seconds = remaining % 60
        return f'⛔ IP已锁定！请等待 {minutes}分{seconds}秒'
    
    return None 

def record_auth_failure(ip):
    """记录失败次数"""
    if ip not in ADMIN_SECURITY_IP:
        ADMIN_SECURITY_IP[ip] = {'attempts': 0, 'lockout_until': 0}
    
    record = ADMIN_SECURITY_IP[ip]
    
    if time.time() > record['lockout_until'] and record['lockout_until'] != 0:
        record['attempts'] = 0
        record['lockout_until'] = 0

    record['attempts'] += 1
    
    if record['attempts'] >= 3:
        record['lockout_until'] = time.time() + 300 
        record['attempts'] = 0 
        return True 
    
    return False 

def reset_auth_success(ip):
    """登录成功，清除不良记录"""
    if ip in ADMIN_SECURITY_IP:
        del ADMIN_SECURITY_IP[ip]


def init_new_game():
    prizes = PRIZE_POOL[:30]
    random.shuffle(prizes)
    
    initial_counts = {}
    for qq, info in ALLOWED_USERS_CONFIG.items():
        initial_counts[qq] = info['count']

    new_state = {
        'slots': {},
        'is_revealed': False,
        'taken_count': 0,
        'user_remaining': initial_counts 
    }
    
    for i in range(30):
        new_state['slots'][str(i)] = {
            'id': i, 'taken': False, 'user': '', 'prize': prizes[i]
        }
    return new_state

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(game_state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存失败: {e}")

def load_data():
    global game_state
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                game_state = json.load(f)
        except:
            game_state = init_new_game()
            save_data()
    else:
        game_state = init_new_game()
        save_data()

load_data()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    qq = str(data.get('qq', '')).strip()
    
    if qq not in ALLOWED_USERS_CONFIG:
        return jsonify({'success': False, 'message': '❌ 该QQ号不在名单中！'})
    
    user_counts = game_state.get('user_remaining', {})
    remaining = user_counts.get(qq, 0)
    
    if remaining <= 0:
        return jsonify({'success': False, 'message': '⚠️ 您的抽奖次数已用完！'})
    
    nickname = ALLOWED_USERS_CONFIG[qq]['name']
    return jsonify({
        'success': True, 'remaining': remaining, 'name': nickname,
        'message': f'欢迎，{nickname}！您还有 {remaining} 次机会'
    })

@app.route('/api/status')
def get_status():
    if game_state['taken_count'] >= 30 and not game_state['is_revealed']:
        game_state['is_revealed'] = True
        save_data()
        
    safe_slots = {}
    for k, v in game_state['slots'].items():
        safe_slots[k] = v.copy()
        if not game_state['is_revealed']:
             safe_slots[k]['prize'] = "???"

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
    
    if qq not in ALLOWED_USERS_CONFIG:
        return jsonify({'success': False, 'message': '非法用户'})
    
    if game_state['user_remaining'].get(qq, 0) <= 0:
        return jsonify({'success': False, 'message': '您的次数已用完'})

    if game_state['slots'][slot_id]['taken']:
        return jsonify({'success': False, 'message': '手慢了，位置被抢了！'})

    nickname = ALLOWED_USERS_CONFIG[qq]['name']
    
    game_state['user_remaining'][qq] -= 1
    game_state['slots'][slot_id]['taken'] = True
    game_state['slots'][slot_id]['user'] = nickname
    game_state['taken_count'] += 1
    
    save_data()
    return jsonify({'success': True, 'remaining': game_state['user_remaining'][qq]})


@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    client_ip = get_client_ip()
    
    lock_msg = check_ip_lockout(client_ip)
    if lock_msg:
        return jsonify({'success': False, 'message': lock_msg})

    data = request.json
    input_pwd = data.get('password', '')

    if input_pwd != ADMIN_PASSWORD:
        just_locked = record_auth_failure(client_ip)
        if just_locked:
            return jsonify({'success': False, 'message': '⛔ 连续错误3次！您已被锁定 5 分钟！'})
        
        attempts = ADMIN_SECURITY_IP[client_ip]['attempts']
        return jsonify({'success': False, 'message': f'密码错误！再错 {3 - attempts} 次将被锁定。'})
    
    reset_auth_success(client_ip)
    global game_state
    game_state = init_new_game()
    save_data()
    return jsonify({'success': True, 'message': '✅ 系统已重置！'})

@app.route('/api/admin/early_reveal', methods=['POST'])
def admin_early_reveal():
    client_ip = get_client_ip()
    
    lock_msg = check_ip_lockout(client_ip)
    if lock_msg:
        return jsonify({'success': False, 'message': lock_msg})

    data = request.json
    input_pwd = data.get('password', '')
    
    if input_pwd != ADMIN_PASSWORD:
        just_locked = record_auth_failure(client_ip)
        if just_locked:
            return jsonify({'success': False, 'message': '⛔ 连续错误3次！您已被锁定 5 分钟！'})
            
        attempts = ADMIN_SECURITY_IP[client_ip]['attempts']
        return jsonify({'success': False, 'message': f'密码错误！再错 {3 - attempts} 次将被锁定。'})
    
    reset_auth_success(client_ip)
    
    if game_state['is_revealed']:
        return jsonify({'success': False, 'message': '已经是开奖状态了！'})

    game_state['is_revealed'] = True
    save_data()
    return jsonify({'success': True, 'message': '⚡ 已执行提前开奖！'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)