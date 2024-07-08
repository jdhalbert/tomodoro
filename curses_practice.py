import curses

HEADER_COLOR = 1
PRODUCT_COLOR = 2
BORDER_COLOR = 3


def make_header(scn_h, scn_w):
    # Create a window for the header
    # Get screen dimensions
    header = curses.newwin(3, scn_w - (int(scn_w / 3)), 15, int(scn_w / 6))
    header.bkgd(curses.color_pair(BORDER_COLOR))
    header.box()
    header.addstr(1, 2, "Welcome to MyTerminalShop", curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
    header.refresh()
    return header


def main(stdscr: curses.window):
    stdscr.refresh()
    # Hide the cursor
    curses.curs_set(0)

    # Define color pairs
    curses.init_pair(HEADER_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(PRODUCT_COLOR, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(BORDER_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Create a window for the main content
    main_win = curses.newwin(height - 5, width, 3, 0)
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
