import pygame
import math
import random

pygame.init()

# SCREEN
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tower Defense")

FPS = 60

# COLORS
BLACK = (10, 10, 15)
NEON_GREEN = (0, 255, 150)
NEON_BLUE = (0, 200, 255)
NEON_RED = (255, 80, 80)
NEON_PURPLE = (200, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

FONT = pygame.font.SysFont("arial", 24)

# PATH
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

dist = distance

# PATH CHECK
def on_path(x, y):
    SAFE = 40
    for i in range(len(PATH) - 1):
        x1, y1 = PATH[i]
        x2, y2 = PATH[i + 1]
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            continue

        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        cx, cy = x1 + t * dx, y1 + t * dy

        if dist((x, y), (cx, cy)) < SAFE:
            return True
    return False


# ENEMY
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

        else:
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
        d = math.hypot(dx, dy)

        if d < 5:
            self.index += 1
        else:
            self.x += (dx / d) * self.speed * self.slow_factor
            self.y += (dy / d) * self.speed * self.slow_factor

        return False

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.size)

        # HEALTH BAR
        w = 40
        h = 5
        ratio = max(self.health / self.max_health, 0)

        pygame.draw.rect(win, (80, 0, 0), (self.x - 20, self.y - 25, w, h))
        pygame.draw.rect(win, (0, 255, 100), (self.x - 20, self.y - 25, w * ratio, h))


# PROJECTILE
class Projectile:
    def __init__(self, x, y, target, dmg):
        self.x = x
        self.y = y
        self.target = target
        self.dmg = dmg
        self.speed = 8

    def update(self, game):
        if self.target not in game.enemies:
            return True

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        d = math.hypot(dx, dy)

        if d < 5:
            self.target.health -= self.dmg
            return True

        self.x += (dx / d) * self.speed
        self.y += (dy / d) * self.speed
        return False

    def draw(self, win):
        pygame.draw.circle(win, YELLOW, (int(self.x), int(self.y)), 3)


# TOWER
class Tower:
    def __init__(self, x, y, ttype):
        self.x = x
        self.y = y
        self.type = ttype
        self.cooldown = 0

        if ttype == "sniper":
            self.range = 300
            self.damage = 50
            self.rate = 90
        elif ttype == "base":
            self.range = 150
            self.damage = 20
            self.rate = 40
        else:
            self.range = 120
            self.damage = 0
            self.rate = 60

    def update(self, game):
        if self.type == "slow":
            for e in game.enemies:
                if distance((self.x, self.y), (e.x, e.y)) < self.range:
                    e.slow_factor = 0.5
            return

        if self.cooldown > 0:
            self.cooldown -= 1
            return

        targets = [e for e in game.enemies if distance((self.x, self.y), (e.x, e.y)) < self.range]
        if targets:
            t = max(targets, key=lambda e: e.index)
            game.projectiles.append(Projectile(self.x, self.y, t, self.damage))
            self.cooldown = self.rate

    def draw(self, win):
        color = NEON_BLUE if self.type == "base" else NEON_RED if self.type == "sniper" else NEON_PURPLE
        pygame.draw.circle(win, color, (int(self.x), int(self.y)), 10)


# GAME
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

        self.build_phase = True

        # UI STATE
        self.selected = "base"
        self.selected_tower = None

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

        for e in self.enemies:
            e.slow_factor = 1

        for e in self.enemies[:]:
            if e.move():
                self.lives -= e.damage
                self.enemies.remove(e)
            elif e.health <= 0:
                self.gold += e.gold
                self.enemies.remove(e)

        for t in self.towers:
            t.update(self)

        for p in self.projectiles[:]:
            if p.update(self):
                self.projectiles.remove(p)

        if self.spawn_count >= 10 + self.wave and not self.enemies:
            self.wave += 1
            self.build_phase = True

    # ================= DRAW (UPDATED WITH FULL UI) =================
    def draw(self, win):
        win.fill(BLACK)

        pygame.draw.lines(win, WHITE, False, PATH, 3)

        for e in self.enemies:
            e.draw(win)

        for t in self.towers:
            t.draw(win)

        for p in self.projectiles:
            p.draw(win)

        # TOP UI
        ui = f"Wave: {self.wave}  Gold: {self.gold}  Lives: {self.lives}"
        win.blit(FONT.render(ui, True, WHITE), (20, 20))

        # BUILD TEXT
        if self.build_phase:
            msg = "BUILD PHASE - Press SPACE"
            win.blit(FONT.render(msg, True, NEON_GREEN), (WIDTH // 2 - 150, 50))

        # ================= BOTTOM HUD =================
        pygame.draw.rect(win, (20, 20, 30), (0, HEIGHT - 90, WIDTH, 90))

        opts = [("base", 60), ("sniper", 100), ("slow", 90)]
        x = 30

        for name, cost in opts:
            r = pygame.Rect(x, HEIGHT - 75, 150, 50)
            pygame.draw.rect(win, (60, 60, 80), r)

            if self.selected == name:
                pygame.draw.rect(win, YELLOW, r, 2)

            win.blit(FONT.render(f"{name} ${cost}", True, WHITE), (x + 10, HEIGHT - 60))
            x += 170

        # selected tower range
        if self.selected_tower:
            t = self.selected_tower
            pygame.draw.circle(win, (0, 200, 255),
                               (int(t.x), int(t.y)),
                               int(t.range), 2)

        pygame.display.update()


# MAIN
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
                mx, my = pygame.mouse.get_pos()

                # ===== UI CLICK CHECK =====
                if my > HEIGHT - 90:
                    opts = [("base", 60), ("sniper", 100), ("slow", 90)]
                    x = 30
                    for name, cost in opts:
                        rect = pygame.Rect(x, HEIGHT - 75, 150, 50)
                        if rect.collidepoint(mx, my):
                            game.selected = name
                        x += 170
                    continue

                # ===== SELECT TOWER =====
                clicked = False
                for t in game.towers:
                    if distance((mx, my), (t.x, t.y)) < 20:
                        game.selected_tower = t
                        clicked = True
                        break

                if clicked:
                    continue

                # ===== PLACE TOWER =====
                if game.build_phase:
                    cost_map = {"base": 60, "sniper": 100, "slow": 90}
                    cost = cost_map[game.selected]

                    if game.gold >= cost and not on_path(mx, my):
                        game.towers.append(Tower(mx, my, game.selected))
                        game.gold -= cost

        game.update()
        game.draw(WIN)

    pygame.quit()


if __name__ == "__main__":
    main()