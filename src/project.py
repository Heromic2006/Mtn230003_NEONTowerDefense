import pygame
import math
import random

# Initialize pygame
pygame.init()

# Screen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tower Defense")

FPS = 60

# Colors
BLACK = (10, 10, 15)
NEON_GREEN = (0, 255, 150)
NEON_BLUE = (0, 200, 255)
NEON_RED = (255, 80, 80)
NEON_PURPLE = (200, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

FONT = pygame.font.SysFont("arial", 24)

# Path
PATH = [
    (0, HEIGHT // 2),
    (WIDTH // 4, HEIGHT // 2),
    (WIDTH // 4, HEIGHT // 3),
    (WIDTH // 2, HEIGHT // 3),
    (WIDTH // 2, HEIGHT // 1.5),
    (WIDTH * 0.75, HEIGHT // 1.5),
    (WIDTH * 0.75, HEIGHT // 2),
    (WIDTH, HEIGHT // 2)
]

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

#ENEMY
class Enemy:
    def __init__(self, enemy_type, wave):
        self.path = PATH
        self.index = 0
        self.x, self.y = self.path[0]

        scale = 1 + wave * 0.2

        if enemy_type == "goblin":
            self.speed = 3
            self.health = 40 * scale
            self.damage = 1
            self.gold = 5
            self.size = 8
            self.color = NEON_GREEN

        elif enemy_type == "medium":
            self.speed = 4
            self.health = 80 * scale
            self.damage = 2
            self.gold = 10
            self.size = 12
            self.color = NEON_BLUE

        elif enemy_type == "big":
            self.speed = 1.5
            self.health = 200 * scale
            self.damage = 5
            self.gold = 20
            self.size = 18
            self.color = NEON_RED

        elif enemy_type == "final":
            self.speed = 0.7
            self.health = 1000 * scale
            self.damage = 10
            self.gold = 100
            self.size = 30
            self.color = NEON_PURPLE

        self.max_health = self.health
        self.slow_factor = 1

    def move(self):
        if self.index >= len(self.path) - 1:
            return True

        target = self.path[self.index + 1]
        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = math.hypot(dx, dy)

        if dist < 5:
            self.index += 1
        else:
            self.x += (dx / dist) * self.speed * self.slow_factor
            self.y += (dy / dist) * self.speed * self.slow_factor

        return False

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.size)

#PROJECTILE
class Projectile:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.speed = 8

    def update(self, game):
        if self.target not in game.enemies:
            return True

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist < 5:
            self.target.health -= self.damage
            return True

        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed
        return False

    def draw(self, win):
        pygame.draw.circle(win, YELLOW, (int(self.x), int(self.y)), 3)

#TOWER
class Tower:
    def __init__(self, x, y, tower_type):
        self.x = x
        self.y = y
        self.type = tower_type
        self.cooldown = 0

        if tower_type == "sniper":
            self.range = 300
            self.damage = 50
            self.fire_rate = 90

        elif tower_type == "base":
            self.range = 150
            self.damage = 20
            self.fire_rate = 40

        elif tower_type == "slow":
            self.range = 120
            self.damage = 0
            self.fire_rate = 60

    def update(self, game):
        if self.type == "slow":
            for enemy in game.enemies:
                if distance((self.x, self.y), (enemy.x, enemy.y)) < self.range:
                    enemy.slow_factor = 0.5
            return

        if self.cooldown > 0:
            self.cooldown -= 1
            return

        targets = [e for e in game.enemies if distance((self.x, self.y), (e.x, e.y)) < self.range]
        if targets:
            target = max(targets, key=lambda e: e.index)
            game.projectiles.append(Projectile(self.x, self.y, target, self.damage))
            self.cooldown = self.fire_rate

    def draw(self, win):
        color = NEON_BLUE if self.type == "base" else NEON_RED if self.type == "sniper" else NEON_PURPLE
        pygame.draw.circle(win, color, (int(self.x), int(self.y)), 10)

#GAME
class Game:
    def __init__(self):
        self.enemies = []
        self.towers = []
        self.projectiles = []

        self.wave = 1
        self.spawn_timer = 0
        self.spawn_count = 0

        self.lives = 20
        self.gold = 150

        self.build_phase = True  # <-- key addition

    def start_wave(self):
        self.build_phase = False
        self.spawn_timer = 0
        self.spawn_count = 0

    def spawn_enemy(self):
        types = ["goblin", "medium", "big"]
        if self.wave % 5 == 0:
            types.append("final")
        self.enemies.append(Enemy(random.choice(types), self.wave))

    def update(self):
        if self.build_phase:
            return

        self.spawn_timer += 1
        if self.spawn_timer > 30 and self.spawn_count < 10 + self.wave:
            self.spawn_enemy()
            self.spawn_timer = 0
            self.spawn_count += 1

        # Reset slows
        for e in self.enemies:
            e.slow_factor = 1

        # Enemies
        for e in self.enemies[:]:
            if e.move():
                self.lives -= e.damage
                self.enemies.remove(e)
            elif e.health <= 0:
                self.gold += e.gold
                self.enemies.remove(e)

        # Towers
        for t in self.towers:
            t.update(self)

        # Projectiles
        for p in self.projectiles[:]:
            if p.update(self):
                self.projectiles.remove(p)

        # End of wave
        if self.spawn_count >= 10 + self.wave and not self.enemies:
            self.wave += 1
            self.build_phase = True

    def draw(self, win):
        win.fill(BLACK)

        pygame.draw.lines(win, WHITE, False, PATH, 3)

        for e in self.enemies:
            e.draw(win)

        for t in self.towers:
            t.draw(win)

        for p in self.projectiles:
            p.draw(win)

        # UI
        text = f"Wave: {self.wave}  Gold: {self.gold}  Lives: {self.lives}"
        win.blit(FONT.render(text, True, WHITE), (20, 20))

        if self.build_phase:
            msg = "BUILD PHASE - Press SPACE to start"
            win.blit(FONT.render(msg, True, NEON_GREEN), (WIDTH//2 - 200, 50))

        pygame.display.update()
#MAIN
def main():
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game.build_phase:
                    game.start_wave()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                if game.build_phase:
                    if event.button == 1 and game.gold >= 50:
                        game.towers.append(Tower(x, y, "base"))
                        game.gold -= 50

                    elif event.button == 3 and game.gold >= 75:
                        game.towers.append(Tower(x, y, "sniper"))
                        game.gold -= 75

        game.update()
        game.draw(WIN)

    pygame.quit()

if __name__ == "__main__":
    main()