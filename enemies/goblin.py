from config import SCALE, TILE, ENEMY_SPEED
from enemies.enemy import Enemy

HALF_W, HEIGHT = 15, 50       # 충돌 박스 (발 중앙 기준, 스프라이트 키 33px x 1.5)
FOOT_ROW = 87                 # 시트 칸 안에서 발바닥 아래 끝 (원본 px)


class Goblin(Enemy):
    """좌우로만 걷는 적. 앞이 벽이거나 땅이 끝나면 돌아섬"""
    ROW_MOVE, ROW_DIE, ROW_RESPAWN = 0, 1, 2

    def __init__(self, col, row):
        super().__init__((col + 0.5) * TILE, row * TILE)     # 발이 아래 칸 바닥 윗면에 닿게

    def hitbox(self):
        return self.x - HALF_W, self.y, self.x + HALF_W, self.y + HEIGHT

    def move(self, dt, tilemap):
        self.patrol(dt, tilemap, ENEMY_SPEED, HALF_W, HEIGHT)

    def draw_y(self):
        # 발바닥을 타일 위 2px 잔디 속에 살짝 묻히게 (캐릭터와 같은 기준)
        return self.y + (FOOT_ROW - 50 - 2) * SCALE
