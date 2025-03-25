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
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 2, 2, 2, 0, 0, 0, 1, 0, 0, 0, 3, 3, 3, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 1],
    [1, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 4, 4, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 5, 5, 0, 0, 1],
    [1, 0, 0, 4, 4, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 5, 5, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# Define wall textures for different wall types
WALL_TEXTURES = {
    1: "stone",      # Regular stone walls
    2: "tech",       # Tech walls (like computer panels)
    3: "slime",      # Slime-covered walls
    4: "blood",      # Blood-stained walls
    5: "metal"       # Metal walls
}

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
        'power_ups_used': [],
        'health': 100,
        'armor': 0,
        'current_weapon': 'pistol',
        'weapons': ['pistol'],
        'ammo': {
            'bullets': 50,
            'shells': 0,
            'cells': 0
        },
        'weapon_cooldown': 0
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
    'imp': {
        'color': '#ff4500',
        'speed': 0.04,
        'health': 3,
        'damage': 2,
        'points': 100,
        'attack_type': 'melee',
        'sprite': 'imp'
    },
    'demon': {
        'color': '#8b0000',
        'speed': 0.03,
        'health': 5,
        'damage': 3,
        'points': 200,
        'attack_type': 'charge',
        'sprite': 'demon'
    },
    'cacodemon': {
        'color': '#ff1493',
        'speed': 0.02,
        'health': 8,
        'damage': 4,
        'points': 300,
        'attack_type': 'projectile',
        'sprite': 'cacodemon'
    },
    'baron': {
        'color': '#006400',
        'speed': 0.015,
        'health': 15,
        'damage': 6,
        'points': 500,
        'attack_type': 'projectile',
        'sprite': 'baron'
    }
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

# Define weapons similar to Doom
WEAPONS = {
    'pistol': {
        'damage': 1,
        'speed': 0.3,
        'cooldown': 20,
        'sprite': 'pistol',
        'sound': 'pistol',
        'ammo_type': 'bullets'
    },
    'shotgun': {
        'damage': 2,
        'speed': 0.25,
        'cooldown': 30,
        'spread': 3,
        'pellets': 7,
        'sprite': 'shotgun',
        'sound': 'shotgun',
        'ammo_type': 'shells'
    },
    'chaingun': {
        'damage': 1,
        'speed': 0.3,
        'cooldown': 5,
        'sprite': 'chaingun',
        'sound': 'chaingun',
        'ammo_type': 'bullets'
    },
    'plasma': {
        'damage': 2,
        'speed': 0.4,
        'cooldown': 10,
        'sprite': 'plasma',
        'sound': 'plasma',
        'ammo_type': 'cells'
    },
    'bfg': {
        'damage': 10,
        'speed': 0.2,
        'cooldown': 60,
        'sprite': 'bfg',
        'sound': 'bfg',
        'ammo_type': 'cells',
        'explosion_radius': 3
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
    game_state['player']['health'] = 100
    game_state['player']['armor'] = 0
    game_state['player']['current_weapon'] = 'pistol'
    game_state['player']['weapons'] = ['pistol']
    game_state['player']['ammo'] = {
        'bullets': 50,
        'shells': 0,
        'cells': 0
    }
    game_state['player']['weapon_cooldown'] = 0
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
            'health': 100,
            'armor': 0,
            'current_weapon': 'pistol',
            'weapons': ['pistol'],
            'ammo': {
                'bullets': 50,
                'shells': 0,
                'cells': 0
            },
            'weapon_cooldown': 0,
            'bullets': [],
            'explosions': [],
            'power_ups': [],
            'lures': 10,  # Assuming 10 is the starting count of lures
            'lure_power': 1.0,
            'lure_speed': 1.0,
            'casting_speed': 1.0
        }
        self.fish = []
        self.score = 0
        self.game_over = False
        self.power_ups = []
        
        # Spawn initial fish
        self.spawn_fish(5)
        
        # Spawn initial power-ups
        self.spawn_power_ups(3)
        
        # Spawn initial weapon pickup
        self.spawn_weapon_pickup()
        
        # Spawn initial ammo pickup
        self.spawn_ammo_pickup()
        
        print("Game reset complete")
    
    def spawn_fish(self, count=1):
        for _ in range(count):
            # Choose a random fish type
            fish_type = random.choice(list(FISH_TYPES.keys()))
            
            # Get fish properties
            fish_props = FISH_TYPES[fish_type]
            
            # Find a valid spawn position
            valid_position = False
            x, y = 0, 0
            
            while not valid_position:
                # Spawn fish at a random position away from the player
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(5, 10)  # Spawn 5-10 units away from player
                
                x = self.player['x'] + math.cos(angle) * distance
                y = self.player['y'] + math.sin(angle) * distance
                
                # Check if position is valid (not in a wall)
                if self.is_valid_position(x, y):
                    valid_position = True
            
            # Create the fish
            fish = {
                'x': x,
                'y': y,
                'type': fish_type,
                'speed': fish_props['speed'],
                'health': fish_props['health'],
                'direction': random.uniform(0, 2 * math.pi),
                'state': 'patrol',
                'state_timer': 0
            }
            
            self.fish.append(fish)
            print(f"Spawned {fish_type} at ({x:.2f}, {y:.2f})")
        
        return True
    
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
        # Check if weapon is on cooldown
        if 'weapon_cooldown' in self.player and self.player['weapon_cooldown'] > 0:
            return False
        
        # Get current weapon
        weapon_name = self.player.get('current_weapon', 'pistol')
        
        # Check if we have the WEAPONS dictionary
        if 'WEAPONS' in globals() and weapon_name in WEAPONS:
            weapon = WEAPONS[weapon_name]
            ammo_type = weapon['ammo_type']
            
            # Check if player has ammo - make sure ammo is a dictionary with numeric values
            if isinstance(self.player['ammo'], dict) and ammo_type in self.player['ammo']:
                ammo_count = self.player['ammo'][ammo_type]
                if isinstance(ammo_count, int) and ammo_count <= 0:
                    print(f"Out of {ammo_type}")
                    return False
                
                # Consume ammo
                self.player['ammo'][ammo_type] -= 1
            else:
                print("Invalid ammo structure")
                return False
            
            # Set weapon cooldown
            self.player['weapon_cooldown'] = weapon['cooldown']
            
            # Handle different weapon types
            if 'pellets' in weapon:  # Shotgun-like
                for _ in range(weapon['pellets']):
                    spread = random.uniform(-weapon['spread'] * 0.01, weapon['spread'] * 0.01)
                    self.create_bullet(self.player['angle'] + spread, weapon['damage'], weapon['speed'])
            elif weapon_name == 'bfg':  # BFG-like
                self.create_bullet(self.player['angle'], weapon['damage'], weapon['speed'], explosion_radius=weapon.get('explosion_radius', 0))
            else:  # Regular weapon
                self.create_bullet(self.player['angle'], weapon['damage'], weapon['speed'])
        else:
            # Fallback to old fishing game logic
            bullet = {
                'x': self.player['x'],
                'y': self.player['y'],
                'angle': self.player['angle'],
                'speed': 0.2 * self.player.get('lure_speed', 1.0),
                'damage': 1 * self.player.get('lure_power', 1.0),
                'distance': 0,
                'max_distance': 10,
                'active': True
            }
            
            # Add bullet to player
            if 'bullets' not in self.player:
                self.player['bullets'] = []
            
            self.player['bullets'].append(bullet)
        
        return True
    
    def create_bullet(self, angle, damage, speed, explosion_radius=0):
        bullet = {
            'x': self.player['x'],
            'y': self.player['y'],
            'angle': angle,
            'speed': speed,
            'damage': damage,
            'distance': 0,
            'max_distance': 15,
            'active': True,
            'explosion_radius': explosion_radius
        }
        
        if 'bullets' not in self.player:
            self.player['bullets'] = []
        
        self.player['bullets'].append(bullet)
    
    def update(self):
        # Ensure lures is an integer
        if 'lures' not in self.player:
            self.player['lures'] = 10  # Default starting count

        # Check if there are no lures and fish exist
        if self.player['lures'] <= 0 and len(self.fish) > 0:
            # Your logic here
            pass

        # Make sure we have bullet and explosion arrays
        if 'bullets' not in self.player:
            self.player['bullets'] = []
        
        if 'explosions' not in self.player:
            self.player['explosions'] = []
        
        if 'lures' not in self.player:
            self.player['lures'] = []
        
        if 'lure_power' not in self.player:
            self.player['lure_power'] = 1.0
        
        if 'lure_speed' not in self.player:
            self.player['lure_speed'] = 1.0
        
        if 'casting_speed' not in self.player:
            self.player['casting_speed'] = 1.0
        
        # Update existing explosions
        for explosion in self.player['explosions'][:]:
            explosion['time'] -= 1
            if explosion['time'] <= 0:
                self.player['explosions'].remove(explosion)
        
        # Process each bullet
        print(f"Processing {len(self.player['bullets'])} bullets")
        for bullet in list(self.player['bullets']):  # Use list() to create a copy
            # Move bullet
            bullet['x'] += math.cos(bullet['angle']) * bullet['speed']
            bullet['y'] += math.sin(bullet['angle']) * bullet['speed']
            bullet['distance'] += bullet['speed']
            
            # Check if bullet hit a wall or exceeded max distance
            if not self.is_valid_position(bullet['x'], bullet['y']) or bullet['distance'] >= bullet['max_distance']:
                print(f"Bullet hit wall or exceeded max distance at ({bullet['x']}, {bullet['y']})")
                # Create explosion at wall hit
                self.player['explosions'].append({
                    'x': bullet['x'],
                    'y': bullet['y'],
                    'size': 0.3,
                    'time': 5
                })
                self.player['bullets'].remove(bullet)
                continue
            
            # Check for fish collisions
            hit = False
            for i, fish in enumerate(list(self.fish)):  # Use list() to create a copy
                # Calculate distance between bullet and fish
                dx = fish['x'] - bullet['x']
                dy = fish['y'] - bullet['y']
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Very generous hit radius to make hitting fish easier
                if dist < 2.0:
                    print(f"BULLET HIT FISH! Distance: {dist}")
                    print(f"Bullet position: ({bullet['x']}, {bullet['y']})")
                    print(f"Fish position: ({fish['x']}, {fish['y']})")
                    
                    # Apply damage to fish
                    damage = bullet.get('damage', 1) * self.player['lure_power']
                    fish['health'] -= damage
                    
                    print(f"Fish hit! Type: {fish['type']}, Health before: {fish['health'] + damage}, after: {fish['health']}")
                    
                    # Create explosion at hit location
                    self.player['explosions'].append({
                        'x': bullet['x'],
                        'y': bullet['y'],
                        'size': 0.5,
                        'time': 10
                    })
                    
                    # Remove bullet
                    if bullet in self.player['bullets']:
                        self.player['bullets'].remove(bullet)
                    
                    # Check if fish is dead
                    if fish['health'] <= 0:
                        print(f"Fish killed! Type: {fish['type']}, Points: {FISH_TYPES[fish['type']]['points']}")
                        # Add score
                        self.score += FISH_TYPES[fish['type']]['points']
                        
                        # Remove fish
                        if fish in self.fish:
                            self.fish.remove(fish)
                        
                        # Spawn a new fish
                        self.spawn_fish(1)
                    
                    hit = True
                    break
            
            if hit:
                continue
        
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
                speed = fish['speed'] * 0.5  # Slower when patrolling - REDUCED SPEED
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
                speed = fish['speed'] * 1.2  # Faster when chasing - REDUCED SPEED
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
        
        # Update pickups
        if hasattr(self, 'pickups'):
            for pickup in self.pickups[:]:
                # Decrease time
                pickup['time'] -= 1
                
                # Remove expired pickups
                if pickup['time'] <= 0:
                    self.pickups.remove(pickup)
                    continue
                
                # Check if player picked up
                dx = pickup['x'] - self.player['x']
                dy = pickup['y'] - self.player['y']
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist < 1.0:
                    if pickup['type'] == 'weapon':
                        # Add weapon to player's inventory
                        if pickup['weapon'] not in self.player['weapons']:
                            self.player['weapons'].append(pickup['weapon'])
                            print(f"Player picked up weapon: {pickup['weapon']}")
                            
                            # Switch to the new weapon
                            self.player['current_weapon'] = pickup['weapon']
                            
                            # Add some ammo for the weapon
                            ammo_type = WEAPONS[pickup['weapon']]['ammo_type']
                            if ammo_type == 'bullets':
                                self.player['ammo']['bullets'] += 20
                            elif ammo_type == 'shells':
                                self.player['ammo']['shells'] += 8
                            else:  # cells
                                self.player['ammo']['cells'] += 30
                    
                    elif pickup['type'] == 'ammo':
                        # Add ammo to player's inventory
                        self.player['ammo'][pickup['ammo_type']] += pickup['amount']
                        print(f"Player picked up {pickup['amount']} {pickup['ammo_type']}")
                    
                    # Remove the pickup
                    self.pickups.remove(pickup)
                    
                    # Create explosion effect
                    self.player['explosions'].append({
                        'x': pickup['x'],
                        'y': pickup['y'],
                        'size': 0.5,
                        'time': 10,
                        'color': '#ffff00'  # Yellow for pickups
                    })
    
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

    def fish_attack(self, fish):
        # Calculate distance to player
        dx = self.player['x'] - fish['x']
        dy = self.player['y'] - fish['y']
        dist = math.sqrt(dx**2 + dy**2)
        
        # Only attack if close enough
        if dist > 5:
            return
        
        attack_type = FISH_TYPES[fish['type']]['attack_type']
        
        if attack_type == 'melee' and dist < 1.5:
            # Melee attack - direct damage to player
            if 'health' not in self.player:
                self.player['health'] = 100
            
            self.player['health'] -= FISH_TYPES[fish['type']]['damage']
            
            # Create explosion for attack visualization
            self.player['explosions'].append({
                'x': self.player['x'],
                'y': self.player['y'],
                'size': 0.5,
                'time': 5,
                'color': '#ff0000'
            })
            
            # Check if player died
            if self.player['health'] <= 0:
                self.game_over = True
        
        elif attack_type == 'charge' and dist < 4:
            # Charge attack - fish rushes at player
            fish['state'] = 'charge'
            fish['state_timer'] = 30
            fish['target_x'] = self.player['x']
            fish['target_y'] = self.player['y']
        
        elif attack_type == 'projectile' and dist < 8 and random.random() < 0.05:
            # Projectile attack - fish shoots at player
            if 'projectiles' not in fish:
                fish['projectiles'] = []
            
            angle = math.atan2(dy, dx)
            fish['projectiles'].append({
                'x': fish['x'],
                'y': fish['y'],
                'angle': angle,
                'speed': 0.1,
                'damage': FISH_TYPES[fish['type']]['damage'] / 2,
                'distance': 0,
                'max_distance': 10
            })

    def spawn_weapon_pickup(self):
        # Determine which weapons the player doesn't have
        available_weapons = [w for w in WEAPONS.keys() if w not in self.player['weapons']]
        
        if not available_weapons:
            return  # Player has all weapons
        
        # Choose a random weapon
        weapon = random.choice(available_weapons)
        
        # Find a valid position
        valid_position = False
        x, y = 0, 0
        
        while not valid_position:
            x = random.uniform(1, len(MAP[0]) - 1)
            y = random.uniform(1, len(MAP) - 1)
            
            # Check if position is valid (not in a wall)
            if self.is_valid_position(x, y):
                valid_position = True
        
        # Create the pickup
        pickup = {
            'type': 'weapon',
            'weapon': weapon,
            'x': x,
            'y': y,
            'time': 600  # How long the pickup stays
        }
        
        if 'pickups' not in self.__dict__:
            self.pickups = []
        
        self.pickups.append(pickup)
        print(f"Spawned weapon pickup: {weapon} at ({x}, {y})")

    def spawn_ammo_pickup(self):
        # Choose a random ammo type
        ammo_type = random.choice(['bullets', 'shells', 'cells'])
        
        # Determine amount based on type
        if ammo_type == 'bullets':
            amount = random.randint(5, 20)
        elif ammo_type == 'shells':
            amount = random.randint(2, 8)
        else:  # cells
            amount = random.randint(10, 30)
        
        # Find a valid position
        valid_position = False
        x, y = 0, 0
        
        while not valid_position:
            x = random.uniform(1, len(MAP[0]) - 1)
            y = random.uniform(1, len(MAP) - 1)
            
            # Check if position is valid (not in a wall)
            if self.is_valid_position(x, y):
                valid_position = True
        
        # Create the pickup
        pickup = {
            'type': 'ammo',
            'ammo_type': ammo_type,
            'amount': amount,
            'x': x,
            'y': y,
            'time': 600  # How long the pickup stays
        }
        
        if 'pickups' not in self.__dict__:
            self.pickups = []
        
        self.pickups.append(pickup)
        print(f"Spawned {amount} {ammo_type} pickup at ({x}, {y})")

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

@app.route('/spawn-fish', methods=['POST'])
def spawn_fish_route():
    print("Spawn fish request received")
    data = request.get_json()
    count = data.get('count', 1)
    
    game.spawn_fish(count)
    
    state = game.get_state()
    print(f"After spawning fish: {len(state['fish'])} fish in game")
    return jsonify(state)

@app.route('/hit-fish', methods=['POST'])
def hit_fish_route():
    print("Hit fish request received")
    data = request.get_json()
    index = data.get('index', 0)
    damage = data.get('damage', 1)
    
    if game.fish and len(game.fish) > index:
        fish = game.fish[index]
        fish['health'] -= damage
        
        print(f"Fish hit directly! Type: {fish['type']}, Health: {fish['health']}")
        
        if fish['health'] <= 0:
            # Fish is caught
            game.score += FISH_TYPES[fish['type']]['points']
            game.fish.pop(index)
            # Spawn a new fish
            game.spawn_fish(1)
    
    state = game.get_state()
    return jsonify(state)

@app.route('/switch-weapon', methods=['POST'])
def switch_weapon():
    data = request.get_json()
    weapon = data.get('weapon')
    
    if weapon in WEAPONS and weapon in game.player['weapons']:
        game.player['current_weapon'] = weapon
        print(f"Switched to weapon: {weapon}")
    else:
        print(f"Cannot switch to weapon: {weapon}")
    
    return jsonify(game.get_state())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)