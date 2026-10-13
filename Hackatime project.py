import tkinter as tk
window=tk.Tk()
window.title("Non-Ai Games-Python edition")
window.geometry("900x450")
window.config(bg="#060810")
tk.Label(window, text="Welcome, to the Game of non-Ai games!", bg="White", fg="Black").grid(row=0,column=0,padx=10, pady=10, sticky="e")
entry_name = tk.Entry(window)
entry_name.grid(row=0, column=1, padx=10, pady=10)
window.mainloop()