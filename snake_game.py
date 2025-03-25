from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import time
import json
import math

app = Flask(__name__)
CORS(app)

# Load high scores from file or create new
try:
    with open('high_scores.json', 'r') as f:
        HIGH_SCORES = json.load(f)
except:
    HIGH_SCORES = {'scores': []}

# Map definition (1 = wall, 0 = empty)
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# Game state
game_state = {
    'player': {
        'x': 2.0,
        'y': 2.0,
        'angle': 0.0,
        'lures': 10,
        'lures_used': 0,
        'lure_power': 1.0,
        'casting_speed': 1.0,
        'power_ups': [],
        'current_lure': 'fly',
        'power_ups_used': []
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
    'bluegill': {'speed': 0.03, 'health': 1, 'damage': 1, 'points': 10},
    'bass': {'speed': 0.02, 'health': 2, 'damage': 2, 'points': 20},
    'pike': {'speed': 0.04, 'health': 1, 'damage': 3, 'points': 15},
    'muskie': {'speed': 0.01, 'health': 4, 'damage': 5, 'points': 30}
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
    game_state['player']['x'] = 2.0
    game_state['player']['y'] = 2.0
    game_state['player']['angle'] = 0.0
    game_state['player']['lures'] = 10
    game_state['player']['lures_used'] = 0
    game_state['player']['lure_power'] = 1.0
    game_state['player']['casting_speed'] = 1.0
    game_state['player']['power_ups'] = []
    game_state['player']['current_lure'] = 'fly'
    game_state['player']['power_ups_used'] = []
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

class Game:
    def __init__(self):
        self.reset()
    
    def reset(self):
        # Initialize game state properties
        self.player = {
            'x': 2.0,
            'y': 2.0,
            'angle': 0.0,
            'lures': float('inf'),  # Unlimited lures
            'lure_power': 1.0,      # Base lure power
            'lure_speed': 1.0,      # Base lure speed
            'power_ups': []         # Active power-ups
        }
        self.fish = []
        self.score = 0
        self.game_over = False
        self.power_ups = []  # Power-ups in the level
        
        # Spawn initial fish
        self.spawn_fish(3)
        
        # Spawn initial power-ups
        self.spawn_power_ups(5)
    
    def spawn_fish(self, count):
        # Limit the number of fish that can exist at once
        if len(self.fish) >= 3:  # Reduced max fish count to 3
            return
        
        for _ in range(count):
            # Find a valid position (not in a wall and not too close to player)
            while True:
                # Place fish randomly throughout the map
                x = random.uniform(1, len(MAP[0]) - 2)
                y = random.uniform(1, len(MAP) - 2)
                
                # Check if position is in a wall
                if MAP[int(y)][int(x)] != 0:
                    continue
                
                # Make sure fish aren't too close to the player
                dist = math.sqrt((x - self.player['x'])**2 + (y - self.player['y'])**2)
                if dist < 8:  # Increased minimum distance even more
                    continue
                
                break
            
            fish_type = random.choice(list(FISH_TYPES.keys()))
            self.fish.append({
                'x': x,
                'y': y,
                'type': fish_type,
                'health': FISH_TYPES[fish_type]['health'],
                'direction': random.uniform(0, 2 * math.pi),
                'speed': FISH_TYPES[fish_type]['speed'] * random.uniform(0.8, 1.2),
                'state': 'patrol',
                'state_timer': random.randint(50, 150),
                'spawn_time': time.time()  # Track when fish was spawned
            })
    
    def move_player(self, direction, amount=1):
        move_speed = 0.1
        rotation_speed = 0.05
        
        if direction == 'FORWARD':
            new_x = self.player['x'] + math.cos(self.player['angle']) * move_speed * amount
            new_y = self.player['y'] + math.sin(self.player['angle']) * move_speed * amount
            if self.is_valid_position(new_x, new_y):
                self.player['x'] = new_x
                self.player['y'] = new_y
        
        elif direction == 'BACKWARD':
            new_x = self.player['x'] - math.cos(self.player['angle']) * move_speed * amount
            new_y = self.player['y'] - math.sin(self.player['angle']) * move_speed * amount
            if self.is_valid_position(new_x, new_y):
                self.player['x'] = new_x
                self.player['y'] = new_y
        
        elif direction == 'LEFT':
            self.player['angle'] -= rotation_speed * amount
        
        elif direction == 'RIGHT':
            self.player['angle'] += rotation_speed * amount
        
        elif direction == 'LOOK':
            self.player['angle'] += rotation_speed * amount
    
    def is_valid_position(self, x, y):
        # Check if position is within map bounds
        if x < 0 or y < 0 or x >= len(MAP[0]) or y >= len(MAP):
            return False
        
        # Check if position is in a wall
        if MAP[int(y)][int(x)] != 0:
            return False
        
        return True
    
    def shoot(self):
        if self.player['lures'] <= 0:
            return False
        
        self.player['lures'] -= 1
        
        # Create a new bullet with current power-up effects
        bullet = {
            'x': self.player['x'],
            'y': self.player['y'],
            'angle': self.player['angle'],
            'speed': 0.2 * self.player['lure_speed'],
            'damage': 1 * self.player['lure_power'],
            'distance': 0,
            'max_distance': 10,
            'active': True
        }
        
        # Add bullet to player
        if 'bullets' not in self.player:
            self.player['bullets'] = []
        
        self.player['bullets'].append(bullet)
        
        # If spread shot is active, add additional bullets
        has_spread = any(pu['effect'] == 'spread_shot' for pu in self.player['power_ups'])
        if has_spread:
            # Add bullets at angles to the left and right
            for angle_offset in [-0.2, 0.2]:
                spread_bullet = {
                    'x': self.player['x'],
                    'y': self.player['y'],
                    'angle': self.player['angle'] + angle_offset,
                    'speed': 0.2 * self.player['lure_speed'],
                    'damage': 1 * self.player['lure_power'],
                    'distance': 0,
                    'max_distance': 10,
                    'active': True
                }
                self.player['bullets'].append(spread_bullet)
        
        return True
    
    def update(self):
        # Update bullets
        if 'bullets' not in self.player:
            self.player['bullets'] = []
        
        # Track explosions
        if 'explosions' not in self.player:
            self.player['explosions'] = []
        
        # Update existing explosions
        for explosion in self.player['explosions'][:]:
            explosion['time'] -= 1
            if explosion['time'] <= 0:
                self.player['explosions'].remove(explosion)
        
        # Update bullets and check for hits
        for bullet in self.player['bullets'][:]:
            # Move bullet
            bullet['x'] += math.cos(bullet['angle']) * bullet['speed']
            bullet['y'] += math.sin(bullet['angle']) * bullet['speed']
            bullet['distance'] += bullet['speed']
            
            # Check if bullet hit a wall
            if not self.is_valid_position(bullet['x'], bullet['y']) or bullet['distance'] >= bullet['max_distance']:
                self.player['bullets'].remove(bullet)
                continue
            
            # Check if bullet hit a fish
            for i, fish in enumerate(self.fish):
                dx = fish['x'] - bullet['x']
                dy = fish['y'] - bullet['y']
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist < 0.5:  # Hit radius
                    # Hit the fish
                    fish['health'] -= 1
                    
                    # Create explosion
                    self.player['explosions'].append({
                        'x': bullet['x'],
                        'y': bullet['y'],
                        'size': 0.5,
                        'time': 10  # frames the explosion lasts
                    })
                    
                    # Remove bullet
                    self.player['bullets'].remove(bullet)
                    
                    if fish['health'] <= 0:
                        # Fish is caught
                        self.score += FISH_TYPES[fish['type']]['points']
                        self.fish.pop(i)
                        # Spawn a new fish
                        self.spawn_fish(1)
                    break
        
        # Move fish
        for fish in self.fish[:]:
            # Update fish state
            fish['state_timer'] -= 1
            if fish['state_timer'] <= 0:
                # Change state
                if fish['state'] == 'patrol':
                    # 30% chance to chase player if close enough
                    dx = fish['x'] - self.player['x']
                    dy = fish['y'] - self.player['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist < 10 and random.random() < 0.3:
                        fish['state'] = 'chase'
                        fish['state_timer'] = random.randint(50, 100)
                    else:
                        # Just change direction
                        fish['direction'] = random.uniform(0, 2 * math.pi)
                        fish['state_timer'] = random.randint(50, 150)
                
                elif fish['state'] == 'chase':
                    # Go back to patrol
                    fish['state'] = 'patrol'
                    fish['state_timer'] = random.randint(50, 150)
            
            # Move fish based on state
            if fish['state'] == 'patrol':
                # Occasionally change direction
                if random.random() < 0.01:
                    fish['direction'] = random.uniform(0, 2 * math.pi)
                
                # Move fish in its direction
                speed = fish['speed'] * 0.7  # Slower when patrolling
                new_x = fish['x'] + math.cos(fish['direction']) * speed
                new_y = fish['y'] + math.sin(fish['direction']) * speed
                
            elif fish['state'] == 'chase':
                # Calculate direction to player
                dx = self.player['x'] - fish['x']
                dy = self.player['y'] - fish['y']
                angle = math.atan2(dy, dx)
                
                # Add some randomness to chase
                angle += random.uniform(-0.1, 0.1)
                
                # Move toward player
                speed = fish['speed'] * 1.8  # Faster when chasing
                new_x = fish['x'] + math.cos(angle) * speed
                new_y = fish['y'] + math.sin(angle) * speed
                
                # Update direction for rendering
                fish['direction'] = angle
            
            # Check if new position is valid
            if self.is_valid_position(new_x, new_y):
                fish['x'] = new_x
                fish['y'] = new_y
            else:
                # If not valid, bounce off wall
                fish['direction'] += math.pi + random.uniform(-0.5, 0.5)
                fish['state'] = 'patrol'  # Go back to patrol after hitting wall
            
            # Check if fish is too close to player
            dx = fish['x'] - self.player['x']
            dy = fish['y'] - self.player['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < 0.5:
                # Fish attacks player
                self.game_over = True
        
        # Spawn new fish with a delay between spawns
        current_time = time.time()
        last_spawn_time = 0
        
        # Find the most recently spawned fish
        if self.fish:
            last_spawn_time = max(fish.get('spawn_time', 0) for fish in self.fish)
        
        # Only spawn a new fish if enough time has passed since the last spawn
        if (current_time - last_spawn_time > 5 and  # 5 second delay between fish
            random.random() < 0.01 and 
            len(self.fish) < 3):  # Maximum of 3 fish at once
            self.spawn_fish(1)
        
        # Check if player is out of lures and no fish are left
        if self.player['lures'] <= 0 and len(self.fish) > 0:
            # Check if any fish is within shooting range
            can_shoot = False
            for fish in self.fish:
                dx = fish['x'] - self.player['x']
                dy = fish['y'] - self.player['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 5:
                    can_shoot = True
                    break
            
            if not can_shoot:
                self.game_over = True
        
        # Update power-ups
        for power_up in self.power_ups[:]:
            # Make power-ups rotate
            power_up['rotation'] += 0.02
            power_up['bob_offset'] += 0.05
            
            # Check if player collected power-up
            dx = power_up['x'] - self.player['x']
            dy = power_up['y'] - self.player['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < 0.7:  # Player is close enough to collect
                # Apply power-up effect
                if power_up['effect'] == 'lure_power':
                    self.player['lure_power'] = power_up['multiplier']
                elif power_up['effect'] == 'lure_speed':
                    self.player['lure_speed'] = power_up['multiplier']
                
                # Add to active power-ups
                self.player['power_ups'].append({
                    'type': power_up['type'],
                    'effect': power_up['effect'],
                    'multiplier': power_up['multiplier'],
                    'duration': power_up['duration'],
                    'start_time': time.time()
                })
                
                # Remove collected power-up
                self.power_ups.remove(power_up)
                
                # Spawn a new power-up elsewhere
                self.spawn_power_ups(1)
        
        # Update active power-ups
        current_time = time.time()
        for power_up in self.player['power_ups'][:]:
            elapsed = current_time - power_up['start_time']
            if elapsed > power_up['duration']:
                # Power-up expired
                if power_up['effect'] == 'lure_power':
                    self.player['lure_power'] = 1.0
                elif power_up['effect'] == 'lure_speed':
                    self.player['lure_speed'] = 1.0
                
                self.player['power_ups'].remove(power_up)
    
    def get_state(self):
        return {
            'player': self.player,
            'fish': self.fish,
            'power_ups': self.power_ups,
            'score': self.score,
            'game_over': self.game_over
        }

    def spawn_power_ups(self, count):
        power_up_types = [
            {'type': 'power', 'color': '#ff0000', 'effect': 'lure_power', 'multiplier': 2.0, 'duration': 30},
            {'type': 'speed', 'color': '#00ff00', 'effect': 'lure_speed', 'multiplier': 1.5, 'duration': 30},
            {'type': 'spread', 'color': '#0000ff', 'effect': 'spread_shot', 'multiplier': 3, 'duration': 20}
        ]
        
        for _ in range(count):
            # Find a valid position (not in a wall and not too close to player)
            while True:
                x = random.uniform(1, len(MAP[0]) - 2)
                y = random.uniform(1, len(MAP) - 2)
                
                # Check if position is in a wall
                if MAP[int(y)][int(x)] != 0:
                    continue
                
                # Make sure power-up isn't too close to the player
                dist = math.sqrt((x - self.player['x'])**2 + (y - self.player['y'])**2)
                if dist < 5:
                    continue
                
                break
            
            power_up_type = random.choice(power_up_types)
            self.power_ups.append({
                'x': x,
                'y': y,
                'type': power_up_type['type'],
                'color': power_up_type['color'],
                'effect': power_up_type['effect'],
                'multiplier': power_up_type['multiplier'],
                'duration': power_up_type['duration'],
                'rotation': random.uniform(0, 2 * math.pi),
                'bob_offset': random.uniform(0, 2 * math.pi)
            })

game = Game()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/high-scores')
def get_high_scores():
    return jsonify(HIGH_SCORES)

@app.route('/game-state')
def get_game_state():
    return jsonify(game.get_state())

@app.route('/change-lure', methods=['POST'])
def change_lure():
    data = request.get_json()
    new_lure = data.get('lure')
    if new_lure in LURE_TYPES:
        game_state['player']['current_lure'] = new_lure
    return jsonify(game_state)

@app.route('/move', methods=['POST'])
def move():
    print("Move request received")
    if game.game_over:
        return jsonify(game.get_state())

    data = request.get_json()
    direction = data.get('direction')
    shoot = data.get('shoot', False)
    amount = data.get('amount', 1)
    
    print(f"Move data: direction={direction}, shoot={shoot}, amount={amount}")
    
    if direction:
        game.move_player(direction, amount)
    
    if shoot:
        game.shoot()
    
    game.update()
    state = game.get_state()
    print(f"Move state: {state}")
    return jsonify(state)

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
    print("Reset request received")
    if game.game_over:
        save_high_score(game.score)
    game.reset()
    state = game.get_state()
    print(f"Reset state: {state}")
    return jsonify(state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)