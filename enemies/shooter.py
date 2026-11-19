from config import SCALE, TILE, PLAYER_H
from enemies.enemy import Enemy

SHOOT_FPS = 10
ORIGIN_FOOT = 84             # 시트(asset/enemy/enemies_ranged.json)에서 발 위치 (원본 px, 칸 위에서부터)
GRASS = 2                    # 발을 타일 위쪽 잔디 속에 묻는 깊이 (원본 px)


class Shooter(Enemy):
    """투사체를 쏘는 적의 공통 부분 (궁수·가고일·서리 마법사).
    대기 → 조준(예고 동작) → 발사 → 휴식 → 대기 를 반복. 몸에 닿아도 피해 없음.
    쏜 투사체는 self.shots 에 담아 두면 게임 루프가 가져감"""
    CONTACT_HIT = False
    ROW_IDLE, ROW_AIM, ROW_SHOOT, ROW_DIE, ROW_RESPAWN = 0, 1, 2, 3, 4
    IDLE_FRAMES, IDLE_FPS, AIM_FRAMES, SHOOT_FRAMES = 4, 5, 4, 3
    FOOT_ROW = ORIGIN_FOOT       # 그림 속 발바닥 아래 끝 (원본 px)
    SHOOT_ORIGIN = (50, 50)      # 투사체가 나오는 자리 (오른쪽 보는 그림 기준 원본 px)
    HALF_W, HEIGHT = 15, 50      # 충돌 박스 (발 중앙 기준)
    AIM_TIME = REST_TIME = 1.0

    def __init__(self, col, row, facing):
        self.start_facing = facing
        self.shots = []
        super().__init__((col + 0.5) * TILE, row * TILE)     # 발이 아래 칸 바닥 윗면에 닿게

    def reset(self):
        super().reset()
        self.facing = self.start_facing
        self.act, self.act_t = 'idle', 0.0

    def set_act(self, act):
        self.act, self.act_t = act, 0.0

    def hitbox(self):
        return self.x - self.HALF_W, self.y, self.x + self.HALF_W, self.y + self.HEIGHT

    def draw_y(self):
        return self.y + (self.FOOT_ROW - 50 - GRASS) * SCALE

    def origin(self):
        """투사체가 나오는 화면 위치 (보는 방향에 맞춰 좌우 뒤집음)"""
        ox, oy = self.SHOOT_ORIGIN
        return self.x + self.facing * (ox - 50) * SCALE, self.y + (self.FOOT_ROW - GRASS - oy) * SCALE

    def face(self, x):
        self.facing = 1 if x >= self.x else -1

    # 자식 클래스가 정함
    def notices(self, tilemap, player):
        """플레이어를 알아차려 조준을 시작할지"""
        raise NotImplementedError

    def fire(self, player):
        """투사체를 만들어 self.shots 에 넣음"""
        raise NotImplementedError

    def move(self, dt, tilemap):
        pass                     # 기본은 제자리

    # ---------------- 갱신 ----------------
    def think(self, dt, tilemap, player):
        self.act_t += dt
        if self.act == 'idle':
            self.move(dt, tilemap)
            if self.notices(tilemap, player):
                self.face(player.x)
                self.set_act('aim')
        elif self.act == 'aim':
            if self.act_t >= self.AIM_TIME:
                self.fire(player)
                self.set_act('shoot')
        elif self.act == 'shoot':
            if self.act_t >= self.SHOOT_FRAMES / SHOOT_FPS:
                self.set_act('rest')
        elif self.act == 'rest':
            if self.act_t >= self.REST_TIME:
                self.set_act('idle')

    def alive_frame(self):
        if self.act == 'aim':
            # 조준 시간에 맞춰 한 번 넘김 (마지막 프레임 = 쏘기 직전 예고)
            return self.ROW_AIM, min(self.AIM_FRAMES - 1, int(self.act_t / self.AIM_TIME * self.AIM_FRAMES))
        if self.act == 'shoot':
            return self.ROW_SHOOT, min(self.SHOOT_FRAMES - 1, int(self.act_t * SHOOT_FPS))
        return self.ROW_IDLE, int(self.t * self.IDLE_FPS) % self.IDLE_FRAMES

    # ---------------- 보조 ----------------
    @staticmethod
    def clear_line(tilemap, x1, y1, x2, y2):
        """두 점 사이에 블록이 없는지 (시야 확인)"""
        n = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) // 12))
        for i in range(1, n):
            x = x1 + (x2 - x1) * i / n
            y = y1 + (y2 - y1) * i / n
            if tilemap.solids_in(x - 1, y - 1, x + 1, y + 1) or tilemap.point_in_slope(x, y):
                return False
        return True

    @staticmethod
    def player_center(player):
        return player.x, player.y + PLAYER_H / 2
