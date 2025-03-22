from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import time
import json

app = Flask(__name__)
CORS(app)

# Load high scores from file or create new
try:
    with open('high_scores.json', 'r') as f:
        HIGH_SCORES = json.load(f)
except:
    HIGH_SCORES = {'scores': []}

# Game state
game_state = {
    'player': {
        'x': 15,
        'y': 35,
        'lures': [],  # [{'x': x, 'y': y, 'type': 'fly', 'power': power}]
        'current_lure': 'fly',
        'power_ups': [],
        'casting_speed': 1.0,
        'lure_power': 1.0
    },
    'fish': [],  # [{'x': x, 'y': y, 'type': 'bass', 'speed': speed, 'health': health}]
    'boss': None,  # {'x': x, 'y': y, 'health': health, 'pattern': pattern}
    'score': 0,
    'game_over': False,
    'level': 1,
    'boss_incoming': False
}

GRID_WIDTH = 40
GRID_HEIGHT = 40

LURE_TYPES = {
    'fly': {'damage': 1, 'speed': 2, 'cooldown': 0.3},
    'spinner': {'damage': 2, 'speed': 1.5, 'cooldown': 0.5},
    'popper': {'damage': 3, 'speed': 1, 'cooldown': 0.8},
    'frog': {'damage': 4, 'speed': 0.8, 'cooldown': 1}
}

FISH_TYPES = {
    'bluegill': {'points': 10, 'speed': 1, 'chance': 0.4, 'health': 1},
    'bass': {'points': 20, 'speed': 2, 'chance': 0.3, 'health': 2},
    'pike': {'points': 30, 'speed': 3, 'chance': 0.2, 'health': 3},
    'muskie': {'points': 50, 'speed': 4, 'chance': 0.1, 'health': 4}
}

POWER_UPS = {
    'rapid_cast': {'duration': 10, 'effect': 'casting_speed', 'multiplier': 2},
    'power_lure': {'duration': 10, 'effect': 'lure_power', 'multiplier': 2},
    'multi_lure': {'duration': 8, 'effect': 'spread_shot', 'multiplier': 3}
}

BOSS_PATTERNS = {
    'largemouth': {
        'health': 50,
        'points': 500,
        'attack_patterns': ['zigzag', 'charge', 'spawn_minions']
    },
    'sturgeon': {
        'health': 75,
        'points': 750,
        'attack_patterns': ['sweep', 'dive', 'shield']
    }
}

def save_high_score(score):
    HIGH_SCORES['scores'].append({
        'score': score,
        'date': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    HIGH_SCORES['scores'].sort(key=lambda x: x['score'], reverse=True)
    HIGH_SCORES['scores'] = HIGH_SCORES['scores'][:10]  # Keep top 10
    
    with open('high_scores.json', 'w') as f:
        json.dump(HIGH_SCORES, f)

def reset_game():
    game_state['player']['x'] = GRID_WIDTH // 2
    game_state['player']['lures'] = []
    game_state['player']['current_lure'] = 'fly'
    game_state['player']['power_ups'] = []
    game_state['player']['casting_speed'] = 1.0
    game_state['player']['lure_power'] = 1.0
    game_state['fish'] = []
    game_state['boss'] = None
    game_state['score'] = 0
    game_state['game_over'] = False
    game_state['level'] = 1
    game_state['boss_incoming'] = False

def spawn_power_up():
    if random.random() < 0.05:  # 5% chance
        power_up_type = random.choice(list(POWER_UPS.keys()))
        return {
            'type': power_up_type,
            'x': random.randint(0, GRID_WIDTH - 1),
            'y': 0
        }
    return None

def spawn_boss():
    if game_state['score'] > 0 and game_state['score'] % 1000 == 0:
        boss_type = random.choice(list(BOSS_PATTERNS.keys()))
        game_state['boss'] = {
            'type': boss_type,
            'x': GRID_WIDTH // 2,
            'y': 5,
            'health': BOSS_PATTERNS[boss_type]['health'],
            'pattern': 'zigzag',
            'pattern_timer': 0
        }
        game_state['boss_incoming'] = True

def spawn_fish():
    if len(game_state['fish']) < 5 + game_state['level']:
        rand = random.random()
        cumulative_chance = 0
        fish_type = 'bluegill'
        
        for fish, stats in FISH_TYPES.items():
            cumulative_chance += stats['chance']
            if rand <= cumulative_chance:
                fish_type = fish
                break
        
        new_fish = {
            'x': random.randint(0, GRID_WIDTH - 1),
            'y': 0,
            'type': fish_type,
            'speed': FISH_TYPES[fish_type]['speed'],
            'health': FISH_TYPES[fish_type]['health'],
            'animation_frame': 0
        }
        game_state['fish'].append(new_fish)
# ... [Previous code remains the same] ...

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/high-scores')
def get_high_scores():
    return jsonify(HIGH_SCORES)

@app.route('/game-state')
def get_game_state():
    return jsonify(game_state)

@app.route('/change-lure', methods=['POST'])
def change_lure():
    data = request.get_json()
    new_lure = data.get('lure')
    if new_lure in LURE_TYPES:
        game_state['player']['current_lure'] = new_lure
    return jsonify(game_state)

@app.route('/move', methods=['POST'])
def move():
    if game_state['game_over']:
        return jsonify(game_state)

    data = request.get_json()
    direction = data.get('direction')
    shoot = data.get('shoot')
    
    # Move player boat (adjusted movement speed)
    if direction == 'LEFT' and game_state['player']['x'] > 0:
        game_state['player']['x'] -= 1
    elif direction == 'RIGHT' and game_state['player']['x'] < GRID_WIDTH - 2:  # Adjusted for boat width
        game_state['player']['x'] += 1

    # Process automatic game updates only if no direction is specified
    if direction is None:
        # Update power-ups
        for power_up in game_state['player']['power_ups'][:]:
            power_up['duration'] -= 0.1
            if power_up['duration'] <= 0:
                game_state['player']['power_ups'].remove(power_up)
                if power_up['effect'] == 'casting_speed':
                    game_state['player']['casting_speed'] = 1.0
                elif power_up['effect'] == 'lure_power':
                    game_state['player']['lure_power'] = 1.0

        # Update lure positions
        for lure in game_state['player']['lures'][:]:
            lure['y'] -= lure['speed']
            if lure['y'] < 0:
                game_state['player']['lures'].remove(lure)

        # Spawn new fish and power-ups
        if random.random() < 0.1:
            spawn_fish()
        
        power_up = spawn_power_up()
        if power_up:
            game_state['fish'].append(power_up)

        # Check for boss spawn
        spawn_boss()

        # Update fish and boss positions
        update_fish_positions()
        if game_state['boss']:
            update_boss_position()

    return jsonify(game_state)

def update_fish_positions():
    for fish in game_state['fish'][:]:
        # Update animation frame
        fish['animation_frame'] = (fish['animation_frame'] + 1) % 8
        
        # Move fish
        fish['y'] += fish['speed'] * 0.2
        
        # Check collision with lures
        for lure in game_state['player']['lures'][:]:
            if (abs(fish['x'] - lure['x']) < 1 and 
                abs(fish['y'] - lure['y']) < 1):
                
                if 'type' in fish and fish['type'] in FISH_TYPES:
                    # Regular fish hit
                    fish['health'] -= lure['damage']
                    if fish['health'] <= 0:
                        game_state['score'] += FISH_TYPES[fish['type']]['points']
                        game_state['fish'].remove(fish)
                    game_state['player']['lures'].remove(lure)
                elif 'type' in fish and fish['type'] in POWER_UPS:
                    # Power-up collected
                    power_up = POWER_UPS[fish['type']]
                    game_state['player']['power_ups'].append({
                        'type': fish['type'],
                        'duration': power_up['duration'],
                        'effect': power_up['effect']
                    })
                    if power_up['effect'] == 'casting_speed':
                        game_state['player']['casting_speed'] = power_up['multiplier']
                    elif power_up['effect'] == 'lure_power':
                        game_state['player']['lure_power'] = power_up['multiplier']
                    game_state['fish'].remove(fish)
                    game_state['player']['lures'].remove(lure)
                break
        
        # Remove fish if it goes off screen
        if fish['y'] >= GRID_HEIGHT:
            if 'type' in fish and fish['type'] in FISH_TYPES:
                game_state['game_over'] = True
            game_state['fish'].remove(fish)

def update_boss_position():
    boss = game_state['boss']
    if not boss:
        return

    # Update boss pattern
    boss['pattern_timer'] += 1
    if boss['pattern_timer'] >= 100:
        boss['pattern'] = random.choice(BOSS_PATTERNS[boss['type']]['attack_patterns'])
        boss['pattern_timer'] = 0

    # Execute pattern
    if boss['pattern'] == 'zigzag':
        boss['x'] += math.sin(boss['pattern_timer'] * 0.1) * 0.5
    elif boss['pattern'] == 'charge':
        if boss['pattern_timer'] < 50:
            boss['y'] += 0.1
        else:
            boss['y'] -= 0.1
    elif boss['pattern'] == 'spawn_minions':
        if boss['pattern_timer'] % 25 == 0:
            spawn_fish()

    # Check collision with lures
    for lure in game_state['player']['lures'][:]:
        if (abs(boss['x'] - lure['x']) < 2 and 
            abs(boss['y'] - lure['y']) < 2):
            boss['health'] -= lure['damage']
            game_state['player']['lures'].remove(lure)
            
            if boss['health'] <= 0:
                game_state['score'] += BOSS_PATTERNS[boss['type']]['points']
                game_state['boss'] = None
                game_state['level'] += 1
                break

@app.route('/reset', methods=['POST'])
def reset():
    if game_state['game_over']:
        save_high_score(game_state['score'])
    reset_game()
    return jsonify(game_state)

if __name__ == '__main__':
    reset_game()
    app.run(host='0.0.0.0', port=5000)