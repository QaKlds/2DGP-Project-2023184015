from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, ENEMY_RESPAWN_TIME, ENEMY_KNOCK, ENEMY_HIT_INTERVAL

SHEET = 'asset/enemy/monsters_right.png'   # 원본은 오른쪽을 보고 있음
MOVE_FPS, DIE_FPS, RESPAWN_FPS = 10, 12, 10


class Enemy:
    """고블린·박쥐가 함께 쓰는 부분: 죽음 → 5초 뒤 처음 자리에서 리스폰, 플레이어와 닿으면 피격"""
    sheet = None
    ROW_MOVE = ROW_DIE = ROW_RESPAWN = 0      # 시트에서 쓰는 줄 (자식 클래스가 정함)
    MOVE_FRAMES, DIE_FRAMES, RESPAWN_FRAMES = 6, 5, 5

    def __init__(self, x, y):
        if Enemy.sheet is None:
            Enemy.sheet = load_image(SHEET)
        self.spawn_x, self.spawn_y = x, y
        self.reset()

    def reset(self):
        """처음 자리로 되돌림 (리스폰할 때도 사용)"""
        self.hit_wait = 0.0        # 플레이어를 다시 때릴 수 있을 때까지 남은 시간
        self.x, self.y = self.spawn_x, self.spawn_y
        self.facing = 1
        self.state, self.t = 'alive', 0.0

    def is_alive(self):
        return self.state == 'alive'

    def kill(self):
        if self.is_alive():
            self.state, self.t = 'dying', 0.0
            self.dead_time = 0.0

    # 자식 클래스가 정함
    def hitbox(self):
        raise NotImplementedError

    def move(self, dt, tilemap):
        raise NotImplementedError

    def draw_y(self):
        """시트 칸의 중심을 그릴 높이"""
        raise NotImplementedError

    # ---------------- 갱신 ----------------
    def update(self, dt, tilemap, player):
        self.t += dt
        if self.state == 'alive':
            self.move(dt, tilemap)
            self.hit_wait = max(0.0, self.hit_wait - dt)
            if self.hit_wait == 0 and overlap(self.hitbox(), player.hitbox()):
                # 닿으면 맞고, 계속 닿아 있으면 ENEMY_HIT_INTERVAL 마다 다시 맞음. 넘어진 중이면 적 반대쪽으로 다시 밀려남
                player.hit(*ENEMY_KNOCK, source_x=self.x)
                self.hit_wait = ENEMY_HIT_INTERVAL
            return

        self.dead_time += dt
        if self.state == 'dying' and self.t >= self.DIE_FRAMES / DIE_FPS:
            self.state, self.t = 'dead', 0.0
        elif self.state == 'dead' and self.dead_time >= ENEMY_RESPAWN_TIME:
            self.reset()
            self.state, self.t = 'respawn', 0.0
        elif self.state == 'respawn' and self.t >= self.RESPAWN_FRAMES / RESPAWN_FPS:
            self.state, self.t = 'alive', 0.0

    # ---------------- 그리기 ----------------
    def draw(self, cam_y):
        if self.state == 'dead':
            return
        if self.state == 'alive':
            row, frame = self.ROW_MOVE, int(self.t * MOVE_FPS) % self.MOVE_FRAMES
        elif self.state == 'dying':
            row, frame = self.ROW_DIE, min(self.DIE_FRAMES - 1, int(self.t * DIE_FPS))
        else:
            row, frame = self.ROW_RESPAWN, min(self.RESPAWN_FRAMES - 1, int(self.t * RESPAWN_FPS))
        flip = 'h' if self.facing < 0 else ''
        sheet = Enemy.sheet
        sheet.clip_composite_draw(frame * CELL, sheet.h - (row + 1) * CELL, CELL, CELL, 0, flip,
                                  self.x, self.draw_y() - cam_y, CELL * SCALE, CELL * SCALE)
