import tkinter as tk
root = tk.Tk()
root.title("Non - AI Games --- Python Edition")
root.geometry("1200x600")

tk.Label(root, text="Welcome to Non - AI Games --- Python Edition", font=("Arial", 24, "bold"), fg="#00f5ff", bg="#060810").pack(pady=20).grid(row=0, column=0, columnspan=2, padx=10, pady=10, pady=10, sticky="e")
entry_name=tk.Entry(root)
entry_name.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

tk.Label(root, text=("Please Enter your name for future references"), font=("Arial", 14), fg="#00f5ff", bg="#060810").pack(pady=20).grid(row=2, column=0, columnspan=2, padx=10, pady=10, pady=10, sticky="e")
entry_total=tk.Entry(root)
entry_total.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

tk.Label
root.mainloop()