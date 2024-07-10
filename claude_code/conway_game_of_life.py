
import tkinter as tk
from tkinter import ttk
import random

class ConwayGameOfLife:
    def __init__(self, master):
        self.master = master
        master.title("Conway's Game of Life")
        master.configure(bg='#2E2E2E')

        self.cell_size = 15
        self.grid_width = 40
        self.grid_height = 30
        self.speed = 100  # Update interval in milliseconds
        self.zoom = 1.0

        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.next_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        self.running = False

        self.create_widgets()

    def create_widgets(self):
        self.canvas = tk.Canvas(self.master, width=self.cell_size*self.grid_width, 
                                height=self.cell_size*self.grid_height, bg='black')
        self.canvas.pack(pady=10)

        self.canvas.bind("<Button-1>", self.toggle_cell)

        control_frame = ttk.Frame(self.master)
        control_frame.pack(pady=10)

        ttk.Button(control_frame, text="Start", command=self.start).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Stop", command=self.stop).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Clear", command=self.clear).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Random", command=self.randomize).grid(row=0, column=3, padx=5)

        ttk.Label(control_frame, text="Speed:").grid(row=1, column=0, padx=5, pady=10)
        self.speed_scale = ttk.Scale(control_frame, from_=50, to=500, orient=tk.HORIZONTAL, 
                                     command=self.update_speed)
        self.speed_scale.set(self.speed)
        self.speed_scale.grid(row=1, column=1, columnspan=3, padx=5, pady=10)

        ttk.Label(control_frame, text="Zoom:").grid(row=2, column=0, padx=5, pady=10)
        self.zoom_scale = ttk.Scale(control_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, 
                                    command=self.update_zoom)
        self.zoom_scale.set(self.zoom)
        self.zoom_scale.grid(row=2, column=1, columnspan=3, padx=5, pady=10)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        zoomed_cell_size = int(self.cell_size * self.zoom)
        self.canvas.config(width=zoomed_cell_size*self.grid_width, height=zoomed_cell_size*self.grid_height)
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                x1 = j * zoomed_cell_size
                y1 = i * zoomed_cell_size
                x2 = x1 + zoomed_cell_size
                y2 = y1 + zoomed_cell_size
                color = "white" if self.grid[i][j] else "black"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")

    def toggle_cell(self, event):
        zoomed_cell_size = int(self.cell_size * self.zoom)
        col = event.x // zoomed_cell_size
        row = event.y // zoomed_cell_size
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            self.grid[row][col] = 1 - self.grid[row][col]
            self.draw_grid()

    def update_speed(self, value):
        self.speed = int(float(value))

    def update_zoom(self, value):
        self.zoom = float(value)
        self.draw_grid()

    def start(self):
        self.running = True
        self.update()

    def stop(self):
        self.running = False

    def clear(self):
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.draw_grid()

    def randomize(self):
        self.grid = [[random.choice([0, 1]) for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.draw_grid()

    def update(self):
        if self.running:
            self.next_generation()
            self.draw_grid()
            self.master.after(self.speed, self.update)

    def next_generation(self):
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                neighbors = self.count_neighbors(i, j)
                if self.grid[i][j]:
                    if neighbors < 2 or neighbors > 3:
                        self.next_grid[i][j] = 0
                    else:
                        self.next_grid[i][j] = 1
                else:
                    if neighbors == 3:
                        self.next_grid[i][j] = 1
                    else:
                        self.next_grid[i][j] = 0
        self.grid, self.next_grid = self.next_grid, self.grid

    def count_neighbors(self, row, col):
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                ni, nj = (row + i) % self.grid_height, (col + j) % self.grid_width
                count += self.grid[ni][nj]
        return count

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='#2E2E2E')
    game = ConwayGameOfLife(root)
    root.mainloop()
