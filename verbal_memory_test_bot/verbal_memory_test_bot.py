import pynput, pytesseract, time
from PIL import Image, ImageGrab


WORD_BOX = (0, 350, 1300, 450)  # the rectangular area where the word will appear
START_BUTTON_COORDINATES = (680, 570)  # the position of the start button
NEW_BUTTON_COORDINATES = (740, 490)  # the position of the new word button
SEEN_BUTTON_COORDINATES = (610, 490)  # the position of the seen word button

RUN_BOT_KEY = pynput.keyboard.Key.f2
PAUSE_BOT_KEY = pynput.keyboard.Key.f3
RESET_BOT_KEY = pynput.keyboard.Key.f4
EXIT_KEY = pynput.keyboard.Key.esc

LEFT_MOUSE_BUTTON = pynput.mouse.Button.left

running = True
has_bot_started = False
is_bot_running = False
reset_bot = False


def main():
    global running, has_bot_started, is_bot_running, reset_bot
    keyboard_listener = pynput.keyboard.Listener(on_press=on_key_press)
    mouse = pynput.mouse.Controller()

    seen_words = set()

    keyboard_listener.start()
    while running:
        if is_bot_running:
            if not has_bot_started:
                mouse.position = START_BUTTON_COORDINATES
                mouse.click(LEFT_MOUSE_BUTTON)
                has_bot_started = True
                time.sleep(0.1)
            screen_shot = ImageGrab.grab(WORD_BOX)
            word = pytesseract.image_to_string(screen_shot)
            if word in seen_words:
                mouse.position = SEEN_BUTTON_COORDINATES
            else:
                mouse.position = NEW_BUTTON_COORDINATES
                seen_words.add(word)
            mouse.click(LEFT_MOUSE_BUTTON)
            time.sleep(0.03)

        if reset_bot:
            seen_words.clear()
            is_bot_running = False
            reset_bot = False
            has_bot_started = False

    keyboard_listener.stop()


def on_key_press(key):
    # runs in a separate thread
    global running, has_bot_started, is_bot_running, reset_bot
    if key == RUN_BOT_KEY:
        is_bot_running = True
    if key == PAUSE_BOT_KEY:
        is_bot_running = False
    if key == RESET_BOT_KEY:
        reset_bot = True
    if key == EXIT_KEY:
        running = False


main()
