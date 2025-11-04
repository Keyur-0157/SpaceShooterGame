"""
Retro 2D Space Shooter
Self-contained Pygame script. No external image files required — sprites are built from tiny pixel maps and scaled up.

Controls:
  - Left / A : move left
  - Right / D: move right
  - Space     : shoot
  - Enter     : start / restart
  - Esc       : quit

How to run:
  1. Install Python 3.8+ (3.10+ recommended).
  2. Install pygame:     pip install pygame
  3. Save this file as space_shooter.py and run:   python space_shooter.py

Enjoy! - Code written for easy reading and customization.
"""

import pygame
import random
import sys
from pygame.locals import *

# ---------- Configuration ----------
WIDTH, HEIGHT = 480, 720
FPS = 60
SCALE = 5              # scale factor for pixel-art sprites (change to make sprites bigger/smaller)
PLAYER_SPEED = 300     # pixels per second
BULLET_SPEED = 480
ENEMY_SPEED = 80
ENEMY_SPAWN_INTERVAL = 0.9
MAX_ENEMIES = 6

# Optional developer credit (set to empty string to hide)
DEVELOPER_CREDIT = "Developed by Keyur Padia"

# ---------- Utility: build pixel sprites from text maps ----------

def sprite_from_map(map_rows, palette, scale=SCALE):
    """Create a pygame.Surface from a list of strings. Each char maps to a palette color.
    ' ' (space) means transparent.
    """
    h = len(map_rows)
    w = max(len(r) for r in map_rows)
    surface = pygame.Surface((w, h), flags=SRCALPHA, depth=32)
    surface.fill((0, 0, 0, 0))
    for y, row in enumerate(map_rows):
        for x, ch in enumerate(row):
            if ch == ' ':
                continue
            color = palette.get(ch, (255, 0, 255))
            surface.set_at((x, y), color)
    # scale nearest neighbor to keep pixel-art crisp
    surf_scaled = pygame.transform.scale(surface, (w * scale, h * scale))
    return surf_scaled

# ---------- Pixel maps and palettes ----------
PLAYER_MAP = [
    "     r     ",
    "    rrr    ",
    "   rccrr   ",
    "  rrrrrr   ",
    " rrrrrrrr  ",
    "rrrrddddrrr",
    "rrr rrr rrr",
    "   rrrr    ",
    "   rrrr    ",
    "    rr     ",
    "    ff     ",
    "     f     ",
]
PLAYER_PALETTE = {
    'r': (220, 70, 30),   # main red/orange body
    'd': (170, 50, 25),   # darker red for shading
    'c': (56, 140, 210),  # cockpit blue
    'f': (255, 170, 40),  # engine flame
}

ENEMY_MAP = [
    "  xx  ",
    " xxxxx ",
    "xxyyyx",
    " xyyx ",
]
ENEMY_PALETTE = {
    'x': (18, 100, 40),
    'y': (100, 220, 100),
}

ASTEROID_MAP = [
    " zzz ",
    "zzzzzz",
    " zzz ",
]
AST_PALETTE = {'z': (200, 120, 40)}

BULLET_MAP = ["o"]
BULLET_PALETTE = {'o': (255, 200, 50)}

# ---------- Game objects ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 40))
        self.speed = PLAYER_SPEED
        self.shoot_cooldown = 0.18
        self._cool = 0

    def update(self, dt, keys):
        move = 0
        if keys[K_LEFT] or keys[K_a]:
            move -= 1
        if keys[K_RIGHT] or keys[K_d]:
            move += 1
        self.rect.x += move * self.speed * dt
        # clamp
        if self.rect.left < 8:
            self.rect.left = 8
        if self.rect.right > WIDTH - 8:
            self.rect.right = WIDTH - 8
        if self._cool > 0:
            self._cool -= dt

    def can_shoot(self):
        return self._cool <= 0

    def shoot(self):
        self._cool = self.shoot_cooldown


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image, dy=-BULLET_SPEED):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.dy = dy

    def update(self, dt):
        self.rect.y += self.dy * dt
        if self.rect.bottom < -10 or self.rect.top > HEIGHT + 10:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, image, x, y, speed=ENEMY_SPEED):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.hp = 1

    def update(self, dt):
        self.rect.y += self.speed * dt
        if self.rect.top > HEIGHT + 20:
            self.kill()


# ---------- Helper drawing: stars and decorative items ----------

def build_starfield(count=80):
    stars = []
    for _ in range(count):
        x = random.randrange(0, WIDTH)
        y = random.randrange(0, HEIGHT)
        size = random.choice([1, 1, 2])
        speed = random.uniform(5, 25)
        stars.append([x, y, size, speed])
    return stars


def update_starfield(stars, dt):
    for s in stars:
        s[1] += s[3] * dt
        if s[1] > HEIGHT:
            s[0] = random.randrange(0, WIDTH)
            s[1] = -2
            s[3] = random.uniform(5, 25)


def draw_starfield(surface, stars):
    for s in stars:
        if s[2] == 1:
            surface.fill((220, 220, 220), (int(s[0]), int(s[1]), 1, 1))
        else:
            pygame.draw.rect(surface, (180, 180, 180), (int(s[0]), int(s[1]), 2, 2))


# Decorative shapes drawn as scaled pixel sprites (planet, saucer, comet)

PLANET_MAP = [
    "  ppp  ",
    " ppppp ",
    "ppppppp",
    " ppppp ",
    "  ppp  "
]
PLANET_PALETTE = {'p': (200, 80, 80)}

SAUCER_MAP = [
    "  sss  ",
    " ssssss",
    "sssss  "
]
SAUCER_PALETTE = {'s': (100, 160, 210)}

COMET_MAP = [
    " c   ",
    "ccc  ",
    " ccc "
]
COMET_PALETTE = {'c': (210, 140, 80)}

# ---------- Game class to hold state ----------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Retro Space Shooter")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self.title_font = pygame.font.Font(pygame.font.get_default_font(), 48)

        # build sprites
        self.player_sprite = sprite_from_map(PLAYER_MAP, PLAYER_PALETTE)
        self.enemy_sprite = sprite_from_map(ENEMY_MAP, ENEMY_PALETTE)
        self.asteroid_sprite = sprite_from_map(ASTEROID_MAP, AST_PALETTE)
        self.bullet_sprite = sprite_from_map(BULLET_MAP, BULLET_PALETTE, scale=3)
        self.planet_sprite = sprite_from_map(PLANET_MAP, PLANET_PALETTE)
        self.saucer_sprite = sprite_from_map(SAUCER_MAP, SAUCER_PALETTE)
        self.comet_sprite = sprite_from_map(COMET_MAP, COMET_PALETTE)

        # groups
        self.player_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()

        self.player = Player(self.player_sprite)
        self.player_group.add(self.player)

        # stars
        self.stars = build_starfield(120)

        # timers and state
        self.enemy_spawn_timer = 0
        self.score = 0
        self.state = 'MENU'  # MENU, PLAYING, GAME_OVER
        self.game_over_timer = 0

        # decorative positions (used in menus)
        self.decor_positions = [
            (60, 80, 'planet'),
            (WIDTH - 70, 70, 'saucer'),
            (WIDTH - 90, HEIGHT - 120, 'comet'),
        ]

    def reset(self):
        self.enemy_group.empty()
        self.bullet_group.empty()
        self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 40)
        self.score = 0
        self.enemy_spawn_timer = 0

    def spawn_enemy(self):
        if len(self.enemy_group) >= MAX_ENEMIES:
            return
        x = random.randint(30, WIDTH - 30)
        y = -30
        e = Enemy(self.enemy_sprite, x, y, speed=ENEMY_SPEED + random.uniform(-10, 40))
        self.enemy_group.add(e)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    if self.state == 'MENU' and event.key == K_RETURN:
                        self.state = 'PLAYING'
                        self.reset()
                    if self.state == 'GAME_OVER' and event.key == K_RETURN:
                        self.state = 'PLAYING'
                        self.reset()

            keys = pygame.key.get_pressed()

            # update
            update_starfield(self.stars, dt)
            if self.state == 'PLAYING':
                self.update_playing(dt, keys)
            # render
            self.draw()

        pygame.quit()
        sys.exit()

    def update_playing(self, dt, keys):
        self.player.update(dt, keys)
        self.enemy_group.update(dt)
        self.bullet_group.update(dt)

        # shooting
        if (keys[K_SPACE] or keys[K_UP]) and self.player.can_shoot():
            b = Bullet(self.player.rect.centerx, self.player.rect.top - 6, self.bullet_sprite)
            self.bullet_group.add(b)
            self.player.shoot()

        # collisions: bullet hits enemy
        hits = pygame.sprite.groupcollide(self.enemy_group, self.bullet_group, True, True)
        if hits:
            for en in hits:
                self.score += 20

        # enemy hits player
        for e in self.enemy_group:
            if e.rect.colliderect(self.player.rect):
                # go to game over
                self.state = 'GAME_OVER'
                self.game_over_timer = 0

        # spawn enemies
        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL:
            self.enemy_spawn_timer = 0
            self.spawn_enemy()

    def draw(self):
        self.screen.fill((20, 28, 36))
        draw_starfield(self.screen, self.stars)

        if self.state == 'MENU':
            self.draw_menu()
        elif self.state == 'PLAYING':
            self.draw_playing()
        elif self.state == 'GAME_OVER':
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self):
        # Title
        title_surf = self.title_font.render('SPACE SHOOTER', True, (240, 230, 210))
        title_rect = title_surf.get_rect(center=(WIDTH//2, 80))
        # simple shadow
        shadow = self.title_font.render('SPACE SHOOTER', True, (40, 30, 30))
        self.screen.blit(shadow, shadow.get_rect(center=(title_rect.centerx+3, title_rect.centery+3)))
        self.screen.blit(title_surf, title_rect)

        # decorative sprites
        self.screen.blit(self.player_sprite, self.player_sprite.get_rect(center=(WIDTH//2, HEIGHT//2 - 10)))
        for x,y,t in self.decor_positions:
            if t == 'planet':
                self.screen.blit(self.planet_sprite, self.planet_sprite.get_rect(center=(x,y)))
            elif t == 'saucer':
                self.screen.blit(self.saucer_sprite, self.saucer_sprite.get_rect(center=(x,y)))
            elif t == 'comet':
                self.screen.blit(self.comet_sprite, self.comet_sprite.get_rect(center=(x,y)))

        # start hint
        hint = self.font.render('Press ENTER to start', True, (220,220,220))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH//2, HEIGHT - 120)))
        # developer credit optional
        if DEVELOPER_CREDIT:
            cred = self.font.render(DEVELOPER_CREDIT, True, (180,180,180))
            self.screen.blit(cred, cred.get_rect(center=(WIDTH//2, HEIGHT - 40)))

    def draw_playing(self):
        # sprites
        self.enemy_group.draw(self.screen)
        self.bullet_group.draw(self.screen)
        self.player_group.draw(self.screen)

        # HUD
        score_s = self.font.render(f'SCORE: {self.score}', True, (240,240,230))
        self.screen.blit(score_s, (16, 12))

    def draw_game_over(self):
        # draw some decorative objects in corners
        self.screen.blit(self.planet_sprite, self.planet_sprite.get_rect(topleft=(20, 20)))
        self.screen.blit(self.saucer_sprite, self.saucer_sprite.get_rect(topright=(WIDTH - 20, 20)))
        # comet trailing in lower right
        self.screen.blit(self.comet_sprite, self.comet_sprite.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20)))

        # big text
        over = self.title_font.render('GAME OVER', True, (240,230,210))
        over_rect = over.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        shadow = self.title_font.render('GAME OVER', True, (40,30,30))
        self.screen.blit(shadow, shadow.get_rect(center=(over_rect.centerx+3, over_rect.centery+3)))
        self.screen.blit(over, over_rect)

        score_lbl = self.font.render(f'SCORE: {self.score}', True, (240,240,230))
        self.screen.blit(score_lbl, score_lbl.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))

        # decorative stars/arcs
        for i in range(6):
            x = 40 + i * 60
            y = HEIGHT//2 + 120 + (i % 2) * 10
            pygame.draw.rect(self.screen, (180,180,180), (x, y, 3, 3))

        # replaced 'Developed by' removed from game over screen by default: user asked it removed
        # show restart hint
        hint = self.font.render('Press ENTER to play again', True, (200,200,200))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH//2, HEIGHT - 80)))


if __name__ == '__main__':
    Game().run()
