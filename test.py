from pico2d import *

# ---------------------------------------------------------------
# 애니메이션 테스트
#   ←→ : 이동          ↑ : 점프      Z : 공격
#   TAB    : 무기 교체 (칼 <-> 총)       X : 넘어졌다 일어나기
#   ESC    : 종료
# ---------------------------------------------------------------

WIDTH, HEIGHT = 800, 600
CELL = 100            # 스프라이트 한 칸 크기 (100x100)
SCALE = 1             # 화면에 그릴 배율
GROUND_Y = 150        # 발이 닿는 바닥 높이
FOOT_IN_CELL = 12     # 셀 아래쪽에서 발까지의 거리(px)

MOVE_SPEED = 300      # px/s
JUMP_SPEED = 600      # px/s  (꾹 누를 때 최대 점프, 약 128px)
JUMP_CUT_SPEED = 200  # px/s  (상승 중 키를 떼면 이 속도로 줄임 → 살짝 누르면 약 46px)
GRAVITY = 2200        # px/s^2


class Anim:
    """시트 이미지에서 한 줄(row)을 애니메이션으로 사용"""
    def __init__(self, image, row, frames, fps, loop=True):
        self.image = image
        self.row = row          # 위에서부터 몇 번째 줄인지 (0부터)
        self.frames = frames
        self.fps = fps
        self.loop = loop

    @property
    def duration(self):
        return self.frames / self.fps

    def frame_at(self, t):
        f = int(t * self.fps)
        return f % self.frames if self.loop else min(f, self.frames - 1)

    def draw(self, frame, x, y, facing):
        bottom = self.image.h - (self.row + 1) * CELL     # pico2d는 좌하단이 원점
        flip = 'h' if facing < 0 else ''                  # 원본이 오른쪽을 보고 있음
        self.image.clip_composite_draw(frame * CELL, bottom, CELL, CELL, 0, flip,
                                       x, y, CELL * SCALE, CELL * SCALE)


class Player:
    def __init__(self):
        main = load_image('spritesheet_left.png')
        extra = load_image('player_extra_left.png')
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


def main():
    open_canvas(WIDTH, HEIGHT)
    try:
        font = load_font('C:/Windows/Fonts/malgun.ttf', 18)
    except Exception:
        font = None

    player = Player()
    running = True
    last = get_time()

    while running:
        now = get_time()
        dt = min(now - last, 0.05)
        last = now

        for e in get_events():
            if e.type == SDL_QUIT or (e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE):
                running = False
            else:
                player.handle_event(e)

        player.update(dt)

        clear_canvas()
        draw_rectangle(0, 0, WIDTH, HEIGHT, 255, 255, 255, 255, filled=True)   # 흰 배경
        draw_rectangle(0, GROUND_Y - 2, WIDTH, GROUND_Y, 180, 180, 180, 255, filled=True)
        player.draw()
        if font:
            weapon = '칼' if player.weapon == 'sword' else '총'
            font.draw(10, HEIGHT - 20, f'무기: {weapon}   상태: {player.state}', (0, 0, 0))
            font.draw(10, HEIGHT - 45, '←→ 이동 / ↑ 점프 / Z 공격 / TAB 무기교체 / X 넘어짐 / ESC 종료', (90, 90, 90))
        update_canvas()
        delay(0.01)

    close_canvas()


if __name__ == '__main__':
    main()
