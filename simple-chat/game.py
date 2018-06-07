import sys
import pygame as pg
import random


pg.init()

SIZE = WIDTH, HEIGHT = 720, 540
BG_COLOR = 255, 255, 255
RECT_COLOR = (128, 0, 0)
TARGET_COLOR = (128, 128, 128)

screen = pg.display.set_mode(SIZE)
pg.display.set_caption('Simple APP')

target_x = random.randint(0, WIDTH - 100) // 10 * 10
target_y = random.randint(0, HEIGHT - 100) // 10 * 10

rect = pg.Rect(WIDTH / 2 - 50, HEIGHT / 2 - 50, 100, 100)
target = pg.Rect(target_x, target_y, 100, 100)
moves_font = pg.font.SysFont('Arial', 32, True)

victory_font = pg.font.SysFont('Comic Sans MS', 72, True)

moves = 0
won = False

while 1:
    for event in pg.event.get():
        pg.display.update()

        if event.type == pg.QUIT:
            sys.exit()

        if event.type == pg.VIDEORESIZE:
            screen = pg.display.set_mode((event.w, event.h), pg.RESIZABLE)

        if event.type == pg.KEYDOWN and not won:
            if event.key == pg.K_UP:
                if rect.y > 0:
                    rect.y -= 10
                    moves += 1
            if event.key == pg.K_DOWN:
                if rect.y < HEIGHT:
                    rect.y += 10
                    moves += 1
            if event.key == pg.K_LEFT:
                if rect.x > 0:
                    rect.x -= 10
                    moves += 1
            if event.key == pg.K_RIGHT:
                if rect.x < WIDTH:
                    rect.x += 10
                    moves += 1

    screen.fill(BG_COLOR)

    if target.x == rect.x and target.y == rect.y:
        victory_text = victory_font.render('Victory!!!',
                                           False, (0, 0, 0))
        screen.blit(victory_text, (200, HEIGHT / 2))
        won = True

    textsurface = moves_font.render('Moves: {}'.format(moves), False, (0, 0, 0))
    screen.blit(textsurface, (0, 0))
    pg.draw.rect(screen, RECT_COLOR, rect, 0)
    pg.draw.rect(screen, TARGET_COLOR, target, 2)

    pg.display.flip()
