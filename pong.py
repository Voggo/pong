import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the game window
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pong")

# Define game colors
bg_color = pygame.Color("grey12")
light_grey = (200, 200, 200)

# Define game elements
ball = pygame.Rect(screen_width/2 - 15, screen_height/2 - 15, 30, 30)
player = pygame.Rect(screen_width - 20, screen_height/2 - 70, 10,140)
opponent = pygame.Rect(10, screen_height/2 - 70, 10, 140)

# Define game physics
ball_speed_x = 7 + random.choice((1, -1))
ball_speed_y = 7 + random.choice((1, -1))
player_speed = 0
opponent_speed = 7

# Define game logic
player_score = 0
opponent_score = 0
game_font = pygame.font.Font("freesansbold.ttf", 32)

def reset_ball():
    global ball_speed_x, ball_speed_y
    ball.center = (screen_width/2, screen_height/2) # Reset ball position
    ball_speed_y = 0
    ball_speed_x = 0

def start_ball():
    global ball_speed_x, ball_speed_y
    ball_speed_y = 7 + random.choice((1, -1))
    ball_speed_x = 7 + random.choice((1, -1))

# Game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if ball_speed_x == 0:
                start_ball()
            if event.key == pygame.K_DOWN:
                player_speed += 7
            if event.key == pygame.K_UP:
                player_speed -= 7
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                player_speed -= 7
            if event.key == pygame.K_UP:
                player_speed += 7
    print(player_speed)
    # Move game elements
    player.centery += player_speed
    
    ball.centerx += ball_speed_x
    ball.centery += ball_speed_y
    if ball.top <= 0 or ball.bottom >= screen_height:
        ball_speed_y *= -1
    if ball.left <= 0:
        ball_speed_x *= -1
        player_score += 1
        reset_ball()
    if ball.right >= screen_width:
        ball_speed_x *= -1
        opponent_score += 1
        reset_ball()
    if ball.colliderect(player) or ball.colliderect(opponent):
        ball_speed_x *= -1

    # Move opponent paddle
    if opponent.top < ball.y:
        opponent.top += opponent_speed
    if opponent.bottom > ball.y:
        opponent.bottom -= opponent_speed

    # Draw game elements
    screen.fill(bg_color)
    pygame.draw.rect(screen, light_grey, player)
    pygame.draw.rect(screen, light_grey, opponent)
    pygame.draw.ellipse(screen, light_grey, ball)
    pygame.draw.aaline(screen, light_grey, (screen_width/2, 0), (screen_width/2, screen_height))

    # Draw scores
    player_text = game_font.render(f"{player_score}", False, light_grey)
    screen.blit(player_text, (screen_width/2 + 20, screen_height/2 - 16))
    opponent_text = game_font.render(f"{opponent_score}", False, light_grey)
    screen.blit(opponent_text, (screen_width/2 - 42, screen_height/2 - 16))

    # Update the display
    pygame.display.flip()
    pygame.time.Clock().tick(24)

