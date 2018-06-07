import curses
import traceback


def main(args):
    stdscr = curses.initscr()

    stdscr.clear()

    curses.echo()
    curses.start_color()
    curses.use_default_colors()

    win = curses.newwin(10, 100, 0, 0)

    # win.box()
    win.refresh()
    win.border()

    try:
        while True:
            string = win.getstr()  # type: bytes
            print(string.decode())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    print(dir(win))


if __name__ == '__main__':
    curses.wrapper(main)
    curses.endwin()
