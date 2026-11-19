from pico2d import load_image

from config import TILE, TILE_SRC, PLAYER_HALF_W, MOVING_SPEED, MOVING_PAUSE

SOLID_H = int(20 * TILE / TILE_SRC)     # 발판 그림은 칸 위쪽 20px(원본)만 차지하므로 충돌도 그만큼만
ANIM_FPS = 4                            # 톱니가 돌고 화살표가 깜빡이는 속도


class MovingPlatform:
    """움직이는 발판: 가로로 이어진 칸들이 한 덩어리로 정해진 범위를 왕복.
    axis = 'x'(좌우) / 'y'(위아래). lo~hi = 발판 왼쪽 아래 칸이 갈 수 있는 범위 (열 또는 줄 번호).
    끝에 닿으면 MOVING_PAUSE 동안 멈췄다가 돌아섬. 위에 서 있는 플레이어를 함께 옮김"""
    sheets = {}

    def __init__(self, c0, c1, row, axis, lo, hi, style, ice):
        if style not in MovingPlatform.sheets:
            MovingPlatform.sheets[style] = load_image(f'asset/tiles/tiles_moving_{style}.png')
        self.sheet = MovingPlatform.sheets[style]
        self.width = (c1 - c0 + 1) * TILE
        self.axis = axis
        self.ice = ice
        self.x, self.y = c0 * TILE, (row + 1) * TILE          # 발판 왼쪽 위 (윗면)
        if axis == 'x':
            self.lo, self.hi = lo * TILE, hi * TILE
            start = self.x
        else:
            self.lo, self.hi = (lo + 1) * TILE, (hi + 1) * TILE
            start = self.y
        # 넓은 쪽으로 먼저 출발
        self.dir = 1 if self.hi - start >= start - self.lo else -1
        self.wait = 0.0
        self.t = 0.0

    def rect(self):
        return self.x, self.y - SOLID_H, self.x + self.width, self.y

    def solid_rects(self):
        return [(self.rect(), self.ice)]

    def carries(self, player):
        """플레이어가 발판 위에 서 있는지"""
        return (player.on_ground and abs(player.y - self.y) < 1
                and player.x + PLAYER_HALF_W > self.x and player.x - PLAYER_HALF_W < self.x + self.width)

    def update(self, dt, tilemap, player):
        self.t += dt
        if self.wait > 0:
            self.wait -= dt
            return
        riding = self.carries(player)
        pos = self.x if self.axis == 'x' else self.y
        new = pos + self.dir * MOVING_SPEED * dt
        if new >= self.hi or new <= self.lo:
            new = min(self.hi, max(self.lo, new))
            self.dir = -self.dir
            self.wait = MOVING_PAUSE
        delta = new - pos

        if self.axis == 'x':
            self.x = new
        else:
            self.y = new
            # 올라오다 아래에서 플레이어 발에 닿으면 위로 받쳐 올림 (뚫고 지나가지 않게)
            if (not riding and delta > 0 and player.vy <= 0 and pos - 1 <= player.y <= new
                    and player.x + PLAYER_HALF_W > self.x and player.x - PLAYER_HALF_W < self.x + self.width):
                riding = True
                player.y = pos
        if riding:
            # 올라탄 플레이어도 같이 움직임 (가로는 벽에 막힘)
            if self.axis == 'x':
                player.move_x(delta, tilemap)
            else:
                player.y += delta
                if not player.on_ground:
                    player.vy = 0.0
                    player.on_ground = True
                    player.on_landed(0.0, tilemap)

    def draw(self, cam_y):
        frame = int(self.t * ANIM_FPS) % 2
        n = int(round(self.width / TILE))
        for i in range(n):
            kind = 1 if n == 1 else 0 if i == 0 else 2 if i == n - 1 else 1   # 0 왼쪽 끝, 1 가운데, 2 오른쪽 끝
            self.sheet.clip_draw(kind * TILE_SRC, self.sheet.h - (frame + 1) * TILE_SRC, TILE_SRC, TILE_SRC,
                                 self.x + (i + 0.5) * TILE, self.y - TILE / 2 - cam_y, TILE, TILE)
