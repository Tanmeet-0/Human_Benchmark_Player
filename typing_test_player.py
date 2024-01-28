import pynput, pytesseract, time, os
from PIL import ImageGrab


def on_key_press(key):
    if key == start_stop_key:
        global start_typing
        start_typing = not start_typing
    if key == exit_key:
        global running
        running = False
    if key == immediate_shutdown_key:
        #stop everything and exit
        os._exit(0)


key_typer = pynput.keyboard.Controller()
key_listener = pynput.keyboard.Listener(on_press=on_key_press)
page_up_key = pynput.keyboard.Key.page_up
website_reload_key = pynput.keyboard.Key.f5
start_stop_key = pynput.keyboard.Key.f2
exit_key = pynput.keyboard.Key.f4 # exit the program after completing the current typing
immediate_shutdown_key = pynput.keyboard.Key.esc # just in case the program activates somewhere it's not supposed to
running = True
start_typing = False

# take a screenshot where the text box will definitely be present without the other clutter of the website
screen_shot_boundaries = (
    0,
    200,
    1300,
    620,
)  # top_left,bottom_right ; hardcoded magic numbers

# the color of the text box where all the text that need to be typed will be present
text_box_colour = (234, 243, 250)  # rgb colour ; hardcoded magic numbers


key_listener.start()
while running:
    if start_typing:
        #reload the webpage so that the cursor focuses on the text box
        key_typer.tap(website_reload_key)
        #wait for the webpage to reload
        time.sleep(1)
        #take a screenshot
        screen_shot = ImageGrab.grab(screen_shot_boundaries)
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
            text: "str" = pytesseract.image_to_string(text_box)
            text = text.replace("[", "")  # the ocr interprets the cursor as [
            text = text.replace("|", "I")  # the ocr interprets Capital I as pipe |
            text = text.replace("\n", " ")  # spaces are needed instead of newlines
            text = text.replace("  "," ") # sometimes there are accidental two spaces in a row
            key_typer.type(text)
            print(text)
            print()
            #after the typing is completed the webpage randomly scrolls down sometimes
            #so to get back to the top of the page press page up
            #wait for the webpage to actually go down
            time.sleep(1.5)
            key_typer.tap(page_up_key)
            #wait before the next typing
            time.sleep(5)
        else:
            print("Cannot Find Text Box")


key_listener.stop()
print("Exiting...")
