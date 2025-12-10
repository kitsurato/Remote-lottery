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
            document.getElementById('displayQQ').innerText = data.name; // 显示名字
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
        .then(data => { updateUI(data); })
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
            
            // 使用名字生成独特颜色
            const color = getDistinctColor(slotData.user);
            
            if (!isRevealedState) {
                slotDiv.style.backgroundColor = `hsl(${color.h}, ${color.s}%, ${color.l}%)`;
                slotDiv.style.borderColor = "rgba(0,0,0,0.1)";
            } else {
                slotDiv.style.backgroundColor = `hsl(${color.h}, ${Math.min(color.s + 10, 100)}%, ${Math.max(color.l - 15, 20)}%)`;
                slotDiv.classList.add('revealed');
                slotDiv.querySelector('.slot-prize').innerText = slotData.prize;
            }
        } else if (isRevealedState && !slotData.taken) {
             slotDiv.classList.add('revealed');
             slotDiv.querySelector('.slot-prize').innerText = slotData.prize;
             slotDiv.style.backgroundColor = "#78909c"; 
        } else {
            slotDiv.className = 'slot'; 
            slotDiv.style.backgroundColor = ""; 
            slotDiv.querySelector('.slot-user').innerText = "";
            slotDiv.querySelector('.slot-prize').innerText = "???";
        }
    }
}

function getDistinctColor(str) {
    if (!str) return { h: 0, s: 0, l: 50 };
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const goldenAngle = 137.508; 
    const hue = Math.abs((hash * goldenAngle) % 360);
    const saturation = 65 + (Math.abs(hash) % 20); 
    const lightness = 40 + (Math.abs(hash) % 10);
    return { h: hue, s: saturation, l: lightness };
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
    .then(data => { alert(data.message); if (data.success) location.reload(); });
}

function earlyReveal() {
    const pwd = document.getElementById('adminPwd').value;
    if (!pwd) { alert("请输入管理员密码！"); return; }
    if(!confirm("⚠️ 确定要在人数未满的情况下【提前开奖】吗？")) return;

    fetch('/api/admin/early_reveal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd })
    })
    .then(res => res.json())
    .then(data => { alert(data.message); if (data.success) fetchStatus(); });
}

window.onload = initGrid;