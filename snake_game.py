import pygame
import time
import random

# Initialize Pygame
pygame.init()

# Define colors
water_blue = (65, 105, 225)  # Deep blue for water
boat_color = (139, 69, 19)   # Brown for boat
fish_color = (255, 140, 0)   # Orange for fish
fishing_line_color = (255, 255, 255)  # White for fishing line
score_color = (255, 255, 102)  # Yellow for score
text_color = (255, 255, 255)  # White for text
game_over_color = (213, 50, 80)  # Red for game over
win_color = (0, 255, 0)  # Green for win message
powerup_color = (147, 112, 219)  # Purple for power-ups

# Fishing game variables
fishing_lines = []  # List to store active fishing lines
line_speed = 3  # Speed multiplier for fishing lines
line_size = 3  # Default size of fishing lines
max_line_size = 9  # Maximum size of fishing lines with power-ups
powerup_active = False  # Flag to track if a power-up is on screen
powerup_x = 0  # Power-up x coordinate
powerup_y = 0  # Power-up y coordinate
powerup_timer = 0  # Timer for spawning power-ups

# Display dimensions
dis_width = 600
dis_height = 400

# Create display window
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('Fishing Adventure')

# Clock for controlling the game's frame rate
clock = pygame.time.Clock()
boat_size = 10
game_speed = 15

# Font styles for score and messages
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

def draw_boat(boat_size, boat_segments):
    """Draws the fishing boat on the screen."""
    for segment in boat_segments:
        pygame.draw.rect(dis, boat_color, [segment[0], segment[1], boat_size, boat_size])

def draw_fishing_lines():
    """Draws all active fishing lines."""
    for line in fishing_lines:
        pygame.draw.rect(dis, fishing_line_color, [line[0], line[1], line_size, line_size])

def draw_powerup():
    """Draws the power-up if active."""
    if powerup_active:
        pygame.draw.rect(dis, powerup_color, [powerup_x, powerup_y, boat_size, boat_size])

def your_catch(score):
    """Displays the current fish caught."""
    value = score_font.render("Fish Caught: " + str(score), True, score_color)
    dis.blit(value, [0, 0])

def message(msg, color):
    """Displays a message on the screen."""
    mesg = font_style.render(msg, True, color)
    dis.blit(mesg, [dis_width / 6, dis_height / 3])

def gameLoop():
    game_over = False
    game_close = False
    
    # Starting position of the boat
    x1 = dis_width / 2
    y1 = dis_height / 2
    x1_change = 0
    y1_change = 0
    
    boat_segments = []
    boat_length = 1
    
    # Set initial fish coordinates
    fish_x = round(random.randrange(0, dis_width - boat_size) / 10.0) * 10.0
    fish_y = round(random.randrange(0, dis_height - boat_size) / 10.0) * 10.0
    
    # Add fishing line direction variables
    line_direction_x = 0
    line_direction_y = 0
    
    # Add a maximum score to reach
    max_score = 100
    
    # Power-up variables
    global powerup_active, powerup_x, powerup_y, powerup_timer, line_size
    powerup_active = False
    powerup_timer = 0
    line_size = 3  # Reset line size at start of game

    while not game_over:

        # Game Over screen loop
        while game_close:
            dis.fill(water_blue)
            if boat_length - 1 >= max_score:
                message("You're a master angler! Fish: " + str(boat_length - 1) + " Press Q-Quit or C-Play Again", win_color)
            else:
                message("Fishing trip over! Press Q-Quit or C-Cast Again", game_over_color)
            your_catch(boat_length - 1)
            pygame.display.update()

            # Event loop for game over screen
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                # Change boat direction based on arrow keys
                if event.key == pygame.K_LEFT:
                    x1_change = -boat_size
                    y1_change = 0
                    line_direction_x = -1
                    line_direction_y = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = boat_size
                    y1_change = 0
                    line_direction_x = 1
                    line_direction_y = 0
                elif event.key == pygame.K_UP:
                    y1_change = -boat_size
                    x1_change = 0
                    line_direction_x = 0
                    line_direction_y = -1
                elif event.key == pygame.K_DOWN:
                    y1_change = boat_size
                    x1_change = 0
                    line_direction_x = 0
                    line_direction_y = 1
                # Cast fishing line with spacebar
                elif event.key == pygame.K_SPACE:
                    if line_direction_x != 0 or line_direction_y != 0:
                        fishing_lines.append([x1, y1, line_direction_x, line_direction_y])

        # Check for collision with boundaries (boat can't go on land)
        if x1 >= dis_width or x1 < 0 or y1 >= dis_height or y1 < 0:
            game_close = True

        # Update boat's position
        x1 += x1_change
        y1 += y1_change
        dis.fill(water_blue)
        pygame.draw.rect(dis, fish_color, [fish_x, fish_y, boat_size, boat_size])
        
        # Handle power-up spawning and collection
        powerup_timer += 1
        if not powerup_active and powerup_timer > 300:  # Spawn power-up every ~5 seconds
            powerup_active = True
            powerup_x = round(random.randrange(0, dis_width - boat_size) / 10.0) * 10.0
            powerup_y = round(random.randrange(0, dis_height - boat_size) / 10.0) * 10.0
            powerup_timer = 0
        
        # Draw power-up if active
        if powerup_active:
            draw_powerup()
            
            # Check if boat collected power-up
            if x1 == powerup_x and y1 == powerup_y:
                powerup_active = False
                if line_size < max_line_size:
                    line_size += 2  # Increase fishing line size
                powerup_timer = 0

        # Update and draw fishing lines
        for line in fishing_lines[:]:
            line[0] += line[2] * boat_size * line_speed
            line[1] += line[3] * boat_size * line_speed
            
            # Remove fishing lines that are off-screen
            if (line[0] < 0 or line[0] > dis_width or 
                line[1] < 0 or line[1] > dis_height):
                fishing_lines.remove(line)
                continue
            
            # Check for catching fish with fishing line
            if (line[0] >= fish_x and line[0] < fish_x + boat_size and
                line[1] >= fish_y and line[1] < fish_y + boat_size):
                fishing_lines.remove(line)
                fish_x = round(random.randrange(0, dis_width - boat_size) / 10.0) * 10.0
                fish_y = round(random.randrange(0, dis_height - boat_size) / 10.0) * 10.0
                boat_length += 1
            
            # Check for power-up collection with fishing line
            if powerup_active and (line[0] >= powerup_x and line[0] < powerup_x + boat_size and
                                  line[1] >= powerup_y and line[1] < powerup_y + boat_size):
                fishing_lines.remove(line)
                powerup_active = False
                if line_size < max_line_size:
                    line_size += 2  # Increase fishing line size
                powerup_timer = 0

        draw_fishing_lines()
        
        # Append new boat position
        boat_head = []
        boat_head.append(x1)
        boat_head.append(y1)
        boat_segments.append(boat_head)
        if len(boat_segments) > boat_length:
            del boat_segments[0]

        # Check for collision with self (boat crashed into itself)
        for segment in boat_segments[:-1]:
            if segment == boat_head:
                game_close = True

        draw_boat(boat_size, boat_segments)
        your_catch(boat_length - 1)

        pygame.display.update()

        # Check if player has reached the maximum score
        if boat_length - 1 >= max_score:
            game_close = True

        # Check if boat has caught a fish directly
        if x1 == fish_x and y1 == fish_y:
            # Generate new fish position
            fish_x = round(random.randrange(0, dis_width - boat_size) / 10.0) * 10.0
            fish_y = round(random.randrange(0, dis_height - boat_size) / 10.0) * 10.0
            boat_length += 1

        clock.tick(game_speed)

    pygame.quit()
    quit()

gameLoop()