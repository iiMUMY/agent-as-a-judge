class GridworldEnv:
    def __init__(self, grid_size=(5, 5), start_pos=(0, 0), end_pos=(4, 4)):
        self.grid_size = grid_size
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.state = start_pos

    def reset(self):
        self.state = self.start_pos
        return self.state

    def step(self, action):
        # Placeholder dynamics for evaluation artifact.
        return self.state, 0.0, self.state == self.end_pos, {}
