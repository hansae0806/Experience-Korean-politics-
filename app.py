from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 게임 상태 저장
games = {}

class Party:
    def __init__(self, name, color="red", ideology="중도", is_ai=False):
        self.name = name
        self.popularity = random.randint(40, 60)
        self.seats = 0
        self.ideology = ideology
        self.political_power = 0
        self.color = color
        self.is_ai = is_ai  # ⬅️ AI 여부

    def to_dict(self):
        return {
            "name": self.name + (" (AI)" if self.is_ai else ""),
            "popularity": self.popularity,
            "seats": self.seats,
            "ideology": self.ideology,
            "political_power": self.political_power,
            "color": self.color
        }

    def enact_policy(self, policy_name):
        success = random.randint(0, 100) > 50
        if success:
            change = random.randint(5, 15)
            self.popularity += change
            return f"[{self.name}] {policy_name} 성공! (+{change})"
        else:
            change = random.randint(5, 15)
            self.popularity -= change
            return f"[{self.name}] {policy_name} 실패... (-{change})"

    def hold_campaign(self):
        success = random.randint(0, 100) > 50
        if success:
            change = random.randint(10, 20)
            self.popularity += change
            return f"[{self.name}] 선거 유세 성공! (+{change})"
        else:
            change = random.randint(5, 10)
            self.popularity -= change
            return f"[{self.name}] 선거 유세 실패... (-{change})"

    def special_policy(self):
        success = random.randint(0, 100) > 40
        if success:
            change = random.randint(15, 25)
            self.popularity += change
            return f"[{self.name}] 특별 정책 성공! (+{change})"
        else:
            change = random.randint(10, 20)
            self.popularity -= change
            return f"[{self.name}] 특별 정책 실패... (-{change})"

basic_ai_names = ["국민AI당", "개혁AI당", "한국AI국사당", "민주AI당"]
colors = ["red", "blue", "green", "purple", "orange", "cyan", "magenta", "yellow"]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_game')
def on_join(data):
    room = data['room']
    username = data['username']
    join_room(room)

    if room not in games:
        games[room] = {
            'players': {},
            'ai_players': [],
            'ruling_party': None,
            'current_date': datetime.date(2020, 1, 1),
            'government_budget': 5000,
            'messages': [],
            'turn': 0
        }

        # 첫 사람이 들어올 때 AI 생성
        ai_count = random.randint(2, 4)
        for i in range(ai_count):
            ai_name = random.choice(basic_ai_names) + str(random.randint(1,99))
            ai_party = Party(ai_name, color=random.choice(colors), is_ai=True)
            games[room]['ai_players'].append(ai_party)

    player_party = Party(username, color=random.choice(colors))
    games[room]['players'][request.sid] = player_party

    if games[room]['ruling_party'] is None:
        games[room]['ruling_party'] = player_party

    update_game(room)

@socketio.on('player_action')
def on_action(data):
    room = data['room']
    action = data['action']

    player = games[room]['players'].get(request.sid)
    if not player:
        return

    message = handle_action(player, action, room)
    games[room]['messages'].append(message)

    next_turn(room)

def handle_action(player, action, room):
    if action == "policy":
        return player.enact_policy("복지 정책 추진")
    elif action == "campaign":
        return player.hold_campaign()
    elif action == "special":
        if player == games[room]['ruling_party']:
            return player.special_policy()
        else:
            return "여당만 특별 정책을 수행할 수 있습니다."
    elif action == "budget_increase":
        games[room]['government_budget'] += 500
        player.popularity -= 10
        return f"[{player.name}] 세금 인상: 예산 +500, 인기 -10"
    elif action == "budget_welfare":
        games[room]['government_budget'] -= 500
        player.popularity += 10
        return f"[{player.name}] 복지 확대: 예산 -500, 인기 +10"
    return "알 수 없는 행동입니다."

def next_turn(room):
    game = games[room]
    game['turn'] += 1
    game['current_date'] += datetime.timedelta(days=60)

    # AI들도 행동
    for ai in game['ai_players']:
        ai_action = random.choice(["policy", "campaign", "special", "budget_increase", "budget_welfare"])
        message = handle_action(ai, ai_action, room)
        game['messages'].append(message)

    # 선거
    if (game['current_date'].year - 2020) % 5 == 0 and game['current_date'].month == 1:
        election(room)

    # 이벤트
    if random.random() < 0.2:
        special_event(room)

    # 몰락 체크
    fallen_check(room)

    update_game(room)

def election(room):
    game = games[room]
    all_parties = list(game['players'].values()) + game['ai_players']
    total_popularity = sum(p.popularity for p in all_parties)

    if total_popularity == 0:
        return

    max_seats = 0
    new_ruling_party = None
    for party in all_parties:
        party.seats = int((party.popularity / total_popularity) * 300)
        if party.seats > max_seats:
            max_seats = party.seats
            new_ruling_party = party

    game['ruling_party'] = new_ruling_party
    game['messages'].append(f"🗳️ 선거 완료! 새 여당은 [{new_ruling_party.name}]")

def special_event(room):
    game = games[room]
    event = random.choice(["부정부패", "외교 성과", "망언"])
    ruling = game['ruling_party']

    if event == "부정부패":
        ruling.popularity -= random.randint(5, 15)
        msg = f"🔥 {ruling.name} 부정부패 발생! 인기 하락"
    elif event == "외교 성과":
        ruling.popularity += random.randint(5, 15)
        msg = f"🌎 {ruling.name} 외교 성과! 인기 상승"
    else:
        ruling.popularity -= random.randint(10, 20)
        msg = f"💬 {ruling.name} 망언 발생! 인기 크게 하락"

    game['messages'].append(msg)

def fallen_check(room):
    game = games[room]
    for sid, player in list(game['players'].items()):
        if player.popularity <= 0:
            new_name = f"신{player.name}"
            new_party = Party(new_name, color=random.choice(colors))
            game['players'][sid] = new_party
            game['messages'].append(f"☠️ {player.name} 몰락! {new_name}로 재창당")

    for i in range(len(game['ai_players'])):
        ai = game['ai_players'][i]
        if ai.popularity <= 0:
            new_name = f"AI-{random.choice(basic_ai_names)}{random.randint(1,99)}"
            game['ai_players'][i] = Party(new_name, color=random.choice(colors), is_ai=True)
            game['messages'].append(f"☠️ {ai.name} 몰락! {new_name}로 재창당")

def update_game(room):
    game = games[room]
    socketio.emit('game_update', {
        'players': {sid: player.to_dict() for sid, player in game['players'].items()},
        'ai_players': [ai.to_dict() for ai in game['ai_players']],
        'ruling_party': game['ruling_party'].name if game['ruling_party'] else "",
        'budget': game['government_budget'],
        'date': game['current_date'].strftime("%Y-%m-%d"),
        'messages': game['messages'][-5:]
    }, room=room)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
