import pygame
import math
import random


pygame.init()


WIDTH, HEIGHT = 1600, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon TD - Final Stable")


FPS = 60


# Colors
BLACK = (10,10,15)
WHITE = (240,240,240)
GREEN = (0,255,150)
RED = (255,80,80)
BLUE = (0,200,255)
PURPLE = (200,0,255)
YELLOW = (255,255,0)
GRAY = (60,60,80)


FONT = pygame.font.SysFont("arial", 20)
BIG = pygame.font.SysFont("arial", 60)


# ================= PATH =================
PATH = [
    (0, HEIGHT//2),
    (WIDTH//5, HEIGHT//2),
    (WIDTH//5, HEIGHT//3),
    (WIDTH//2, HEIGHT//3),
    (WIDTH//2, HEIGHT//1.6),
    (WIDTH*0.75, HEIGHT//1.6),
    (WIDTH*0.75, HEIGHT//2),
    (WIDTH, HEIGHT//2)
]


def dist(a,b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def on_path(x,y):
    SAFE = 40
    for i in range(len(PATH)-1):
        x1,y1 = PATH[i]
        x2,y2 = PATH[i+1]
        dx,dy = x2-x1,y2-y1
        if dx==dy==0: continue
        t = max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
        cx,cy = x1+t*dx,y1+t*dy
        if dist((x,y),(cx,cy))<SAFE:
            return True
    return False


# ================= ENEMY =================
class Enemy:
    def __init__(self, wave, enemy_type):
        self.i = 0
        self.x, self.y = PATH[0]
        self.type = enemy_type


        if self.type == "small":
            self.base_speed = 3.8
            self.max_health = 40
            self.size = 5
            self.color = YELLOW
            self.gold = 10
        elif self.type == "medium":
            self.base_speed = 2.3
            self.max_health = 100
            self.size = 10
            self.color = GREEN
            self.gold = 25
        elif self.type == "tank":
            self.base_speed = 1.3
            self.max_health = 180
            self.size = 15
            self.color = RED
            self.gold = 50
        else: # Boss
            self.base_speed = 0.6
            self.max_health = 450
            self.size = 20
            self.color = PURPLE
            self.gold = 120


        difficulty_tier = wave // 5
        self.max_health *= (1 + difficulty_tier * 0.25)
        self.health = self.max_health
        self.base_speed *= (1 + difficulty_tier * 0.05)


        self.speed = self.base_speed
        self.slow = 0


    def move(self):
        if self.slow > 0:
            self.slow -= 1
            self.speed = self.base_speed * 0.5
        else:
            self.speed = self.base_speed


        if self.i >= len(PATH)-1:
            return True


        tx,ty = PATH[self.i+1]
        dx,dy = tx-self.x, ty-self.y
        d = math.hypot(dx,dy)


        if d < 5:
            self.i += 1
        else:
            self.x += dx/d * self.speed
            self.y += dy/d * self.speed
        return False


    def draw(self):
        pygame.draw.circle(WIN, self.color, (int(self.x),int(self.y)), self.size)
        w = 40
        r = self.health/self.max_health
        pygame.draw.rect(WIN,(80,0,0),(self.x-20,self.y-25,w,5))
        pygame.draw.rect(WIN,(0,255,100),(self.x-20,self.y-25,w*r,5))


# ================= PROJECTILE =================
class Projectile:
    def __init__(self,x,y,tower,target):
        self.x,self.y = x,y
        self.t = target
        self.speed = 12
        self.damage = tower.real_damage()


    def update(self):
        if not self.t or self.t.health <= 0:
            return True
        dx,dy = self.t.x-self.x, self.t.y-self.y
        d = math.hypot(dx,dy)
        if d < 6:
            self.t.health -= self.damage
            return True
        self.x += dx/d*self.speed
        self.y += dy/d*self.speed
        return False


    def draw(self):
        pygame.draw.circle(WIN,YELLOW,(int(self.x),int(self.y)),3)


# ================= TOWER =================
class Tower:
    def __init__(self,x,y,t):
        self.x,self.y = x,y
        self.type = t
        self.cd = 0
        self.range = 130
        self.damage = 20
        self.fire_rate = 60
        self.price = 60


        if t=="sniper":
            self.range = 260
            self.damage = 100
            self.fire_rate = 180
            self.price = 100
        if t=="slow":
            self.range = 120
            self.damage = 0
            self.fire_rate = 20
            self.price = 90


        self.dmg_lvl = 0
        self.rng_lvl = 0
        self.spd_lvl = 0


    def real_range(self): return self.range * (1 + self.rng_lvl*0.10)
    def real_damage(self): return self.damage * (1 + self.dmg_lvl*0.25)
    def real_cd(self): return int(self.fire_rate * (1 - self.spd_lvl*0.15))


    def draw(self):
        col = BLUE if self.type=="base" else RED if self.type=="sniper" else PURPLE
        pygame.draw.circle(WIN,(0,0,0),(int(self.x),int(self.y)),13)
        pygame.draw.circle(WIN,col,(int(self.x),int(self.y)),10)


# ================= GAME =================
class Game:
    def __init__(self):
        self.reset()


    def reset(self):
        self.towers=[]
        self.enemies=[]
        self.proj=[]
        self.gold = 150
        self.pending_gold = 0
        self.lives = 30
        self.selected = "base"
        self.selected_tower = None
        self.ui_open = False
        self.wave = 0
        self.spawned = 0
        self.timer = 0
        self.wave_size = 6
        self.running = False
        self.placing = True
        self.game_over = False
        self.auto_run = False
        self.upgrade_close_rect = None
        self.restart_rect = pygame.Rect(0,0,0,0)
        self.auto_rect = pygame.Rect(WIDTH-310, HEIGHT-80, 140, 50)


    def start(self):
        self.running=True
        self.placing=False


    def can_place(self,x,y):
        if on_path(x,y): return False
        for t in self.towers:
            if dist((x,y),(t.x,t.y))<45: return False
        return True


    def get_enemy_type(self):
        w = self.wave
        if w < 3: return "small"
        elif w < 6: return random.choice(["small","medium"])
        elif w < 10: return random.choice(["small","medium","tank"])
        else: return random.choice(["small","medium","tank","boss"])


    def update(self):
        if self.game_over or not self.running: return


        if self.spawned < self.wave_size:
            self.timer += 1
            if self.timer > 40:
                self.enemies.append(Enemy(self.wave,self.get_enemy_type()))
                self.timer = 0
                self.spawned += 1


        for e in self.enemies[:]:
            if e.move():
                self.enemies.remove(e)
                self.lives -= 1
            elif e.health <= 0:
                self.enemies.remove(e)
                self.pending_gold += int(e.gold)


        if self.lives <= 0: self.game_over = True


        for t in self.towers:
            for e in self.enemies:
                if dist((t.x,t.y),(e.x,e.y)) < t.real_range():
                    if t.type=="slow":
                        e.slow = 60
                        t.cd = t.real_cd()
                    else:
                        if t.cd <= 0:
                            self.proj.append(Projectile(t.x,t.y,t,e))
                            t.cd = t.real_cd()
                    break
            if t.cd > 0: t.cd -= 1


        for p in self.proj[:]:
            if p.update(): self.proj.remove(p)


        if self.spawned >= self.wave_size and not self.enemies:
            self.gold += (self.pending_gold + 50)
            self.pending_gold = 0
            self.wave += 1
            self.spawned = 0
            self.wave_size += 2
            if self.auto_run:
                self.start()
            else:
                self.running = False
                self.placing = True


    def draw_upgrade_ui(self):
        t = self.selected_tower
        panel = pygame.Rect(WIDTH-270,120,250,260)
        pygame.draw.rect(WIN,GRAY,panel)
        self.upgrade_close_rect = pygame.Rect(WIDTH-40,120,20,20)
        pygame.draw.rect(WIN,RED,self.upgrade_close_rect)
        WIN.blit(FONT.render("X",True,WHITE),(WIDTH-36,118))
        WIN.blit(FONT.render("UPGRADES",True,WHITE),(WIDTH-230,130))
        buttons = {}
        dmg_cost = 50*(t.dmg_lvl+1)
        rng_cost = 60*(t.rng_lvl+1)
        spd_cost = 70*(t.spd_lvl+1)
        r1 = pygame.Rect(WIDTH-250,170,220,30); pygame.draw.rect(WIN,(90,90,120),r1)
        WIN.blit(FONT.render(f"Damage L{t.dmg_lvl} (${dmg_cost})",True,WHITE),(WIDTH-240,175)); buttons["dmg"] = r1
        r2 = pygame.Rect(WIDTH-250,210,220,30); pygame.draw.rect(WIN,(90,90,120),r2)
        WIN.blit(FONT.render(f"Range L{t.rng_lvl} (${rng_cost})",True,WHITE),(WIDTH-240,215)); buttons["rng"] = r2
        r3 = pygame.Rect(WIDTH-250,250,220,30); pygame.draw.rect(WIN,(90,90,120),r3)
        WIN.blit(FONT.render(f"Speed L{t.spd_lvl} (${spd_cost})",True,WHITE),(WIDTH-240,255)); buttons["spd"] = r3
        return buttons


    def draw(self):
        WIN.fill(BLACK)
        for i in range(len(PATH)-1):
            pygame.draw.line(WIN,(0,120,255),PATH[i],PATH[i+1],18)


        for e in self.enemies: e.draw()
        for t in self.towers: t.draw()
        for p in self.proj: p.draw()


        ui_text = f"Gold: {self.gold} (+{self.pending_gold}) | Lives: {self.lives} | Wave: {self.wave}"
        WIN.blit(FONT.render(ui_text,True,WHITE),(20,20))


        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)); WIN.blit(overlay, (0,0))
            msg = BIG.render("NEON DEPLETED", True, RED)
            WIN.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 100))
            stats = FONT.render(f"Final Score: Wave {self.wave}", True, WHITE)
            WIN.blit(stats, (WIDTH//2 - stats.get_width()//2, HEIGHT//2 - 20))
            self.restart_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 40, 200, 50)
            pygame.draw.rect(WIN, GREEN, self.restart_rect, 2)
            btn_txt = FONT.render("REBOOT SYSTEM", True, GREEN)
            WIN.blit(btn_txt, (WIDTH//2 - btn_txt.get_width()//2, HEIGHT//2 + 55))
            pygame.display.update(); return


        pygame.draw.rect(WIN,(20,20,30),(0,HEIGHT-90,WIDTH,90))
        opts=[("base",60),("sniper",100),("slow",90)]
        x=30
        for n,c in opts:
            r=pygame.Rect(x,HEIGHT-75,150,50); pygame.draw.rect(WIN,(60,60,80),r)
            if self.selected==n: pygame.draw.rect(WIN,YELLOW,r,2)
            WIN.blit(FONT.render(f"{n} ${c}",True,WHITE),(x+10,HEIGHT-60)); x+=170


        # AUTO RUN BUTTON
        auto_col = GREEN if self.auto_run else GRAY
        pygame.draw.rect(WIN, auto_col, self.auto_rect, 2)
        auto_label = "AUTO: ON" if self.auto_run else "AUTO: OFF"
        WIN.blit(FONT.render(auto_label, True, auto_col), (WIDTH-300, HEIGHT-60))


        # START BUTTON
        pygame.draw.rect(WIN,(0,200,150),(WIDTH-160,HEIGHT-80,140,50))
        WIN.blit(FONT.render("START",True,WHITE),(WIDTH-120,HEIGHT-60))


        if self.placing:
            mx,my=pygame.mouse.get_pos()
            g=Tower(mx,my,self.selected)
            col=(0,255,0) if self.can_place(mx,my) else (255,0,0)
            pygame.draw.circle(WIN,col,(mx,my),int(g.range),1)


        if self.selected_tower:
            t=self.selected_tower
            pygame.draw.circle(WIN,(0,200,255),(int(t.x),int(t.y)),int(t.real_range()),2)
            self.buttons = self.draw_upgrade_ui()


        pygame.display.update()


    def click(self, x, y):
        if self.game_over:
            if self.restart_rect.collidepoint(x, y): self.reset()
            return


        if self.auto_rect.collidepoint(x,y):
            self.auto_run = not self.auto_run
            if self.auto_run and not self.running: self.start()
            return


        if x > WIDTH - 160 and y > HEIGHT - 80:
            self.start(); return


        if y > HEIGHT - 90:
            if x < 170: self.selected = "base"
            elif x < 340: self.selected = "sniper"
            elif x < 510: self.selected = "slow"
            return


        if self.selected_tower and self.draw_upgrade_ui():
            panel_rect = pygame.Rect(WIDTH - 270, 120, 250, 260)
            if panel_rect.collidepoint(x, y):
                if self.upgrade_close_rect and self.upgrade_close_rect.collidepoint(x, y):
                    self.selected_tower = None; return
                for k, r in self.buttons.items():
                    if r.collidepoint(x, y):
                        t = self.selected_tower
                        if k == "dmg":
                            c = 50*(t.dmg_lvl+1)
                            if self.gold >= c and t.dmg_lvl < 3: self.gold -= c; t.dmg_lvl += 1
                        elif k == "rng":
                            c = 60*(t.rng_lvl+1)
                            if self.gold >= c and t.rng_lvl < 3: self.gold -= c; t.rng_lvl += 1
                        elif k == "spd":
                            c = 70*(t.spd_lvl+1)
                            if self.gold >= c and t.spd_lvl < 3: self.gold -= c; t.spd_lvl += 1
                return


        for t in self.towers:
            if dist((x, y), (t.x, t.y)) < 20:
                self.selected_tower = t; return


        if self.placing and self.can_place(x, y):
            t = Tower(x, y, self.selected)
            if self.gold >= t.price:
                self.towers.append(t); self.gold -= t.price; self.selected_tower = None
            return


def main():
    g=Game()
    clock=pygame.time.Clock()
    run=True
    while run:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: run=False
            if e.type==pygame.MOUSEBUTTONDOWN:
                g.click(*pygame.mouse.get_pos())
        g.update()
        g.draw()
    pygame.quit()


if __name__=="__main__":
    main()

