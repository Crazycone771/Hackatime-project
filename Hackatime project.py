import tkinter as tk
import random, math, time

WIDTH, HEIGHT = 800,600

class game:
    def __init__(self,root):
        self.root = root
        self.root.title("Space Balster (Python/Tkinter)")
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
        self.player = {"x": WIDTH//2, "y": HEIGHT-60, "w": 32, "h": 32, "hp": 100, "maxhp": 100,
                       "speed": 6.0, "rapid": 0, "shield": 0, "alive": True, "cooldown": 0}
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.rings = []
        self.texts = []
        self.trails = []
        self.powerups = []
        self.stars = [{"x": random.random()*WIDTH, "y": random.random()*HEIGHT,
                       "s": random.random()*1.5+0.5, "v":random.random()*1.2+0.3} for _ in range(120)]
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False
        self.spawn_timer = 0
        self.boss = None
        self.shake = 0
        self.flash = 0
        self.paused = False
    def key_press(self,event):
        self.pressed.add(event.keysym)
        if event.keysym == "p":
            self.paused = not self.paused
        if event.keysym == "r" and self.game_over:
            self.init_game()
            self.game_over = False
        if event.keysym == "space" and self.player["cooldown"] <= 0:
            self.shoot_bullet()
            self.player["cooldown"] = 0.2
    def key_release(self,event):
        if event.keysym in self.pressed:
            self.pressed.remove(event.keysym)
    def shoot_bullet(self):
        if self.player["rapid"] > 0:
            for i in range(3):
                self.bullets.append({"x": self.player["x"]+16, "y": self.player["y"], "dx": (i-1)*0.2, "dy": -8, "size": 4, "color": "cyan"})
        else:
            self.bullets.append({"x": self.player["x"]+16, "y": self.player["y"], "dx": 0, "dy": -8, "size": 4, "color": "yellow"})
        # muzzle flash
        self.explode(self.player["x"]+16, self.player["y"], "yellow",4 , size=1, shake=0, ring=False)
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
        self.shake = min(16, self.shake + shake)

    def popup(self, x, y, text, color):
        self.texts.append({"x": x, "y": y, "text": text, "color": color, "life": 0.8})
    def loop(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        if not self.paused:
            self.update(dt)
            self.draw()
        self.root.after(16, self.loop)
    def update(self,dt):
        if self.player["alive"]:
            if "Left" in self.pressed:
                self.player["x"] -= self.player["speed"]
            if "Right" in self.pressed:
                self.player["x"] += self.player["speed"]
            if "Up" in self.pressed:
                self.player["y"] -= self.player["speed"]
            if "Down" in self.pressed:
                self.player["y"] += self.player["speed"]
            self.player["x"] = max(0, min(WIDTH-32, self.player["x"]))
            self.player["y"] = max(0, min(HEIGHT-32, self.player["y"]))
            if self.player["cooldown"] > 0:
                self.player["cooldown"] -= dt
            if self.player["rapid"] > 0:
                self.player["rapid"] -= dt
            if self.player["shield"] > 0:
                self.player["shield"] -= dt
            # ship trail
            self.trails.append({"x": self.player["x"]+16, "y": self.player["y"]+16, "life": 0.35, "max": 0.35})
        for bullet in list(self.bullets):
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            if bullet["y"] < 0 or bullet["x"] < 0 or bullet["x"] > WIDTH: self.bullets.remove(bullet)
        for enemy in list(self.enemies):
            enemy["y"] += enemy.get("speed", 2)
            if enemy.get("type") == "boss":
                enemy["x"] += enemy.get("vx", 1)
                if enemy["x"] < 70 or enemy["x"] > WIDTH-70:
                    enemy["vx"] *= -1
            else:
                if enemy["y"] > HEIGHT:
                    self.enemies.remove(enemy)
                    continue
                if (self.player["x"] < enemy["x"] + enemy.get("w", 32) and self.player["x"] + 32 > enemy["x"] and self.player["y"] < enemy["y"] + enemy.get("h", 32) and
                    self.player["y"] + 32 > enemy["y"]):
                    if not (self.player.get("shield", 0) > 0):
                        self.player_hit()
                        if enemy in self.enemies:
                            self.explode(enemy["x"]+16, enemy["y"]+16, "red", 18)
                            self.enemies.remove(enemy)
                    else:
                        self.explode(enemy["x"]+16, enemy["y"]+16, "cyan", 14)
                        self.enemies.remove(enemy)
        if random.random() < 0.02:
            self.spawn_enemy()
        if random.random() < 0.008:
            self.spawn_powerup()
        for bullet in list(self.bullets):
            hit_enemy = None
            for enemy in list(self.enemies):
                w = enemy.get("w", 32)
                h = enemy.get("h", 32)
                if (bullet["x"] < enemy["x"] + w and bullet["x"] + bullet["size"] > enemy["x"] and bullet["y"] < enemy["y"] + h and bullet["y"] + bullet["size"] > enemy["y"]):
                    hit_enemy = enemy
                    break
            if hit_enemy is not None and bullet in self.bullets:
                self.bullets.remove(bullet)
                self.explode(bullet["x"], bullet["y"], "orange", 5, size=1, shake=1)
                if hit_enemy.get("type") == "boss":
                    hit_enemy["hp"] -= 1
                    if hit_enemy["hp"] <= 0:
                        self.enemies.remove(hit_enemy)
                        self.boss = None
                        self.score += 500
                        self.explode(hit_enemy["x"]+hit_enemy["w"]/2, hit_enemy["y"]+hit_enemy["h"]/2, "magenta", 60, size=4, shake=12)
                        self.flash = 1
                        self.popup(hit_enemy["x"]+64, hit_enemy["y"], "+500", "gold")
                else:
                    self.enemies.remove(hit_enemy)
                    self.score += 10
                    self.explode(hit_enemy["x"]+16, hit_enemy["y"]+16, "orange", 20, shake=3)
                    self.popup(hit_enemy["x"], hit_enemy["y"], "+10", "yellow")
        self.update_powerups(dt)
        self.update_effects(dt)
    def update_powerups(self, dt):
        for powerup in list(self.powerups):
            powerup["y"] += powerup["speed"]
            if powerup["y"] > HEIGHT:
                self.powerups.remove(powerup)
                continue
            if (self.player["x"] < powerup["x"] + 32 and
                self.player["x"] + 32 > powerup["x"] and
                self.player["y"] < powerup["y"] + 32 and
                self.player["y"] + 32 > powerup["y"]):
                self.apply_powerup(powerup)
                self.powerups.remove(powerup)
    def apply_powerup(self, powerup):
        if powerup["type"] == "rapid":
            self.player["rapid"] = 5.0
        elif powerup["type"] == "shield":
            self.player["shield"] = 5.0
        elif powerup["type"] == "heal":
            self.player["hp"] = min(self.player["maxhp"], self.player["hp"] + 30)
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
        self.shake = max(0, self.shake - dt*30)
        self.flash = max(0, self.flash - dt*3)
    def player_hit(self):
        self.player["hp"] -= 20
        self.explode(self.player["x"]+16, self.player["y"]+16, "orange", 10, shake=3)
        if self.player["hp"] <= 0:
            self.explode(self.player["x"]+16, self.player["y"]+16, "red", 40, size=4, shake=10)
            self.explode(self.player["x"]+16, self.player["y"]+16, "orange", 30, size=3, shake=6)
            self.explode(self.player["x"]+16, self.player["y"]+16, "yellow", 20, size=2, shake=3)
            self.flash = 1
            self.player["alive"] = False
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.player["x"] = WIDTH//2
                self.player["y"] = HEIGHT-60
                self.player["hp"] = self.player["maxhp"]
                self.player["alive"] = True
    def draw(self):
        self.canvas.delete("all")
        ox = (random.random()-0.5)*self.shake
        oy = (random.random()-0.5)*self.shake

        for star in self.stars:
            self.canvas.create_oval(star["x"]+ox, star["y"]+oy, star["x"]+ox+star["s"], star["y"]+oy+star["s"], fill="white", outline="")
            star["y"] += star["v"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.random()*WIDTH
        for t in self.trails:
            r = 2+t["life"]/t["max"]*12
            self.canvas.create_oval(t["x"]+ox-r, t["y"]+oy-r, t["x"]+ox+r, t["y"]+oy+r, fill="deepskyblue", outline="")
        for g in self.rings: self.canvas.create_oval(g["x"]+ox-g["r"], g["y"]+oy-g["r"], g["x"]+ox+g["r"], g["y"]+oy+g["r"], outline="white", width=2)
        for p in self.particles:
            rr = max(1, p["r"]*p["life"]/p["max"])
            self.canvas.create_oval(p["x"]+ox-rr, p["y"]+oy-rr, p["x"]+ox+rr, p["y"]+oy+rr, fill=p["color"], outline="")
        if self.player["alive"]:
            self.canvas.create_rectangle(self.player["x"]+ox, self.player["y"]+oy, self.player["x"]+ox+32, self.player["y"]+oy+32, fill="blue")
            if self.player.get("shield", 0)>0: self.canvas.create_oval(self.player["x"]+ox-5, self.player["y"]+oy-5, self.player["x"]+ox+37, self.player["y"]+oy+37, outline="cyan", width=2)
        for b in self.bullets:
            self.canvas.create_oval(b["x"]+ox, b["y"]+oy, b["x"]+ox+b["size"], b["y"]+oy+b["size"], fill=b.get("color", "yellow"))
            self.canvas.create_oval(b["x"]+ox, b["y"]+oy+b["size"], b["x"]+ox+b["size"]/2, b["y"]+oy+b["size"]*2, fill="orange", outline="")
        for e in self.enemies:
            w, h = e.get("w", 32), e.get("h", 32)
            self.canvas.create_rectangle(e["x"]+ox, e["y"]+oy, e["x"]+ox+w, e["y"]+oy+h, fill="purple" if e.get("type")=="boss" else "red")
            if e.get("type")=="boss":
                fr = max(0, e["hp"]/e.get("maxhp", 500))
                self.canvas.create_rectangle(e["x"]+ox, e["y"]+oy-8, e["x"]+ox+w, e["y"]+oy-4, fill="gray40", outline="")
                self.canvas.create_rectangle(e["x"]+ox, e["y"]+oy-8, e["x"]+ox+w*fr, e["y"]+oy-4, fill="magenta", outline="")
        for pw in self.powerups:
            self.canvas.create_rectangle(pw["x"]+ox, pw["y"]+oy, pw["x"]+ox+24, pw["y"]+oy+24, fill="gold")
            self.canvas.create_text(pw["x"]+ox+12, pw["y"]+oy+12, text=pw["type"][0].upper(), fill="black")
        for t in self.texts: self.canvas.create_text(t["x"]+ox, t["y"]+oy, text=t["text"], fill=t["color"], font=("Arial", 14, "bold"))
        if self.flash>0: self.canvas.create_rectangle(0,0,WIDTH,HEIGHT,fill="white",stipple="gray75" if self.flash<0.5 else "gray25")
        self.canvas.create_text(10,10,anchor="nw",text=f"score: {self.score}",fill="white")
        self.canvas.create_text(10,30,anchor="nw",text=f"lives: {self.lives}",fill="white")
        if not self.player["alive"]: self.canvas.create_text(WIDTH//2, HEIGHT//2, text="game over", fill="red", font=("Arial", 24))
        if self.paused: self.canvas.create_text(WIDTH//2, HEIGHT//2, text="paused", fill="yellow", font=("Arial", 24))
    def spawn_enemy(self):
        t = random.choice(["normal","normal","normal","boss"])
        if t=="normal": self.enemies.append({"x":random.random()*(WIDTH-32),"y":-32,"w":32,"h":32,"speed":random.random()*2+1,"type":None})
        elif t=="boss" and self.boss is None:
            self.boss = {"x":WIDTH//2-64,"y":-128,"w":128,"h":128,"speed":1,"hp":500,"maxhp":500,"type":"boss","vx":1}
            self.enemies.append(self.boss)
    def spawn_powerup(self):
        t = random.choice(["rapid","shield","heal"])
        self.powerups.append({"x":random.random()*(WIDTH-32),"y":-32,"type":t,"speed":2})
if __name__ == "__main__":
    root = tk.Tk()
    Game = game(root)
    root.mainloop()


  