import tkinter as tk
from tkinter import ttk
import random
import time

class ConwayGameOfLife:

    def __init__(self, width=50, height=50, cell_size=10):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.running = False
        self.speed = 100
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.root = tk.Tk()
        self.root.title("Conway's Game of Life")
        self.root.resizable(False, False)
        canvas_width = width * cell_size
        canvas_height = height * cell_size
        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height, bg='white', bd=1, relief='solid')
        self.canvas.pack(pady=10)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5)
        self.start_button = ttk.Button(control_frame, text='Start', command=self.start_game)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(control_frame, text='Stop', command=self.stop_game)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.clear_button = ttk.Button(control_frame, text='Clear', command=self.clear_grid)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        self.random_button = ttk.Button(control_frame, text='Random', command=self.randomize_grid)
        self.random_button.pack(side=tk.LEFT, padx=5)
        speed_frame = ttk.Frame(self.root)
        speed_frame.pack(pady=5)
        ttk.Label(speed_frame, text='Speed:').pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=self.speed)
        self.speed_scale = ttk.Scale(speed_frame, from_=10, to=1000, variable=self.speed_var, orient=tk.HORIZONTAL, length=200, command=self.update_speed)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        self.generation = 0
        self.gen_label = ttk.Label(self.root, text=f'Generation: {self.generation}')
        self.gen_label.pack(pady=5)
        self.draw_grid()

    def get_cell_coords(self, x, y):
        """Convert canvas coordinates to grid coordinates"""
        col = x // self.cell_size
        row = y // self.cell_size
        return (row, col)

    def on_click(self, event):
        """Handle mouse click to toggle cell state"""
        if not self.running:
            row, col = self.get_cell_coords(event.x, event.y)
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = 1 - self.grid[row][col]
                self.draw_grid()

    def on_drag(self, event):
        """Handle mouse drag to draw cells"""
        if not self.running:
            row, col = self.get_cell_coords(event.x, event.y)
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = 1
                self.draw_grid()

    def draw_grid(self):
        """Draw the current state of the grid"""
        self.canvas.delete('all')
        for row in range(self.height):
            for col in range(self.width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                if self.grid[row][col] == 1:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill='black', outline='gray')
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='gray')

    def count_neighbors(self, row, col):
        """Count the number of living neighbors for a cell"""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = (row + dr, col + dc)
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    count += self.grid[nr][nc]
        return count

    def next_generation(self):
        """Calculate the next generation based on Conway's rules"""
        new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for row in range(self.height):
            for col in range(self.width):
                neighbors = self.count_neighbors(row, col)
                current_cell = self.grid[row][col]
                if current_cell == 1:
                    if neighbors == 2 or neighbors == 3:
                        new_grid[row][col] = 1
                    else:
                        new_grid[row][col] = 0
                elif neighbors == 3:
                    new_grid[row][col] = 1
                else:
                    new_grid[row][col] = 0
        self.grid = new_grid
        self.generation += 1
        self.gen_label.config(text=f'Generation: {self.generation}')
        self.draw_grid()

    def game_loop(self):
        """Main game loop"""
        if self.running:
            self.next_generation()
            self.root.after(self.speed, self.game_loop)

    def start_game(self):
        """Start the game simulation"""
        if not self.running:
            self.running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.game_loop()

    def stop_game(self):
        """Stop the game simulation"""
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def clear_grid(self):
        """Clear all cells"""
        if not self.running:
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
            self.generation = 0
            self.gen_label.config(text=f'Generation: {self.generation}')
            self.draw_grid()

    def randomize_grid(self):
        """Randomly populate the grid"""
        if not self.running:
            for row in range(self.height):
                for col in range(self.width):
                    self.grid[row][col] = random.choice([0, 1])
            self.generation = 0
            self.gen_label.config(text=f'Generation: {self.generation}')
            self.draw_grid()

    def update_speed(self, value):
        """Update the simulation speed"""
        self.speed = int(float(value))

    def run(self):
        """Start the tkinter main loop"""
        self.root.mainloop()

def create_glider(game, start_row=5, start_col=5):
    """Create a glider pattern"""
    pattern = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
    for i, row in enumerate(pattern):
        for j, cell in enumerate(row):
            r, c = (start_row + i, start_col + j)
            if 0 <= r < game.height and 0 <= c < game.width:
                game.grid[r][c] = cell

def create_blinker(game, start_row=10, start_col=10):
    """Create a blinker pattern"""
    pattern = [[1], [1], [1]]
    for i, row in enumerate(pattern):
        for j, cell in enumerate(row):
            r, c = (start_row + i, start_col + j)
            if 0 <= r < game.height and 0 <= c < game.width:
                game.grid[r][c] = cell

def create_block(game, start_row=15, start_col=15):
    """Create a block pattern (still life)"""
    pattern = [[1, 1], [1, 1]]
    for i, row in enumerate(pattern):
        for j, cell in enumerate(row):
            r, c = (start_row + i, start_col + j)
            if 0 <= r < game.height and 0 <= c < game.width:
                game.grid[r][c] = cell

def main():
    """Main function to run the game"""
    game = ConwayGameOfLife(width=60, height=40, cell_size=12)
    create_glider(game, 5, 5)
    create_blinker(game, 10, 20)
    create_block(game, 15, 30)
    game.draw_grid()
    print("Conway's Game of Life")
    print('Controls:')
    print('- Click to toggle individual cells')
    print('- Drag to draw multiple cells')
    print('- Use Start/Stop to control simulation')
    print('- Use Random to generate random pattern')
    print('- Use Clear to reset the grid')
    print('- Adjust speed slider to change simulation speed')
    game.run()
if __name__ == '__main__':
    main()