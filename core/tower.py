from pico2d import load_image

from config import (TILE, TOWER_DIR, TOWER_SCALE, TOWER_PIECE, TOWER_PILLAR,
                    TOWER_INNER_COL, TOWER_INNER_COLS, TOWER_PIECES, HEIGHT)


class Tower:
    """맵 뒤에 그리는 탑 배경. 조각을 아래부터 쌓고, 기둥 안쪽 가운데에 플레이 공간이 오도록 위치를 맞춤"""
    def __init__(self):
        self.images = [load_image(f'{TOWER_DIR}/{name}.png') for name in TOWER_PIECES]
        self.size = TOWER_PIECE * TOWER_SCALE
        inner_w = (TOWER_PIECE - 2 * TOWER_PILLAR) * TOWER_SCALE
        slack = (inner_w - TOWER_INNER_COLS * TILE) / 2           # 칸으로 다 못 채운 양옆 여백
        inner_left = TOWER_INNER_COL * TILE - slack
        self.cx = inner_left - TOWER_PILLAR * TOWER_SCALE + self.size / 2
        self.height = self.size * len(self.images)

    def draw(self, cam_y):
        for i, img in enumerate(self.images):
            bottom = i * self.size
            if bottom > cam_y + HEIGHT or bottom + self.size < cam_y:
                continue
            img.draw(self.cx, bottom + self.size / 2 - cam_y, self.size, self.size)
