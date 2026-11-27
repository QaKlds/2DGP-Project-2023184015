from pico2d import (load_image, SDL_KEYDOWN, SDL_KEYUP,
                    SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_TAB, SDLK_z, SDLK_x)

from core.anim import Anim
from config import (TICK, CELL, SCALE, FOOT_IN_CELL, PLAYER_HALF_W, PLAYER_H,
                    MOVE_SPEED, JUMP_SPEED, JUMP_CUT_SPEED, GRAVITY, MAX_FALL_SPEED,
                    ICE_ACCEL, ICE_FRICTION, ICE_EDGE_SPEED, ICE_LANDING_SPEED, INVINCIBLE_TIME, GUN_RECOIL_UP, GUN_RECOIL_BACK,
                    FALL_HEIGHT_SLIDE, SLOPE_SPEED, SLOPE_ACCEL, SLOPE_AIR_DECEL, KNOCK_BOUNCE_UP, KNOCK_SLIDE_DECEL, TILE)
from core.tilemap import FLOOR_SLOPES, SLOPES

KNOCKED = ('fall', 'fall_height', 'down', 'getup')     # 넘어져서 조작할 수 없는 상태
MAX_STEP = TICK                         # 빠르게 떨어질 때 타일을 뚫지 않도록 나눠서 이동 (게임 계산 한 번 = 한 걸음)
BLINK_RATE = 12                         # 무적일 때 1초에 깜빡이는 횟수 x2 (켜짐/꺼짐)
SLOPE_DEPTH = 16                        # 발 중앙이 경사면 속으로 이만큼(px)까지 파고들면 위로 올려 줌 (더 깊으면 옆면에 막힘)

# 총 반동: 목표 높이까지 뜨는 속도와, 떴다 내려오는 시간 동안 목표 거리만큼 밀리는 속도
RECOIL_VY = (2 * GRAVITY * GUN_RECOIL_UP) ** 0.5 + GRAVITY * MAX_STEP / 2   # 뒤쪽은 나눠서 계산할 때 생기는 오차 보정
RECOIL_TIME = 2 * RECOIL_VY / GRAVITY
RECOIL_VX = GUN_RECOIL_BACK / RECOIL_TIME
# 넘어져 누우면 몸이 그림 속에서 뒤로 18px(원본) 가 있음. 그 자리에서 일어나도록
# 누울 때 실제 x를 그만큼 뒤로 옮기고, 일어나는 동안 프레임별로 그림을 보정해서 몸이 제자리에 있게 함
LIE_BACK = 18
GETUP_BODY_SHIFT = [18, 16, 4, -1, -2, 0]   # 일어나기 프레임별 (서 있을 때 몸 위치 - 그 프레임 몸 위치), 원본 px

# 넘어진 동작 프레임별로 실제 그려지는 몸의 범위 (왼쪽, 오른쪽, 위) - 셀 기준 원본 px, 오른쪽을 볼 때
# 누운 몸은 서 있는 충돌 박스보다 훨씬 넓어서, 이 범위가 블록과 겹치지 않게 캐릭터를 밀어냄
BODY_BOX = {
    'fall_height': [(51, 77, 47), (33, 74, 46), (18, 67, 50), (11, 58, 56), (8, 54, 65), (7, 53, 67)],
    'fall':        [(39, 63, 47), (33, 66, 41), (17, 63, 41), (9, 55, 62), (8, 54, 65), (7, 53, 67)],
    'getup':       [(7, 53, 67), (9, 55, 53), (28, 61, 47), (35, 63, 46), (38, 62, 42), (37, 60, 38)],
}
BODY_BOTTOM_ROW = 84                        # 몸 범위의 아래쪽 = 발바닥 줄

# 총구에서 불꽃이 나오는 프레임 (이때 반동이 생김)
GUN_FIRE_FRAME = {'gun': 3, 'jump_gun': 1}
GUN_MUZZLE = (40, 46)          # 총알이 나오는 위치: 발 중앙에서 (앞으로, 위로) px (스프라이트 총구 위치)

# 칼 공격이 적에게 닿는 프레임과 범위 (칼을 휘두르는 프레임만)
SWORD_ACTIVE = {'sword': range(4, 7), 'jump_sword': range(4, 7)}
SWORD_REACH = 75               # 몸 중앙에서 앞으로 닿는 거리 (px)
SWORD_HEIGHT = 80              # 발에서 위로 닿는 높이 (px)


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
            'fall_height': Anim(main, 8, 6, 12, loop=False),     # 높은 곳에서 떨어져 착지하며 뒤로 넘어짐
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
        self.from_ice = False          # 마지막으로 서 있던 땅이 얼음이었는지 (공중에서는 떠나기 직전 땅)
        self.on_slope = 0              # 서 있는 경사면이 올라가는 방향 (1: 오른쪽이 높음, -1: 왼쪽이 높음, 0: 경사면 아님)
        self.invincible = 0.0          # 남은 무적 시간 (맞은 순간부터 INVINCIBLE_TIME 동안 다시 안 맞음)
        self.frozen = 0.0              # 얼음 구슬에 맞아 얼어붙은 남은 시간 (조작 불가, 동작 멈춤)
        self.frozen_pose = None        # 얼어붙은 순간의 (애니메이션, 프레임)
        self.slide_fly = False         # 경사면·얼음 끝에서 미끄러지던 속도로 날아가는 중 (착지할 때까지 조작 불가, 가로 속도가 천천히 줄어듦)
        self.slide_decel = 0.0         # 높은 곳에서 떨어져 넘어질 때 미끄러짐 감속
        self.recoil = 0.0              # 총 반동으로 밀려나는 남은 시간
        self.prev_x, self.prev_y = x, y    # 이번 계산 직전 위치 (경사 속으로 어느 면을 넘어 들어왔는지 판단용)
        self.shots = []                # 이번에 쏜 총알 (x, y, 방향). 게임 루프가 가져가서 Bullet으로 만듦
        self.set_state('idle')

    # ---------------- 상태 ----------------
    def set_state(self, state):
        self.state = state
        self.t = 0.0
        self.fired = False             # 이번 공격에서 총을 이미 쐈는지

    def sword_rect(self):
        """칼을 휘두르는 프레임이면 칼이 닿는 범위, 아니면 None"""
        if self.weapon != 'sword' or self.state not in ('attack', 'jump_attack'):
            return None
        name = 'sword' if self.state == 'attack' else 'jump_sword'
        if self.anims[name].frame_at(self.t) not in SWORD_ACTIVE[name]:
            return None
        x1, x2 = self.x, self.x + self.facing * SWORD_REACH
        return min(x1, x2), self.y, max(x1, x2), self.y + SWORD_HEIGHT

    def hitbox(self):
        return (self.x - PLAYER_HALF_W, self.y, self.x + PLAYER_HALF_W, self.y + PLAYER_H)

    def can_control(self):
        """좌우 입력을 받는 상태인지 (넘어짐 중, 땅에서 공격 중에는 X)"""
        if self.state in KNOCKED or self.recoil > 0 or self.on_slope or self.slide_fly or self.frozen > 0:
            return False
        return not (self.state == 'attack' and self.on_ground)

    def hit(self, knock_x, knock_y, source_x=None, push_dir=0):
        """함정·적에 맞음: 보고 있는 방향 기준 뒤로 날아가며 넘어짐.
        이미 넘어진 중에 또 맞으면 때린 쪽(source_x) 반대로 다시 날아감.
        push_dir(1/-1)을 주면 그 방향으로 날아감 (화살처럼 날아온 쪽 반대로). 이때 맞은 쪽을 보며 뒤로 넘어짐"""
        knocked = self.state in KNOCKED
        if self.invincible > 0 or (knocked and source_x is None and not push_dir):
            return
        self.invincible = INVINCIBLE_TIME
        self.recoil = 0.0
        self.frozen = 0.0                       # 얼어 있었으면 얼음이 깨지며 넘어짐
        if push_dir:
            self.vx = push_dir * knock_x
            if knocked:
                self.set_state('down' if self.state in ('down', 'getup') else 'fall')
            else:
                self.facing = -push_dir         # 날아온 쪽을 보고 뒤로 넘어지는 그림이 되게
        elif knocked:
            away = 1 if self.x > source_x else -1 if self.x < source_x else -self.facing
            self.vx = away * knock_x
            if self.state in ('down', 'getup'):
                self.set_state('down')          # 누워 있거나 일어나는 중이면 누운 자세 그대로 날아감
            else:
                self.set_state('fall')          # 넘어지는 중이면 넘어지는 동작을 처음부터
        else:
            self.vx = -self.facing * knock_x
        if knock_y > 0:
            self.vy = knock_y
            self.on_ground = False
            self.on_slope = 0
            self.slide_fly = False
        if not knocked:
            self.set_state('fall')

    def freeze(self, time):
        """서리 마법사의 얼음 구슬에 맞음: time 초 동안 그 자세 그대로 얼어붙어 조작 불가.
        맞은 순간 속도대로 땅에서는 얼음처럼 미끄러지다 멈추고, 공중이면 그대로 떨어짐.
        넘어진 중이거나 무적 시간에는 얼지 않음"""
        if self.invincible > 0 or self.state in KNOCKED:
            return
        if self.frozen <= 0:
            self.frozen_pose = self.current_frame()
        self.frozen = max(self.frozen, time)
        self.recoil = 0.0

    def is_slippery(self):
        """얼음 위이거나 얼어붙어 미끄러지는 중"""
        return self.on_ice or self.frozen > 0

    # ---------------- 입력 ----------------
    def handle_event(self, e):
        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_LEFT:
                self.left = True
            elif e.key == SDLK_RIGHT:
                self.right = True
            elif self.frozen > 0:
                pass                                # 얼어붙은 동안에는 점프·공격·무기 교체 불가
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
            elif e.key == SDLK_UP and self.frozen <= 0:
                # 올라가는 도중에 키를 떼면 상승 속도를 깎아서 낮은 점프
                if not self.on_ground and self.vy > JUMP_CUT_SPEED:
                    self.vy = JUMP_CUT_SPEED

    # ---------------- 갱신 ----------------
    def update(self, dt, tilemap):
        if self.frozen > 0:
            self.frozen = max(0.0, self.frozen - dt)    # 얼어 있는 동안 동작 시간이 흐르지 않음
        else:
            self.t += dt
        self.invincible = max(0.0, self.invincible - dt)
        direction = self.right - self.left
        self.check_gun_fire()
        control = self.can_control()

        # 수평 속도
        target = direction * MOVE_SPEED if control else 0.0
        if control and direction != 0:
            self.facing = direction
        if self.on_slope:
            if self.state not in KNOCKED:
                self.facing = -self.on_slope    # 경사면에서는 미끄러지는 쪽을 봄 (누워서 미끄러질 때는 그대로)
        elif self.recoil > 0:
            pass                            # 반동 중에는 밀려나는 속도 유지
        elif self.on_ground and self.state in ('fall_height', 'down'):
            pass                            # 넘어지며/누운 채 미끄러지는 중 (아래 이동 계산에서 감속)
        elif self.on_ground:
            out = self.ice_edge(tilemap) if self.on_ice else 0
            if out:
                # 얼음 끝에 걸쳐 있음: 발 중앙 밑이 비었으면 바깥쪽으로 계속 미끄러져 떨어짐 (조작 무시)
                if self.vx * out < ICE_EDGE_SPEED:
                    self.vx = approach(self.vx, out * ICE_EDGE_SPEED, ICE_ACCEL * dt)
            elif self.is_slippery():
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
            if self.slide_fly:
                # 경사면·얼음에서 미끄러지다 떨어지는 중: 가로 속도가 천천히 줄어듦
                self.vx = approach(self.vx, 0.0, SLOPE_AIR_DECEL * step)
            if self.on_slope:
                # 경사면 아래쪽으로 점점 빨라지며 미끄러짐
                self.vx = approach(self.vx, -self.on_slope * SLOPE_SPEED, SLOPE_ACCEL * step)
            if self.on_ground and self.state == 'fall_height':
                self.vx = approach(self.vx, 0.0, self.slide_decel * step)   # 넘어지며 미끄러지다 점점 멈춤
            elif self.on_ground and self.state == 'down' and not self.on_slope:
                self.vx = approach(self.vx, 0.0, KNOCK_SLIDE_DECEL * step)  # 누운 채 미끄러지다 점점 멈춤
            if self.recoil > 0 and self.recoil < step:
                step_x = self.recoil                # 반동이 끝나는 순간까지만 밀림
            else:
                step_x = step
            self.prev_x, self.prev_y = self.x, self.y
            self.move_x(self.vx * step_x, tilemap)
            self.move_y(self.vy * step, tilemap)
            self.follow_slope(step, tilemap)
            self.push_out_of_slopes(tilemap)
            if self.recoil > 0:
                self.recoil -= step
                if self.recoil <= 0 and not self.is_slippery():
                    self.vx = 0.0                   # 얼음 위(미끄러운 중)가 아니면 반동 끝나면 멈춤

        self.check_ground(tilemap)
        if self.on_ground:
            self.slide_fly = False
        if self.frozen <= 0:
            self.update_state(direction, tilemap)
        self.push_body_out(tilemap)

    def ice_edge(self, tilemap):
        """얼음 끝에 몸 한쪽만 걸쳐 있으면 떨어지는 쪽 방향(1/-1), 아니면 0"""
        if tilemap.solids_in(self.x - 1, self.y - 1, self.x + 1, self.y):
            return 0                                   # 발 중앙 밑에 땅이 있음
        if tilemap.solids_in(self.x - PLAYER_HALF_W + 1, self.y - 1, self.x - 1, self.y):
            return 1                                   # 땅이 왼쪽에만 있음 → 오른쪽으로 떨어짐
        return -1

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
            mx, my = GUN_MUZZLE
            self.shots.append((self.x + self.facing * mx, self.y + my, self.facing))
            self.on_ground = False

    # 블록과의 충돌은 그 블록 쪽에서 다가왔을 때만 막음.
    # 경사면 위에 서 있으면 몸 한쪽이 옆 블록과 살짝 겹치는데, 이걸 반대편으로 밀어내지 않기 위함
    def move_x(self, dx, tilemap):
        if dx == 0:
            return
        prev_l, prev_r = self.x - PLAYER_HALF_W, self.x + PLAYER_HALF_W
        self.x += dx
        for (l, b, r, t), _ in tilemap.solids_in(*self.hitbox()):
            if dx > 0 and prev_r <= l + 0.01:
                self.x = l - PLAYER_HALF_W
                self.vx = 0.0
            elif dx < 0 and prev_l >= r - 0.01:
                self.x = r + PLAYER_HALF_W
                self.vx = 0.0
        self.collide_slopes_x(dx, tilemap)

    def move_y(self, dy, tilemap):
        if dy == 0:
            return
        prev_b, prev_t = self.y, self.y + PLAYER_H
        self.y += dy
        for (l, b, r, t), ice in tilemap.solids_in(*self.hitbox()):
            if dy < 0 and prev_b >= t - 0.01:
                if l <= self.x <= r and tilemap.at(int(l // TILE), int(t // TILE)) in FLOOR_SLOPES:
                    continue        # 경사면 밑에 묻힌 블록: 발 중앙이 그 위면 경사면이 받아 줌
                self.y = t
                impact = self.vy
                self.vy = 0.0
                if not self.on_ground:
                    self.on_ground = True
                    self.on_landed(impact, tilemap)
                    if self.vy > 0:
                        return              # 착지하자마자 튀어 오름 (같은 높이의 다른 블록에 다시 착지하지 않게)
            elif dy > 0 and prev_t <= b + 0.01:
                self.y = b - PLAYER_H
                self.vy = 0.0
        self.collide_slopes_y(dy, tilemap)

    # ---------------- 경사면 ----------------
    def ceiling_slope_depth(self, c, b, ch):
        """천장 경사 칸에 머리 쪽 모서리가 파고든 깊이 (안 파고들었으면 0)
        [ 는 오른쪽 아래가 비어 있어서 머리 왼쪽 위 모서리가, ] 는 왼쪽 아래가 비어 있어서 오른쪽 위 모서리가 닿음"""
        corner_x = self.x - PLAYER_HALF_W if ch == '[' else self.x + PLAYER_HALF_W
        rx, ry = corner_x - c * TILE, self.y + PLAYER_H - b * TILE
        if not (0 <= rx <= TILE and 0 <= ry <= TILE):
            return 0.0
        return max(0.0, ry - rx if ch == '[' else rx + ry - TILE)

    def collide_slopes_x(self, dx, tilemap):
        prev_l, prev_r = self.x - dx - PLAYER_HALF_W, self.x - dx + PLAYER_HALF_W
        for c, b, ch in tilemap.slopes_in(*self.hitbox()):
            l, r = c * TILE, (c + 1) * TILE
            # 경사면 칸의 세로로 꽉 찬 옆면에 옆에서 부딪힘
            full_right = ch in '/]'          # 오른쪽 면이 꽉 참
            full_left = ch in '\\['          # 왼쪽 면이 꽉 참
            if dx < 0 and full_right and prev_l >= r - 0.01:
                self.x = r + PLAYER_HALF_W
                self.vx = 0.0
            elif dx > 0 and full_left and prev_r <= l + 0.01:
                self.x = l - PLAYER_HALF_W
                self.vx = 0.0
            elif ch in FLOOR_SLOPES:
                # 발 중앙이 경사면 속 깊이 들어가면 (경사면 아래쪽 옆에서 들어온 경우) 더 못 들어감
                if l <= self.x <= r and tilemap.slope_height(c, b, self.x) - self.y > SLOPE_DEPTH and not self.on_slope:
                    self.x -= dx
                    self.vx = 0.0
            else:
                depth = self.ceiling_slope_depth(c, b, ch)
                if depth and dx * (1 if ch == ']' else -1) > 0:
                    self.x -= depth if ch == ']' else -depth
                    self.vx = 0.0

    def collide_slopes_y(self, dy, tilemap):
        prev_b, prev_t = self.y - dy, self.y - dy + PLAYER_H
        for c, b, ch in tilemap.slopes_in(*self.hitbox()):
            bottom, top = b * TILE, (b + 1) * TILE
            if dy > 0 and ch in FLOOR_SLOPES and prev_t <= bottom + 0.01:
                self.y = bottom - PLAYER_H          # 바닥 경사 칸의 평평한 아랫면에 머리를 부딪힘
                self.vy = 0.0
            elif dy > 0 and ch in '[]':
                depth = self.ceiling_slope_depth(c, b, ch)
                if depth:
                    self.y -= depth                 # 천장 경사면에 머리를 부딪힘
                    self.vy = 0.0
            elif dy < 0 and ch in '[]' and prev_b >= top - 0.01 and not tilemap.is_solid(c, b + 1):
                # 윗면이 드러난 천장 경사 칸에만 착지 (위에 블록·경사면이 덮여 있으면 그쪽이 받아 줌)
                self.y = top                        # 천장 경사 칸의 평평한 윗면에 착지
                impact = self.vy
                self.vy = 0.0
                if not self.on_ground:
                    self.on_ground = True
                    self.on_landed(impact, tilemap)

    def push_out_of_slopes(self, tilemap):
        """몸 옆면·머리(·발 모서리)가 경사 칸의 채워진 삼각형 속에 들어갔으면 밖으로 밀어냄.
        (기존 경사 충돌은 발 가운데·머리 모서리 한 점만 봐서, 경사 옆에서 뛰거나 비스듬히 부딪히면 몸이 경사를 통과했음)
        이번 계산 직전 위치를 보고 경사의 어느 면(비스듬한 면 / 세로 옆면 / 평평한 면)을 넘어 들어왔는지 골라 그쪽으로 되돌림"""
        for _ in range(3):
            moved = False
            # 발 모서리는 발 가운데가 경사면 위·근처가 아닐 때만 봄 (경사 위에 서거나 내려앉는 중이면 원래 경사 처리가 맡음)
            over_slope = self.on_slope or tilemap.floor_slope(self.x, self.y, TILE, TILE)
            heights = (20, PLAYER_H / 2 + 10, PLAYER_H - 1) if over_slope else (1, 20, PLAYER_H / 2 + 10, PLAYER_H - 1)
            points = [(self.x + sx * PLAYER_HALF_W, self.y + h, h)
                      for sx in (-1, 1) for h in heights]
            points.append((self.x, self.y + PLAYER_H - 1, PLAYER_H - 1))
            ddx, ddy = self.x - self.prev_x, self.y - self.prev_y
            for px, py, h in points:
                head = h == PLAYER_H - 1
                c, b = int(px // TILE), int(py // TILE)
                ch = tilemap.at(c, b)
                if ch not in SLOPES:
                    continue
                rx, ry = px - c * TILE, py - b * TILE
                prx, pry = rx - ddx, ry - ddy             # 직전 위치에서 이 점 (같은 칸 기준)
                mx = my = 0.0
                if h == 1 and ch in FLOOR_SLOPES and (ry < rx if ch == '/' else ry < TILE - rx):
                    # 발 모서리만 바닥 경사에 걸침 (몸 가운데는 경사 칸 밖): 몸 가운데가 있는 쪽으로 빼냄
                    mx = -rx if self.x < c * TILE else TILE - rx
                elif ch == '/' and ry < rx:                 # 오른쪽 아래가 꽉 참 (비스듬한 면은 왼쪽 위를 봄)
                    if prx >= TILE:
                        mx = TILE - rx                    # 오른쪽 세로 옆면으로 들어옴
                    elif pry <= 0:
                        my = -ry                          # 평평한 아랫면으로 들어옴
                    else:
                        mx = -(rx - ry)
                elif ch == '\\' and ry < TILE - rx:     # 왼쪽 아래가 꽉 참 (비스듬한 면은 오른쪽 위를 봄)
                    if prx <= 0:
                        mx = -rx
                    elif pry <= 0:
                        my = -ry
                    else:
                        mx = TILE - rx - ry
                elif ch == '[' and ry > rx:               # 왼쪽 위가 꽉 참 (비스듬한 면은 오른쪽 아래를 봄)
                    if prx <= 0:
                        mx = -rx
                    elif pry >= TILE:
                        my = TILE - ry
                    elif head and self.vy > 0:
                        my = -(ry - rx)
                    else:
                        mx = ry - rx
                elif ch == ']' and ry > TILE - rx:        # 오른쪽 위가 꽉 참 (비스듬한 면은 왼쪽 아래를 봄)
                    d = ry - (TILE - rx)
                    if prx >= TILE:
                        mx = TILE - rx
                    elif pry >= TILE:
                        my = TILE - ry
                    elif head and self.vy > 0:
                        my = -d
                    else:
                        mx = -d
                else:
                    continue
                if abs(mx) + abs(my) <= 0.5:
                    continue
                self.x += mx + (0.01 if mx > 0 else -0.01 if mx < 0 else 0)
                self.y += my + (0.01 if my > 0 else -0.01 if my < 0 else 0)
                if mx * self.vx < 0:
                    self.vx = 0.0
                if my * self.vy < 0:
                    self.vy = 0.0
                moved = True
                break
            if not moved:
                return

    def follow_slope(self, step, tilemap):
        """바닥 경사면에 닿으면 붙어서 미끄러지고, 경사면이 끝나면 미끄러지던 속도로 떨어짐"""
        if self.vy > 0:
            self.on_slope = 0
            return
        # 경사면을 따라 내려가는 중이면 한 번에 움직인 만큼 아래까지 찾아서 붙음
        # 평평한 블록 모서리에 몸 한쪽만 걸치고 발 중앙은 경사면 위면, 경사면으로 내려가 미끄러짐
        below = max(abs(self.vx) * step + 2, PLAYER_HALF_W + 1) if self.on_ground else 0.5
        hit = tilemap.floor_slope(self.x, self.y, below, SLOPE_DEPTH)
        if hit:
            self.y, up = hit
            if not self.on_slope:
                impact = self.vy
                self.vy = 0.0
                self.on_ground = True
                self.recoil = 0.0
                if self.state in KNOCKED:
                    self.lie_flat(tilemap, move=False)  # 넘어진 채로 닿으면 누운 채 미끄러짐 (경사면에서 벗어나지 않게 위치는 그대로)
                elif impact <= -MAX_FALL_SPEED:
                    # 최고 속도로 떨어지다 경사면에 닿음: 평지처럼 넘어지되, 누운 채로 경사면을 미끄러져 내려감
                    self.frozen = 0.0
                    self.set_state('down')
                else:
                    self.set_state('slide')
            self.on_slope = up
        elif self.on_slope:
            up = self.on_slope
            self.on_slope = 0
            # 발 중앙 밑에 땅이 있으면 평지로 이어진 것 (착지), 없으면 경사면 끝에서 떨어짐
            if not tilemap.solids_in(self.x - 1, self.y - 1, self.x + 1, self.y):
                # 경사 칸 밑 블록 모서리에 몸 한쪽이 걸려 서 버리지 않도록 몸을 경사 칸 밖으로 내보냄
                c = int(self.x // TILE)
                if up < 0:                          # 오른쪽으로 미끄러짐: 왼쪽 칸이 경사면
                    self.x = max(self.x, c * TILE + PLAYER_HALF_W + 0.01)
                else:                               # 왼쪽으로 미끄러짐: 오른쪽 칸이 경사면
                    self.x = min(self.x, (c + 1) * TILE - PLAYER_HALF_W - 0.01)
                self.on_ground = False
                self.vy = -abs(self.vx)             # 미끄러지던 속도 그대로 비스듬히 떨어짐
                self.slide_fly = True

    def check_ground(self, tilemap):
        """발 바로 아래(1px 이내)에 땅이 있는지, 얼음인지 확인"""
        if self.on_slope:
            self.on_ground, self.on_ice = True, False
            return
        # 발밑 확인 폭은 충돌 박스 폭과 똑같이 (다르면 블록 끝에 1px 걸쳤을 때 착지↔떨어짐을 반복하며 공중에 멈춤)
        feet = (self.x - PLAYER_HALF_W, self.y - 1, self.x + PLAYER_HALF_W, self.y)
        under = tilemap.solids_in(*feet) if self.vy <= 0 else []
        if self.vy <= 0:
            # 천장 경사 칸([ ])의 평평한 윗면도 땅 (경사가 아닌 부분이라 서 있어도 미끄러지지 않음)
            under += [(rect, False) for rect in tilemap.ceiling_slope_tops_in(*feet)]
        if under and not self.on_ground:
            # 땅에 거의 닿은 채로 프레임이 끝난 경우에도 확실하게 착지 처리
            self.y = max(rect[3] for rect, _ in under)
            impact = self.vy
            self.vy = 0.0
            self.on_ground = True
            self.on_landed(impact, tilemap)
            if self.vy > 0:                         # 착지하자마자 튀어 오름
                self.on_ground = False
                return
        if self.on_ground and not under and self.on_ice and self.vy <= 0 and self.vx != 0:
            self.slide_fly = True           # 얼음 위를 미끄러지다 끝에서 떨어짐: 미끄러지던 속도를 이어감
        self.on_ground = bool(under)
        self.on_ice = any(ice for _, ice in under)
        if self.on_ground:
            self.from_ice = self.on_ice

    def on_landed(self, impact_vy, tilemap):
        """땅에 닿은 순간. impact_vy = 닿기 직전의 세로 속도(음수 = 아래로)"""
        feet = (self.x - PLAYER_HALF_W, self.y - 1, self.x + PLAYER_HALF_W, self.y)
        if not self.from_ice and any(ice for _, ice in tilemap.solids_in(*feet)):
            # 보통 땅에서 뛰어 얼음에 내려앉으면 공중 속도를 이어받지 않고 낮은 속도부터 다시 가속.
            # 얼음에서 뛰었다 얼음에 내려앉으면 미끄러지던 속도 그대로 (높이 떨어져 넘어질 때 미끄러지는 속도는 아래에서 따로 정함)
            self.vx = max(-ICE_LANDING_SPEED, min(ICE_LANDING_SPEED, self.vx))
        s = self.state
        if impact_vy <= -MAX_FALL_SPEED and s in KNOCKED:
            self.bounce_back(tilemap)                # 넘어진 채로 다시 높이 떨어짐: 누운 채 튀어 오르며 뒤로 밀림
        elif impact_vy <= -MAX_FALL_SPEED:
            # 최고 속도로 떨어지다 땅에 닿음: 공격·함정에 맞아 날아가는 중이어도 뒤로 넘어짐 (얼어 있었으면 얼음이 깨짐)
            self.recoil = 0.0
            self.frozen = 0.0
            self.set_state('fall_height')
            # 넘어지는 애니메이션 동안 FALL_HEIGHT_SLIDE 만큼 뒤로 미끄러지다 멈추도록 (일정하게 감속)
            duration = self.anims['fall_height'].duration
            speed = 2 * FALL_HEIGHT_SLIDE / duration
            self.slide_decel = speed / duration
            self.vx = -self.facing * speed
        elif s == 'jump':
            self.set_state('land')
        elif s == 'jump_attack':
            # 공중 공격 스프라이트는 그림 안에서 위로 떠 있으므로,
            # 착지하면 진행된 비율만큼 지상 공격 애니메이션으로 이어서 재생
            progress = self.t / self.anims['jump_' + self.weapon].duration
            self.set_state('attack')
            self.t = progress * self.anims[self.weapon].duration

    def lie_flat(self, tilemap, move=True):
        """누운 상태로 바꿈 (넘어지는 중이었으면 누운 몸 위치로 옮김)"""
        if self.state in ('fall', 'fall_height'):
            self.set_state('down')
            if move:
                self.lie_down(tilemap)
        elif self.state == 'getup':
            self.set_state('down')

    def bounce_back(self, tilemap):
        """넘어진 채로 최고 속도로 착지: 누운 자세로 KNOCK_BOUNCE_UP 만큼 튀어 오르며,
        처음 넘어질 때와 같은 거리(미끄러짐 + 누울 때 옮기는 거리)를 뒤로 밀려남"""
        self.lie_flat(tilemap)
        self.set_state('down')
        self.recoil = 0.0
        self.vy = (2 * GRAVITY * KNOCK_BOUNCE_UP) ** 0.5
        air = 2 * self.vy / GRAVITY                   # 튀어 올랐다 내려오는 시간
        dist = FALL_HEIGHT_SLIDE + LIE_BACK * SCALE
        a = KNOCK_SLIDE_DECEL
        # 공중에서 v*air + 바닥에서 v^2/(2a) = dist 가 되는 속도
        v = -a * air + ((a * air) ** 2 + 2 * a * dist) ** 0.5
        self.vx = -self.facing * v
        self.on_ground = False

    def update_state(self, direction, tilemap):
        s = self.state
        if s == 'slide':
            if not self.on_slope:
                self.set_state('land' if self.on_ground else 'jump')   # 경사면 끝: 평지면 착지, 아니면 떨어짐
        elif s in ('idle', 'walk', 'land') and not self.on_ground:
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
        elif s in ('fall', 'fall_height') and self.on_ground and self.t >= self.anims[s].duration:
            self.set_state('down')
            self.lie_down(tilemap)
        elif s == 'down' and self.on_ground and not self.on_slope and abs(self.vx) < 1 and self.t >= 0.6:
            self.set_state('getup')                      # 넘어진 채로 떨어지는 중이면 착지할 때까지 누운 자세 유지
        elif s == 'getup' and self.on_ground and self.t >= self.anims['getup'].duration:
            self.set_state('idle')

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
        if s in ('land', 'slide'):
            return self.anims['jump'], 5            # 경사면에서 미끄러질 때도 웅크린 착지 자세
        if s == 'attack':
            a = self.anims[self.weapon]
        elif s == 'jump_attack':
            a = self.anims['jump_' + self.weapon]
        elif s == 'down':
            return self.anims['getup'], 0          # 누워있는 프레임
        else:
            a = self.anims[s]
        return a, a.frame_at(self.t)

    def lie_down(self, tilemap):
        """누운 몸 위치로 실제 x를 옮김. 뒤에 벽이 있으면 push_body_out이 몸이 벽에 안 겹치게 밀어냄"""
        self.x -= self.facing * LIE_BACK * SCALE
        self.push_body_out(tilemap)

    def body_rect(self):
        """넘어진 동작 중 실제로 그려지는 몸의 범위 (left, bottom, right, top) 또는 None"""
        anim, frame = self.current_frame()
        name = 'getup' if self.state == 'down' else self.state
        if name not in BODY_BOX:
            return None
        l, r, top = BODY_BOX[name][frame]
        draw_x = self.x + self.body_shift(frame)
        x1 = draw_x + (l - CELL / 2) * SCALE * self.facing
        x2 = draw_x + (r - CELL / 2) * SCALE * self.facing
        # 위쪽은 서 있는 충돌 박스 높이까지만 (일어날 때 머리가 3px 더 높아서 낮은 천장에 걸리지 않게)
        height = min((BODY_BOTTOM_ROW - top) * SCALE, PLAYER_H)
        return min(x1, x2), self.y + 1, max(x1, x2), self.y + height

    def push_body_out(self, tilemap):
        """넘어진 몸(머리 포함)이 블록에 겹치면 겹친 만큼 반대쪽으로 밀어냄"""
        rect = self.body_rect()
        if rect is None or self.on_slope:
            return              # 경사면 위에서는 누운 몸이 경사 밑 블록과 겹쳐 보여도 밀어내지 않음
        l, b, r, t = rect
        center = (l + r) / 2
        push_right = push_left = 0.0
        for (sl, sb, sr, st), _ in tilemap.solids_in(l, b, r, t):
            if (sl + sr) / 2 < center:
                push_right = max(push_right, sr - l)       # 블록이 왼쪽에 있음 → 오른쪽으로
            else:
                push_left = max(push_left, r - sl)         # 블록이 오른쪽에 있음 → 왼쪽으로
        push = push_right - push_left
        if push:
            self.x += push
            if self.vx * push < 0:
                self.vx = 0.0                              # 벽 쪽으로 미끄러지던 속도는 멈춤

    def body_shift(self, frame):
        """누워 있거나 일어나는 동안 몸이 누운 자리에 있도록 그림을 옮길 거리 (px)"""
        if self.state == 'down':
            shift = GETUP_BODY_SHIFT[0]
        elif self.state == 'getup':
            shift = GETUP_BODY_SHIFT[frame]
        else:
            return 0
        return self.facing * shift * SCALE

    def draw(self, cam_y):
        if self.invincible > 0 and int(self.invincible * BLINK_RATE) % 2:
            return                                  # 무적 시간 동안 깜빡임
        anim, frame = self.frozen_pose if self.frozen > 0 else self.current_frame()
        cy = self.y + (CELL // 2 - FOOT_IN_CELL) * SCALE - cam_y
        anim.draw(frame, self.x + self.body_shift(frame), cy, self.facing)


def approach(value, target, amount):
    if value < target:
        return min(value + amount, target)
    return max(value - amount, target)
