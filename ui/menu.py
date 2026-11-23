from pico2d import (SDL_KEYDOWN, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT,
                    SDLK_UP, SDLK_DOWN, SDLK_RETURN, SDLK_KP_ENTER, SDLK_z)

from config import HEIGHT

CONFIRM_KEYS = (SDLK_RETURN, SDLK_KP_ENTER, SDLK_z)


def draw_at(image, x, y):
    """그림의 왼쪽 위가 화면 (x, y) (왼쪽 위 기준)에 오도록 원래 크기로 그림"""
    image.draw_to_origin(x, HEIGHT - y - image.h, image.w, image.h)


def clip_at(image, left, w, h, x, y):
    """시트 맨 위 줄의 한 칸(left부터 w x h)을 왼쪽 위가 화면 (x, y)에 오도록 그림"""
    image.clip_draw_to_origin(left, image.h - h, w, h, x, HEIGHT - y - h, w, h)


class ButtonMenu:
    """세로로 늘어선 버튼 메뉴 (시작화면·일시정지 메뉴가 함께 씀).
    ↑↓ 또는 마우스를 올려서 고르고 Enter·Z·클릭으로 결정. buttons = [(이름, (x, y) 왼쪽 위, 보통 그림, 선택 그림)]"""
    def __init__(self, buttons, selected=0):
        self.buttons = buttons
        self.selected = selected

    def handle_event(self, e):
        """결정한 버튼 이름, 아니면 None"""
        if e.type == SDL_KEYDOWN:
            if e.key in (SDLK_UP, SDLK_DOWN):
                step = -1 if e.key == SDLK_UP else 1
                self.selected = (self.selected + step) % len(self.buttons)
            elif e.key in CONFIRM_KEYS:
                return self.buttons[self.selected][0]
        elif e.type == SDL_MOUSEMOTION:
            i = self.button_at(e.x, e.y)
            if i is not None:
                self.selected = i
        elif e.type == SDL_MOUSEBUTTONDOWN and e.button == SDL_BUTTON_LEFT:
            i = self.button_at(e.x, e.y)
            if i is not None:
                return self.buttons[i][0]
        return None

    def button_at(self, mx, my):
        """마우스 위치(왼쪽 위 기준)에 있는 버튼 번호"""
        for i, (_, (x, y), image, _) in enumerate(self.buttons):
            if x <= mx < x + image.w and y <= my < y + image.h:
                return i
        return None

    def draw_buttons(self):
        for i, (_, pos, normal, selected) in enumerate(self.buttons):
            draw_at(selected if i == self.selected else normal, *pos)
