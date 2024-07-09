import curses
from time import sleep

HEADER_COLOR = 1
PRODUCT_COLOR = 2
GRAY = 244
BORDER_COLOR = 3


def draw_box(win: curses.window, height, width):
    win.attron(curses.color_pair(BORDER_COLOR))
    win.box()
    win.addch(0, 0, curses.ACS_ULCORNER)
    win.addch(0, width - 1, curses.ACS_URCORNER)
    win.addch(height - 1, 0, curses.ACS_LLCORNER)
    win.addch(height - 1, width - 1, curses.ACS_LRCORNER)
    win.attroff(curses.color_pair(BORDER_COLOR))


def make_header(scn_h, scn_w):
    # Create a window for the header
    # Get screen dimensions

    height = 3
    width = 15  # int(0.8 * scn_w)
    start_y, start_x = 1, 1

    terminal = curses.newwin(height, width, start_y, start_x)
    shop = curses.newwin(height, width, start_y, start_x + width - 1)
    about = curses.newwin(height, width, start_y, start_x + 2 * (width - 1))
    faq = curses.newwin(height, width, start_y, start_x + 3 * (width - 1))
    cart = curses.newwin(height, width + 5, start_y, start_x + 4 * (width - 1))

    draw_box(terminal, height, width)
    draw_box(shop, height, width)
    draw_box(about, height, width)
    draw_box(faq, height, width)
    draw_box(cart, height, width + 5)

    terminal.addstr(1, 2, "terminal")
    shop.addstr(1, 2, "s shop")
    about.addstr(1, 2, "a about")
    faq.addstr(1, 2, "f faq")
    cart.addstr(1, 2, "c cart $ 0")

    terminal.refresh()
    shop.refresh()
    about.refresh()
    faq.refresh()
    cart.refresh()

    """
    header1_contents = "terminal"
    header1 = curses.newwin(3, len(header1_contents) + 5, 0, int(scn_w / 6))
    header1.bkgd(curses.color_pair(BORDER_COLOR))
    header1.box()
    header1.addstr(1, 2, header1_contents, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
    header1.refresh()

    header2_contents = "s shop"
    header2 = curses.newwin(3, 8, 0, int(scn_w / 6) + len(header1_contents) + 5)
    header2.bkgd(curses.color_pair(BORDER_COLOR))
    header2.box()
    header2.addstr(1, 2, header2_contents, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
    header2.refresh()
    """
    # return header1, header2
    return cart


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
