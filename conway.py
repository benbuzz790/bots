import pygame


class GameOfLife:

    def __init__(self, width=800, height=600, cell_size=20):
        pygame.init()
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(
            "Conway's Game of Life - Click to toggle cells, SPACE to play/pause"
            )
        self.grid = [[(0) for x in range(self.cols)] for y in range(self.rows)]
        self.next_grid = [[(0) for x in range(self.cols)] for y in range(
            self.rows)]
        self.running = True
        self.paused = True
        self.clock = pygame.time.Clock()

    def count_neighbors(self, row, col):
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                r = (row + i + self.rows) % self.rows
                c = (col + j + self.cols) % self.cols
                count += self.grid[r][c]
        return count

    def update_grid(self):
        if self.paused:
            return
        for row in range(self.rows):
            for col in range(self.cols):
                neighbors = self.count_neighbors(row, col)
                state = self.grid[row][col]
                if state == 0 and neighbors == 3:
                    self.next_grid[row][col] = 1
                elif state == 1 and (neighbors < 2 or neighbors > 3):
                    self.next_grid[row][col] = 0
                else:
                    self.next_grid[row][col] = state
        self.grid, self.next_grid = self.next_grid, self.grid

    def toggle_cell(self, pos):
        col = pos[0] // self.cell_size
        row = pos[1] // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = 1 - self.grid[row][col]

    def draw(self):
        self.screen.fill((0, 0, 0))
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 1:
                    pygame.draw.rect(self.screen, (255, 255, 255), (col *
                        self.cell_size, row * self.cell_size, self.
                        cell_size - 1, self.cell_size - 1))
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.toggle_cell(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
            self.update_grid()
            self.draw()
            self.clock.tick(10)
        pygame.quit()


def main():
    game = GameOfLife()
    game.run()

if __name__ == '__main__':
    main()
