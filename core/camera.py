from config import HEIGHT


class Camera:
    """세로로만 움직이는 카메라. y = 화면 맨 아래가 보여주는 월드 높이"""
    def __init__(self, map_height):
        self.map_height = map_height
        self.y = 0.0

    def target_of(self, player_y):
        want = player_y + 60 - HEIGHT / 2
        return max(0.0, min(self.map_height - HEIGHT, want))

    def snap(self, player_y):
        self.y = self.target_of(player_y)

    def update(self, dt, player_y):
        self.y += (self.target_of(player_y) - self.y) * min(1.0, dt * 8)
