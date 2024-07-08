import curses
from time import sleep

HEADER_COLOR = 1
PRODUCT_COLOR = 2
GRAY = 244
BORDER_COLOR = 3


def make_header(scn_h, scn_w):
    # Create a window for the header
    # Get screen dimensions
    header1_contents = "terminal"
    header1 = curses.newwin(3, len(header1_contents) + 5, 0, int(scn_w / 6))
    header1.bkgd(curses.color_pair(BORDER_COLOR))
    header1.border(
        curses.ACS_VLINE,
        curses.ACS_VLINE,
        curses.ACS_HLINE,
        curses.ACS_HLINE,
        curses.ACS_ULCORNER,
        curses.ACS_URCORNER,
        curses.ACS_LLCORNER,
        curses.ACS_LRCORNER,
    )
    header1.addstr(1, 2, header1_contents, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
    header1.refresh()

    header2_contents = "s shop"
    header2 = curses.newwin(3, 8, 0, int(scn_w / 6) + len(header1_contents) + 4)
    header2.bkgd(curses.color_pair(BORDER_COLOR))
    header2.border(
        curses.ACS_VLINE,
        curses.ACS_VLINE,
        curses.ACS_HLINE,
        curses.ACS_HLINE,
        curses.ACS_ULCORNER,
        curses.ACS_URCORNER,
        curses.ACS_LLCORNER,
        curses.ACS_LRCORNER,
    )
    header2.addstr(1, 2, header2_contents, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
    header2.refresh()
    return header1, header2


def show_welcome_screen(scn_h, scn_w) -> None:
    curses.curs_set(1)
    message = "terminal"
    welcome_screen = curses.newwin(1, len(message) + 1, int(scn_h / 2), int(scn_w / 2) - int(len(message) / 2))
    for char in message:
        welcome_screen.addch(char, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        sleep(0.25)
        welcome_screen.refresh()
    sleep(1)
    curses.curs_set(0)
    del welcome_screen


def main(stdscr: curses.window):
    stdscr.refresh()

    # Hide the cursor
    curses.curs_set(0)

    # Define color pairs
    curses.init_pair(HEADER_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(PRODUCT_COLOR, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(BORDER_COLOR, GRAY, curses.COLOR_BLACK)

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # show_welcome_screen(height, width)

    # Create a window for the main content
    main_win = curses.newwin(height - 6, width, 3, 0)
    main_win.attron(curses.color_pair(BORDER_COLOR))
    main_win.box()

    # Sample product data
    products = [
        {"name": "Laptop", "price": 999.99},
        {"name": "Smartphone", "price": 499.99},
        {"name": "Headphones", "price": 99.99},
    ]

    # Display products
    for i, product in enumerate(products):
        main_win.addstr(i + 1, 2, f"{i + 1}. {product['name']}", curses.color_pair(PRODUCT_COLOR))
        main_win.addstr(i + 1, width - 15, f"${product['price']:.2f}")

    main_win.refresh()

    header = make_header(height, width)

    # Create a window for user input
    input_win = curses.newwin(3, width, height - 3, 0)
    input_win.box()
    input_win.addstr(1, 2, "Enter product number (q to quit): ")
    input_win.refresh()

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key in [ord("1"), ord("2"), ord("3")]:
            product_index = int(chr(key)) - 1
            main_win.addstr(height - 7, 2, f"You selected: {products[product_index]['name']}")
            main_win.refresh()
        elif key == ord("d"):
            del header
            main_win.touchwin()
            main_win.refresh()
        elif key == ord("h"):
            header = make_header(height, width)


if __name__ == "__main__":
    curses.wrapper(main)
