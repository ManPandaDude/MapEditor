import pygame
import os
from shutil import copyfile
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfile, askdirectory
import data.scripts.text as scripts_text
import json

# Init
os.environ['SDL_VIDEO_WINDOW_POS'] = str(0) + "," + str(23)  # Sets pos of window to (0, 23)
Tk().withdraw()
pygame.init()
WINDOW_SIZE = (1920, 1056)
display = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED + pygame.RESIZABLE)  # Creates window, makes it resizable & scalable with pygame.SCALED + pygame.RESIZEABLE
screen = pygame.Surface(WINDOW_SIZE)
pygame.display.set_caption("Map Editor")

# Colors
very_dark_purple = (31, 24, 60)
dark_purple = (51, 44, 80)
purple = (71, 64, 100)
cyan = (70, 135, 145)
img_colorkey = (0, 0, 0)
bg_color = (15, 15, 15)

# Images
null_img = pygame.transform.scale(pygame.image.load('data/null.png').convert(), (32, 32))
background_img = pygame.image.load('data/background.png').convert()
sidebar_img = pygame.transform.scale(pygame.image.load('data/editor gui.png').convert(), (416, 1056))
sidebar_img.set_colorkey(img_colorkey)
tiny_mouse_dot_img = pygame.image.load('data/mouse.png').convert()
right_arrow1 = pygame.transform.scale(pygame.image.load('data/arrow1.png').convert_alpha(), (32, 32))
right_arrow2 = pygame.transform.scale(pygame.image.load('data/arrow2.png').convert_alpha(), (32, 32))
left_arrow1 = pygame.transform.flip(right_arrow1, True, False)
left_arrow2 = pygame.transform.flip(right_arrow2, True, False)
orig_player_img = pygame.image.load('data/player.png').convert()
orig_player_img = pygame.transform.scale(orig_player_img, (orig_player_img.get_width() * 2, orig_player_img.get_height() * 2))
orig_player_img.set_colorkey(img_colorkey)
orig_player_img.set_alpha(150)
player_img = orig_player_img.copy()
# mouse_img = pygame.transform.scale(mouse_img, (32, 32))

tile_index = {"null": null_img}  # Dictionary of images
rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}  # Used for tabs inside of editor


def create_sidebar_image(rect_image_dict_, new_tile_index, image, name, gap):
    """Loops through images and creates positions for them to be blitted on the sidebar"""
    image_rect = image.get_rect()
    starting_pos = [15, 243]
    ending_pos = 1051
    # Finds out which tab the image belongs in
    if name[0:5] == "enemy":
        tab_ = "mobs"
    elif image_rect.width == 32 and image_rect.height == 32:
        tab_ = "tiles"
    else:
        tab_ = "decorations"

    if len(rect_image_dict_[tab_]) > 0:  # If tab isn't empty
        # If the y position is colliding with the bottom of sidebar, set y position to the top and starts a new row
        if list(rect_image_dict_[tab_].values())[-1].y + (list(rect_image_dict_[tab_].values())[-1].height * 2) + gap > ending_pos:
            image_rect.x, image_rect.y, = (list(rect_image_dict_[tab_].values())[-1].x + image_rect.width + gap), starting_pos[1]
        else:
            # Creates the position normally by putting it under whichever image was last
            image_rect.x, image_rect.y, = list(rect_image_dict_[tab_].values())[-1].x, (list(rect_image_dict_[tab_].values())[-1].y +
                                                                                        list(rect_image_dict_[tab_].values())[-1].height) + gap
    else:
        # If there aren't any images in the tab, set the position of the image to the start
        image_rect.x, image_rect.y, = tuple(starting_pos)
    # If image collides with last image move it down by 1 pixel until it doesn't collide anymore, then add the gap
    for rect in rect_image_dict_[tab_].values():
        if image_rect.colliderect(rect):
            while image_rect.colliderect(rect):
                image_rect.y += 1
            image_rect.y += gap

    new_tile_index[name] = image  # Adds image to tile_index
    # If image rect is already inside rect_image_dict, remove it and replace it with current image
    if name in rect_image_dict_[tab_]:
        image_rect.x, image_rect.y, = rect_image_dict_[tab_][name].x, rect_image_dict_[tab_][name].y
        rect_image_dict_[tab_].pop(name)
        rect_image_dict_[tab_][name] = image_rect
    else:
        rect_image_dict_[tab_][name] = image_rect
    return rect_image_dict_, new_tile_index, image_rect


def clip(surf, x_, y_, x_size, y_size):
    """Clips image based on x and y"""
    handle_surf = surf.copy()  # Copy of surface that we're clipping from
    clip_rect = pygame.Rect(x_, y_, x_size, y_size)  # Creates a rect with the same size and positions as the area we're clipping
    handle_surf.set_clip(clip_rect)  # Sets the current clipping area of the surface
    image = surf.subsurface(handle_surf.get_clip())  # Clip the area out of surf and set it to image
    return image.copy()


def load_spritesheet(path, new_tile_index, rect_image_dict_, scale=2):
    """Loads a spritesheet by clipping out areas marked with pink and cyan pixels"""
    row_content = {}
    new_ui_images = {}
    rows = []
    spritesheet_ = pygame.image.load(path).convert()
    spritesheet_.set_colorkey((0, 0, 0))
    name = path.split("/")[-1].split(".")[0]
    # looks down and stores the positions of all pink pixels in row variable
    for y_ in range(spritesheet_.get_height()):
        c = spritesheet_.get_at((0, y_))
        c = (c[0], c[1], c[2])
        if c == (255, 0, 255):
            rows.append(y_)
    i_ = 0
    for row in rows:
        row_content = {}
        # Looks to the right until it finds a pink pixel
        for x_ in range(spritesheet_.get_width()):
            c = spritesheet_.get_at((x_, row))
            c = (c[0], c[1], c[2])
            if c == (255, 0, 255):  # found tile
                # Looks to the right of pink pixel for a blue one
                x2_ = 0
                while True:
                    x2_ += 1
                    c = spritesheet_.get_at((x_ + x2_, row))
                    c = (c[0], c[1], c[2])
                    if c == (0, 255, 255):
                        break
                # Looks to the bottom of the blue pixel until it finds another blue pixel
                y2_ = 0
                while True:
                    y2_ += 1
                    c = spritesheet_.get_at((x2_, row + y2_))
                    c = (c[0], c[1], c[2])
                    if c == (0, 255, 255):
                        break
                # Cuts image out and adds it to the list
                img = clip(spritesheet_, x_ + 1, row + 1, x2_ - 1, y2_ - 1)
                img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
                img.set_colorkey((255, 255, 255))
                row_content[name + str(i_)] = img
                rect_image_dict_, new_tile_index, image_rect = create_sidebar_image(rect_image_dict_, new_tile_index, img, name + str(i_), 5)
                i_ += 1
        # spritesheet_images[name] = row_content  # Saves each row into its own list
        new_tile_index.update(row_content)
        new_ui_images = new_tile_index.copy()
    return row_content, rect_image_dict_, new_tile_index, new_ui_images


def load_saved_images(path, rect_image_dict_, new_tile_index, scale=2):
    """Loads all images in 'saved images' folder"""
    # folder_name = path.split("/")[-2]
    # rect_image_dict2 = {"tiles": {}, "decorations": {}, "mobs": {}}
    for entry in os.scandir(path):  # Loops through all files in directory
        # Checks if entry has the attributes 'path', 'is_file' and 'name'. Pycharm makes the annoying yellow squiggles even though entry always has those attributes
        if hasattr(entry, 'path') and hasattr(entry, 'is_file') and hasattr(entry, 'name'):

            # Checks if the file is an image
            if (entry.path.endswith(".png") or entry.path.endswith(".jpg") or entry.path.endswith(".PNG") or entry.path.endswith(".JPG")) and entry.is_file():
                # If the image is in the 'spritesheets' folder, load it as a spritesheet
                if path == settings["spritesheets_path"] + "/":
                    image = pygame.image.load(entry.path).convert()  # Loads image and converts for performance
                    image.set_colorkey(img_colorkey)  # Sets the colorkey to black because we used convert to load the image
                    # Loads spritesheet
                    spritesheet, rect_image_dict_, new_tile_index, new_ui_images = load_spritesheet(path + entry.name, tile_index, rect_image_dict)
                else:  # If image is NOT in 'spritesheets' folder load as a normal image
                    image = pygame.image.load(entry.path).convert()  # Loads image and converts for performance
                    image.set_colorkey(img_colorkey)  # Sets the colorkey to black because we used convert to load the image
                    image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))  # Scales image to 2x resolution because pixel art
                    name = os.path.splitext(entry.name)[0]  # Removes the .png/.jpg from end of name
                    # Creates a sidebar image for each image loaded
                    rect_image_dict_, new_tile_index, image_rect = create_sidebar_image(rect_image_dict_, new_tile_index, image, name, 5)
    new_ui_images = new_tile_index.copy()  # Updates ui_images, ui_images stores all the images at normal resolution to display on the sidebar
    return rect_image_dict_, new_tile_index, new_ui_images


if not os.path.isfile("data/settings.json"):  # If settings file doesn't exist:
    file = open('data/settings.json', 'w')  # Creates settings file
    # Writes data to settings file, I use new lines to make settings file readable for humans
    settings = {"tiles_path": "data/images/tiles/", "spritesheets_path": "data/images/spritesheets/", "maps_path": "data/maps"}  # Settings
    json.dump(settings, file, indent=0)  # Writes settings to settings file
    file.close()
else:
    # Loads settings
    file = open('data/settings.json', 'r')  # Opens settings file
    settings = json.load(file)  # Loads settings
    file.close()  # Closes file

rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
# noinspection PyRedeclaration
rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict, tile_index)  # Loads all images from spritesheets path
# noinspection PyRedeclaration
rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

# Editor

tab = "tiles"  # The current tab, defaulted to 'tiles'
tile_map = {}  # Declaring tile_map, to stop pycharm from yelling at me
selection = None  # The current tile that's selected
tile_size = 32  # The current size of tiles, changes when player zooms in/out
mouse = pygame.mouse.get_pos()  # Mouse location
mouse_rect = pygame.Rect(mouse, (1, 1))  # Mouse rect used for collisions
scroll = [0, 0]  # Scroll
zoom = 0  # Current zoom, used for zooming in/out
update = False  # If true it redraws every tile on the screen
map_file_path = ""  # Map file path
error = ""  # Error message for menu
old_pressed = pygame.mouse.get_pressed(3)[1]
pixels_scrolled = [0, 0]  # Used for scrolling
screen_copy = screen.copy()  # Copy of the screen
tile_pos = [0, 0]  # Position of the tile
tile_range = [34, 60]  # Pycharm yells at me
offset = [16, 16]  # Used for blitting tiles on screen in a grid
left_mouse_button = False  # Left mouse click, can be true or false
clock = pygame.time.Clock()  # Clock
current_layer = "0"  # Current layer
layer_dict = {}  # Dictionary of every layer surface

# Fonts
white_font = scripts_text.Font("data/fonts/large_font.png", (240, 240, 240), img_colorkey, 1, )
dark_purple_font = scripts_text.Font("data/fonts/large_font.png", dark_purple, img_colorkey, 1.5, )
warning_text = scripts_text.Font("data/fonts/large_font.png", dark_purple, img_colorkey, 5, )
purple_menu_font1 = scripts_text.Font("data/fonts/large_font.png", dark_purple, img_colorkey, 6, )
purple_menu_font2 = scripts_text.Font("data/fonts/large_font.png", purple, img_colorkey, 6, )
purple_editor_font1 = scripts_text.Font("data/fonts/large_font.png", dark_purple, img_colorkey, 2, )
purple_editor_font2 = scripts_text.Font("data/fonts/large_font.png", purple, img_colorkey, 2, )
jumbo_purple_font = scripts_text.Font("data/fonts/large_font.png", dark_purple, img_colorkey, 9, )


# Buttons
class TextButton:
    """Button made from text"""

    def __init__(self, font1, font2, text, surf, position, num_x=0):
        self.font1 = font1  # Default font used
        self.font2 = font2  # Font used for mouse over
        self.text = text
        self.surf = surf
        self.position = position
        self.num_x = num_x  # Increases or decreases the hitbox down along the x-axis
        self.clicked = False
        self.width = self.font1.width(self.text)[-1]
        self.height = self.font1.height(self.text)
        self.positions = {"top": self.position[1], "left": self.position[0], "bottom": self.position[1] + self.height, "right": self.position[0] + self.width}

    def update(self, _pressed):
        """Draws button and handles button function by setting clicked to True or False depending on if button was clicked or not.
        font1 is the main color, font2 is the hover color. text is the text of the button. surf is the surface that the button will be blitted on.
        pos_ is the position that the button will be blitted. _pressed is left mouse button down, can be true or false.
        """
        mouse_ = pygame.mouse.get_pos()
        self.clicked = False
        # If mouse is over button and clicking:
        if self.positions["left"] <= mouse_[0] <= self.positions["right"] and self.positions["bottom"] - self.num_x >= mouse_[1] >= self.positions["top"] and _pressed:
            self.clicked = True
        # If mouse is over button, change color of button
        if self.positions["left"] <= mouse_[0] <= self.positions["right"] and self.positions["bottom"] - self.num_x >= mouse_[1] >= self.positions["top"]:
            self.font2.render(self.text, self.surf, (self.position[0], self.position[1] - 5))
        # Else, draw button on normal color
        else:
            self.font1.render(self.text, self.surf, self.position)

    def change_text(self, text):
        """Changes text I guess"""
        self.text = text
        self.width = self.font1.width(self.text)[-1]
        self.height = self.font1.height(self.text)
        self.positions = {"top": self.position[1], "left": self.position[0], "bottom": self.position[1] + self.height, "right": self.position[0] + self.width}


class ImageButton:
    """Button made from images"""

    def __init__(self, surf1, surf2, position, num_x=0):
        self.surf1 = surf1  # Default image for button
        self.surf2 = surf2  # Image for button hover
        self.position = position  # Pos that button will be blitted
        self.num_x = num_x  # Increases or decreases the hitbox down along the x-axis
        self.clicked = False
        self.width = surf1.get_width()  # Width of button
        self.height = surf1.get_height()  # Height of button
        # Positions of the sides of the button
        self.positions = {"top": self.position[1], "left": self.position[0], "bottom": self.position[1] + self.height, "right": self.position[0] + self.width}

    def update(self, _pressed):
        """Blits button to screen"""
        _mouse = pygame.mouse.get_pos()  # Mouse pos
        self.clicked = False
        # If mouse is over button and clicking:
        if self.position[0] <= _mouse[0] <= self.position[0] + self.width and self.positions["bottom"] - self.num_x >= _mouse[1] >= self.positions["top"] and _pressed:
            self.clicked = True
        # If mouse is over button, blit second surface
        if self.position[0] <= _mouse[0] <= self.position[0] + self.width and self.positions["bottom"] - self.num_x >= _mouse[1] >= self.positions["top"]:
            display.blit(self.surf2, (self.position[0], self.position[1] - 5))
        # Else, draw button on normal surface
        else:
            display.blit(self.surf1, self.position)


left_arrow_button = ImageButton(left_arrow1, left_arrow2, (13, 190))  # Left arrow button used for changing layers
right_arrow_button = ImageButton(right_arrow1, right_arrow2, [80, 190])  # Right arrow button used for changing layers

load_map_button = TextButton(purple_menu_font1, purple_menu_font2, "Load Map", screen,  # Load map button, button for loading map
                             (screen.get_width() / 2 - purple_menu_font1.width("Load Map")[-1] / 2, 285), )
new_map_button = TextButton(purple_menu_font1, purple_menu_font2, "New Map", screen,  # Button for creating a new map
                            (screen.get_width() / 2 - purple_menu_font1.width("New Map")[-1] / 2, 415), )
settings_button = TextButton(purple_menu_font1, purple_menu_font2, "Settings", screen,  # Button for creating a new map
                             (screen.get_width() / 2 - purple_menu_font1.width("New Map")[-1] / 2, 545), )
exit_button = TextButton(purple_menu_font1, purple_menu_font2, "Exit", screen,  # Button for exiting program
                         (screen.get_width() / 2 - purple_menu_font1.width("Exit")[-1] / 2, 675), )

tiles_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Tiles Path", screen,  # Tiles path button for settings
                               (screen.get_width() / 2 - purple_menu_font1.width("Tiles Path")[-1] / 2, 285), )
spritesheets_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Spritesheets Path", screen,  # Spritesheets path button for settings
                                      (screen.get_width() / 2 - purple_menu_font1.width("Spritesheets Path")[-1] / 2, 415), )
maps_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Map Folder", screen,  # Maps path button for settings
                              (screen.get_width() / 2 - purple_menu_font1.width("Map Folder")[-1] / 2, 545), )
back_button = TextButton(purple_menu_font1, purple_menu_font2, "Back", screen,  # Back button for settings
                         (screen.get_width() / 2 - purple_menu_font1.width("Back")[-1] / 2, 675), )

tiles_button = TextButton(purple_editor_font1, purple_editor_font2, "TILES", display, (15, 17))  # Button for "tiles" tab
decorations_button = TextButton(purple_editor_font1, purple_editor_font2, "DECOR", display, (15, 52))  # Button for "decorations" tab
mobs_button = TextButton(purple_editor_font1, purple_editor_font2, "MOBS", display, (15, 87))  # Button for "mobs" tab
editor_load_map_button = TextButton(purple_editor_font1, purple_editor_font2, "LOAD MAP", display, (100, 17))  # Load map button for editor
editor_load_image_button = TextButton(purple_editor_font1, purple_editor_font2, "LOAD IMAGE", display, (100, 52))  # Load image  button for editor
editor_settings_button = TextButton(purple_editor_font1, purple_editor_font2, "SETTINGS", display, (100, 87))  # Load image  button for editor
# List of buttons for editor, this is used to loop through each button in editor and display them
editor_button_list = (tiles_button, decorations_button, mobs_button, editor_load_map_button, editor_load_image_button, left_arrow_button, right_arrow_button,
                      editor_settings_button)


def load_image(rect_image_dict_, path, new_tile_index, ui_images_):
    """ Loads an image"""
    file_path = askopenfilename()  # Creates a file dialog for user to choose an image
    basename = os.path.basename(file_path)  # Name of the file
    name = basename.split(".")[0]  # Name of the file without the .png/.jpg
    if not file_path:  # If user closed file dialog:
        return rect_image_dict_, new_tile_index, ui_images_  # Ends function with nothing changed
    copyfile(file_path, path + str(basename))  # Saves the image
    gap = 5  # Gap to place inbetween sidebar images
    image = pygame.image.load(file_path).convert()  # Image
    image.set_colorkey(img_colorkey)  # Erases all black pixels(0, 0, 0)
    image = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))  # Scales image to 2x size
    image_rect = image.get_rect()  # Creates a rect out of image, used for sidebar image collisions

    # Finds out which tab image belongs in
    if name[0:5] == "enemy":  # If the first 5 characters in the name are "enemy"
        tab_ = "mobs"  # Then put it in "mobs" tab
    elif image_rect.width == 32 and image_rect.height == 32:  # Else if image is 32x32:
        tab_ = "tiles"  # Then put in it "tiles" tab
    else:
        tab_ = "decorations"  # Else put it in decorations

    # Determines what pos image should be at for sidebar
    if len(rect_image_dict_[tab_]) > 0:  # If tab is not empty
        # If previous_image.y + current_image.height * 2 + gap > sidebar_ending_pos
        # Basically if image pos is past ending pos
        if list(rect_image_dict_[tab_].values())[-1].y + (list(rect_image_dict_[tab_].values())[-1].height * 2) + gap > 1011:
            image_rect.x, image_rect.y, = (list(rect_image_dict_[tab_].values())[-1].x + image_rect.width + gap), 323  # Then set image to be on top and to the
            # -right of image that's on top
        else:
            # Else set image to be below last image
            image_rect.x, image_rect.y, = list(rect_image_dict_[tab_].values())[-1].x, (list(rect_image_dict_[tab_].values())[-1].y +
                                                                                        list(rect_image_dict_[tab_].values())[-1].height) + gap
    else:  # Else tab is empty:
        image_rect.x, image_rect.y, = (39, 323)  # Set image to default position on sidebar
    for rect in rect_image_dict_[tab_].values():  # Loops through all image_rects inside all tabs
        if image_rect.colliderect(rect):  # If image_rect collides with rect:
            while image_rect.colliderect(rect):  # Adds 1 to image_rect.y until image_rect doesn't collide with rect anymore
                image_rect.y += 1
            image_rect.y += gap  # Adds gap

    new_tile_index[name] = image  # Adds image to tile_index
    # If image already exists replace it
    if name in rect_image_dict_[tab_]:
        image_rect.x, image_rect.y, = rect_image_dict_[tab_][name].x, rect_image_dict_[tab_][name].y  # Sets image x and y to the x and y of image being replaced
        rect_image_dict_[tab_].pop(name)  # Removes image that will be replaced
        rect_image_dict_[tab_][name] = image_rect  # Adds image to rect_image_dict
    else:
        rect_image_dict_[tab_][name] = image_rect  # If it doesn't exist already add image in normally
    new_ui_images = new_tile_index.copy()

    return rect_image_dict_, new_tile_index, new_ui_images


def save_map():
    """Saves map and adds layers to 'all_layers' by looping through 'map' and 'mobs'"""
    layer_list = []
    f = open(map_file_path, "w")  # Opens map file
    # Loops through every tile in map and saves them to layer_list
    for chunk_ in tile_map["map"].values():
        for tile_ in chunk_.values():
            for layer_ in tile_:
                if layer_ not in layer_list:
                    layer_list.append(layer_)
    # Loops through every tile in map and saves them to layer_list
    for chunk_ in tile_map["mobs"].values():
        for tile_ in chunk_.values():
            for layer_ in tile_:
                if layer_ not in layer_list:
                    layer_list.append(layer_)

    if "0" not in layer_list:  # If layer "0" not in layer_list: add it, because the way I coded things layer 0 NEEDS to exist, without this code layer "0" won't exist
        layer_list.append("0")
    tile_map["all_layers"] = layer_list  # Saves the layers to map
    tile_map["all_layers"].sort(key=int)  # Sorts the layers inside of map, sorts them in order of (-10, -6, -1, 0, 2, 7, etc)
    json.dump(tile_map, f)  # Save the map by dumping map into json map file
    f.close()  # Closes file


def load_map(current_map_file_path=None, current_map_file=None, layer_dictionary=None):
    """Loads map"""
    try:
        # Creates a file dialog for user to open a json map
        file_name = askopenfilename(initialdir=settings["maps_path"], filetypes=[("jpeg files", "*.json")], defaultextension="*.json")
        f = open(file_name, 'r')  # Opens file
        data = json.load(f)  # Loads the contents from the json map, if file isn't json the function will crash and nothing will happen
        if file_name.endswith(".json") and isinstance(data, dict):  # If file is json and the json contents are a dictionary:
            f.close()  # Closes file
            layer_dict_ = {}
            # Loops through layers in the map and creates a surface for each one
            for i_ in data["all_layers"]:  # Loops through the layers in the map
                layer_dict_[str(i_)] = pygame.Surface(WINDOW_SIZE)  # Creates a surface for each layer
                layer_dict_[str(i_)].set_colorkey(bg_color)  # Sets the colorkey of surface to black, because when using convert() it sets the images fully transparent
                # -pixels to black
            return data, file_name, None, "editor", layer_dict_  # Returns stuff, except for the error, which is returned to None
        else:  # Else if the file is not a json file or the contents of the json file aren't a dictionary: function ends and nothing happens
            f.close()  # Closes map file
            return tile_map, current_map_file, "Load failed!", "menu", layer_dictionary  # Returns stuff, error is "Load failed!"
    except FileNotFoundError:  # If function crashed, nothing happens, error is "Load failed!"
        return current_map_file_path, current_map_file, "Load failed!", "menu", layer_dictionary


# def draw_button(font1, font2, text, surf, loc, num=0):
#     """Draws a button that can be hovered and clicked """
#     width = font1.width(text)[-1]  # Width of button
#     height = font1.height(text)  # Height of button
#     positions = {"top": loc[1], "left": loc[0], "bottom": loc[1] + height, "right": loc[0] + width}  # Positions of all sides of the button
#     # If button is being hovered:
#     if positions["left"] <= mouse[0] <= positions["right"] and positions["bottom"] - num >= mouse[1] >= positions["top"]:
#         font2.render(text, surf, (loc[0] - 10, loc[1] - 10))  # Render button with hover color
#     else:
#         font1.render(text, surf, loc)  # Else render with normal color
#     return positions


def calculate_line(x1, y1, x2, y2, fun, _zoom, layer_, offset_):
    """Calculates a line between last_mouse_position and current_mouse_position and calls a function for each one, used for drawing and erasing tiles"""
    w = x2 - x1
    h = y2 - y1
    dx1 = 0
    dy1 = 0
    dx2 = 0
    dy2 = 0
    if w < 0:
        dx1 = -1
    elif w > 0:
        dx1 = 1
    if h < 0:
        dy1 = -1
    elif h > 0:
        dy1 = 1
    if w < 0:
        dx2 = -1
    elif w > 0:
        dx2 = 1
    longest = abs(w)
    shortest = abs(h)
    if not longest > shortest:
        longest = abs(h)
        shortest = abs(w)
        if h < 0:
            dy2 = -1
        elif h > 0:
            dy2 = 1
        dx2 = 0

    numerator = longest >> 1
    _i = 0
    while _i <= longest:
        mouse_rect.x, mouse_rect.y = x1, y1
        if fun is not None:
            fun(_zoom, layer_, offset_)  # Calls function to either draw or erase tiles
        numerator += shortest
        if not numerator < longest:
            numerator -= longest
            x1 += dx1
            y1 += dy1
        else:
            x1 += dx2
            y1 += dy2
        _i += 1


def draw_tile(_zoom, layer_, offset_):
    """Draws tiles and enemies"""
    # If mouse isn't over sidebar:
    if mouse_rect.x > sidebar_img.get_width():  # if mouse_rect.x > 383 and mouse_rect.x < 1856 and mouse_rect.y > 96 and mouse_rect.y < 1024:

        tile_pos_ = [round(((mouse_rect.x - offset_[0]) + round(scroll[0])) / tile_size),  # Position of tile in pixels
                     round(((mouse_rect.y - offset_[1]) + round(scroll[1])) / tile_size)]
        chunk_pos_ = str(int((tile_pos_[0]) / 8)) + ";" + str(int((tile_pos_[1]) / 8))  # Position of chunk
        pos_ = str(tile_pos_[0]) + ";" + str(tile_pos_[1])  # Position of tile

        if selection[:5] == "enemy":  # If selected tile is an enemy: draw an enemy
            if chunk_pos_ not in tile_map["mobs"]:  # If the chunk doesn't exist in map:
                tile_map["mobs"][chunk_pos_] = {}  # Then create the chunk
            if pos_ not in tile_map["mobs"][chunk_pos_]:  # If tile doesn't exist:
                tile_map["mobs"][chunk_pos_][pos_] = {}  # Then create a dictionary for the tile

            tile_map["mobs"][chunk_pos_][pos_][layer_] = [selection]  # Adds the tile to layer

            # Sorts all tiles inside of layer
            tile_map["mobs"][chunk_pos_][pos_] = {key_: val for key_, val in sorted(tile_map["mobs"][chunk_pos_][pos_].items(), key=lambda ele: int(ele[0]))}
            # Blits all tiles inside layer
            for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]),
                            (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
        else:  # If tile is not an enemy:
            if chunk_pos_ not in tile_map["map"]:  # If the chunk doesn't exist in map:
                tile_map["map"][chunk_pos_] = {}  # Then create the chunk
            if pos_ not in tile_map["map"][chunk_pos_]:  # If tile doesn't exist:
                tile_map["map"][chunk_pos_][pos_] = {}  # Then create a dictionary for the tile

            tile_map["map"][chunk_pos_][pos_][layer_] = [selection]  # Adds tile to layer

            # Sorts the tiles inside of layer
            tile_map["map"][chunk_pos_][pos_] = {key_: val for key_, val in sorted(tile_map["map"][chunk_pos_][pos_].items(), key=lambda ele: int(ele[0]))}

            # Blits all tiles inside of layer
            for i_ in tile_map["map"][chunk_pos_][pos_]:
                if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                    screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]),
                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                else:
                    screen.blit((tile_index["null"]),
                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))


def erase_tile(_zoom, layer_, offset_):
    """Erases tiles and enemies"""
    # if mouse_rect.x > 383 and mouse_rect.x < 1856 and mouse_rect.y > 96 and mouse_rect.y < 1024:
    if mouse_rect.x > sidebar_img.get_width():  # If mouse isn't over sidebar:
        erased = False  # If function erases a tile: erased will be True and function will skip the "erase mob" part, if tile not erased then function will erase mob

        tile_pos_ = [round(((mouse_rect.x - offset_[0]) + round(scroll[0])) / tile_size),  # Position of tile in pixels
                     round(((mouse_rect.y - offset_[1]) + round(scroll[1])) / tile_size)]
        chunk_pos_ = str(int((tile_pos_[0]) / 8)) + ";" + str(int((tile_pos_[1]) / 8))  # Position of chunk
        pos_ = str(tile_pos_[0]) + ";" + str(tile_pos_[1])  # Position of tile

        if chunk_pos_ in tile_map["map"]:  # If chunk in map
            if pos_ in tile_map["map"][chunk_pos_]:  # If pos in map
                if layer_ in tile_map["map"][chunk_pos_][pos_]:  # If current_layer in tile
                    if tile_map["map"][chunk_pos_][pos_][layer_][0] in tile_index:
                        background_surface = tile_index[tile_map["map"][chunk_pos_][pos_][layer_][0]].copy()  # Creates a copy of tile being erased:
                    else:
                        background_surface = tile_index["null"].copy()  # Creates a copy of tile being erased:
                    background_surface.fill(bg_color)  # And fills it with background color:
                    # And blits it to screen to erase the tile visually
                    screen.blit(background_surface, (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                    tile_map["map"][chunk_pos_][pos_].pop(layer_)  # Removes tile from map
                    erased = True

                    for i_ in tile_map["map"][chunk_pos_][pos_]:  # Loops through tile and blits all layers
                        if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                            screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]), (int(tile_pos_[0] * tile_size) - scroll[0],
                                                                                                 int(tile_pos_[1] * tile_size) - scroll[1]))
                        else:
                            screen.blit((tile_index["null"]),
                                        (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                    if chunk_pos_ in tile_map["mobs"]:  # If chunk in map
                        if pos_ in tile_map["mobs"][chunk_pos_]:  # If tile in chunk
                            # Loops through layers inside tile and blits them all
                            for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                                screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]),
                                            (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                if chunk_pos_ in tile_map["map"]:  # If chunk in map
                    if pos_ in tile_map["map"][chunk_pos_]:  # If tile in chunk
                        # If tile is empty: delete tile
                        if not tile_map["map"][chunk_pos_][pos_]:
                            tile_map["map"][chunk_pos_].pop(pos_)
                    # If chunk is empty: delete chunk
                    if not tile_map["map"][chunk_pos_]:
                        tile_map["map"].pop(chunk_pos_)

        if chunk_pos_ in tile_map["mobs"] and erased is False:  # If chunk in map["mobs"]
            if pos_ in tile_map["mobs"][chunk_pos_]:  # If tile in chunk
                if layer_ in tile_map["mobs"][chunk_pos_][pos_]:  # If layer in tile
                    background_surface = tile_index[tile_map["mobs"][chunk_pos_][pos_][layer_][0]].copy()  # Creates a copy of tile being erased:
                    background_surface.fill(bg_color)  # And fills it with background color:
                    # And blits it over the tile being erased to erase it visually
                    screen.blit(background_surface, (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                    tile_map["mobs"][chunk_pos_][pos_].pop(layer_)  # Deletes tile

                    # Blits all tiles/mobs in the erased tile
                    for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                        screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]), (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size)
                                                                                              - scroll[1]))
                    if chunk_pos_ in tile_map["map"]:  # If chunk in map:
                        if pos_ in tile_map["map"][chunk_pos_]:  # If pos in chunk:
                            for i_ in tile_map["map"][chunk_pos_][pos_]:  # Loops through all layers in tile and blits them all
                                if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                                    screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]),
                                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                                else:
                                    screen.blit((tile_index["null"]), (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                if chunk_pos_ in tile_map["mobs"]:  # If chunk in map
                    if pos_ in tile_map["mobs"][chunk_pos_]:  # If tile in chunk
                        if not tile_map["mobs"][chunk_pos_][pos_]:  # If tile is empty:
                            tile_map["mobs"][chunk_pos_].pop(pos_)  # Delete tile
                    if not tile_map["mobs"][chunk_pos_]:  # If chunk is empty:
                        tile_map["mobs"].pop(chunk_pos_)  # Delete chunk


def scale_tiles(t_index, tile_index_copy, operator=""):
    """Scales every tile image, this is used for zooming the screen in and out, I simply scale every tile image and blit them with certain offset to give the illusion
    of zooming in/out. operator is a string, either '*' for multiplying tile images by zoom or '/' for dividing tile images by zoom"""
    if operator == "*":
        for key_ in tile_index_copy:  # Loops through all images in tile_index, and multiplies them by zoom
            img = tile_index_copy[key_]  # Creates a copy of the original image
            t_index[key_] = pygame.transform.scale(img, (img.get_width() * zoom, img.get_height() * zoom))  # Scales image

    elif operator == "/":
        for key_ in tile_index_copy:  # Loops through all images in tile_index, and divides them by zoom
            img = tile_index_copy[key_]  # Creates copy of original image
            t_index[key_] = pygame.transform.scale(img, (round(img.get_width() / abs(zoom)), round(img.get_height() / abs(zoom))))  # Scales image down

    else:
        for key_ in tile_index_copy:  # Loops through all images in tile_index, and sets them to normal resolution
            img = tile_index_copy[key_]  # Creates copy of original image
            t_index[key_] = pygame.transform.scale(img, (img.get_width(), img.get_height()))  # Sets image to original image
    return t_index, tile_index_copy


last_state = "menu"
state = "menu"  # The game state, can be 'menu' or 'editor'
running = True  # If true the game is running, if false game closes
while running:  # Main loop

    # Menu -------------------------------------------------------------------------------------------------------------------------------------------------------------
    if state == "menu":

        left_mouse_button = False  # Resets left mouse button click
        screen.blit(background_img, (0, 0))  # Blits background image

        mouse = pygame.mouse.get_pos()  # Mouse

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # If user clicks the close button:
                running = False  # Exit game

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # If left mouse button click:
                left_mouse_button = True  # Set left mouse button click to True

        # Blits buttons
        load_map_button.update(left_mouse_button)
        new_map_button.update(left_mouse_button)
        settings_button.update(left_mouse_button)
        exit_button.update(left_mouse_button)

        if load_map_button.clicked:  # If user clicks on load_map_button:
            tile_map, map_file_path, error, state, layer_dict = load_map(layer_dictionary=layer_dict)  # Load map

        # Creates new map
        elif new_map_button.clicked:  # If user clicks new_map_button:
            try:
                # Creates a file dialog to create a json map file
                tile_map = asksaveasfile(initialdir=settings["maps_path"], defaultextension=".json", filetypes=[("jpeg files", "*.json")])
                map_file_path = tile_map.name  # Map file path
                file = open(tile_map.name, 'w')  # Map file that was created
                file.write('{"all_layers": ["0"], "mobs": {}, "map": {}}')  # Writes stuff to make it readable by game
                file.close()  # Closes file
                file = open(tile_map.name, "r")  # Opens file again
                tile_map = json.load(file)  # Loads map
                file.close()  # Closes file
                for i in tile_map["all_layers"]:  # Loops through every layer in map:
                    layer_dict[i] = pygame.Surface(WINDOW_SIZE)  # And creates a surface for each one, used for blitting the entire screen with layers
                    layer_dict[i].set_colorkey(bg_color)  # Sets colorkey to black

                state = "editor"  # Sets game state to "editor"
            except AttributeError:  # If create_map fails:
                error = "Failed to create map"  # Error that will be displayed in menu
        elif settings_button.clicked:
            state = "settings"
            last_state = "menu"
        elif exit_button.clicked:  # If exit_button was clicked:
            running = False  # Closes game
        if error:  # If there's an error:
            warning_text.render(error, screen, (screen.get_width() / 2 - warning_text.width(error)[-1] / 2, 182))  # Display error
        if state == "editor":  # If game state is editor:
            update = True  # Draw entire screen
        display.blit(screen, (0, 0))  # Displays screen

    # settings --------------------------------------------------------------------------------------------------------------------------------------------------------

    elif state == "settings":

        left_mouse_button = False  # Resets left mouse button click
        screen.fill((70, 135, 143))  # Blits background image
        # Displays "SETTINGS" text at top of screen
        jumbo_purple_font.render("SETTINGS", screen, (screen.get_width() / 2 - jumbo_purple_font.width("SETTINGS")[-1] / 2, 27))
        mouse = pygame.mouse.get_pos()  # Mouse

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # If user clicks the close button:
                running = False  # Exit game

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # If left mouse button click:
                left_mouse_button = True  # Set left mouse button click to True

        # Button updates
        back_button.update(left_mouse_button)  # Updates back button
        tiles_path_button.update(left_mouse_button)  # Updates tiles_path button
        spritesheets_path_button.update(left_mouse_button)  # Updates spritesheets_path button
        maps_path_button.update(left_mouse_button)  # Updates map_folder_path button

        # Button logic
        if back_button.clicked:  # If back_button is clicked:
            state = last_state  # Sets state to menu
            update = True

        if tiles_path_button.clicked:

            p = askdirectory()  # Opens a file dialog for user to choose a directory
            if not p == "":  # If user chose a valid directory:
                settings["tiles_path"] = p  # Saves directory to settings
                file = open('data/settings.json', 'w')  # Opens settings file
                json.dump(settings, file, indent=0)  # Writes settings to settings file
                file.close()  # Closes file

                tile_index = {"null": null_img}  # Erases all images from tile_index
                rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}  # Erases all rect images used for collisions
                ui_images = {}  # Erases all sidebar images

                # Reloads all images with new path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict,
                                                                           tile_index)  # Loads all images from spritesheets path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

        if spritesheets_path_button.clicked:

            p = askdirectory()  # Opens a file dialog for user to choose a directory
            if not p == "":  # If user chose a valid directory:
                settings["spritesheets_path"] = p  # Saves directory to settings
                file = open('data/settings.json', 'w')  # Opens settings file
                json.dump(settings, file, indent=0)  # Writes settings to settings file
                file.close()  # Closes file

                tile_index = {"null": null_img}  # Erases all images from tile_index
                rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}  # Erases all rect images used for collisions
                ui_images = {}  # Erases all sidebar images

                # Reloads all images with new path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict,
                                                                           tile_index)  # Loads all images from spritesheets path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

        if maps_path_button.clicked:

            p = askdirectory()  # Opens a file dialog for user to choose a directory
            if not p == "":  # If user chose a valid directory:
                settings["maps_path"] = p  # Saves directory to settings
                file = open('data/settings.json', 'w')  # Opens settings file
                json.dump(settings, file, indent=0)  # Writes settings to settings file
                file.close()  # Closes file

        display.blit(screen, (0, 0))  # Blits screen

    # Editor -----------------------------------------------------------------------------------------------------------------------------------------------------------

    elif state == "editor":
        mouse = pygame.mouse.get_pos()  # Position of mouse
        left_mouse_button = False  # Resets left mouse button click

        for event in pygame.event.get():  # Events

            # Exits game
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:  # If player clicks x or presses esc:
                save_map()  # Save map
                running = False  # Close game

            if event.type == pygame.KEYDOWN:  # Pygame key down event
                if event.key == pygame.K_u:  # If player presses the "u" key:
                    update = True  # Fully draws every tile on screen

                # Resets scroll
                if event.key == pygame.K_SPACE:  # If player presses space bar:
                    scroll = [0, 0]  # Resets scroll (the position of player view)
                    update = True  # Fully draws every tile on screen

                # Moves screen to the left
                if event.key == pygame.K_LEFT:  # If player presses left arrow key:
                    old_scroll = scroll.copy()  # Creates a copy of scroll
                    old_mouse_rect = mouse_rect.copy()  # Creates copy of mouse_rect
                    scroll[0] -= 2  # Moves screen two pixels the left
                    screen_copy.blit(screen, (0, 0))  # Blits the screen onto a separate surface # Tanks fps from 600 to 300
                    screen.fill(bg_color)  # Fills screen with background color
                    screen.blit(screen_copy, (2, 0))  # Blits screen copy onto screen with two pixels of offset
                    pixels_scrolled[0] += -2  # Used to blit tiles on the edges of screen

                # Moves screen to the right
                elif event.key == pygame.K_RIGHT:  # If player presses right arrow key:
                    old_scroll = scroll.copy()  # Creates a copy of scroll
                    old_mouse_rect = mouse_rect.copy()  # Creates copy of mouse_rect
                    scroll[0] -= -2  # Moves screen two pixels the right
                    screen_copy.blit(screen, (0, 0))  # Blits the screen onto a separate surface # Tanks fps from 600 to 300
                    screen.fill(bg_color)  # Fills screen with background color
                    screen.blit(screen_copy, (-2, 0))  # Blits screen copy onto screen with two pixels of offset
                    pixels_scrolled[0] += 2  # Used to blit tiles on the edges of screen

                # Moves screen up
                if event.key == pygame.K_UP:  # If player presses up arrow key:
                    old_scroll = scroll.copy()  # Creates a copy of scroll
                    old_mouse_rect = mouse_rect.copy()  # Creates copy of mouse_rect
                    scroll[1] -= 2  # Moves screen two pixels up
                    screen_copy.blit(screen, (0, 0))  # Blits the screen onto a separate surface # Tanks fps from 600 to 300
                    screen.fill(bg_color)  # Fills screen with background color
                    screen.blit(screen_copy, (0, 2))  # Blits screen copy onto screen with two pixels of offset
                    pixels_scrolled[1] += -2  # Used to blit tiles on the edges of screen

                # Moves screen down
                elif event.key == pygame.K_DOWN:  # If player presses down arrow key:
                    old_scroll = scroll.copy()  # Creates a copy of scroll
                    old_mouse_rect = mouse_rect.copy()  # Creates copy of mouse_rect
                    scroll[1] -= -2  # Moves screen two pixels down
                    screen_copy.blit(screen, (0, 0))  # Blits the screen onto a separate surface # Tanks fps from 600 to 300
                    screen.fill(bg_color)  # Fills screen with background color
                    screen.blit(screen_copy, (0, -2))  # Blits screen copy onto screen with two pixels of offset
                    pixels_scrolled[1] += 2  # Used to blit tiles on the edges of screen

                elif event.key == pygame.K_i:  # If player presses "i" key:
                    screen.fill(bg_color)  # Fills the screen with background color

            if event.type == pygame.MOUSEBUTTONDOWN:  # Mouse button down event

                mouse_rect.x, mouse_rect.y = mouse[0], mouse[1]  # Resets mouse_rects pos on click

                if event.button == 1:  # If left mouse button click
                    left_mouse_button = True  # Left mouse button click set to True

                # Tile selection
                for key in rect_image_dict[tab].keys():  # Loops through tiles on sidebar
                    if rect_image_dict[tab][key].collidepoint(mouse):  # If mouse is over tile and mouse left click:
                        selection = key  # Sets selection to clicked tile

                # Position of tile player is mousing over
                tile_position = [round(((mouse[0] - offset[0]) + round(scroll[0]))), round(((mouse[1] - offset[1]) + round(scroll[1])))]

                # By default, it zooms zoom to the center of the screen, adding zoom_mouse_offset zooms to the mouse cursor
                zoom_mouse_offset = [mouse[0], mouse[1]]
                if zoom_mouse_offset[0] > screen.get_width() / 2:
                    zoom_mouse_offset[0] = zoom_mouse_offset[0] - (screen.get_width() / 2)
                elif zoom_mouse_offset[0] < screen.get_width() / 2:
                    zoom_mouse_offset[0] = -((screen.get_width() / 2) - zoom_mouse_offset[0])

                if zoom_mouse_offset[1] > screen.get_height() / 2:
                    zoom_mouse_offset[1] = zoom_mouse_offset[1] - (screen.get_height() / 2)
                elif zoom_mouse_offset[1] < screen.get_height() / 2:
                    zoom_mouse_offset[1] = -((screen.get_height() / 2) - zoom_mouse_offset[1])

                # Zoom
                if event.button == 4:  # If mouse scroll up

                    # If mouse isn't colliding with sidebar:
                    if mouse[0] > sidebar_img.get_width():  # if mouse[0] > 383 and mouse_rect.x < 1856 and mouse_rect.y > 96 and mouse_rect.y < 1024:
                        if zoom < 4:  # If zoom is less than max zoom:
                            zoom += 2  # Zooms in
                            # Scales tiles and blits them with offset to give illusion of being zoomed in/out
                            if zoom > 0:  # If zoom is zoomed in:
                                tile_size = 32 * zoom  # Multiplies tile_size by zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "*")  # Scales tiles
                                # Scales player_img
                                player_img = pygame.transform.scale(orig_player_img, (orig_player_img.get_width() * zoom, orig_player_img.get_height() * zoom))
                                # Modifies zoom so that screen zooms in around mouse
                                scroll = [((tile_position[0] * 2) - 928 - zoom_mouse_offset[0]),
                                          ((tile_position[1] * 2) - 496 - zoom_mouse_offset[1])]
                                if zoom > 2:
                                    scroll = [(tile_position[0] * 2) - 896 - zoom_mouse_offset[0],
                                              (tile_position[1] * 2) - 464 - zoom_mouse_offset[1]]
                            elif zoom < 0:  # If zoom is zoomed out
                                tile_size = 32 / abs(zoom)  # Divides tile_size by zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "/")  # Scales tiles
                                # Scales player_img
                                player_img = pygame.transform.scale(orig_player_img, (round(orig_player_img.get_width() / abs(zoom)), round(orig_player_img.get_height()
                                                                                                                                            / abs(zoom))))
                                # Modifies zoom so that screen zooms in around mouse
                                scroll = [((tile_position[0] * 2) - 952) - zoom_mouse_offset[0],
                                          ((tile_position[1] * 2) - 520) - zoom_mouse_offset[1]]
                            else:  # If zoom is neither
                                tile_size = 32  # Sets tile size to default
                                tile_index, ui_images = scale_tiles(tile_index, ui_images)  # Sets tiles to default scale
                                player_img = orig_player_img.copy()  # Sets player_img to default scale
                                # Modifies zoom so that screen zooms in around mouse
                                scroll = [((tile_position[0] * 2) - 944 - zoom_mouse_offset[0]),
                                          ((tile_position[1] * 2) - 512 - zoom_mouse_offset[1])]
                            update = True  # Flag to redraw every tile on screen

                # Zoom
                elif event.button == 5:  # If mouse scroll down
                    # If mouse isn't colliding with sidebar:
                    if mouse[0] > sidebar_img.get_width():  # if mouse[0] > 383 and mouse_rect.x < 1856 and mouse_rect.y > 96 and mouse_rect.y < 1024:
                        if zoom > -4:  # If zoom is greater than max zoom:
                            zoom -= 2  # Zooms out
                            # Scales tiles and blits them with offset to give illusion of being zoomed in/out
                            if zoom > 0:  # If zoom is zoomed in:
                                tile_size = 32 * zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "*")  # Scales tiles
                                # Scales player_img
                                player_img = pygame.transform.scale(orig_player_img, (orig_player_img.get_width() * zoom, orig_player_img.get_height() * zoom))
                                # Modifies zoom so that screen zooms out around mouse
                                scroll = [((tile_position[0] / 2) - 928 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 496 - zoom_mouse_offset[1])]

                            elif zoom < 0:  # If zoom is zoomed out
                                tile_size = 32 / abs(zoom)  # Divides tile_size by zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "/")  # Scales tiles
                                # Scales player_img
                                player_img = pygame.transform.scale(orig_player_img, (round(orig_player_img.get_width() / abs(zoom)), round(orig_player_img.get_height()
                                                                                                                                            / abs(zoom))))
                                # Modifies zoom so that screen zooms out around mouse
                                scroll = [((tile_position[0] / 2) - 952 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 520 - zoom_mouse_offset[1])]
                                if zoom < -2:
                                    scroll = [((tile_position[0] / 2) - 956 - zoom_mouse_offset[0]),
                                              ((tile_position[1] / 2) - 524 - zoom_mouse_offset[1])]
                            else:  # If zoom is neither
                                tile_size = 32  # Sets tile size to default
                                tile_index, ui_images = scale_tiles(tile_index, ui_images)  # Sets tiles to default scale
                                player_img = orig_player_img.copy()  # Sets player_img to default scale
                                # Modifies zoom so that screen zooms out around mouse
                                scroll = [((tile_position[0] / 2) - 944 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 512 - zoom_mouse_offset[1])]
                            update = True  # Flag to redraw every tile on screen

            # On mouse button up the screen updates all tiles
            if event.type == pygame.MOUSEBUTTONUP:
                update = True

            # Scroll
            if pygame.mouse.get_pressed(3)[1]:  # If middle mouse button pressed:
                if not old_pressed == pygame.mouse.get_pressed(3)[1]:  # If player just started pressing middle mouse button:
                    mouse_rect.x, mouse_rect.y = mouse[0], mouse[1]  # Reset mouse_rect position
                old_scroll = scroll.copy()  # Creates copy of scroll
                old_mouse_rect = mouse_rect.copy()  # Creates copy of mouse_rect
                mouse_rect.x, mouse_rect.y, = mouse[0], mouse[1]  # Sets mouse_rect position to mouse
                scroll[0] -= (mouse_rect.x - old_mouse_rect.x)  # Updates scroll
                scroll[1] -= (mouse_rect.y - old_mouse_rect.y)  # Updates scroll
                screen_copy.blit(screen, (0, 0))  # Blits the screen onto a separate surface # Tanks fps from 600 to 300
                screen.fill(bg_color)  # Fills screen with background color
                screen.blit(screen_copy, (mouse_rect.x - old_mouse_rect.x, mouse_rect.y - old_mouse_rect.y))  # Blits screen copy onto screen with offset
                pixels_scrolled[0] += scroll[0] - old_scroll[0]  # Updates pixels scrolled, used for blitting tiles on the edges of screen
                pixels_scrolled[1] += scroll[1] - old_scroll[1]  # Updates pixels scrolled, used for blitting tiles on the edges of screen

            old_pressed = pygame.mouse.get_pressed(3)[1]

            # Offset used for blitting tiles in a grid
            if zoom < 0:
                offset = [16 / abs(zoom), 16 / abs(zoom)]
            elif zoom > 0:
                offset = [16 * zoom, 16 * zoom]
            else:
                offset = [16, 16]

            # Blits tiles on the edges of screen for scroll
            if not pixels_scrolled[0] == 0 or not pixels_scrolled[1] == 0:  # If the screen has scrolled this frame
                # Decides how many tiles should be blitted:
                if zoom > 0:  # If zoomed in:
                    # Then blit less tiles
                    tile_range[0] = round(23 / (zoom / 2))
                    tile_range[1] = round(38 / (zoom / 2))
                elif zoom < 0:  # If zoomed out:
                    # Then blit more tiles
                    tile_range[0] = round(38 * abs(zoom))
                    tile_range[1] = round(64 * abs(zoom))
                else:
                    # Blits normal amount of tiles
                    tile_range[0] = 38
                    tile_range[1] = 64

                if not pixels_scrolled[0] == 0:  # If player moved the view along the x-axis
                    last_tile_pos = ""  # Allows it to blit at pixels_scrolled 0
                    # Blits tiles on the sides of screen when player moves view around
                    while True:  # Infinite loop
                        if pixels_scrolled[0] > 0 or last_tile_pos == "right":  # If player moved view to the right:
                            # Right of the screen - pixels_scrolled
                            tile_pos[0] = round(((((display.get_width() - 0) - pixels_scrolled[0]) - offset[0]) + round(scroll[0])) / tile_size)
                            last_tile_pos = "right"  # If pixels scrolled == 0 then tile_pos won't update, so we use this
                        elif pixels_scrolled[0] < 0 or last_tile_pos == "left":  # If player moved view to the left:
                            # Left of the screen - pixels_scrolled
                            tile_pos[0] = round((((0 - offset[0]) - pixels_scrolled[0]) + round(scroll[0])) / tile_size)
                            last_tile_pos = "left"  # If pixels scrolled == 0 then tile_pos won't update, so we use this

                        # Blits tiles on the right/left of screen from top to bottom by looping
                        for y in range(tile_range[0]):  # Loops through tile range
                            tile_pos[1] = int((y - 3) + round(scroll[1] / tile_size))  # y
                            chunk_pos = str(int(tile_pos[0] / 8)) + ";" + str(int(tile_pos[1] / 8))  # Position of chunk

                            # Blits tiles
                            if chunk_pos in tile_map["map"]:  # If chunk in map
                                tile = str(int(tile_pos[0])) + ";" + str(int((y - 3) + round(scroll[1] / tile_size)))  # Tile
                                if tile in tile_map["map"][chunk_pos]:  # If tile in chunk
                                    pos = tile.split(";")  # Position of tile
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])  # Turns pos from string to int
                                    # Loops through all layers inside tile and blits them all
                                    for layer in tile_map["map"][chunk_pos][tile]:  # Loops through layers inside tile:
                                        if str(tile_map["map"][chunk_pos][tile][layer][0]) in tile_index:  # If tile image in tile_index:
                                            screen.blit((tile_index[str(tile_map["map"][chunk_pos][tile][layer][0])]),  # Blit tile
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                        elif str(tile_map["map"][chunk_pos][tile][layer][0]) not in tile_index:  # Else if image doesn't exist:
                                            # Blits null image
                                            screen.blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                            # Blits tiles
                            if chunk_pos in tile_map["mobs"]:  # If chunk in mobs
                                tile = str(int(tile_pos[0])) + ";" + str(int((y - 3) + round(scroll[1] / tile_size)))  # Tile
                                if tile in tile_map["mobs"][chunk_pos]:  # If tile in chunk
                                    pos = tile.split(";")  # Position of tile
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])  # Turns pos from string to int
                                    # Loops through all layers inside tile and blits them all
                                    for layer in tile_map["mobs"][chunk_pos][tile]:  # Loops through layers inside tile:
                                        if str(tile_map["mobs"][chunk_pos][tile][layer][0]) in tile_index:  # If tile image in tile_index:
                                            screen.blit((tile_index[str(tile_map["mobs"][chunk_pos][tile][layer][0])]),  # Blit tile
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                        elif str(tile_map["mobs"][chunk_pos][tile][layer][0]) not in tile_index:  # Else if image doesn't exist:
                                            # Blits null image
                                            screen.blit((tile_index["null"]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                        # Removes tile_size from pixels_scrolled[0] and blits tiles until it's 0 then it breaks out of the loop
                        if pixels_scrolled[0] == 0:
                            pixels_scrolled[0] = 0
                            break
                        # Right
                        elif pixels_scrolled[0] > 0 - tile_size:
                            pixels_scrolled[0] -= tile_size - 1
                            if pixels_scrolled[0] < 0:
                                pixels_scrolled[0] = 0
                        # Left
                        elif pixels_scrolled[0] < 0 + tile_size:
                            pixels_scrolled[0] += tile_size - 1
                            if pixels_scrolled[0] > 0:
                                pixels_scrolled[0] = 0

                if not pixels_scrolled[1] == 0:  # If player moved the view along the y-axis
                    # Blits tiles on the sides of screen when player moves screen around
                    last_tile_pos = ""  # For if pixels_scrolled is 0
                    while True:  # Infinite loop
                        if pixels_scrolled[1] > 0 or last_tile_pos == "bottom":  # If player moved view down:
                            # Bottom of the screen - pixels_scrolled
                            tile_pos[1] = round(((((display.get_height() - 1) - pixels_scrolled[1]) - offset[1]) + round(scroll[1])) / tile_size)
                            last_tile_pos = "bottom"  # If pixels scrolled == 0 then tile_pos won't update, so we use this
                        elif pixels_scrolled[1] < 0 or last_tile_pos == "top":  # If player moved view up:
                            # Top of the screen - pixels_scrolled
                            tile_pos[1] = round((((0 - offset[1]) + round(scroll[1])) - pixels_scrolled[1]) / tile_size)
                            last_tile_pos = "top"  # If pixels scrolled == 0 then tile_pos won't update, so we use this

                        # Blits tiles on the top/bottom of screen from top to bottom by looping
                        for x in range(tile_range[1]):  # Loops through tile range
                            tile_pos[0] = int((x - 3) + round(scroll[0] / tile_size))  # x
                            chunk_pos = str(int(tile_pos[0] / 8)) + ";" + str(int(tile_pos[1] / 8))  # Position of chunk

                            # Blits tiles
                            if chunk_pos in tile_map["map"]:  # If chunk in map
                                tile = str(int((x - 3) + round(scroll[0] / tile_size))) + ";" + str(int(tile_pos[1]))  # Tile
                                if tile in tile_map["map"][chunk_pos]:  # If tile in chunk
                                    pos = tile.split(";")  # Position of tile
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])  # Turns pos from string to int
                                    # Loops through all layers inside tile and blits them all
                                    for layer in tile_map["map"][chunk_pos][tile]:  # Loops through layers inside tile:
                                        if str(tile_map["map"][chunk_pos][tile][layer][0]) in tile_index:  # If tile image in tile_index:
                                            screen.blit((tile_index[str(tile_map["map"][chunk_pos][tile][layer][0])]),  # Blit tile
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                        elif str(tile_map["map"][chunk_pos][tile][layer][0]) not in tile_index:  # Else if image doesn't exist:
                                            # Blits null image
                                            screen.blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                            # Blits mobs
                            if chunk_pos in tile_map["mobs"]:  # If chunk in mobs
                                tile = str(int((x - 3) + round(scroll[0] / tile_size))) + ";" + str(int(tile_pos[1]))  # Tile
                                if tile in tile_map["mobs"][chunk_pos]:  # If tile in chunk
                                    pos = tile.split(";")  # Position of tile
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])  # Turns pos from string to int
                                    # Loops through all layers inside tile and blits them all
                                    for layer in tile_map["mobs"][chunk_pos][tile]:  # Loops through layers inside tile:
                                        if str(tile_map["mobs"][chunk_pos][tile][layer][0]) in tile_index:  # If tile image in tile_index:
                                            screen.blit((tile_index[str(tile_map["mobs"][chunk_pos][tile][layer][0])]),  # Blit tile
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                        elif str(tile_map["mobs"][chunk_pos][tile][layer][0]) not in tile_index:  # Else if image doesn't exist:
                                            # Blits null image
                                            screen.blit((tile_index["null"]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                        # Removes tile_size from pixels_scrolled[1] and blits tiles until it's 0 then it breaks out of the loop
                        if pixels_scrolled[1] == 0:
                            break
                        # Bottom
                        elif pixels_scrolled[1] > 0 - tile_size and not pixels_scrolled[1] == 0:
                            pixels_scrolled[1] -= tile_size - 1
                            if pixels_scrolled[1] < 0:
                                pixels_scrolled[1] = 0
                        # Top
                        elif pixels_scrolled[1] < 0 + tile_size and not pixels_scrolled[1] == 0:
                            pixels_scrolled[1] += tile_size - 1
                            if pixels_scrolled[1] > 0:
                                pixels_scrolled[1] = 10

        # Draw tiles
        if pygame.mouse.get_pressed(3)[0]:  # If left click:
            if selection is not None:  # If player has a tile selected:
                # Draws tile
                calculate_line(mouse_rect.x, mouse_rect.y, mouse[0], mouse[1], draw_tile, zoom, current_layer, offset)

        # Erases tiles
        elif pygame.mouse.get_pressed(3)[2]:  # If right click:
            # Erases tile
            calculate_line(mouse_rect.x, mouse_rect.y, mouse[0], mouse[1], erase_tile, zoom, current_layer, offset)

        # Blitting -----------------------------------------------------------------------------------------------------------------------------------------------------
        if update:  # If update flag is True, then redraw every tile on screen
            screen.fill(bg_color)  # Erases screen
            for i in layer_dict.keys():  # Loops through all layer surfaces and erases them all
                layer_dict[i].fill(bg_color)

            layer_dict["0"].blit(player_img, (int(16 * tile_size) - scroll[0], int(15 * tile_size) - scroll[1]))  # Blits player image on layer "0"
            # Decides how many chunks will be blitted
            if zoom < 0:
                tile_range = [round(5 * abs(zoom)), 9 * abs(zoom)]
            else:
                tile_range = [7, 9]

            # Blits tiles in chunks
            for y in range(tile_range[0]):
                for x in range(tile_range[1]):
                    target_x = x - 1 + int(round(scroll[0] / (8 * tile_size)))  # First pos
                    target_y = y - 1 + int(round(scroll[1] / (8 * tile_size)))  # Second pos
                    target_chunk = str(target_x) + ';' + str(target_y)  # Chunk that will be blitted

                    # Blits tiles
                    if target_chunk in tile_map["map"]:  # If chunk exists in map:
                        for tile in tile_map["map"][target_chunk]:  # Loops through tiles in chunk
                            for layer in tile_map["map"][target_chunk][tile]:  # Loops through layers in tile
                                if layer not in layer_dict:  # If a layer surface doesn't exist:
                                    # Create layer surface
                                    layer_dict[layer] = pygame.Surface(WINDOW_SIZE)  # Creates surface
                                    layer_dict[layer].set_colorkey(bg_color)  # Sets colorkey to background color
                                    layer_dict[layer].fill(bg_color)  # Fills with background color to make it transparent
                                    # Sorts the layer surfaces in layer_dict, sorts them like numbers: (-10, -4, -1, 0, 2, 6, 9)
                                    layer_dict = {key: val for key, val in sorted(layer_dict.items(), key=lambda ele: int(ele[0]))}

                                pos = tile.split(";")  # Position of tile that will be blitted
                                pos[0], pos[1], = int(pos[0]), int(pos[1])  # Converts tile position from string to int
                                if str(tile_map["map"][target_chunk][tile][layer][0]) in tile_index:  # If the tile image exists:
                                    layer_dict[layer].blit((tile_index[str(tile_map["map"][target_chunk][tile][layer][0])]),  # Then blit tile image at pos
                                                           (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                elif str(tile_map["map"][target_chunk][tile][layer][0]) not in tile_index:  # Else if tile image doesn't exist:
                                    # Blit null image
                                    layer_dict[layer].blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                    # Blits mobs
                    if target_chunk in tile_map["mobs"]:  # If chunk exists in map:
                        for tile in tile_map["mobs"][target_chunk]:  # Loops through tiles in chunk
                            for layer in tile_map["mobs"][target_chunk][tile]:  # Loops through layers in tile
                                if layer not in layer_dict:  # If a layer surface doesn't exist:
                                    # Create layer surface
                                    layer_dict[layer] = pygame.Surface(WINDOW_SIZE)  # Creates surface
                                    layer_dict[layer].set_colorkey(bg_color)  # Sets colorkey to background color
                                    layer_dict[layer].fill(bg_color)  # Fills with background color to make it transparent
                                    # Sorts the layer surfaces in layer_dict, sorts them like numbers: (-10, -4, -1, 0, 2, 6, 9)
                                    layer_dict = {key: val for key, val in sorted(layer_dict.items(), key=lambda ele: int(ele[0]))}

                                pos = tile.split(";")  # Position of tile that will be blitted
                                pos[0], pos[1], = int(pos[0]), int(pos[1])  # Converts tile position from string to int
                                if str(tile_map["mobs"][target_chunk][tile][layer][0]) in tile_index:  # If the tile image exists:
                                    layer_dict[layer].blit((tile_index[str(tile_map["mobs"][target_chunk][tile][layer][0])]),  # Then blit tile image at pos
                                                           (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))
                                elif str(tile_map["mobs"][target_chunk][tile][layer][0]) not in tile_index:  # Else if tile image doesn't exist:
                                    # Blit null image
                                    layer_dict[layer].blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

            for i in layer_dict.keys():  # Loops through layer surfaces in layer_dict:
                screen.blit(layer_dict[i], (0, 0))  # And blits them on screen
            update = False  # Sets update flag to False

        display.blit(screen, (0, 0))  # Blits screen onto surface

        # Blits mouse position text
        tile_position = [round(((mouse[0] - offset[0]) + round(scroll[0])) / tile_size), round(((mouse[1] - offset[1]) + round(scroll[1])) / tile_size)]
        chunk_pos = str(int((tile_position[0]) / 8)) + ":" + str(int((tile_position[1]) / 8))  # Blits chunk position text
        chunk_pos = chunk_pos.replace(":", ";")  # Makes chunk_pos readable by the mouse tile code

        # Blits mouse tile
        if not pygame.mouse.get_pressed(3)[2]:  # If player is not holding down left click:
            # and mouse[0] < 1856 and mouse[1] > 96 and mouse[1] < 1024
            if mouse[0] > sidebar_img.get_width():  # If mouse not over sidebar:
                mouse_scroll = [scroll[0] % tile_size, scroll[1] % tile_size]  # Mouse scroll
                if selection in tile_index:  # If selected tile exists:
                    blitted_selection = tile_index[selection].copy()  # Creates a copy of the image from selected tile
                    tinted_selection = pygame.Surface((blitted_selection.get_width(), blitted_selection.get_height()))  # Creates a surface the size of selected image
                    tinted_selection.fill((0, 0, 0))  # Fills with black
                    tinted_selection.set_alpha(30)  # Sets alpha to 30
                    blitted_selection.set_alpha(180)  # Sets alpha for selected tile image copy
                    pos = str(tile_position[0]) + ";" + str(tile_position[1])  # Position of tile

                    # If player is mousing over a tile with the same image as selection: then blit mouse tile without any transparency:
                    if chunk_pos in tile_map["map"]:  # If chunk exists in map:
                        if pos in tile_map["map"][chunk_pos]:  # If pos in chunk:
                            for layer in tile_map["map"][chunk_pos][pos]:  # Loops through layers in tile
                                if tile_map["map"][chunk_pos][pos][layer][0] == selection:  # If tile that player is mousing over is the same as selection:
                                    # Then blit mouse tile as fully opaque
                                    blitted_selection.set_alpha(255)  # Sets alpha to be fully opaque
                                    tinted_selection.set_alpha(0)  # Makes tinted_selection fully transparent
                                    break

                    blitted_selection.blit(tinted_selection, (0, 0))  # Tints blitted_selection slightly black and make it slightly transparent

                    mouse_tile_flag = True
                    if chunk_pos in tile_map["map"]:  # If chunk exists in map:
                        if pos in tile_map["map"][chunk_pos]:  # If tile pos exists in chunk:
                            for layer in tile_map["map"][chunk_pos][pos]:  # Loops through layers in tile
                                if layer > current_layer and mouse_tile_flag:  # If layer is bigger than current layer and mouse_tile_flag:
                                    # Blits mouse tile
                                    display.blit(blitted_selection, (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                                     round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))
                                    mouse_tile_flag = False
                                if tile_map["map"][chunk_pos][pos][layer][0] in tile_index:  # If tile image exists:
                                    display.blit((tile_index[tile_map["map"][chunk_pos][pos][layer][0]]),  # Blits other layers in tile
                                                 (int(tile_position[0] * tile_size) - scroll[0], int(tile_position[1] * tile_size) - scroll[1]))
                                else:
                                    # If tile images doesn't exist: blit null image
                                    display.blit((tile_index["null"]), (int(tile_position[0] * tile_size) - scroll[0], int(tile_position[1] * tile_size) - scroll[1]))

                    if mouse_tile_flag:  # If layer >= current_layer
                        display.blit(blitted_selection, (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                         round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))

                else:  # If selection doesn't exist:
                    if selection is not None:
                        # Blits null image
                        display.blit(tile_index["null"], (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                          round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))
        # display.blit(sidebar_img, (0, 0))  # Blits sidebar image
        chunk_pos = chunk_pos.replace(";", ":")  # Makes chunk_pos readable by the white_font.render
        # Renders chunk and tile positions
        white_font.render("Chunk: " + chunk_pos + "   Tile: " + str(tile_position[0]) + ":" + str(tile_position[1]), display, (420, 2))
        dark_purple_font.render("Layer: " + str(current_layer), display, (46, 197))  # Renders "layer" + current layer
        # Scales layer right arrow button's position based on how long the current layer text is
        right_arrow_button.position[0] = 47 + (dark_purple_font.width("Layer: " + str(current_layer))[0])
        display.blit(tiny_mouse_dot_img, mouse_rect)  # Blits little mouse dot

        # Displays sidebar images
        for key in rect_image_dict[tab].keys():  # Loops through sidebar image positions
            if key in ui_images:  # If position in ui_images:
                if not rect_image_dict[tab][key].collidepoint(mouse):  # If mouse isn't mousing over sidebar image rect:
                    display.blit(ui_images[key], rect_image_dict[tab][key])  # Blit sidebar image normally
                else:  # If mouse is over sidebar image:
                    # Blit sidebar image 5 pixels higher than normal
                    display.blit(ui_images[key], (rect_image_dict[tab][key].x, rect_image_dict[tab][key].y - 5))
            else:  # If image doesn't exist:
                display.blit(ui_images["null"], rect_image_dict[tab][key])  # Blit null image

        # BUTTONS ------------------------------------------------------------------------------------------------------------------------------------------------------

        # Loops through all editor buttons and updates them all
        for button in editor_button_list:
            button.update(left_mouse_button)

        # If player clicks "tiles" button set tab to "tiles"
        if tiles_button.clicked:
            tab = "tiles"

        # If player clicks "decorations" button set tab to "decorations"
        if decorations_button.clicked:
            tab = "decorations"

        # If player clicks "mobs" button set tab to "mobs"
        if mobs_button.clicked:
            tab = "mobs"

        if editor_load_map_button.clicked:  # If player clicks the "load map" button:
            save_map()  # Save current map
            # Load new map
            tile_map, map_file_path, error, _, layer_dict = load_map(tile_map, map_file_path, layer_dict)
            update = True  # Flag for redrawing every tile on screen

        # If player clicks "load image" button: load an image
        if editor_load_image_button.clicked:
            rect_image_dict, tile_index, ui_images = load_image(rect_image_dict, "//data/map editor/saved images/", tile_index, ui_images)

        # If player clicks "layer left arrow button": current_layer -= 1
        if left_arrow_button.clicked:
            current_layer = str(int(current_layer) - 1)

        # If player clicks "layer right arrow button": current_layer += 1
        if right_arrow_button.clicked:
            current_layer = str(int(current_layer) + 1)

        if editor_settings_button.clicked:
            state = "settings"
            last_state = "editor"

    clock.tick(1000)  # Sets max framerate to 1000
    pygame.display.update()  # Updates display
