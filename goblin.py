from config import SCALE, TILE, ENEMY_SPEED
from enemy import Enemy

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
        self.x += self.facing * ENEMY_SPEED * dt
        front = self.x + self.facing * HALF_W
        col = int(front // TILE)
        # 몸 앞쪽 끝이 블록에 닿았는지 (머리 위에 떠 있는 발판은 상관없음)
        blocked = bool(tilemap.solids_in(front - 1, self.y + 1, front + 1, self.y + HEIGHT - 1))
        # 앞발 바로 아래에 땅이 없는지
        no_ground = not tilemap.solids_in(front - 1, self.y - 2, front + 1, self.y - 1)
        if blocked or no_ground:
            # 앞이 막혔거나 낭떠러지면 돌아섬 (넘어간 만큼 되돌림)
            edge = (col * TILE) if self.facing > 0 else ((col + 1) * TILE)
            self.x = edge - self.facing * (HALF_W + 0.01)
            self.facing = -self.facing

    def draw_y(self):
        # 발바닥을 타일 위 2px 잔디 속에 살짝 묻히게 (캐릭터와 같은 기준)
        return self.y + (FOOT_ROW - 50 - 2) * SCALE
