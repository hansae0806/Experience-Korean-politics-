const socket = io();
const room = "default_room";

function joinGame() {
    const username = document.getElementById('username').value;
    if (!username) {
        alert("정당 이름을 입력하세요!");
        return;
    }
    socket.emit('join_game', { room: room, username: username });

    document.getElementById('login').style.display = 'none';
    document.getElementById('game').style.display = 'block';
}

function sendAction(action) {
    socket.emit('player_action', { room: room, action: action });
}

socket.on('game_update', function(data) {
    document.getElementById('current_date').innerText = "📅 날짜: " + data.date;
    document.getElementById('ruling_party').innerText = "🏛️ 여당: " + data.ruling_party;
    document.getElementById('budget').innerText = "💰 정부 예산: " + data.budget + "억원";

    const playersDiv = document.getElementById('players');
    playersDiv.innerHTML = "<h3>참가자 목록</h3>";
    for (const sid in data.players) {
        const p = data.players[sid];
        playersDiv.innerHTML += `
            <div class="player-card" style="border-color: ${p.color}">
                <strong>${p.name}</strong><br/>
                인기: ${p.popularity}<br/>
                의석: ${p.seats}<br/>
                이념: ${p.ideology}<br/>
                정치력: ${p.political_power}
            </div>
        `;
    }

    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = "<h3>최근 소식</h3>";
    data.messages.forEach(msg => {
        messagesDiv.innerHTML += `<p>📰 ${msg}</p>`;
    });
});