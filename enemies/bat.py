import math

from config import TILE, ENEMY_SPEED
from enemies.enemy import Enemy

HALF_W, HALF_H = 20, 16       # 충돌 박스 (몸 중앙 기준)


class Bat(Enemy):
    """정해진 범위 안에서 위아래로 부드럽게 오가는 적.
    범위는 맵에서 B 위아래로 이어 붙인 ':' 칸들 (가장 아래 칸 ~ 가장 위 칸의 가운데 사이)"""
    ROW_MOVE, ROW_DIE, ROW_RESPAWN = 3, 4, 5

    def __init__(self, col, row, low_row, high_row):
        self.low = (low_row + 0.5) * TILE
        self.high = (high_row + 0.5) * TILE
        super().__init__((col + 0.5) * TILE, (row + 0.5) * TILE)

    def reset(self):
        super().reset()
        mid = (self.low + self.high) / 2
        amp = (self.high - self.low) / 2
        # 맵에 놓은 B 위치에서 시작하도록 위상을 맞춤
        self.phase = math.asin(max(-1.0, min(1.0, (self.spawn_y - mid) / amp))) if amp > 0 else 0.0

    def hitbox(self):
        return self.x - HALF_W, self.y - HALF_H, self.x + HALF_W, self.y + HALF_H

    def move(self, dt, tilemap):
        amp = (self.high - self.low) / 2
        if amp <= 0:
            return
        # 사인 곡선으로 오가면서 가장 빠를 때 속도가 ENEMY_SPEED가 되도록
        self.phase += ENEMY_SPEED / amp * dt
        self.y = (self.low + self.high) / 2 + amp * math.sin(self.phase)

    def face_toward(self, player_x):
        """박쥐는 플레이어 쪽을 바라봄 (그림만)"""
        self.facing = 1 if player_x >= self.x else -1

    def update(self, dt, tilemap, player):
        if self.is_alive():
            self.face_toward(player.x)
        super().update(dt, tilemap, player)

    def draw_y(self):
        return self.y
