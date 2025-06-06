from collections import deque
import numpy as np
from PIL import Image, ImageDraw
import os
import re
from cv2 import cvtColor, COLOR_BGR2RGB, VideoWriter, VideoWriter_fourcc
from time import sleep

DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 333
COLUMN_WIDTH = 85

original_image = {}
updated_image = {}

GRAVITATIONAL_ACCELERATION = 0.5*9.8*0.003  # (1/2)a t^2
INITIAL_SPEED = 0

speed = INITIAL_SPEED
y = 0
positionList = []
rows = deque()
positionList.append(y)
for row in range(DISPLAY_HEIGHT+50):
    rows.append([])
    speed = speed + GRAVITATIONAL_ACCELERATION
    y = y + speed
    positionList.append(y)
    if y > DISPLAY_HEIGHT:
        break

counter = 1


def cleanup():
    """
    Cleans up video and picture files from previous sessions.
    """
    for root, dirs, files in os.walk("./static/"):
        for file in files:
            if file.startswith("Video") or file.startswith("Image"):
                old_vid_file_path = "./static/{}".format(file)
                os.remove(old_vid_file_path)


def validate_image_errors(image):
    """
    Checks the image for serious issues that might lead to error on the
    main page.
    """
    # If image is not in suitable format, raise error.
    if (image.format != "PNG") and (image.format != "BMP"):
        return "☝️ Error: The fountain only accepts .png or .bmp images. \
        Upload a new file with correct format."
    # If image is empty, raise error.
    try:
        if len(list(image.getcolors())) < 2:
            return "☝️ Error: You uploaded empty, once color file. There is not \
            much point in simulating it. Try something else."
    except TypeError:
        pass


def validate_image_warnings(image, dt):
    """
    Checks the image for non-serious issues that will be communicated on the
    results page. Saves size info about original and updated image.
    """
    converted = ""
    resized = ""
    saved_img_file_name = "None"
    global original_image
    original_image['width'] = image.width
    original_image['height'] = image.height
    # If the image has more than 2 colors, convert it to black-and-white.
    if len(image.getcolors()) > 2:
        image = image.convert("1")
        converted = "Converted"
    # If image bigger than 1024, make the image smaller.
    if original_image['width'] > 1024:
        factor = original_image['width'] / 1024
        updated_image['width'] = 1024
        updated_image['height'] = int(original_image['height'] / factor)
        size = updated_image['width'], updated_image['height']
        image.thumbnail(size, Image.Resampling.LANCZOS)
        resized = "Resized"
    else:
        updated_image['width'] = original_image['width']
        updated_image['height'] = original_image['height']
        size = updated_image['width'], updated_image['height']
    # If image was resized or converted, save the image.
    if resized == "Resized" or converted == "Converted":
        saved_img_file_name = 'Image{}.png'.format(dt)
        image.save(os.path.join("./static/", saved_img_file_name))
    return image, converted, resized


def prepare_pixels(image):
    '''
    Flips image, loads it pixel by pixel as a list and adds one empty display
    of pixels to the end. Returns a list of pixels.
    '''
    pixelList = []
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    pixelList = list(image.getdata())
    one_more_scene = DISPLAY_WIDTH*DISPLAY_HEIGHT
    for pixel in range(one_more_scene):
        pixelList.append(255)
    return pixelList


def cycle(pixelList, updated_image):
    global counter
    global drops
    global rows
    '''
    Updates drops y-position.
    ---
    Pops out the last row and appends a new one to the beginning.
    '''
    rows.pop()
    rows.appendleft([])
    '''
    Creates drops for each black pixel in pixelList. Checks for the end
    of the picture.
    '''
    listLength = len(pixelList)
    for column in range(updated_image['width']):  # range(DISPLAY_WIDTH):
        if counter < (listLength-1):
            if pixelList[counter] == 0:  # if pixel is black
                rows[1].append(column)
        counter += 1


def make_frame_color(size, pixelList, figure, background, rows):
    """
    Runs drop computations. Creates and draws PIL image and converts it
    to OpenCV image afterwards. Returns OpenCV np.array.
    """
    # global rows
    global positionList
    # Compute drops positions
    for i in range(5):  # For every 5th cround a frame is created.
        cycle(pixelList, updated_image)
    # Create image and draw drops
    im_pil = Image.new("RGB", size, color=background)
    draw = ImageDraw.Draw(im_pil)
    counter = 1
    for row in rows:
        for column in row:
            draw.point((column, int(round(positionList[counter], 0))), figure)
        counter += 1
    # Convert PIL image to OpenCV np.array
    im_cv = np.array(im_pil)
    im_cv = cvtColor(im_cv, COLOR_BGR2RGB)
    return im_cv


def make_frame_photo(size, pixelList, figure, background, rows):
    """
    Runs drop computations. Creates and draws PIL image and converts it
    to OpenCV image afterwards. Returns OpenCV np.array.
    """
    global positionList
    # Compute drops positions
    for i in range(5):  # For every 5th cround a frame is created.
        cycle(pixelList, updated_image)
    # Create image and draw drops
    im_pil = Image.open(background)
    draw = ImageDraw.Draw(im_pil)
    counter = 1
    for row in rows:
        for column in row:
            color = '#'+figure[int(column / COLUMN_WIDTH)]
            draw.point((column, int(round(positionList[counter], 0))), color)
        counter += 1
    # Convert PIL image to OpenCV np.array
    im_cv = np.array(im_pil)
    im_cv = cvtColor(im_cv, COLOR_BGR2RGB)
    return im_cv


def prepare_frames(pixelList, vid_file_name, rows):
    """
    Prepares a list of frames that matches visualisation style that
    user selected.
    """
    global original_image
    frameList = []
    duration = int((len(pixelList)/5)/1024)
    size = (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    if "RedOnBlack" in vid_file_name:
        background = "black"
        figure = "red"
        for i in range(duration):
            im_cv = make_frame_color(size, pixelList, figure, background, rows)
            frameList.append(im_cv)
    elif len(vid_file_name) > 70:
        background = "./static/fountain_background.png"
        figure = re.findall('-(.{6})', vid_file_name)
        figure.append('FFFFFF')
        for i in range(duration):
            im_cv = make_frame_photo(size, pixelList, figure, background, rows)
            frameList.append(im_cv)
    else:
        background = "white"
        figure = "black"
        for i in range(duration):
            im_cv = make_frame_color(size, pixelList, figure, background, rows)
            frameList.append(im_cv)
    return frameList


def create_video(vid_file_name, frameList):
    """
    Creates webm video from the list of frames and saves it into static
    directory.
    """
    global rows
    global counter
    size = (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    # Create video
    video_name = "{}.webm".format(vid_file_name)
    out = VideoWriter(video_name, VideoWriter_fourcc(*'VP80'), 61, size)
    length_of_frameList = len(frameList)
    for i in range(length_of_frameList):
        sleep(0.01)
        out.write(frameList[i])
    out.release()
    # Move video file to /static directory
    path1 = os.getcwd() + "/" + video_name
    path2 = os.getcwd() + "/static/" + video_name
    try:
        os.remove(path2)
    except FileNotFoundError:
        pass
    os.rename(path1, path2)
    counter = 0
    for row in rows:
        rows[counter] = []
        counter += 1
    counter = 0
