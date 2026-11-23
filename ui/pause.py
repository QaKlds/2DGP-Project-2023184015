from pico2d import load_image, draw_rectangle, SDL_KEYDOWN, SDLK_ESCAPE
from pico2d import pico2d as pico_core
from sdl2 import SDL_SetRenderDrawBlendMode, SDL_BLENDMODE_BLEND

from config import WIDTH, HEIGHT, PAUSE_DIM
from ui.menu import ButtonMenu, draw_at

DIR = 'asset/pause'
# 배치는 asset/pause/pause.json 참고. 패널을 화면 가운데에 두고, 버튼 위치는 패널 왼쪽 위 기준
BUTTONS = [('resume', (50, 116)), ('restart', (50, 212)), ('main_menu', (50, 308)), ('quit', (50, 404))]


class PauseMenu(ButtonMenu):
    """게임 중 ESC로 여는 일시정지 메뉴. 게임 화면 위에 어둡게 덮고 가운데에 패널을 그림.
    handle_event가 'resume' / 'restart' / 'main_menu' / 'quit' 을 돌려줌 (ESC를 다시 누르면 'resume')"""
    def __init__(self):
        self.panel = load_image(f'{DIR}/pause_panel.png')
        self.px = (WIDTH - self.panel.w) // 2
        self.py = (HEIGHT - self.panel.h) // 2
        img = lambda name: load_image(f'{DIR}/pause_btn_{name}.png')
        buttons = [(name, (self.px + x, self.py + y), img(name), img(f'{name}_sel')) for name, (x, y) in BUTTONS]
        super().__init__(buttons)

    def open(self):
        """열 때마다 '계속하기'를 고른 상태로 시작"""
        self.selected = 0

    def handle_event(self, e):
        if e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            return 'resume'
        return super().handle_event(e)

    def draw(self):
        # 반투명 검은색으로 게임 화면을 어둡게 (pico2d는 기본으로 투명도를 섞지 않아서 직접 켬)
        SDL_SetRenderDrawBlendMode(pico_core.renderer, SDL_BLENDMODE_BLEND)
        draw_rectangle(0, 0, WIDTH, HEIGHT, 0, 0, 0, int(255 * PAUSE_DIM), filled=True)
        draw_at(self.panel, self.px, self.py)
        self.draw_buttons()
