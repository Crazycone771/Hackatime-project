import tkinter as tk
import random, math, time

WIDTH, HEIGHT = 800, 600

SHOP = [
    ("rapid",  "TRIPLE SHOT", 40,  "3 bullets always"),
    ("boots",  "BOOSTER",     45,  "faster"),
    ("shield", "SHIELD",      60,  "block a hit"),
    ("bomb",   "BOMB  (1)",   50,  "screen clear"),
    ("laser",  "LASER  (2)",  80,  "piercing"),
    ("drone",  "DRONE",       100, "orbiting gun"),
    ("life",   "EXTRA LIFE",  70,  "+1 life"),
]

class game:
    def __init__(self,root):
        self.root = root
        self.root.title("Space Blaster (Python/Tkinter)")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False,False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)
        self.pressed = set()
        self.init_game()
        self.last = time.time()
        self.loop()

    def init_game(self):
        self.player = {"x": WIDTH//2, "y": HEIGHT-60, "w": 32, "h": 32, "hp": 1, "maxhp": 1, "speed": 7.0, "rapid": 0, "shield": 0, "alive": True, "cooldown": 0, "iframes": 0, "bomb_cd": 0, "laser_cd": 0, "drone_cd": 0}
        self.bullets = []
        self.ebullets = []
        self.enemies = []
        self.particles = []
        self.rings = []
        self.texts = []
        self.trails = []
        self.powerups = []
        self.drones = []
        self.laser = None
        self.stars = [{"x": random.random()*WIDTH, "y": random.random()*HEIGHT, "s": random.random()*1.5+0.5, "v":random.random()*1.2+0.3} for _ in range(120)]
        self.score = 0
        self.gold = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False
        self.boss = None
        self.shake = 0
        self.flash = 0
        self.paused = False
        self.shop = False
        self.spawn_cd = 1.0
        self.powerup_cd = 6.0
        self.wave_left = 0
        self.wave_total = 0
        self.break_timer = 0
        self.banner = ""
        self.banner_t = 0
        self.combo = 1
        self.combo_t = 0
        self.owned = {"rapid": False, "boots": False, "shield": False,  "bomb": False, "laser": False, "drone": False}
        self.start_wave()

    def wave_config(self, w):
        boss = w % 3 == 0
        return {
            "boss": boss,
            "count": (5 + w//2) if boss else 4 + int(w*1.7),
            "tank_chance": max(0.0, (w-3)*0.09),         
            "fast_chance": max(0.0, (w-2)*0.13),
            "seeker_chance": max(0.0, (w-5)*0.08),
            "speed_mul": 0.5 + min(1.5, (w-1)*0.18), 
            "fire_every": 0 if w < 2 else max(0.45, 2.6-w*0.22),
            "hp_bonus": max(0, w-4),
        }

    def start_wave(self):
        c = self.wave_config(self.wave)
        self.wave_left = c["count"]
        self.wave_total = c["count"]
        self.banner = ("WAVE %d - BOSS" % self.wave) if c["boss"] else ("WAVE %d" % self.wave)
        self.banner_t = 2.0
        self.spawn_cd = 0.6
        if c["boss"]:
            self.spawn_boss()

    def wave_clear(self):
        bonus = 25 + self.wave*10
        self.score += self.wave*100
        self.gold += bonus
        self.popup(self.player["x"]+16, self.player["y"]-40, "WAVE CLEAR +%dg" % bonus, "lime")
        self.explode(self.player["x"]+16, self.player["y"], "lime", 25, size=3, shake=4)
        if self.wave % 5 == 0:
            self.lives += 1
            self.popup(self.player["x"]+16, self.player["y"]-60, "+1 LIFE", "lime")
        self.wave += 1
        self.break_timer = 2.0
        self.banner = "NEXT WAVE IN 2..."
        self.banner_t = 2.0

    def key_press(self,event):
        self.pressed.add(event.keysym)
        k = event.keysym.lower()
        if k == "p":
            self.paused = not self.paused
        if k == "r" and self.game_over:
            self.init_game()
        if k == "b":
            self.shop = not self.shop
        if self.shop:
            if event.keysym.isdigit():
                self.buy(int(event.keysym)-1)
            return
        if k == "e" or k == "escape":
            self.shop = False
        if event.keysym == "space" and self.player["cooldown"] <= 0:
            self.shoot_bullet()
            self.player["cooldown"] = 0.2
        if event.keysym == "1":
            self.use_bomb()
        if event.keysym == "2":
            self.use_laser()

    def key_release(self,event):
        self.pressed.discard(event.keysym)

    def buy(self, idx):
        if idx < 0 or idx >= len(SHOP):
            return
        key, name, price, desc = SHOP[idx]
        if key == "life":
            if self.gold >= price:
                self.gold -= price
                self.lives += 1
                self.popup(self.player["x"], self.player["y"]-30, "+1 LIFE", "lime")
            return
        if self.owned[key]:
            return
        if self.gold >= price:
            self.gold -= price
            self.owned[key] = True
            self.popup(self.player["x"], self.player["y"]-30, name, "gold")
            if key == "boots":
                self.player["speed"] = 11.0
            if key == "drone":
                self.drones = [{"a": 0.0}]
            if key == "shield":
                self.player["shield"] = 1
            self.explode(self.player["x"]+16, self.player["y"]+16, "gold", 14, shake=2)

    def shoot_bullet(self):
        p = self.player
        if self.owned["rapid"]:
            for i in range(3):
                self.bullets.append({"x": p["x"]+16, "y": p["y"], "dx": (i-1)*0.3, "dy": -9, "size": 4, "color": "cyan"})
        else:
            self.bullets.append({"x": p["x"]+16, "y": p["y"], "dx": 0, "dy": -9, "size": 4, "color": "yellow"})
        self.explode(p["x"]+16, p["y"], "yellow", 3, size=1, shake=0, ring=False)

    def use_bomb(self):
        p = self.player
        if not self.owned["bomb"] or p["bomb_cd"] > 0:
            return
        p["bomb_cd"] = 6.0
        self.ebullets.clear()
        self.explode(p["x"]+16, p["y"], "orange", 70, size=5, shake=14)
        self.flash = 1
        for e in list(self.enemies):
            self.damage_enemy(e, 6)
        self.popup(p["x"], p["y"]-30, "BOMB!", "orange")

    def use_laser(self):
        p = self.player
        if not self.owned["laser"] or p["laser_cd"] > 0:
            return
        p["laser_cd"] = 2.0
        self.laser = {"x": p["x"]+16, "y": p["y"], "life": 0.25}
        for e in list(self.enemies):
            if abs((e["x"]+e.get("w",32)/2) - (p["x"]+16)) < 26:
                self.damage_enemy(e, 15)
        self.explode(p["x"]+16, p["y"], "cyan", 12, shake=2)

    def update_drones(self, dt):
        if not self.owned["drone"]:
            return
        p = self.player
        for i, d in enumerate(self.drones):
            d["a"] = d.get("a", 0.0) + dt*3.0
            d["x"] = p["x"]+16 + math.cos(d["a"])*46
            d["y"] = p["y"]+16 + math.sin(d["a"])*46
            d["cd"] = d.get("cd", 0) - dt
            if d["cd"] <= 0:
                d["cd"] = 0.6
                self.bullets.append({"x": d["x"], "y": d["y"], "dx": 0, "dy": -9, "size": 3, "color": "magenta"})

    def explode(self, x, y, color, n, size=3, shake=4, ring=True):
        for _ in range(n):
            ang = random.random()*math.pi*2
            sp = random.random()*160 + 40
            life = random.uniform(0.25, 0.7)
            self.particles.append({"x": x, "y": y,
                                   "vx": math.cos(ang)*sp, "vy": math.sin(ang)*sp,
                                   "life": life, "max": life,
                                   "r": random.randint(size, size*3),
                                   "color": color})
        if ring:
            self.rings.append({"x": x, "y": y, "r": 2, "max_r": 30+size*8, "life": 0.35})
        self.shake = min(18, self.shake + shake)

    def popup(self, x, y, text, color):
        self.texts.append({"x": x, "y": y, "text": text, "color": color, "life": 0.9})

    def loop(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        if dt > 0.05: dt = 0.05
        if not self.paused:
            self.update(dt)
        self.draw()
        self.root.after(16, self.loop)

    def update(self, dt):
        p = self.player
        if p["alive"] and not self.shop and not self.game_over:
            sp = p["speed"]
            if "Left" in self.pressed:  p["x"] -= sp
            if "Right" in self.pressed: p["x"] += sp
            if "Up" in self.pressed:    p["y"] -= sp
            if "Down" in self.pressed:  p["y"] += sp
            p["x"] = max(0, min(WIDTH-32, p["x"]))
            p["y"] = max(0, min(HEIGHT-32, p["y"]))
            if p["cooldown"] > 0: p["cooldown"] -= dt
            if p["bomb_cd"] > 0:  p["bomb_cd"] -= dt
            if p["laser_cd"] > 0: p["laser_cd"] -= dt
            if p["iframes"] > 0:  p["iframes"] -= dt
            if self.owned["shield"] and p["shield"] <= 0:
                p["shield"] = 1
            self.trails.append({"x": p["x"]+16, "y": p["y"]+16, "life": 0.35, "max": 0.35})
            self.update_drones(dt)
        if self.break_timer > 0:
            self.break_timer -= dt
            if self.break_timer <= 0:
                self.break_timer = 0
                self.start_wave()
        else:
            self.spawn_cd -= dt
            if self.spawn_cd <= 0 and self.wave_left > 0:
                self.spawn_cd = max(0.25, 1.3 - self.wave*0.07)   
                self.spawn_enemy()
                self.wave_left -= 1
            if self.wave_left <= 0 and len(self.enemies) == 0 and not self.game_over:
                self.wave_clear()
        self.powerup_cd -= dt
        if self.powerup_cd <= 0:
            self.powerup_cd = random.uniform(6, 11)
            self.spawn_powerup()
        if self.boss is not None:
            self.boss["cd"] = self.boss.get("cd", 60) - dt
            if self.boss["cd"] <= 0:
                self.boss["cd"] = 1.6
                self.boss_shoot()
        self.banner_t = max(0, self.banner_t - dt)
        for b in list(self.bullets):
            b["x"] += b["dx"]; b["y"] += b["dy"]
            if b["y"] < 0 or b["x"] < 0 or b["x"] > WIDTH:
                self.bullets.remove(b)
        for b in list(self.ebullets):
            if b.get("homing", 0) > 0:
                b["homing"] -= dt
                a = math.atan2(p["y"]+16-b["y"], p["x"]+16-b["x"])
                b["dx"] += math.cos(a)*18*dt
                b["dy"] += math.sin(a)*18*dt
                n = math.hypot(b["dx"], b["dy"])
                if n > 0:
                    b["dx"] = b["dx"]/n*3.4
                    b["dy"] = b["dy"]/n*3.4
            b["x"] += b["dx"]; b["y"] += b["dy"]
            if b["y"] < 0 or b["y"] > HEIGHT or b["x"] < 0 or b["x"] > WIDTH:
                self.ebullets.remove(b)
        for e in list(self.enemies):
            if e.get("type") == "boss":
                e["x"] += e.get("vx", 1.4)
                if e["x"] < 80 or e["x"] > WIDTH-80: e["vx"] *= -1
                e["y"] = min(90, e["y"] + 1.2)
            else:
                e["y"] += e.get("speed", 2)
                if e["x"] < 0 or e["x"] > WIDTH-e.get("w",32): e["vx"] = -e.get("vx", 0)
                e["x"] += e.get("vx", 0)
            e["cd"] = e.get("cd", 0) - dt
            if e["cd"] <= 0 and e["y"] > 0 and e.get("fire", 0):
                e["cd"] = e["fire"] * random.uniform(0.7, 1.4)
                self.enemy_shoot(e)
            if e.get("type") != "boss" and e["y"] > HEIGHT:
                self.enemies.remove(e); continue
            if p["alive"] and p["iframes"] <= 0 and self.hit_player(e):
                if self.owned["shield"] and p["shield"] > 0:
                    p["shield"] = 0; p["iframes"] = 1.0
                    self.explode(p["x"]+16, p["y"]+16, "cyan", 20, shake=4)
                else:
                    self.player_hit()
                    if e in self.enemies:
                        self.explode(e["x"]+16, e["y"]+16, "red", 18)
                        self.enemies.remove(e)
        for b in list(self.ebullets):
            if p["alive"] and p["iframes"] <= 0 and \
               abs(b["x"]-(p["x"]+16)) < 18 and abs(b["y"]-(p["y"]+16)) < 18:
                self.ebullets.remove(b)
                if self.owned["shield"] and p["shield"] > 0:
                    p["shield"] = 0; p["iframes"] = 1.0
                    self.explode(p["x"]+16, p["y"]+16, "cyan", 16, shake=3)
                else:
                    self.player_hit()
        for b in list(self.bullets):
            hit = None
            for e in self.enemies:
                w, h = e.get("w", 32), e.get("h", 32)
                if b["x"] < e["x"]+w and b["x"]+b["size"] > e["x"] and \
                   b["y"] < e["y"]+h and b["y"]+b["size"] > e["y"]:
                    hit = e; break
            if hit:
                self.bullets.remove(b)
                self.damage_enemy(hit, 1, b["x"], b["y"])
        self.update_powerups(dt)
        self.update_effects(dt)

    def hit_player(self, e):
        p = self.player
        w, h = e.get("w", 32), e.get("h", 32)
        return p["x"] < e["x"]+w and p["x"]+32 > e["x"] and p["y"] < e["y"]+h and p["y"]+32 > e["y"]

    def damage_enemy(self, e, dmg, hx=None, hy=None):
        e["hp"] = e.get("hp", 1) - dmg
        self.explode(hx if hx is not None else e["x"]+16, hy if hy is not None else e["y"]+16, "orange", 4, size=1, shake=1)
        if e["hp"] > 0:
            return
        if e in self.enemies:
            self.enemies.remove(e)
        cx = e["x"]+e.get("w",32)/2
        cy = e["y"]+e.get("h",32)/2
        if e.get("type") == "boss":
            self.boss = None
            self.score += 1000
            self.gold += 200
            self.explode(cx, cy, "magenta", 90, size=6, shake=16)
            self.flash = 1
            self.popup(cx-40, cy, "+1000", "gold")
        else:
            self.combo = min(6, self.combo+1)
            self.combo_t = 3.0
            self.score += e.get("score", 10) * self.combo
            self.gold += e.get("gold", 5)
            self.explode(cx, cy, e.get("color", "red"), 24, size=3, shake=3)
            self.popup(e["x"], e["y"], f"+{e.get('gold',5)}g", "yellow")
            if self.combo > 1:
                self.popup(e["x"]+20, e["y"]-20, "x%d" % self.combo, "orange")
            if e.get("type") == "tank":
                self.score += 15

    def enemy_shoot(self, e):
        cx = e["x"] + e.get("w",32)/2
        cy = e["y"] + e.get("h",32)/2
        ang = math.atan2(self.player["y"]+16-cy, self.player["x"]+16-cx)
        self.ebullets.append({"x": cx-3, "y": cy, "dx": math.cos(ang)*4.2, "dy": math.sin(ang)*4.2, "size": 6, "color": "red"})
        if e.get("type") == "seeker":
            scat = ang + random.uniform(-1.1, 1.1)
            self.ebullets.append({"x": cx-4, "y": cy, "dx": math.cos(scat)*1.6, "dy": math.sin(scat)*1.6, "size": 7, "color": "violet", "homing": 1.0})
        if e.get("type") == "boss":
            for off in (-0.3, 0.3):
                a = ang + off
                self.ebullets.append({"x": cx-3, "y": cy, "dx": math.cos(a)*4.2, "dy": math.sin(a)*4.2, "size": 6, "color": "magenta"})

    def boss_shoot(self):
        b = self.boss
        cx = b["x"] + b["w"]/2
        for i in range(7):
            ang = math.pi/2 -0.9 + i*0.3
            self.ebullets.append({"x": cx-4, "y": b["y"]+b["h"], "dx": math.cos(ang)*4.5, "dy": math.sin(ang)*4.5, "size": 7, "color": "magenta"})
        for _ in range(2):
            self.spawn_enemy(force="minion")

    def update_powerups(self, dt):
        for pw in list(self.powerups):
            pw["y"] += pw["speed"]
            if pw["y"] > HEIGHT:
                self.powerups.remove(pw); continue
            p = self.player
            if p["x"] < pw["x"]+32 and p["x"]+32 > pw["x"] and p["y"] < pw["y"]+32 and p["y"]+32 > pw["y"]:
                self.apply_powerup(pw)
                self.powerups.remove(pw)

    def apply_powerup(self, powerup):
        if powerup["type"] == "rapid":
            self.player["rapid"] = 6.0
        if powerup["type"] == "shield":
            self.player["shield"] = 1
        if powerup["type"] == "gold":
            self.gold += 25
        self.popup(powerup["x"], powerup["y"], powerup["type"].upper(), "white")

    def update_effects(self, dt):
        for p in self.particles:
            p["x"] += p["vx"]*dt
            p["y"] += p["vy"]*dt
            p["vx"] -= p["vx"]*3*dt
            p["vy"] -= p["vy"]*3*dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]
        for r in self.rings:
            r["r"] += (r["max_r"]-r["r"])*min(1, dt*7)
            r["life"] -= dt
        self.rings = [r for r in self.rings if r["life"] > 0]
        for t in self.texts:
            t["y"] -= 30*dt
            t["life"] -= dt
        self.texts = [t for t in self.texts if t["life"] > 0]
        for t in self.trails:
            t["life"] -= dt
        self.trails = [t for t in self.trails if t["life"] > 0]
        if self.laser:
            self.laser["life"] -= dt
            if self.laser["life"] <= 0: self.laser = None
        self.shake = max(0, self.shake - dt*30)
        self.flash = max(0, self.flash - dt*3)
        self.combo_t = max(0, self.combo_t - dt)
        if self.combo_t <= 0: self.combo = 1

    def player_hit(self):
        p = self.player
        self.explode(p["x"]+16, p["y"]+16, "red", 50, size=5, shake=12)
        self.explode(p["x"]+16, p["y"]+16, "orange", 35, size=4, shake=8)
        self.flash = 1
        p["alive"] = False
        self.lives -= 1
        self.combo = 1
        if self.lives <= 0:
            self.game_over = True
            return
        p["x"] = WIDTH//2; p["y"] = HEIGHT-60
        p["alive"] = True
        p["iframes"] = 1.5
        self.ebullets.clear()

    def spawn_enemy(self, force=None):
        c = self.wave_config(self.wave)
        t = force
        if t is None:
            r = random.random()
            t = "normal"
            if r < c["tank_chance"]: t = "tank"
            elif r < c["tank_chance"]+c["fast_chance"]: t = "fast"
            elif r < c["tank_chance"]+c["fast_chance"]+c["seeker_chance"]: t = "seeker"
        fire = c["fire_every"]
        if t == "normal":
            self.enemies.append({"x": random.random()*(WIDTH-32), "y": -32, "w": 32, "h": 32, "hp": 1+c["hp_bonus"], "speed": (1.5+random.random()*1.5)*c["speed_mul"], "vx": 0, "cd": random.uniform(1.5,3.5) if fire else 999, "fire": fire, "type": None, "color": "red", "score": 10, "gold": 5})
        elif t == "fast":
            self.enemies.append({"x": random.random()*(WIDTH-24), "y":-24, "w": 24, "h": 24, "hp": 1+c["hp_bonus"], "speed": (3+random.random()*2)*c["speed_mul"], "vx": random.choice([-1,1])*0.8, "cd": random.uniform(2,4) if fire else 999, "fire": fire, "type": "fast", "color": "orange", "score": 20, "gold": 8})
        elif t == "tank":
            self.enemies.append({"x": random.random()*(WIDTH-48), "y": -44, "w": 48, "h": 44, "hp": 6+c["hp_bonus"]*2, "speed": (0.9+random.random()*0.6)*c["speed_mul"], "vx": 0, "cd": random.uniform(2,3.5) if fire else 999, "fire": fire, "type": "tank", "color": "maroon", "score": 40, "gold": 15})
        elif t == "seeker":
            self.enemies.append({"x": random.random()*(WIDTH-30), "y": -30, "w": 30, "h": 30, "hp": 3+c["hp_bonus"], "speed": (1.2+random.random()*0.8)*c["speed_mul"], "vx": 0, "cd": random.uniform(2,3.5) if fire else 999, "fire": 3.0, "type": "seeker", "color": "blue", "score": 30, "gold": 12})
        elif t == "minion":
            self.enemies.append({"x": random.random()*(WIDTH-28), "y": -28, "w": 28, "h": 28, "hp": 1, "speed": 2.5+self.wave*0.1, "vx": 0, "cd": 2.5, "fire": 3, "type": "minion", "color": "darkorange", "score": 5, "gold": 3})

    def spawn_boss(self):
        hp = 200 + self.wave*70
        self.boss = {"x": WIDTH//2-70, "y": -140, "w": 140, "h": 90, "speed": 1, "hp": hp, "maxhp": hp, "type": "boss", "vx": 1.2+self.wave*0.05, "color": "purple", "score": 1000, "gold": 200, "cd": 3}
        self.enemies.append(self.boss)

    def spawn_powerup(self):
        t = random.choice(["rapid","shield","gold"])
        self.powerups.append({"x": random.random()*(WIDTH-32), "y": -32, "type": t, "speed": 2.2})

    def draw(self):
        c = self.canvas
        self.canvas.delete("all")
        ox = (random.random()-0.5)*self.shake
        oy = (random.random()-0.5)*self.shake
        for star in self.stars:
            c.create_oval(star["x"]+ox, star["y"]+oy, star["x"]+ox+star["s"], star["y"]+oy+star["s"], fill="white", outline="")
            star["y"] += star["v"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.random()*WIDTH
        for t in self.trails:
            r = 2+t["life"]/t["max"]*12
            c.create_oval(t["x"]+ox-r, t["y"]+oy-r, t["x"]+ox+r, t["y"]+oy+r, fill="deepskyblue", outline="")
        for g in self.rings:
            c.create_oval(g["x"]+ox-g["r"], g["y"]+oy-g["r"], g["x"]+ox+g["r"], g["y"]+oy+g["r"], outline="white", width=2)
        for p in self.particles:
            rr = max(1, p["r"]*p["life"]/p["max"])
            c.create_oval(p["x"]+ox-rr, p["y"]+oy-rr, p["x"]+ox+rr, p["y"]+oy+rr, fill=p["color"], outline="")
        if self.laser:
            c.create_rectangle(self.laser["x"]+ox-32, 0, self.laser["x"]+ox+32, self.laser["y"]+oy, fill="cyan", outline="")
        p = self.player
        if p["alive"]:
            col = "cyan" if (self.owned["shield"] and p["shield"] > 0) else "blue"
            if p["iframes"] > 0 and int(p["iframes"]*10) % 2 == 0:
                col = "gray60"
            c.create_rectangle(p["x"]+ox, p["y"]+oy, p["x"]+ox+32, p["y"]+oy+32, fill=col)
            if self.owned["shield"] and p["shield"] > 0:
                c.create_oval(p["x"]+ox-6, p["y"]+oy-6, p["x"]+ox+38, p["y"]+oy+38, outline="cyan", width=2)
        for d in self.drones:
            c.create_oval(d["x"]+ox-7, d["y"]+oy-7, d["x"]+ox+7, d["y"]+oy+7, fill="magenta", outline="white")
        for b in self.bullets:
            c.create_oval(b["x"]+ox, b["y"]+oy, b["x"]+ox+b["size"], b["y"]+oy+b["size"], fill=b["color"])
        for b in self.ebullets:
            r = 6 if b.get("homing", 0) > 0 else 4
            c.create_oval(b["x"]+ox-r, b["y"]+oy-r, b["x"]+ox+r, b["y"]+oy+r, fill=b["color"], outline="white")
        for e in self.enemies:
            c.create_rectangle(e["x"]+ox, e["y"]+oy, e["x"]+ox+e["w"], e["y"]+oy+e["h"], fill=e.get("color","red"), outline="white")
            if e.get("type") == "boss":
                fr = max(0, e["hp"]/e.get("maxhp", 1))
                c.create_rectangle(e["x"]+ox, e["y"]+oy-10, e["x"]+ox+e["w"], e["y"]+oy-5, fill="gray40", outline="white")
                c.create_rectangle(e["x"]+ox, e["y"]+oy-10, e["x"]+ox+e["w"]*fr, e["y"]+oy-5, fill="magenta", outline="")
                c.create_text(e["x"]+ox+e["w"]/2, e["y"]+oy+e["h"]/2, text="BOSS", fill="white", font=("Arial", 14, "bold"))
            elif e.get("hp", 1) > 1:
                c.create_rectangle(e["x"]+ox, e["y"]+oy-6, e["x"]+ox+e["w"], e["y"]+oy-3, fill="gray40", outline="")
                c.create_rectangle(e["x"]+ox, e["y"]+oy-6, e["x"]+ox+e["w"]*(e["hp"]/e["hp"]), e["y"]+oy-3, fill="red", outline="")
        for t in self.texts:
            c.create_text(t["x"]+ox, t["y"]+oy, text=t["text"], fill=t["color"], font=("Arial", 14, "bold"))
        for pw in self.powerups:
            c.create_rectangle(pw["x"]+ox, pw["y"]+oy, pw["x"]+ox+24, pw["y"]+oy+24, fill="gold", outline="white")
            c.create_text(pw["x"]+ox+12, pw["y"]+oy+12, text=pw["type"][0].upper(), fill="black")
        if self.flash > 0:
            c.create_rectangle(0,0,WIDTH,HEIGHT,fill="white", stipple="gray75" if self.flash < 0.5 else "gray25")
        c.create_text(10,16,anchor="nw",text=f"score: {self.score}",fill="white")
        c.create_text(10,36,anchor="nw",text=f"gold: {self.gold}", fill="gold")
        c.create_text(10,56,anchor="nw",text=f"lives: {self.lives}",fill="white")
        c.create_text(10,76,anchor="nw",text=f"wave: {self.wave}   enemies left: {self.wave_left+len(self.enemies)}",fill="white")
        c.create_text(WIDTH-10,16,anchor="ne",text="B = SHOP",fill="cyan",font=("Arial",12,"bold"))
        c.create_text(WIDTH-10,36,anchor="ne",text="1 bomb | 2 laser",fill="gray70")
        c.create_text(WIDTH-10,56,anchor="ne",text=" | ".join(k for k,v in self.owned.items()if v) or "no upgrades", fill="gray60")
        if self.combo > 1:
            c.create_text(WIDTH//2, 100, text="x%d combo" % self.combo, fill="orange", font=("Arial", 16, "bold"))
        c.create_text(WIDTH//2, HEIGHT-14, text="1 hit = death | arrows move | space to shoot | press b for shop | p for pause", fill="white", font=("Arial", 13))
        if self.banner_t > 0:
            c.create_text(WIDTH//2, HEIGHT//2-70, text=self.banner, fill="lime", font=("Arial", 24, "bold"))
        if self.paused:
            c.create_text(WIDTH//2, HEIGHT//2, text="paused(p)", fill="yellow", font=("Arial", 26))
        if self.game_over:
            c.create_text(WIDTH//2, HEIGHT//2, text="game over", fill="red", font=("Arial", 30))
            c.create_text(WIDTH//2, HEIGHT//2+40, text=f"score:{self.score} gold:{self.gold}  -press r to restart", fill="white", font=("Arial", 13))
        if self.shop:
            self.draw_shop()

    def draw_shop(self):
        c = self.canvas
        px, py, pw, ph = 180, 90, 440, 420
        c.create_rectangle(px, py, px+pw, py+ph, fill="black", outline="cyan", width=3)
        c.create_text(WIDTH//2, py+28, text="SHOP", fill="cyan", font=("Arial", 22, "bold"))
        c.create_text(WIDTH//2,py+52, text=f"you have {self.gold} gold", fill="gold", font=("Arial", 13))
        y = py + 84
        for i, (key, name, price, desc) in enumerate(SHOP):
            owned = self.owned.get(key)
            col = "gray45" if owned else ("lime" if self.gold >= price else "gray70")
            label = f"{i+1}. {name:<14} {price:>4}g {desc}"
            if owned:
                label = f"{i+1}, {name:<14} OWNED"
            c.create_text(px+20, y, text=label, fill=col, font=("Courier", 12), anchor="nw")
            y += 30
        c.create_text(WIDTH//2, py+ph-24, text="press number to buy | b or esc to close", fill="cyan", font=("Arial", 11))

if __name__ == "__main__":
    root = tk.Tk()
    Game = game(root)
    root.mainloop()
