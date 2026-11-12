from pico2d import *

from config import WIDTH, HEIGHT, GROUND_Y
from player import Player

# ---------------------------------------------------------------
# 애니메이션 테스트
#   ←→ : 이동          ↑ : 점프      Z : 공격
#   TAB    : 무기 교체 (칼 <-> 총)       X : 넘어졌다 일어나기
#   ESC    : 종료
# ---------------------------------------------------------------


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
