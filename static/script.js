let currentQQ = "";
let isRevealedState = false;

function initGrid() {
    const grid = document.getElementById('lotteryGrid');
    if (!grid) return;
    
    grid.innerHTML = ""; 
    for (let i = 0; i < 30; i++) {
        let slot = document.createElement('div');
        slot.className = 'slot';
        slot.id = 'slot-' + i;
        slot.onclick = () => pickSlot(i);
        slot.innerHTML = `
            <span class="slot-number">${i + 1}</span>
            <span class="slot-user"></span>
            <div class="slot-prize">???</div>
        `;
        grid.appendChild(slot);
    }
    startPolling();
}

function login() {
    const input = document.getElementById('qqNumber');
    const qq = input.value.trim();
    if (qq === "") { alert("请输入QQ号！"); return; }

    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qq: qq })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            currentQQ = qq;
            document.getElementById('inputArea').classList.add('hidden');
            document.getElementById('userInfo').classList.remove('hidden');
            document.getElementById('displayQQ').innerText = currentQQ;
            document.getElementById('remainCount').innerText = data.remaining;
            alert(data.message);
        } else {
            alert(data.message);
        }
    });
}

function pickSlot(slotId) {
    if (currentQQ === "") {
        alert("请先输入QQ号并点击验证！");
        return;
    }
    if (isRevealedState) return;

    fetch('/api/pick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_id: slotId, qq: currentQQ })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert(data.message);
        } else {
            document.getElementById('remainCount').innerText = data.remaining;
            fetchStatus(); 
        }
    });
}

function startPolling() {
    fetchStatus();
    setInterval(fetchStatus, 1000); 
}

function fetchStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateUI(data);
        })
        .catch(err => console.error(err));
}

function updateUI(data) {
    document.getElementById('progress').innerText = data.taken_count;
    isRevealedState = data.is_revealed;

    const statusBtn = document.getElementById('statusBtn');
    if (isRevealedState) {
        statusBtn.innerText = "🎉 已揭晓结果 🎉";
        statusBtn.className = "status-tag revealed";
    } else {
        statusBtn.innerText = "抽选进行中...";
        statusBtn.className = "status-tag picking";
    }

    for (let i = 0; i < 30; i++) {
        const slotData = data.slots[i.toString()];
        const slotDiv = document.getElementById('slot-' + i);
        
        if (!slotDiv || !slotData) continue;

        if (slotData.taken) {
            slotDiv.classList.add('taken');
            
            slotDiv.querySelector('.slot-user').innerText = slotData.user;
            
            const hue = getHueFromStr(slotData.user);
            
            if (!isRevealedState) {
                // 状态A：正常选中
                slotDiv.style.backgroundColor = `hsl(${hue}, 70%, 45%)`;
                slotDiv.style.borderColor = "rgba(0,0,0,0.1)";
            } else {
                // 状态B：已揭晓
                slotDiv.style.backgroundColor = `hsl(${hue}, 85%, 30%)`;
                slotDiv.classList.add('revealed');
                slotDiv.querySelector('.slot-prize').innerText = slotData.prize;
            }

        } else {
            // 重置/未被选状态
            slotDiv.className = 'slot'; 
            slotDiv.style.backgroundColor = ""; 
            slotDiv.querySelector('.slot-user').innerText = "";
            slotDiv.querySelector('.slot-prize').innerText = "???";
        }
    }
}

function getHueFromStr(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash % 360);
}

function resetSystem() {
    const pwd = document.getElementById('adminPwd').value;
    if (!pwd) { alert("请输入管理员密码！"); return; }
    
    if(!confirm("⚠️ 警告：这将清除所有记录！确定要重置吗？")) return;

    fetch('/api/admin/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.success) location.reload();
    });
}


window.onload = initGrid;
