from pico2d import (load_image, SDL_KEYDOWN, SDL_KEYUP,
                    SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_TAB, SDLK_z, SDLK_x)

from anim import Anim
from config import (CELL, SCALE, FOOT_IN_CELL, PLAYER_HALF_W, PLAYER_H,
                    MOVE_SPEED, JUMP_SPEED, JUMP_CUT_SPEED, GRAVITY, MAX_FALL_SPEED,
                    ICE_ACCEL, ICE_FRICTION, INVINCIBLE_TIME, GUN_RECOIL_UP, GUN_RECOIL_BACK)

KNOCKED = ('fall', 'down', 'getup')     # 넘어져서 조작할 수 없는 상태
MAX_STEP = 0.008                        # 빠르게 떨어질 때 타일을 뚫지 않도록 나눠서 이동

# 총 반동: 목표 높이까지 뜨는 속도와, 떴다 내려오는 시간 동안 목표 거리만큼 밀리는 속도
RECOIL_VY = (2 * GRAVITY * GUN_RECOIL_UP) ** 0.5 + GRAVITY * MAX_STEP / 2   # 뒤쪽은 나눠서 계산할 때 생기는 오차 보정
RECOIL_TIME = 2 * RECOIL_VY / GRAVITY
RECOIL_VX = GUN_RECOIL_BACK / RECOIL_TIME
# 총구에서 불꽃이 나오는 프레임 (이때 반동이 생김)
GUN_FIRE_FRAME = {'gun': 3, 'jump_gun': 1}


class Player:
    def __init__(self, x, y):
        main = load_image('asset/player/spritesheet_left.png')
        extra = load_image('asset/player/player_extra_left.png')
        self.anims = {
            'idle':        Anim(main, 0, 4, 6),
            'walk':        Anim(main, 1, 6, 10),
            # feet: 프레임별 발바닥 위치 (공중 동작만, 스프라이트를 바꾸면 다시 재야 함)
            'jump':        Anim(main, 2, 6, 10, loop=False, feet=[83, 80, 57, 48, 66, 83]),
            'sword':       Anim(main, 3, 8, 20, loop=False),
            'gun':         Anim(main, 4, 7, 18, loop=False),
            'getup':       Anim(extra, 0, 6, 10, loop=False),
            'fall':        Anim(extra, 1, 6, 12, loop=False),
            'jump_sword':  Anim(extra, 2, 7, 20, loop=False, feet=[65, 65, 65, 65, 68, 68, 65]),
            'jump_gun':    Anim(extra, 3, 6, 18, loop=False, feet=[77, 74, 69, 65, 64, 66]),
        }
        self.x, self.y = x, y          # 발 중앙
        self.vx = self.vy = 0.0
        self.facing = 1                # -1: 왼쪽, 1: 오른쪽
        self.left = self.right = False
        self.weapon = 'sword'
        self.on_ground = True
        self.on_ice = False
        self.invincible = 0.0
        self.recoil = 0.0              # 총 반동으로 밀려나는 남은 시간
        self.set_state('idle')

    # ---------------- 상태 ----------------
    def set_state(self, state):
        self.state = state
        self.t = 0.0
        self.fired = False             # 이번 공격에서 총을 이미 쐈는지

    def hitbox(self):
        return (self.x - PLAYER_HALF_W, self.y, self.x + PLAYER_HALF_W, self.y + PLAYER_H)

    def can_control(self):
        """좌우 입력을 받는 상태인지 (넘어짐 중, 땅에서 공격 중에는 X)"""
        if self.state in KNOCKED or self.recoil > 0:
            return False
        return not (self.state == 'attack' and self.on_ground)

    def hit(self, knock_x, knock_y):
        """함정에 맞음: 보고 있는 방향 기준 뒤로 날아가며 넘어짐"""
        if self.invincible > 0 or self.state in KNOCKED:
            return
        self.recoil = 0.0
        self.vx = -self.facing * knock_x
        if knock_y > 0:
            self.vy = knock_y
            self.on_ground = False
        self.set_state('fall')

    # ---------------- 입력 ----------------
    def handle_event(self, e):
        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_LEFT:
                self.left = True
            elif e.key == SDLK_RIGHT:
                self.right = True
            elif e.key == SDLK_TAB:
                if self.state not in ('attack', 'jump_attack'):     # 공격 중에는 무기 교체 불가
                    self.weapon = 'gun' if self.weapon == 'sword' else 'sword'
            elif e.key == SDLK_UP:
                if self.on_ground and self.state in ('idle', 'walk', 'land'):
                    self.vy = JUMP_SPEED
                    self.on_ground = False
                    self.set_state('jump')
            elif e.key == SDLK_z:
                if self.state in ('idle', 'walk', 'land'):
                    self.set_state('attack')
                elif self.state == 'jump':
                    self.set_state('jump_attack')
            elif e.key == SDLK_x:
                # 테스트용: 제자리에서 뒤로 넘어지기
                if self.on_ground and self.state in ('idle', 'walk', 'land'):
                    self.hit(0, 0)
        elif e.type == SDL_KEYUP:
            if e.key == SDLK_LEFT:
                self.left = False
            elif e.key == SDLK_RIGHT:
                self.right = False
            elif e.key == SDLK_UP:
                # 올라가는 도중에 키를 떼면 상승 속도를 깎아서 낮은 점프
                if not self.on_ground and self.vy > JUMP_CUT_SPEED:
                    self.vy = JUMP_CUT_SPEED

    # ---------------- 갱신 ----------------
    def update(self, dt, tilemap):
        self.t += dt
        self.invincible = max(0.0, self.invincible - dt)
        direction = self.right - self.left
        self.check_gun_fire()
        control = self.can_control()

        # 수평 속도
        target = direction * MOVE_SPEED if control else 0.0
        if control and direction != 0:
            self.facing = direction
        if self.recoil > 0:
            pass                            # 반동 중에는 밀려나는 속도 유지
        elif self.on_ground:
            if self.on_ice:
                rate = ICE_ACCEL if target != 0 else ICE_FRICTION
                self.vx = approach(self.vx, target, rate * dt)
            else:
                self.vx = target
        elif control:
            self.vx = target            # 공중 조작 (넘어져 날아가는 중에는 속도 유지)

        # 이동 + 충돌 (조금씩 나눠서)
        remaining = dt
        while remaining > 0:
            step = min(MAX_STEP, remaining)
            remaining -= step
            if not self.on_ground:
                self.vy = max(-MAX_FALL_SPEED, self.vy - GRAVITY * step)
            if self.recoil > 0 and self.recoil < step:
                step_x = self.recoil                # 반동이 끝나는 순간까지만 밀림
            else:
                step_x = step
            self.move_x(self.vx * step_x, tilemap)
            self.move_y(self.vy * step, tilemap)
            if self.recoil > 0:
                self.recoil -= step
                if self.recoil <= 0 and not self.on_ice:
                    self.vx = 0.0                   # 얼음 위가 아니면 반동 끝나면 멈춤

        self.check_ground(tilemap)
        self.update_state(direction)

    def check_gun_fire(self):
        """총 공격 애니메이션이 발사 프레임에 닿으면 반동을 줌"""
        if self.weapon != 'gun' or self.fired or self.state not in ('attack', 'jump_attack'):
            return
        name = 'gun' if self.state == 'attack' else 'jump_gun'
        if self.anims[name].frame_at(self.t) >= GUN_FIRE_FRAME[name]:
            self.fired = True
            self.recoil = RECOIL_TIME
            self.vx = -self.facing * RECOIL_VX
            self.vy = RECOIL_VY
            self.on_ground = False

    def move_x(self, dx, tilemap):
        if dx == 0:
            return
        self.x += dx
        for (l, b, r, t), _ in tilemap.solids_in(*self.hitbox()):
            if dx > 0:
                self.x = l - PLAYER_HALF_W
            else:
                self.x = r + PLAYER_HALF_W
            self.vx = 0.0

    def move_y(self, dy, tilemap):
        if dy == 0:
            return
        self.y += dy
        for (l, b, r, t), ice in tilemap.solids_in(*self.hitbox()):
            if dy < 0:
                self.y = t
                self.vy = 0.0
                if not self.on_ground:
                    self.on_ground = True
                    self.on_landed()
            else:
                self.y = b - PLAYER_H
                self.vy = 0.0

    def check_ground(self, tilemap):
        """발 바로 아래(1px 이내)에 땅이 있는지, 얼음인지 확인"""
        feet = (self.x - PLAYER_HALF_W + 1, self.y - 1, self.x + PLAYER_HALF_W - 1, self.y)
        under = tilemap.solids_in(*feet) if self.vy <= 0 else []
        if under and not self.on_ground:
            # 땅에 거의 닿은 채로 프레임이 끝난 경우에도 확실하게 착지 처리
            self.y = max(rect[3] for rect, _ in under)
            self.vy = 0.0
            self.on_ground = True
            self.on_landed()
        self.on_ground = bool(under)
        self.on_ice = any(ice for _, ice in under)

    def on_landed(self):
        s = self.state
        if s == 'jump':
            self.set_state('land')
        elif s == 'jump_attack':
            # 공중 공격 스프라이트는 그림 안에서 위로 떠 있으므로,
            # 착지하면 진행된 비율만큼 지상 공격 애니메이션으로 이어서 재생
            progress = self.t / self.anims['jump_' + self.weapon].duration
            self.set_state('attack')
            self.t = progress * self.anims[self.weapon].duration

    def update_state(self, direction):
        s = self.state
        if s in ('idle', 'walk', 'land') and not self.on_ground:
            self.set_state('jump')                       # 발판에서 걸어 나가 떨어짐
        elif s in ('idle', 'walk'):
            want = 'walk' if direction != 0 else 'idle'
            if want != s:
                self.set_state(want)
        elif s == 'land' and self.t >= 0.08:
            self.set_state('idle')
        elif s == 'attack' and self.on_ground and self.t >= self.anims[self.weapon].duration:
            self.set_state('idle')      # 반동으로 떠 있으면 착지할 때까지 공격 마지막 자세 유지
        elif s == 'jump_attack' and self.t >= self.anims['jump_' + self.weapon].duration:
            self.set_state('jump')
        elif s == 'fall' and self.on_ground and self.t >= self.anims['fall'].duration:
            self.set_state('down')
        elif s == 'down' and self.t >= 0.6:
            self.set_state('getup')
        elif s == 'getup' and self.t >= self.anims['getup'].duration:
            self.set_state('idle')
            self.invincible = INVINCIBLE_TIME

    # ---------------- 그리기 ----------------
    def current_frame(self):
        s = self.state
        if s == 'jump':
            # 점프 프레임은 시간 대신 수직 속도로 고름: 1 도약, 2 상승, 3 정점, 4 하강
            if self.vy > JUMP_SPEED * 0.5:
                f = 1
            elif self.vy > 180:
                f = 2
            elif self.vy > -180:
                f = 3
            else:
                f = 4
            return self.anims['jump'], f
        if s == 'land':
            return self.anims['jump'], 5
        if s == 'attack':
            a = self.anims[self.weapon]
        elif s == 'jump_attack':
            a = self.anims['jump_' + self.weapon]
        elif s == 'down':
            return self.anims['getup'], 0          # 누워있는 프레임
        else:
            a = self.anims[s]
        return a, a.frame_at(self.t)

    def draw(self, cam_y):
        if self.invincible > 0 and int(self.invincible * 12) % 2:
            return                                  # 무적 시간 동안 깜빡임
        anim, frame = self.current_frame()
        cy = self.y + (CELL // 2 - FOOT_IN_CELL) * SCALE - cam_y
        anim.draw(frame, self.x, cy, self.facing)


def approach(value, target, amount):
    if value < target:
        return min(value + amount, target)
    return max(value - amount, target)
