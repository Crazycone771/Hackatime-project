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
        self.last_shot = 0
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
                self.bullets.append({"x": self.player["x"]+16, "y": self.player["y"], "dx": (i-1)*0.2, "dy": -8, "size": 4})
        else:
            self.bullets.append({"x": self.player["x"]+16, "y": self.player["y"], "dx": 0, "dy": -8, "size": 4})
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
        for bullet in list(self.bullets):
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            if bullet["y"] < 0 or bullet["x"] < 0 or bullet["x"] > WIDTH:
                self.bullets.remove(bullet)
        for enemy in list(self.enemies):
            enemy["y"] += enemy.get("speed", 2)
            if enemy.get("type") == "boss":
                pass
            else:
                if enemy["y"] > HEIGHT:
                    self.enemies.remove(enemy)
                    continue
                if (self.player["x"] < enemy["x"] + enemy.get("w", 32) and
                    self.player["x"] + 32 > enemy["x"] and
                    self.player["y"] < enemy["y"] + enemy.get("h", 32) and
                    self.player["y"] + 32 > enemy["y"]):
                    if not (self.player.get("shield", 0) > 0):
                        self.player_hit()
                    else:
                        # Shield absorbs damage
                        pass
        if random.random() < 0.02:
            self.spawn_enemy()
        if random.random() < 0.008:
            self.spawn_powerup()
        for bullet in list(self.bullets):
            hit_enemy = None
            for enemy in list(self.enemies):
                w = enemy.get("w", 32)
                h = enemy.get("h", 32)
                if (bullet["x"] < enemy["x"] + w and bullet["x"] + bullet["size"] > enemy["x"] and
                    bullet["y"] < enemy["y"] + h and bullet["y"] + bullet["size"] > enemy["y"]):
                    hit_enemy = enemy
                    break
            if hit_enemy is not None and bullet in self.bullets:
                self.bullets.remove(bullet)
                if hit_enemy in self.enemies:
                    self.enemies.remove(hit_enemy)
                    self.score += 10
                if hit_enemy.get("type") == "boss":
                    self.boss = None

        self.update_powerups(dt)
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
        elif powerup ["type"] == "heal":
            self.player["hp"] = min(self.player["maxhp"], self.player["hp"] + 30)
    def player_hit(self):
        self.player["hp"] -= 20
        if self.player["hp"] <= 0:
            self.player["alive"] = False
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
    def draw(self):
        self.canvas.delete("all")
        for star in self.stars:
            self.canvas.create_arc(star["x"], star["y"], star["x"]+star["s"], star["y"]+star["s"], start=0, extent=0, fill="white", outline="")
            star["y"] += star["v"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.random()*WIDTH
        if self.player["alive"]:
            self.canvas.create_rectangle(self.player["x"], self.player["y"],
                                         self.player["x"]+32, self.player["y"]+32, fill="blue")
            if self.player.get("shield", 0) > 0:
                self.canvas.create_oval(self.player["x"]-5, self.player["y"]-5,
                                        self.player["x"]+37, self.player["y"]+37, outline="cyan", width=2)
        for bullet in self.bullets:
            self.canvas.create_oval(bullet["x"], bullet["y"],
                                    bullet["x"]+bullet["size"], bullet["y"]+bullet["size"], fill="yellow")
        for enemy in self.enemies:
            color = "red" if enemy.get("type") != "boss" else "purple"
            w = enemy.get("w", 32)
            h = enemy.get("h", 32)
            self.canvas.create_rectangle(enemy["x"], enemy["y"],
                                         enemy["x"]+w, enemy["y"]+h, fill=color)
        self.canvas.create_text(10, 10, anchor="nw", text=f"Score: {self.score}", fill="white")
        self.canvas.create_text(10, 30, anchor="nw", text=f"Lives: {self.lives}", fill="white")
        if not self.player["alive"]:
            self.canvas.create_text(WIDTH//2, HEIGHT//2, text="GAME OVER", fill="red", font=("Arial", 24))
    def spawn_enemy(self):
        enemy_type = random.choice(["normal", "normal", "normal", "boss"])
        if enemy_type == "normal":
            self.enemies.append({"x": random.random()*(WIDTH-32), "y": -32, "w": 32, "h": 32, "speed": random.random()*2+1})
        elif enemy_type == "boss" and self.boss is None:
            self.boss = {"x": WIDTH//2-64, "y": -128, "w": 128, "h": 128, "speed": 1, "hp": 500, "type": "boss"}
            self.enemies.append(self.boss)
    def spawn_powerup(self):
        powerup_type = random.choice(["rapid", "shield", "heal"])
        self.powerups.append({"x": random.random()*(WIDTH-32), "y": -32, "type": powerup_type, "speed": 2})
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
        elif powerup ["type"] == "heal":
            self.player["hp"] = min(self.player["maxhp"], self.player["hp"] + 30)
    def player_hit(self):
        self.player["hp"] -= 20
        if self.player["hp"] <= 0:
            self.player["alive"] = False
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
if __name__ == "__main__":
    root = tk.Tk()
    Game = game(root)
    root.mainloop()

