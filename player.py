from pico2d import (load_image, SDL_KEYDOWN, SDL_KEYUP,
                    SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_TAB, SDLK_z, SDLK_x)

from anim import Anim
from config import (WIDTH, CELL, SCALE, GROUND_Y, FOOT_IN_CELL,
                    MOVE_SPEED, JUMP_SPEED, JUMP_CUT_SPEED, GRAVITY)


class Player:
    def __init__(self):
        main = load_image('asset/player/spritesheet_left.png')
        extra = load_image('asset/player/player_extra_left.png')
        self.anims = {
            'idle':        Anim(main, 0, 4, 6),
            'walk':        Anim(main, 1, 6, 10),
            'jump':        Anim(main, 2, 6, 10, loop=False),
            'sword':       Anim(main, 3, 8, 20, loop=False),
            'gun':         Anim(main, 4, 7, 18, loop=False),
            'getup':       Anim(extra, 0, 6, 10, loop=False),
            'fall':        Anim(extra, 1, 6, 12, loop=False),
            'jump_sword':  Anim(extra, 2, 7, 20, loop=False),
            'jump_gun':    Anim(extra, 3, 6, 18, loop=False),
        }
        self.x, self.y = WIDTH // 2, GROUND_Y
        self.vy = 0
        self.facing = -1          # -1: 왼쪽, 1: 오른쪽
        self.left = self.right = False
        self.weapon = 'sword'
        self.on_ground = True
        self.set_state('idle')

    # ---------------- 상태 ----------------
    def set_state(self, state):
        self.state = state
        self.t = 0.0

    def busy(self):
        """조작을 막는 상태인지"""
        return self.state in ('fall', 'down', 'getup', 'attack')

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
                if self.on_ground and not self.busy():
                    self.vy = JUMP_SPEED
                    self.on_ground = False
                    self.set_state('jump')
            elif e.key == SDLK_z:
                if self.state in ('idle', 'walk', 'land'):
                    self.set_state('attack')
                elif self.state == 'jump':
                    self.set_state('jump_attack')
            elif e.key == SDLK_x:
                if self.on_ground and self.state in ('idle', 'walk', 'land'):
                    self.set_state('fall')
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
    def update(self, dt):
        self.t += dt
        direction = self.right - self.left

        # 수평 이동 (지상 공격/넘어짐 중에는 멈춤)
        if not self.busy() and direction != 0:
            self.facing = direction
            self.x += direction * MOVE_SPEED * dt
            self.x = max(CELL // 2, min(WIDTH - CELL // 2, self.x))

        # 중력
        if not self.on_ground:
            self.vy -= GRAVITY * dt
            self.y += self.vy * dt
            if self.y <= GROUND_Y:
                self.y, self.vy = GROUND_Y, 0
                self.on_ground = True
                if self.state == 'jump_attack':
                    # 공중 공격 스프라이트는 그림 안에서 위로 떠 있으므로,
                    # 착지하면 진행된 비율만큼 지상 공격 애니메이션으로 이어서 재생
                    progress = self.t / self.anims['jump_' + self.weapon].duration
                    self.set_state('attack')
                    self.t = progress * self.anims[self.weapon].duration
                else:
                    self.set_state('land')

        # 상태 전환
        s = self.state
        if s in ('idle', 'walk'):
            want = 'walk' if direction != 0 else 'idle'
            if want != s:
                self.set_state(want)
        elif s == 'land' and self.t >= 0.08:
            self.set_state('idle')
        elif s == 'attack' and self.t >= self.anims[self.weapon].duration:
            self.set_state('idle')
        elif s == 'jump_attack' and self.t >= self.anims['jump_' + self.weapon].duration:
            self.set_state('jump')
        elif s == 'fall' and self.t >= self.anims['fall'].duration:
            self.set_state('down')
        elif s == 'down' and self.t >= 0.6:
            self.set_state('getup')
        elif s == 'getup' and self.t >= self.anims['getup'].duration:
            self.set_state('idle')

    # ---------------- 그리기 ----------------
    def current_frame(self):
        s = self.state
        if s == 'jump':
            # 점프 프레임은 시간 대신 수직 속도로 고름: 1 도약, 2 상승, 3 정점, 4 하강
            if self.vy > JUMP_SPEED * 0.5:
                f = 1
            elif self.vy > 120:
                f = 2
            elif self.vy > -120:
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

    def draw(self):
        anim, frame = self.current_frame()
        cy = self.y + (CELL // 2 - FOOT_IN_CELL) * SCALE
        anim.draw(frame, self.x, cy, self.facing)
