from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Game state
game_state = {
    'fishing_line': [(10, 10)],  # List of (x,y) coordinates for the line
    'fish': (15, 15),           # (x,y) coordinate for the fish
    'direction': 'RIGHT',       # Current direction
    'score': 0,
    'game_over': False,
    'fish_type': 'normal'       # Can be 'normal', 'rare', or 'special'
}

GRID_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20

FISH_TYPES = {
    'normal': {'chance': 0.7, 'points': 1},
    'rare': {'chance': 0.2, 'points': 3},
    'special': {'chance': 0.1, 'points': 5}
}

def reset_game():
    game_state['fishing_line'] = [(10, 10)]
    game_state['direction'] = 'RIGHT'
    game_state['score'] = 0
    game_state['game_over'] = False
    place_fish()

def place_fish():
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if (x, y) not in game_state['fishing_line']:
            game_state['fish'] = (x, y)
            # Randomly select fish type based on chances
            rand = random.random()
            if rand < FISH_TYPES['special']['chance']:
                game_state['fish_type'] = 'special'
            elif rand < FISH_TYPES['special']['chance'] + FISH_TYPES['rare']['chance']:
                game_state['fish_type'] = 'rare'
            else:
                game_state['fish_type'] = 'normal'
            break

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/game-state')
def get_game_state():
    return jsonify(game_state)

@app.route('/move', methods=['POST'])
def move():
    if game_state['game_over']:
        return jsonify(game_state)

    data = request.get_json()
    new_direction = data.get('direction')
    
    # Update direction if valid
    opposite_directions = {
        'UP': 'DOWN',
        'DOWN': 'UP',
        'LEFT': 'RIGHT',
        'RIGHT': 'LEFT'
    }
    if new_direction and new_direction != opposite_directions.get(game_state['direction']):
        game_state['direction'] = new_direction

    # Get current head position
    head_x, head_y = game_state['fishing_line'][0]

    # Calculate new head position
    if game_state['direction'] == 'UP':
        head_y -= 1
    elif game_state['direction'] == 'DOWN':
        head_y += 1
    elif game_state['direction'] == 'LEFT':
        head_x -= 1
    elif game_state['direction'] == 'RIGHT':
        head_x += 1

    # Check for collisions
    if (head_x < 0 or head_x >= GRID_WIDTH or 
        head_y < 0 or head_y >= GRID_HEIGHT or 
        (head_x, head_y) in game_state['fishing_line']):
        game_state['game_over'] = True
        return jsonify(game_state)

    # Add new head
    game_state['fishing_line'].insert(0, (head_x, head_y))

    # Check if fish was caught
    if (head_x, head_y) == game_state['fish']:
        fish_type = game_state['fish_type']
        game_state['score'] += FISH_TYPES[fish_type]['points']
        place_fish()
    else:
        game_state['fishing_line'].pop()

    return jsonify(game_state)

@app.route('/reset', methods=['POST'])
def reset():
    reset_game()
    return jsonify(game_state)

if __name__ == '__main__':
    reset_game()
    app.run(host='0.0.0.0', port=5001)