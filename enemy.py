from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, TILE, ENEMY_RESPAWN_TIME, ENEMY_KNOCK, ENEMY_HIT_INTERVAL

MOVE_FPS, DIE_FPS, RESPAWN_FPS = 10, 12, 10


class Enemy:
    """모든 적이 함께 쓰는 부분: 죽음 → 5초 뒤 처음 자리에서 리스폰, 플레이어와 닿으면 피격"""
    images = {}                               # 시트는 처음 쓸 때 한 번만 불러서 공유
    SHEET = 'asset/enemy/monsters_right.png'  # 원본은 오른쪽을 보고 있음 (왼쪽은 뒤집어 그림)
    ROW_MOVE = ROW_DIE = ROW_RESPAWN = 0      # 시트에서 쓰는 줄 (자식 클래스가 정함)
    MOVE_FRAMES, DIE_FRAMES, RESPAWN_FRAMES = 6, 5, 5
    CONTACT_HIT = True                        # 몸에 닿으면 플레이어가 맞는지

    def __init__(self, x, y):
        if self.SHEET not in Enemy.images:
            Enemy.images[self.SHEET] = load_image(self.SHEET)
        self.sheet = Enemy.images[self.SHEET]
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

    def think(self, dt, tilemap, player):
        """살아 있는 동안 매 프레임 할 일 (기본: 움직이기만)"""
        self.move(dt, tilemap)

    def alive_frame(self):
        """살아 있을 때 그릴 (줄, 프레임)"""
        return self.ROW_MOVE, int(self.t * MOVE_FPS) % self.MOVE_FRAMES

    def patrol(self, dt, tilemap, speed, half_w, height):
        """좌우로 걷다가 앞이 벽이거나 땅이 끝나면 돌아섬 (고블린·궁수)"""
        self.x += self.facing * speed * dt
        front = self.x + self.facing * half_w
        col = int(front // TILE)
        # 몸 앞쪽 끝이 블록에 닿았는지 (머리 위에 떠 있는 발판은 상관없음)
        blocked = bool(tilemap.solids_in(front - 1, self.y + 1, front + 1, self.y + height - 1))
        # 앞발 바로 아래에 땅이 없는지
        no_ground = not tilemap.solids_in(front - 1, self.y - 2, front + 1, self.y - 1)
        if blocked or no_ground:
            # 앞이 막혔거나 낭떠러지면 돌아섬 (넘어간 만큼 되돌림)
            edge = (col * TILE) if self.facing > 0 else ((col + 1) * TILE)
            self.x = edge - self.facing * (half_w + 0.01)
            self.facing = -self.facing

    # ---------------- 갱신 ----------------
    def update(self, dt, tilemap, player):
        self.t += dt
        if self.state == 'alive':
            self.think(dt, tilemap, player)
            self.hit_wait = max(0.0, self.hit_wait - dt)
            if self.CONTACT_HIT and self.hit_wait == 0 and overlap(self.hitbox(), player.hitbox()):
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
            row, frame = self.alive_frame()
        elif self.state == 'dying':
            row, frame = self.ROW_DIE, min(self.DIE_FRAMES - 1, int(self.t * DIE_FPS))
        else:
            row, frame = self.ROW_RESPAWN, min(self.RESPAWN_FRAMES - 1, int(self.t * RESPAWN_FPS))
        flip = 'h' if self.facing < 0 else ''
        sheet = self.sheet
        sheet.clip_composite_draw(frame * CELL, sheet.h - (row + 1) * CELL, CELL, CELL, 0, flip,
                                  self.x, self.draw_y() - cam_y, CELL * SCALE, CELL * SCALE)

