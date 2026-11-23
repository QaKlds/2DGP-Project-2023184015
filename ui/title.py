import random

from pico2d import load_image

from config import WIDTH
from ui.menu import ButtonMenu, draw_at, clip_at

DIR = 'asset/title'
# 배치는 asset/title/title.json 참고. 좌표는 화면 왼쪽 위 기준 (x, y), 크기는 그림 그대로 (1배)
LAYERS = ['title_sky', 'title_clouds_far', 'title_tower', 'title_clouds_near', 'title_ground']   # 뒤 → 앞
CLOUD_SPEED = {'title_clouds_far': 8, 'title_clouds_near': 20}    # 왼쪽으로 흘러가는 속도 (px/s, 가로로 이어 붙임)
LOGO_POS = (80, 72)
CONTROLS_POS = (80, 748)        # 조작법 패널 (아래 끝이 땅 위 1008px에 오도록)
BUTTONS = [('start', (210, 460)), ('quit', (210, 568))]      # 위에서부터 메뉴 순서
TORCH_FRAMES, TORCH_W, TORCH_H, TORCH_FPS = 6, 32, 48, 10
TORCH_POS = [(1184, 904), (1400, 904)]
STAR_FRAMES, STAR_SIZE, STAR_FPS = 6, 18, 8
STAR_COUNT = 14
STAR_AREA = (0, 0, WIDTH, 420)  # 반짝이는 별이 생기는 범위 (왼쪽, 위, 오른쪽, 아래)


class TitleScreen(ButtonMenu):
    """시작화면: 배경(하늘·구름·탑·땅) 위에 로고, START/QUIT 메뉴, 조작법 패널.
    ↑↓ 또는 마우스로 고르고 Enter·Z·클릭으로 결정. handle_event가 'start' / 'quit'을 돌려줌"""
    def __init__(self):
        img = lambda name: load_image(f'{DIR}/{name}.png')
        self.layers = [(name, img(name)) for name in LAYERS]
        self.logo = img('title_logo')
        self.controls = img('title_controls')
        super().__init__([(name, pos, img(f'title_btn_{name}'), img(f'title_btn_{name}_sel')) for name, pos in BUTTONS])
        self.torch = img('title_torch_flame')
        self.star = img('title_star_sparkle')
        self.t = 0.0
        # 별: [x, y, 시작 시각]. 한 번 반짝이고 나면 다른 자리에서 다시 반짝임
        self.stars = [self._new_star(random.uniform(-1.5, 0)) for _ in range(STAR_COUNT)]

    # ---------------- 갱신 ----------------
    def update(self, dt):
        self.t += dt
        star_time = STAR_FRAMES / STAR_FPS
        for i, (_, _, start) in enumerate(self.stars):
            if self.t - start >= star_time:
                self.stars[i] = self._new_star(self.t + random.uniform(0, 1.5))

    def _new_star(self, start):
        l, top, r, bottom = STAR_AREA
        return [random.uniform(l, r - STAR_SIZE), random.uniform(top, bottom - STAR_SIZE), start]

    # ---------------- 그리기 ----------------
    def draw(self):
        for name, image in self.layers:
            if name in CLOUD_SPEED:
                # 왼쪽으로 흘러가며 두 장을 이어 붙여 그림
                offset = (self.t * CLOUD_SPEED[name]) % WIDTH
                draw_at(image, -offset, 0)
                draw_at(image, WIDTH - offset, 0)
            else:
                draw_at(image, 0, 0)
            if name == 'title_sky':
                self._draw_stars()
            elif name == 'title_tower':
                self._draw_torches()
        draw_at(self.logo, *LOGO_POS)
        self.draw_buttons()
        draw_at(self.controls, *CONTROLS_POS)

    def _draw_stars(self):
        for x, y, start in self.stars:
            if self.t >= start:
                frame = min(STAR_FRAMES - 1, int((self.t - start) * STAR_FPS))
                clip_at(self.star, frame * STAR_SIZE, STAR_SIZE, STAR_SIZE, x, y)

    def _draw_torches(self):
        for i, (x, y) in enumerate(TORCH_POS):
            frame = (int(self.t * TORCH_FPS) + i * 3) % TORCH_FRAMES      # 두 횃불이 엇갈려 타오르게
            clip_at(self.torch, frame * TORCH_W, TORCH_W, TORCH_H, x, y)
