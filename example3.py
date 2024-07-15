import math

import tkinter as tk


def calculate():
    try:
        expression = entry.get()
        result = eval(expression)
        if isinstance(result, float):
            result = round(result, 5)
        entry.delete(0, tk.END)
        entry.insert(tk.END, str(result))
    except Exception as e:
        entry.delete(0, tk.END)
        entry.insert(tk.END, "Error")
def clear():
    entry.delete(0, tk.END)

root = tk.Tk()
root.title("Advanced Calculator")

entry = tk.Entry(root, width=20)
entry.grid(row=0, column=0, columnspan=4)

buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    '0', '.', '=', '+'
]

row = 1
col = 0
for button in buttons:
    cmd = lambda x=button: entry.insert(tk.END, x) if x != '=' else calculate()
    tk.Button(root, text=button, command=cmd).grid(row=row, column=col)
    col += 1
    if col > 3:
        col = 0
        row += 1

root.mainloop()

# This calculator was created and modified using bot_tools
