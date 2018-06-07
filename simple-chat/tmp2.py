import sys
import pygame as pg


pg.init()

SIZE = WIDTH, HEIGHT = 720, 540
BG_COLOR = 255, 255, 255
HEADER_HEIGHT = 72
INPUT_HEIGHT = 64
COLOR_INACTIVE = (128, 128, 128)
COLOR_ACTIVE = (0, 0, 255)

screen = pg.display.set_mode(SIZE, pg.RESIZABLE)
pg.display.set_caption('Simple APP')

header = pg.Rect(0, 0, WIDTH, HEADER_HEIGHT)
history = pg.Rect(0, HEADER_HEIGHT - 1, WIDTH,
                  HEIGHT - HEADER_HEIGHT - INPUT_HEIGHT)
input_box = pg.Rect(0, HEIGHT - INPUT_HEIGHT, WIDTH, INPUT_HEIGHT)

font = pg.font.SysFont('Comic Sans MS', 30)

input_text = ''
input_active = False

print(dir(input_box))

while 1:
    for event in pg.event.get():
        pg.display.update()

        if event.type == pg.QUIT:
            sys.exit()

        if event.type == pg.VIDEORESIZE:
            screen = pg.display.set_mode((event.w, event.h), pg.RESIZABLE)
            header.w = event.w
            history.w = event.w
            history.h = event.h - header.h - input_box.h
            input_box.w = event.w
            input_box.top = event.h - 65

        if event.type == pg.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                input_active = not input_active

        # Change the current color of the input box.
        if event.type == pg.KEYDOWN:

            if input_active:
                if event.key == pg.K_RETURN:
                    print(input_text)
                    input_text = ''
                elif event.key == pg.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

    screen.fill(BG_COLOR)

    input_color = COLOR_ACTIVE if input_active else COLOR_INACTIVE

    pg.draw.rect(screen, COLOR_INACTIVE, header, 1)
    pg.draw.rect(screen, COLOR_INACTIVE, history, 1)
    pg.draw.rect(screen, input_color, input_box, 1)

    textsurface = font.render(input_text, False, (0, 0, 0))

    screen.blit(textsurface, (10, input_box.y))

    pg.display.flip()
