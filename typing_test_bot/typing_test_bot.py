import pynput, pytesseract, time, os
from PIL import Image, ImageGrab
from threading import Thread

# global variables
# press this key to start the bot
RUN_BOT_KEY = pynput.keyboard.Key.f2

# press this key to exit the program after completing the current typing
EXIT_KEY = pynput.keyboard.Key.f4

# press this key to stop the bot in the middle of typing
# just in case the program activates somewhere it's not supposed to
TERMINATE_TYPING_KEY = pynput.keyboard.Key.esc

# global variables which are modified by multiple threads
running = True
start_bot = False
terminate_typing = False


def main():
    """
    Things left to be done
    1. the ocr cannot read the word possibility
    2. the ocr randomly interprets the cursor as many different characters like [,l,I ; most common is [
    """
    global start_bot, terminate_typing
    key_typer = pynput.keyboard.Controller()
    # the key listener is a separate thread which listens for key presses
    # when a key is pressed it calls the given on_press function with the key as an argument
    key_listener = pynput.keyboard.Listener(on_press=on_key_press)
    page_up_key = pynput.keyboard.Key.page_up

    # the amount of time to wait between typing characters ; in seconds
    wait_between_characters = 0

    key_listener.start()
    while running:
        if start_bot:
            # take a screenshot
            screen_shot = get_screen_shot()
            # the text box is the area in the screen shot where all the text that need to be typed is contained
            text_box = get_text_box_from_screen_shot(screen_shot)
            if text_box != None:
                text: "str" = pytesseract.image_to_string(text_box)
                text = sanitize_text(text)
                print(text)
                print()
                # start typing text in a separate thread and wait for the typing to complete
                terminate_typing = False
                key_typer_thread = Thread(
                    target=type_text, args=(key_typer, text, wait_between_characters)
                )
                key_typer_thread.start()
                key_typer_thread.join()

                # after the typing is completed the webpage randomly scrolls down sometimes
                # so to get back to the top of the page press page up
                # before that wait for the webpage to actually go down
                time.sleep(2)
                key_typer.press(page_up_key)
                time.sleep(1)
                key_typer.release(page_up_key)
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


def get_screen_shot():
    # in this region the text box will definitely be present without the other clutter of the website
    screenshot_boundaries = (0, 200, 1300, 620)  # top_left,bottom_right
    # hardcoded numbers obtained through trial and error
    screen_shot = ImageGrab.grab(screenshot_boundaries)
    return screen_shot


def get_text_box_from_screen_shot(screen_shot: "Image.Image"):
    # the colour of the text box is different from all the other things in the screenshot
    # this is the colour of the text box when it is focused
    # the text box has a different colour when it is unfocused
    # this is the colour of the textbox when it is focused
    text_box_colour = (234, 243, 250)  # rgb colour ; hardcoded
    width, height = screen_shot.size
    text_box_top_left = None
    text_box_bottom_right = None
    for y in range(height):
        for x in range(width):
            pixel = screen_shot.getpixel((x, y))
            if pixel == text_box_colour:
                if text_box_top_left == None:
                    text_box_top_left = (x, y)
                text_box_bottom_right = (x, y)
    if text_box_top_left != None:
        print("Text Box Found")
        text_box_boundaries = text_box_top_left + text_box_bottom_right
        text_box = screen_shot.crop(text_box_boundaries)
        return text_box
    else:
        print("Cannot Find Text Box")
        return None


def sanitize_text(text: "str"):
    text = text.replace(
        "[", ""
    )  # the ocr most commonly interprets the cursor as [, [ is never going to be in the text to be typed
    if text[0].islower():
        # the first letter of the text is supposed to be uppercase
        # so if the first letter is lowercase, the ocr probably interpreted the cursor as a lowercase letter
        text = text[1:]
    text = text.replace("|", "I")  # the ocr interprets uppercase I as pipe |
    text = text.replace("\n", " ")  # spaces are needed instead of newlines
    text = text.replace(
        "  ", " "
    )  # sometimes there are accidental two spaces in a row when there should be one
    text = text.replace(
        "ona", "on a"
    )  # the ocr interprets "on a" as a single word "ona", the actual word "ona" will probably not be in the text
    return text


def type_text(key_typer: "pynput.keyboard.Controller", text, wait_between_characters):
    # runs in a separate thread so that it can be stopped by pressing a key
    for char in text:
        key_typer.tap(char)
        time.sleep(wait_between_characters)
        if terminate_typing:
            break


main()
