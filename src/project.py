import pygame
import math
import random

pygame.init()

# SCREEN
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tower Defense - Enhanced")

FPS = 60

# COLORS
BLACK = (10, 10, 15)
NEON_GREEN = (0, 255, 150)
NEON_BLUE = (0, 200, 255)
NEON_RED = (255, 80, 80)
NEON_PURPLE = (200, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 80)

FONT = pygame.font.SysFont("arial", 20)

# PATH
PATH = [(0, HEIGHT // 2), (WIDTH // 4, HEIGHT // 2), (WIDTH // 4, HEIGHT // 3),
        (WIDTH // 2, HEIGHT // 3), (WIDTH // 2, HEIGHT // 1.5),
        (WIDTH * 0.75, HEIGHT // 1.5), (WIDTH * 0.75, HEIGHT // 2), (WIDTH, HEIGHT // 2)]

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def on_path(x, y):
    SAFE = 40
    for i in range(len(PATH) - 1):
        x1, y1 = PATH[i]; x2, y2 = PATH[i + 1]
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0: continue
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        cx, cy = x1 + t * dx, y1 + t * dy
        if distance((x, y), (cx, cy)) < SAFE: return True
    return False

# ENEMY
class Enemy:
    def __init__(self, enemy_type, wave):
        self.path = PATH
        self.index = 0
        self.x, self.y = self.path[0]
        
        # --- STAGE 4.3: WAVE SCALING ---
        difficulty_tier = wave // 5
        scale = (1 + difficulty_tier * 0.25)
        
        if enemy_type == "goblin":
            self.speed, self.health, self.damage, self.gold, self.size, self.color = 3.5, 40 * scale, 1, 10, 8, NEON_GREEN
        elif enemy_type == "medium":
            self.speed, self.health, self.damage, self.gold, self.size, self.color = 2.5, 100 * scale, 2, 25, 12, NEON_BLUE
        elif enemy_type == "tank":
            self.speed, self.health, self.damage, self.gold, self.size, self.color = 1.3, 250 * scale, 5, 50, 18, NEON_RED
        else: # Boss
            self.speed, self.health, self.damage, self.gold, self.size, self.color = 0.7, 1000 * scale, 10, 120, 30, NEON_PURPLE

        self.max_health = self.health
        self.slow_factor = 1

    def move(self):
        if self.index >= len(self.path) - 1: return True
        target = self.path[self.index + 1]
        dx, dy = target[0] - self.x, target[1] - self.y
        d = math.hypot(dx, dy)
        if d < 5: self.index += 1
        else:
            self.x += (dx / d) * self.speed * self.slow_factor
            self.y += (dy / d) * self.speed * self.slow_factor
        return False

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.size)
        w, h = 40, 5
        ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(win, (80, 0, 0), (self.x - 20, self.y - 25, w, h))
        pygame.draw.rect(win, (0, 255, 100), (self.x - 20, self.y - 25, w * ratio, h))

# PROJECTILE
class Projectile:
    def __init__(self, x, y, target, tower):
        self.x, self.y = x, y
        self.target = target
        # --- STAGE 4.1: PULL DYNAMIC DAMAGE ---
        self.dmg = tower.real_damage()
        self.speed = 10

    def update(self, game):
        if self.target not in game.enemies: return True
        dx, dy = self.target.x - self.x, self.target.y - self.y
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
        self.x, self.y, self.type = x, y, ttype
        self.cooldown = 0
        # --- STAGE 4.1: BASE STATS & LEVELS ---
        self.dmg_lvl, self.rng_lvl, self.spd_lvl = 0, 0, 0
        if ttype == "sniper":
            self.range, self.damage, self.rate, self.price = 300, 100, 120, 100
        elif ttype == "base":
            self.range, self.damage, self.rate, self.price = 150, 25, 45, 60
        else: # Slow
            self.range, self.damage, self.rate, self.price = 120, 0, 30, 90

    # --- STAGE 4.1: DYNAMIC CALC ---
    def real_range(self): return self.range * (1 + self.rng_lvl * 0.15)
    def real_damage(self): return self.damage * (1 + self.dmg_lvl * 0.30)
    def real_rate(self): return int(self.rate * (1 - self.spd_lvl * 0.15))

    def update(self, game):
        if self.type == "slow":
            for e in game.enemies:
                if distance((self.x, self.y), (e.x, e.y)) < self.real_range():
                    e.slow_factor = 0.5
            return
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        targets = [e for e in game.enemies if distance((self.x, self.y), (e.x, e.y)) < self.real_range()]
        if targets:
            t = max(targets, key=lambda e: e.index)
            game.projectiles.append(Projectile(self.x, self.y, t, self))
            self.cooldown = self.real_rate()

    def draw(self, win):
        color = NEON_BLUE if self.type == "base" else NEON_RED if self.type == "sniper" else NEON_PURPLE
        pygame.draw.circle(win, color, (int(self.x), int(self.y)), 10)

# GAME
class Game:
    def __init__(self):
        self.enemies, self.towers, self.projectiles = [], [], []
        self.wave, self.spawn_timer, self.spawn_count = 1, 0, 0
        self.lives, self.gold, self.pending_gold = 20, 150, 0
        self.build_phase, self.selected = True, "base"
        self.selected_tower, self.buttons = None, {}

    def start_wave(self):
        self.build_phase, self.spawn_timer, self.spawn_count = False, 0, 0

    def spawn_enemy(self):
        types = ["goblin", "medium"]
        if self.wave > 3: types.append("tank")
        if self.wave % 5 == 0: types.append("final")
        self.enemies.append(Enemy(random.choice(types), self.wave))

    def update(self):
        if self.build_phase: return
        self.spawn_timer += 1
        if self.spawn_timer > 30 and self.spawn_count < 10 + self.wave:
            self.spawn_enemy(); self.spawn_timer = 0; self.spawn_count += 1
        for e in self.enemies: e.slow_factor = 1
        for e in self.enemies[:]:
            if e.move():
                self.lives -= e.damage; self.enemies.remove(e)
            elif e.health <= 0:
                # --- STAGE 4.3: PENDING GOLD ---
                self.pending_gold += int(e.gold); self.enemies.remove(e)
        for t in self.towers: t.update(self)
        for p in self.projectiles[:]:
            if p.update(self): self.projectiles.remove(p)
        if self.spawn_count >= 10 + self.wave and not self.enemies:
            # Wave End
            self.gold += (self.pending_gold + 50)
            self.pending_gold = 0; self.wave += 1; self.build_phase = True

    # --- STAGE 4.2: UPGRADE PANEL ---
    def draw_upgrade_ui(self, win):
        t = self.selected_tower
        panel = pygame.Rect(WIDTH - 270, 120, 250, 260)
        pygame.draw.rect(win, GRAY, panel)
        self.close_btn = pygame.Rect(WIDTH - 40, 120, 20, 20)
        pygame.draw.rect(win, NEON_RED, self.close_btn)
        
        self.buttons = {
            "dmg": pygame.Rect(WIDTH - 250, 170, 220, 40),
            "rng": pygame.Rect(WIDTH - 250, 220, 220, 40),
            "spd": pygame.Rect(WIDTH - 250, 270, 220, 40)
        }
        for key, rect in self.buttons.items():
            pygame.draw.rect(win, (40, 40, 60), rect)
            lvl = getattr(t, f"{key}_lvl")
            cost = 50 * (lvl + 1)
            win.blit(FONT.render(f"Upgrade {key.upper()} L{lvl} (${cost})", True, WHITE), (rect.x + 5, rect.y + 10))

    def draw(self, win):
        win.fill(BLACK)
        pygame.draw.lines(win, WHITE, False, PATH, 3)
        for e in self.enemies: e.draw(win)
        for t in self.towers: t.draw(win)
        for p in self.projectiles: p.draw(win)
        
        ui = f"Wave: {self.wave}  Gold: {self.gold} (+{self.pending_gold})  Lives: {self.lives}"
        win.blit(FONT.render(ui, True, WHITE), (20, 20))
        if self.build_phase: win.blit(FONT.render("BUILD PHASE - SPACE TO START", True, NEON_GREEN), (WIDTH//2-150, 50))

        # BOTTOM HUD
        pygame.draw.rect(win, (20, 20, 30), (0, HEIGHT - 90, WIDTH, 90))
        opts, x = [("base", 60), ("sniper", 100), ("slow", 90)], 30
        for name, cost in opts:
            r = pygame.Rect(x, HEIGHT - 75, 150, 50)
            pygame.draw.rect(win, (60, 60, 80), r)
            if self.selected == name: pygame.draw.rect(win, YELLOW, r, 2)
            win.blit(FONT.render(f"{name} ${cost}", True, WHITE), (x+10, HEIGHT-60)); x += 170

        if self.selected_tower:
            pygame.draw.circle(win, NEON_BLUE, (int(self.selected_tower.x), int(self.selected_tower.y)), int(self.selected_tower.real_range()), 2)
            self.draw_upgrade_ui(win)
        pygame.display.update()

def main():
    clock, game, running = pygame.time.Clock(), Game(), True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game.build_phase: game.start_wave()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # --- STAGE 4.2: CLICK LOGIC ---
                if game.selected_tower:
                    if game.close_btn.collidepoint(mx, my): game.selected_tower = None; continue
                    for key, rect in game.buttons.items():
                        if rect.collidepoint(mx, my):
                            t = game.selected_tower
                            lvl = getattr(t, f"{key}_lvl")
                            cost = 50 * (lvl + 1)
                            if game.gold >= cost: game.gold -= cost; setattr(t, f"{key}_lvl", lvl + 1)
                            continue

                if my > HEIGHT - 90:
                    for i, (n, c) in enumerate([("base", 60), ("sniper", 100), ("slow", 90)]):
                        if pygame.Rect(30 + i*170, HEIGHT-75, 150, 50).collidepoint(mx, my): game.selected = n
                    continue

                t_clicked = False
                for t in game.towers:
                    if distance((mx, my), (t.x, t.y)) < 20: game.selected_tower = t; t_clicked = True; break
                
                if not t_clicked and game.build_phase and not on_path(mx, my):
                    costs = {"base": 60, "sniper": 100, "slow": 90}
                    if game.gold >= costs[game.selected]:
                        game.towers.append(Tower(mx, my, game.selected))
                        game.gold -= costs[game.selected]

        game.update(); game.draw(WIN)
    pygame.quit()

if __name__ == "__main__": main()