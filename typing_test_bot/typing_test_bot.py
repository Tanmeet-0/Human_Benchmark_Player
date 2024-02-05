import pynput, pytesseract, time
from PIL import Image, ImageGrab
from threading import Thread

# global constant variables
KEYBOARD = pynput.keyboard.Controller()
MOUSE = pynput.mouse.Controller()
MOUSE_BUTTONS = pynput.mouse.Button
# the amount of time to wait between typing characters ; in seconds
WAIT_BETWEEN_CHARACTERS = 0.003

# press this key to start the bot
RUN_BOT_KEY = pynput.keyboard.Key.f2
# press this key to exit the program after completing the current typing
EXIT_KEY = pynput.keyboard.Key.f4
# press this key to stop the bot in the middle of typing
# just in case the program activates somewhere it's not supposed to
TERMINATE_TYPING_KEY = pynput.keyboard.Key.esc

# in this region the text box will definitely be present without the other clutter of the website
SCREENSHOT_BOUNDARIES = (0, 200, 1300, 620)  # top_left,bottom_right
# hardcoded numbers obtained through trial and error
# this is the colour of the text box when it is focused
TEXT_BOX_COLOUR = (234, 243, 250)  # rgb colour ; hardcoded

# global variables which are modified by multiple threads
running = True
start_bot = False
terminate_typing = False


def main():
    """
    Problems
    1. the ocr cannot read the words possibility, occasionally
    """
    global start_bot, terminate_typing

    # the key listener is a separate thread which listens for key presses
    # when a key is pressed it calls the given on_press function with the key as an argument
    key_listener = pynput.keyboard.Listener(on_press=on_key_press)

    key_listener.start()
    while running:
        if start_bot:
            # take a screenshot
            screen_shot = ImageGrab.grab(SCREENSHOT_BOUNDARIES)
            # the text box is the area in the screen shot where all the text that need to be typed is contained
            text_box = get_text_box_from_screen_shot(screen_shot)
            if text_box != None:
                text: "str" = pytesseract.image_to_string(text_box)
                text = sanitize_text(text)
                print(text)
                print()
                # start typing text in a separate thread and wait for the typing to complete
                terminate_typing = False
                key_typer_thread = Thread(target=type_text, args=(text,))
                key_typer_thread.start()
                key_typer_thread.join()
            start_bot = False
    key_listener.stop()
    print("Exiting...")


def on_key_press(key):
    if key == RUN_BOT_KEY:
        global start_bot
        if not start_bot:
            start_bot = True
    if key == EXIT_KEY:
        global running
        running = False
    if key == TERMINATE_TYPING_KEY:
        global terminate_typing
        terminate_typing = True


def get_text_box_from_screen_shot(screen_shot):
    """
    The text box has no fixed size but it has a fixed colour.
    Use the colour of the text box to find the text box

    The text box has a unique colour when it is focused, meaning nothing on the webpage has the same colour as the text box
    But when the text box is focused it displays a cursor, the ocr interprets the cursor as a character which gives a wrong result
    But when the text box is unfocused it does not have a unique colour, meaning other things on the webpage have the same colour as the text box
    SOOOOO
    Take a screenshot when the text box is focused
    find the boundaries of the text box
    unfocus from the text box
    take a screenshot of just the unfocused text box
    focus on the text box so that it can be typed on
    """
    text_box_boundaries = get_text_box_boundaries_from_screen_shot(screen_shot)
    if text_box_boundaries == None:
        return None

    # unfocus on the text box by clicking outside the text box
    point_outside_text_box = (
        SCREENSHOT_BOUNDARIES[0],
        SCREENSHOT_BOUNDARIES[1],
    )  # top-left of screenshot
    MOUSE.position = point_outside_text_box
    MOUSE.click(MOUSE_BUTTONS.left)

    # wait for the webpage to update
    time.sleep(0.1)

    # the text box boundaries are relative to the screenshot
    # so get the the text box boundaries relative to the screen
    text_box_boundaries = list(text_box_boundaries)
    text_box_boundaries[0] += SCREENSHOT_BOUNDARIES[0]
    text_box_boundaries[1] += SCREENSHOT_BOUNDARIES[1]
    text_box_boundaries[2] += SCREENSHOT_BOUNDARIES[0]
    text_box_boundaries[3] += SCREENSHOT_BOUNDARIES[1]
    # take screenshot of the unfocused text box
    text_box = ImageGrab.grab(text_box_boundaries)

    # focus on the text box by clicking inside the text box
    point_inside_text_box = (
        text_box_boundaries[0],
        text_box_boundaries[1],
    )  # top-left of text box
    MOUSE.position = point_inside_text_box
    MOUSE.click(MOUSE_BUTTONS.left)

    return text_box


def get_text_box_boundaries_from_screen_shot(screen_shot: "Image.Image"):
    """
    Search for the text box colour in the screenshot
    The first match of the colour is the top left of the text box
    And the last match of the colour is the bottom right of the text box
    """
    width, height = screen_shot.size
    text_box_top_left = None
    text_box_bottom_right = None
    for y in range(height):
        for x in range(width):
            pixel = screen_shot.getpixel((x, y))
            if pixel == TEXT_BOX_COLOUR:
                if text_box_top_left == None:
                    text_box_top_left = (x, y)
                text_box_bottom_right = (x, y)
    if text_box_top_left != None:
        print("Text Box Found")
        text_box_boundaries = text_box_top_left + text_box_bottom_right
        return text_box_boundaries
    else:
        print("Cannot Find Text Box")
        return None


def sanitize_text(text: "str"):
    text = text.replace("|", "I")  # the ocr interprets uppercase I as pipe |
    text = text.replace("\n", " ")  # spaces are needed instead of newlines
    text = text.replace(
        "  ", " "
    )  # sometimes there are accidental two spaces in a row when there should be one
    text = text.replace(
        "ona", "on a"
    )  # the ocr interprets "on a" as a single word "ona", the actual word "ona" will probably not be in the text
    text = text.strip()  # remove the leading and trailing whitespaces
    return text


def type_text(text):
    # runs in a separate thread so that it can be stopped by pressing a key
    for char in text:
        KEYBOARD.tap(char)
        time.sleep(WAIT_BETWEEN_CHARACTERS)
        if terminate_typing:
            break


main()
