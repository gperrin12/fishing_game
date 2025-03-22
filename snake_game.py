from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Game state
game_state = {
    'snake': [(10, 10)],  # List of (x,y) coordinates
    'food': (15, 15),     # (x,y) coordinate
    'direction': 'RIGHT', # Current direction
    'score': 0,
    'game_over': False
}

GRID_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20

def reset_game():
    game_state['snake'] = [(10, 10)]
    game_state['direction'] = 'RIGHT'
    game_state['score'] = 0
    game_state['game_over'] = False
    place_food()

def place_food():
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if (x, y) not in game_state['snake']:
            game_state['food'] = (x, y)
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
    head_x, head_y = game_state['snake'][0]

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
        (head_x, head_y) in game_state['snake']):
        game_state['game_over'] = True
        return jsonify(game_state)

    # Add new head
    game_state['snake'].insert(0, (head_x, head_y))

    # Check if food was eaten
    if (head_x, head_y) == game_state['food']:
        game_state['score'] += 1
        place_food()
    else:
        game_state['snake'].pop()

    return jsonify(game_state)

@app.route('/reset', methods=['POST'])
def reset():
    reset_game()
    return jsonify(game_state)

if __name__ == '__main__':
    reset_game()
    app.run(host='0.0.0.0', port=5000)