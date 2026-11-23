from pico2d import load_image

from config import HEIGHT, HUD_SCALE, HUD_MARGIN, HUD_GAP, HUD_MAX_TIME

DIR = 'asset/hud'
# 글꼴 (asset/hud/hud.json): 12x16 칸에 글자가 하나씩, 그린 뒤 글자마다 정해진 만큼 펜을 옮김
GLYPHS = '0123456789:.m'
CELL_W, CELL_H = 12, 16
ADVANCE = {':': 6, '.': 6, 'm': 12}       # 나머지(숫자)는 11
PANEL_W, PANEL_H = 128, 32
TEXT_X, TEXT_Y = 36, 8                   # 패널 왼쪽 위에서 글자가 시작하는 자리
BEST_TEXT_X = 46                         # 최고기록 패널은 BEST 글자 뒤에서 시작


class Hud:
    """화면 왼쪽 위에 경과 시간(시:분:초), 지금 높이(m), 최고기록(m) 패널을 차례로 그림.
    최고기록은 이 객체가 살아 있는 동안(게임을 켜 둔 동안) 기억함"""
    def __init__(self):
        self.font = load_image(f'{DIR}/hud_font.png')
        self.time_panel = load_image(f'{DIR}/hud_panel_time.png')
        self.height_panel = load_image(f'{DIR}/hud_panel_distance.png')
        self.best_panel = load_image(f'{DIR}/hud_panel_best.png')
        self.best = 0                           # 지금까지 올라간 가장 높은 곳 (m)

    def record(self, height_m):
        """지금 높이로 최고기록을 갱신"""
        self.best = max(self.best, int(height_m))

    def draw(self, play_time, height_m):
        s = HUD_SCALE
        top = HEIGHT - HUD_MARGIN * s
        step = (PANEL_H + HUD_GAP) * s
        self._panel(self.time_panel, top, self.format_time(play_time))
        self._panel(self.height_panel, top - step, f'{max(0, int(height_m))}m')
        self._panel(self.best_panel, top - step * 2, f'{self.best}m', BEST_TEXT_X)

    @staticmethod
    def format_time(t):
        """시:분:초 (예: 01:23:45)"""
        sec = int(min(max(0.0, t), HUD_MAX_TIME))   # 초 단위로 버림
        return f'{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}'

    def _panel(self, image, top, text, text_x=TEXT_X):
        """패널 왼쪽 위가 (HUD_MARGIN, top)에 오도록 그리고 글자를 얹음 (글자는 패널 안 text_x부터)"""
        s = HUD_SCALE
        left = HUD_MARGIN * s
        image.clip_draw_to_origin(0, 0, PANEL_W, PANEL_H, left, top - PANEL_H * s, PANEL_W * s, PANEL_H * s)
        self._text(text, left + text_x * s, top - (TEXT_Y + CELL_H) * s)

    def _text(self, text, x, bottom):
        s = HUD_SCALE
        for ch in text:
            i = GLYPHS.find(ch)
            if i < 0:
                continue
            self.font.clip_draw_to_origin(i * CELL_W, 0, CELL_W, CELL_H, x, bottom, CELL_W * s, CELL_H * s)
            x += ADVANCE.get(ch, 11) * s
