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

# ── Game constants ─────────────────────────────────────────────────────────────
PADDLE_WIDTH    = 120
PADDLE_HEIGHT   = 14
PADDLE_SPEED    = 7
PADDLE_Y        = SCREEN_HEIGHT - 60

BALL_RADIUS     = 9
BALL_START_SPEED = 5          # pixels per frame (speed magnitude)

BRICK_COLS      = 10
BRICK_ROWS      = 6
BRICK_WIDTH     = 68
BRICK_HEIGHT    = 24
BRICK_GAP       = 6
BRICK_TOP_OFFSET = 80         # pixels from the top of the screen

# ── Fonts ──────────────────────────────────────────────────────────────────────
font_large  = pygame.font.SysFont("consolas", 52, bold=True)
font_medium = pygame.font.SysFont("consolas", 28)
font_small  = pygame.font.SysFont("consolas", 20)

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: draw a rounded rectangle (pygame < 2.x doesn't have draw.rect radius)
# ══════════════════════════════════════════════════════════════════════════════
def draw_rounded_rect(surface, colour, rect, radius=8):
    pygame.draw.rect(surface, colour, rect, border_radius=radius)


# ══════════════════════════════════════════════════════════════════════════════
#  CLASS: Paddle
# ══════════════════════════════════════════════════════════════════════════════
class Paddle:
    def __init__(self):
        self.reset()

    def reset(self):
        # Start the paddle in the horizontal centre of the screen
        self.x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
        self.y = PADDLE_Y
        self.width  = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT]:
            self.x += PADDLE_SPEED

        # Keep paddle inside the screen
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))

    def draw(self, surface):
        draw_rounded_rect(surface, PADDLE_COL, self.rect, radius=7)
        # Shiny highlight strip on top of the paddle
        highlight = pygame.Rect(self.x + 8, self.y + 3, self.width - 16, 4)
        pygame.draw.rect(surface, WHITE, highlight, border_radius=3)


# ══════════════════════════════════════════════════════════════════════════════
#  CLASS: Ball
# ══════════════════════════════════════════════════════════════════════════════
class Ball:
    def __init__(self, paddle):
        self.radius = BALL_RADIUS
        self.reset(paddle)

    def reset(self, paddle):
        # Sit the ball on top of the paddle before launch
        self.x = paddle.x + paddle.width // 2
        self.y = paddle.y - self.radius - 2
        self.launched = False
        self.speed    = BALL_START_SPEED
        # Start moving at a random upward angle
        angle_bias = random.choice([-1, 1]) * random.uniform(2, 4)
        self.vx = angle_bias
        self.vy = -self.speed

    def launch(self):
        self.launched = True

    def update(self, paddle, bricks):
        """Move the ball and handle all collisions. Returns 'dead' if fell off."""

        if not self.launched:
            # Stick to the paddle until SPACE is pressed
            self.x = paddle.x + paddle.width // 2
            self.y = paddle.y - self.radius - 2
            return None

        self.x += self.vx
        self.y += self.vy

        # ── Wall collisions ────────────────────────────────────────────────────
        if self.x - self.radius <= 0:
            self.x  = self.radius
            self.vx = abs(self.vx)           # bounce right

        if self.x + self.radius >= SCREEN_WIDTH:
            self.x  = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx)          # bounce left

        if self.y - self.radius <= 0:
            self.y  = self.radius
            self.vy = abs(self.vy)           # bounce down

        # ── Fell below the screen ──────────────────────────────────────────────
        if self.y - self.radius > SCREEN_HEIGHT:
            return "dead"

        # ── Paddle collision ───────────────────────────────────────────────────
        ball_rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2,      self.radius * 2
        )
        if ball_rect.colliderect(paddle.rect) and self.vy > 0:
            self.vy = -abs(self.vy)          # bounce upward

            # Vary the horizontal angle based on where the ball hits the paddle
            # Hit the edge → sharp angle; hit the centre → gentle angle
            hit_pos  = (self.x - paddle.x) / paddle.width  # 0.0 … 1.0
            offset   = (hit_pos - 0.5) * 2                 # -1.0 … +1.0
            self.vx  = offset * self.speed

            # Make sure the ball always has some horizontal movement
            if abs(self.vx) < 1:
                self.vx = 1 if self.vx >= 0 else -1

        # ── Brick collisions ───────────────────────────────────────────────────
        broken = None
        for brick in bricks:
            if not brick.alive:
                continue
            if ball_rect.colliderect(brick.rect):
                brick.alive = False
                broken = brick

                # Work out which face of the brick we hit and reflect accordingly
                overlap_left   = (ball_rect.right)  - brick.rect.left
                overlap_right  = brick.rect.right   - ball_rect.left
                overlap_top    = (ball_rect.bottom) - brick.rect.top
                overlap_bottom = brick.rect.bottom  - ball_rect.top

                min_overlap = min(overlap_left, overlap_right,
                                  overlap_top,  overlap_bottom)

                if min_overlap in (overlap_top, overlap_bottom):
                    self.vy = -self.vy
                else:
                    self.vx = -self.vx

                break   # only break one brick per frame

        return broken   # None = nothing special; Brick object = one broken

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    def draw(self, surface):
        pygame.draw.circle(surface, BALL_COL,   self.pos, self.radius)
        pygame.draw.circle(surface, WHITE,       self.pos, self.radius, 2)
        # Small highlight spot
        pygame.draw.circle(surface, WHITE,
                            (int(self.x) - 3, int(self.y) - 3), 3)


# ══════════════════════════════════════════════════════════════════════════════
#  CLASS: Brick
# ══════════════════════════════════════════════════════════════════════════════
class Brick:
    def __init__(self, row, col):
        # Calculate pixel position from grid row/col
        total_grid_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
        start_x = (SCREEN_WIDTH - total_grid_width) // 2

        self.rect = pygame.Rect(
            start_x + col * (BRICK_WIDTH + BRICK_GAP),
            BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_GAP),
            BRICK_WIDTH,
            BRICK_HEIGHT
        )
        self.colour = BRICK_COLOURS[row % len(BRICK_COLOURS)]
        self.alive  = True

    def draw(self, surface):
        if not self.alive:
            return
        draw_rounded_rect(surface, self.colour, self.rect, radius=5)
        # Shine on top edge
        shine = pygame.Rect(self.rect.x + 4, self.rect.y + 3,
                            self.rect.width - 8, 4)
        shine_col = tuple(min(255, c + 60) for c in self.colour)
        pygame.draw.rect(surface, shine_col, shine, border_radius=2)


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCTION: build a fresh grid of bricks
# ══════════════════════════════════════════════════════════════════════════════
def make_bricks():
    return [Brick(row, col)
            for row in range(BRICK_ROWS)
            for col in range(BRICK_COLS)]


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCTION: draw a semi-transparent dark overlay (for menus)
# ══════════════════════════════════════════════════════════════════════════════
def draw_overlay(surface, alpha=160):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCTION: centred text helper
# ══════════════════════════════════════════════════════════════════════════════
def draw_centred_text(surface, text, font, colour, y):
    rendered = font.render(text, True, colour)
    rect = rendered.get_rect(centerx=SCREEN_WIDTH // 2, y=y)
    surface.blit(rendered, rect)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # ── Game state ─────────────────────────────────────────────────────────────
    paddle = Paddle()
    bricks = make_bricks()
    ball   = Ball(paddle)

    score      = 0
    lives      = 3
    level      = 1

    # States: "start", "playing", "game_over", "win"
    state = "start"

    # ── Particle list for brick-break effect ───────────────────────────────────
    particles = []   # each particle: [x, y, vx, vy, radius, colour, lifetime]

    def spawn_particles(brick):
        for _ in range(10):
            particles.append([
                brick.rect.centerx, brick.rect.centery,
                random.uniform(-3, 3), random.uniform(-4, 0.5),
                random.randint(3, 6),
                brick.colour,
                random.randint(20, 40)
            ])

    def update_particles():
        for p in particles:
            p[0] += p[2]   # x
            p[1] += p[3]   # y
            p[3] += 0.2    # gravity
            p[6] -= 1      # lifetime
        particles[:] = [p for p in particles if p[6] > 0]

    def draw_particles(surface):
        for p in particles:
            alpha_ratio = p[6] / 40
            r = max(1, int(p[4] * alpha_ratio))
            pygame.draw.circle(surface, p[5], (int(p[0]), int(p[1])), r)

    # ── Main loop ──────────────────────────────────────────────────────────────
    running = True
    while running:

        # ── Events ─────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_SPACE:
                    if state == "start":
                        state = "playing"
                        ball.launch()

                    elif state == "playing" and not ball.launched:
                        ball.launch()

                    elif state in ("game_over", "win"):
                        # Restart the game completely
                        paddle  = Paddle()
                        bricks  = make_bricks()
                        ball    = Ball(paddle)
                        score   = 0
                        lives   = 3
                        level   = 1
                        particles.clear()
                        state   = "playing"
                        ball.launch()

        # ── Update ─────────────────────────────────────────────────────────────
        if state == "playing":
            keys = pygame.key.get_pressed()
            paddle.move(keys)

            result = ball.update(paddle, bricks)

            if result == "dead":
                lives -= 1
                if lives <= 0:
                    state = "game_over"
                else:
                    # Reset ball onto paddle; player must press SPACE to relaunch
                    ball.reset(paddle)

            elif result is not None:
                # A brick was broken
                spawn_particles(result)
                score += 10

            update_particles()

            # Check if all bricks are gone
            if all(not b.alive for b in bricks):
                state = "win"

        # ── Draw ───────────────────────────────────────────────────────────────
        screen.fill(BLACK)

        # Subtle grid background
        for gx in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(screen, (20, 20, 35), (gx, 0), (gx, SCREEN_HEIGHT))
        for gy in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, (20, 20, 35), (0, gy), (SCREEN_WIDTH, gy))

        for brick in bricks:
            brick.draw(screen)

        draw_particles(screen)
        paddle.draw(screen)
        ball.draw(screen)

        # HUD – score and lives
        score_text = font_small.render(f"SCORE: {score}", True, WHITE)
        lives_text = font_small.render(f"LIVES: {'● ' * lives}", True, CYAN)
        level_text = font_small.render(f"LEVEL: {level}", True, WHITE)
        screen.blit(score_text, (14, 14))
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 14))
        screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 14, 14))

        # Thin divider under HUD
        pygame.draw.line(screen, (40, 40, 60),
                         (0, 46), (SCREEN_WIDTH, 46), 1)

        # ── State overlays ──────────────────────────────────────────────────────
        if state == "start":
            draw_overlay(screen, 140)
            draw_centred_text(screen, "BRICK BREAKER", font_large, CYAN, 190)
            draw_centred_text(screen, "Use  ←  →  to move the paddle", font_small, WHITE, 275)
            draw_centred_text(screen, "Don't let the ball fall!", font_small, WHITE, 305)
            draw_centred_text(screen, "Press  SPACE  to start", font_medium, BALL_COL, 365)

        elif state == "playing" and not ball.launched:
            draw_centred_text(screen, "Press  SPACE  to launch", font_small, BALL_COL,
                              SCREEN_HEIGHT - 30)

        elif state == "game_over":
            draw_overlay(screen, 160)
            draw_centred_text(screen, "GAME OVER", font_large, (255, 70, 70), 200)
            draw_centred_text(screen, f"Final Score: {score}", font_medium, WHITE, 285)
            draw_centred_text(screen, "Press  SPACE  to play again", font_small, BALL_COL, 345)

        elif state == "win":
            draw_overlay(screen, 160)
            draw_centred_text(screen, "YOU WIN!", font_large, (60, 220, 80), 200)
            draw_centred_text(screen, f"Score: {score}", font_medium, WHITE, 285)
            draw_centred_text(screen, "Press  SPACE  to play again", font_small, BALL_COL, 345)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
