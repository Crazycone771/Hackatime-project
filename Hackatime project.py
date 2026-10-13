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

