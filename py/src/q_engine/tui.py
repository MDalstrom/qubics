import curses


def mk_run(tick_fn):
    def run(stdscr):
        key = None
        stdscr.clear()

        while key != ord('q'):
            try:
                tick_fn(stdscr, key)
            except Exception as e:
                stdscr.clear()
                import traceback
                stdscr.addstr(0, 0, traceback.format_exception(e))
            stdscr.refresh()
            key = stdscr.getch()

    return curses.wrapper(run)
