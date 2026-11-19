from config import TILE, ENEMY_SPEED, ARCHER_RANGE, ARCHER_AIM_TIME, ARCHER_REST_TIME, ARROW_SPEED
from enemies.projectile import Projectile
from enemies.shooter import Shooter


class Archer(Shooter):
    """고블린 궁수: 고블린처럼 순찰하다가 바라보는 쪽 같은 높이에 플레이어가 보이면
    멈춰서 활을 당기고(예고) 직선으로 화살을 쏨"""
    SHEET = 'asset/enemy/archer_right.png'
    IDLE_FRAMES, IDLE_FPS = 6, 10        # 대기 줄 = 걷는 동작
    FOOT_ROW = 85
    SHOOT_ORIGIN = (62, 64)
    HALF_W, HEIGHT = 15, 54
    AIM_TIME, REST_TIME = ARCHER_AIM_TIME, ARCHER_REST_TIME

    def move(self, dt, tilemap):
        self.patrol(dt, tilemap, ENEMY_SPEED, self.HALF_W, self.HEIGHT)

    def notices(self, tilemap, player):
        dx = player.x - self.x
        if dx * self.facing <= 0 or abs(dx) > ARCHER_RANGE:
            return False                                   # 등 뒤나 너무 먼 곳은 못 봄
        if abs(player.y - self.y) > TILE * 0.75:
            return False                                   # 거의 같은 높이에 있어야 보임
        ox, oy = self.origin()
        return self.clear_line(tilemap, ox, oy, player.x, oy)

    def fire(self, player):
        ox, oy = self.origin()
        self.shots.append(Projectile('arrow', ox, oy, self.facing * ARROW_SPEED, 0))

    def alive_frame(self):
        if self.act == 'rest':
            return self.ROW_IDLE, 0                        # 쏜 뒤에는 서서 쉼
        return super().alive_frame()
