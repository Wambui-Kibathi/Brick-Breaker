import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Set up the game window
WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker")
clock = pygame.time.Clock()

# Define colors
BLACK = (10, 10, 20)
WHITE = (240, 240, 255)
CYAN = (0, 220, 220)
PADDLE_COLOR = (80, 160, 255)
BALL_COLOR = (255, 220, 50)

# Six rows of bricks, each row has its own color
BRICK_COLORS = [
    (255, 70, 70),   # row 0 - Red
    (255, 140, 40),  # row 1 - Orange
    (255, 220, 40),  # row 2 - Yellow
    (60, 210, 80),   # row 3 - Green
    (60, 160, 255),  # row 4 - Blue
    (180, 80, 255)   # row 5 - Purple
]


