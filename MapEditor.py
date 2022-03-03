import pygame
import os
from shutil import copyfile
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfile, askdirectory
import data.scripts.text as scripts_text
import json
import time

# Init
os.environ['SDL_VIDEO_WINDOW_POS'] = str(0) + "," + str(23)  # Sets pos of window to (0, 23)
Tk().withdraw()
pygame.init()
WINDOW_SIZE = (1920, 1056)
display = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED + pygame.RESIZABLE)
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

tile_index = {"null": null_img}
rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}  # Used for tabs inside of editor


def create_sidebar_image(rect_image_dict_, new_tile_index, image, name, gap):
    """Loops through images and creates positions for them to be blitted on the sidebar"""
    image_rect = image.get_rect()
    starting_pos = [15, 243]
    ending_pos = 1051

    if name[0:5] == "enemy":
        tab_ = "mobs"
    elif image_rect.width == 32 and image_rect.height == 32:
        tab_ = "tiles"
    else:
        tab_ = "decorations"

    if len(rect_image_dict_[tab_]) > 0:
        # If the y position is colliding with the bottom of sidebar, set y position to the top and starts a new row
        if list(rect_image_dict_[tab_].values())[-1].y + (list(rect_image_dict_[tab_].values())[-1].height * 2) + gap > ending_pos:
            image_rect.x, image_rect.y, = (list(rect_image_dict_[tab_].values())[-1].x + image_rect.width + gap), starting_pos[1]
        else:
            # Creates the position normally by putting it under whichever image was last
            image_rect.x, image_rect.y, = list(rect_image_dict_[tab_].values())[-1].x, (list(rect_image_dict_[tab_].values())[-1].y +
                                                                                        list(rect_image_dict_[tab_].values())[-1].height) + gap
    else:
        image_rect.x, image_rect.y, = tuple(starting_pos)

    for rect in rect_image_dict_[tab_].values():
        if image_rect.colliderect(rect):
            while image_rect.colliderect(rect):
                image_rect.y += 1
            image_rect.y += gap

    new_tile_index[name] = image

    if name in rect_image_dict_[tab_]:
        image_rect.x, image_rect.y, = rect_image_dict_[tab_][name].x, rect_image_dict_[tab_][name].y
        rect_image_dict_[tab_].pop(name)
        rect_image_dict_[tab_][name] = image_rect
    else:
        rect_image_dict_[tab_][name] = image_rect
    return rect_image_dict_, new_tile_index, image_rect


def clip(surf, x_, y_, x_size, y_size):
    """Clips image based on x and y"""
    handle_surf = surf.copy()
    clip_rect = pygame.Rect(x_, y_, x_size, y_size)
    handle_surf.set_clip(clip_rect)
    image = surf.subsurface(handle_surf.get_clip())
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

    for entry in os.scandir(path):  # Loops through all files in directory

        if hasattr(entry, 'path') and hasattr(entry, 'is_file') and hasattr(entry, 'name'):

            if (entry.path.endswith(".png") or entry.path.endswith(".jpg") or entry.path.endswith(".PNG") or entry.path.endswith(".JPG")) and entry.is_file():

                if path == settings["spritesheets_path"] + "/":
                    image = pygame.image.load(entry.path).convert()
                    image.set_colorkey(img_colorkey)
                    spritesheet, rect_image_dict_, new_tile_index, new_ui_images = load_spritesheet(path + entry.name, tile_index, rect_image_dict)

                else:
                    image = pygame.image.load(entry.path).convert()
                    image.set_colorkey(img_colorkey)
                    image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
                    name = os.path.splitext(entry.name)[0]
                    rect_image_dict_, new_tile_index, image_rect = create_sidebar_image(rect_image_dict_, new_tile_index, image, name, 5)
    new_ui_images = new_tile_index.copy()
    return rect_image_dict_, new_tile_index, new_ui_images


if not os.path.isfile("data/settings.json"):
    file = open('data/settings.json', 'w')
    settings = {"tiles_path": "data/images/tiles/", "spritesheets_path": "data/images/spritesheets/", "maps_path": "data/maps"}  # Settings
    json.dump(settings, file, indent=0)
    file.close()

else:
    file = open('data/settings.json', 'r')
    settings = json.load(file)
    file.close()

rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
# noinspection PyRedeclaration
rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict, tile_index)  # Loads all images from spritesheets path
# noinspection PyRedeclaration
rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

# Editor

tab = "tiles"
tile_map = {}
selection = None
tile_size = 32
mouse = pygame.mouse.get_pos()
mouse_rect = pygame.Rect(mouse, (1, 1))
scroll = [0, 0]
zoom = 0
update = False
map_file_path = ""
error = ""
old_pressed = pygame.mouse.get_pressed(3)[1]
pixels_scrolled = [0, 0]
screen_copy = screen.copy()
tile_pos = [0, 0]
tile_range = [34, 60]
offset = [16, 16]
left_mouse_button = False
clock = pygame.time.Clock()
current_layer = "0"
layer_dict = {}
undo_list = []
redo_list = []
current_time = time.time()
last_time = time.time()
holding_down = False
undo_redo_flag = False


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
        self.font1 = font1
        self.font2 = font2
        self.text = text
        self.surf = surf
        self.position = position
        self.num_x = num_x  # Increases or decreases the hitbox down along the x-axis
        self.clicked = False
        self.width = self.font1.width(self.text)
        self.height = self.font1.height(self.text)
        self.positions = {"top": self.position[1], "left": self.position[0], "bottom": self.position[1] + self.height, "right": self.position[0] + self.width}

    def update(self, _pressed):
        """Draws button and handles button function by setting clicked to True or False depending on if button was clicked or not."""
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
        self.surf1 = surf1
        self.surf2 = surf2
        self.position = position
        self.num_x = num_x
        self.clicked = False
        self.width = surf1.get_width()
        self.height = surf1.get_height()
        self.positions = {"top": self.position[1], "left": self.position[0], "bottom": self.position[1] + self.height, "right": self.position[0] + self.width}

    def update(self, _pressed):
        """Blits button to screen"""
        _mouse = pygame.mouse.get_pos()
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


left_arrow_button = ImageButton(left_arrow1, left_arrow2, (13, 190))
right_arrow_button = ImageButton(right_arrow1, right_arrow2, [80, 190])

load_map_button = TextButton(purple_menu_font1, purple_menu_font2, "Load Map", screen,
                             (screen.get_width() / 2 - purple_menu_font1.width("Load Map") / 2, 285), )
new_map_button = TextButton(purple_menu_font1, purple_menu_font2, "New Map", screen,
                            (screen.get_width() / 2 - purple_menu_font1.width("New Map") / 2, 415), )
settings_button = TextButton(purple_menu_font1, purple_menu_font2, "Settings", screen,
                             (screen.get_width() / 2 - purple_menu_font1.width("New Map") / 2, 545), )
exit_button = TextButton(purple_menu_font1, purple_menu_font2, "Exit", screen,
                         (screen.get_width() / 2 - purple_menu_font1.width("Exit") / 2, 675), )

tiles_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Tiles Path", screen,
                               (screen.get_width() / 2 - purple_menu_font1.width("Tiles Path") / 2, 285), )
spritesheets_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Spritesheets Path", screen,
                                      (screen.get_width() / 2 - purple_menu_font1.width("Spritesheets Path") / 2, 415), )
maps_path_button = TextButton(purple_menu_font1, purple_menu_font2, "Map Folder", screen,
                              (screen.get_width() / 2 - purple_menu_font1.width("Map Folder") / 2, 545), )
back_button = TextButton(purple_menu_font1, purple_menu_font2, "Back", screen,
                         (screen.get_width() / 2 - purple_menu_font1.width("Back") / 2, 675), )

tiles_button = TextButton(purple_editor_font1, purple_editor_font2, "TILES", display, (15, 17))
decorations_button = TextButton(purple_editor_font1, purple_editor_font2, "DECOR", display, (15, 52))
mobs_button = TextButton(purple_editor_font1, purple_editor_font2, "MOBS", display, (15, 87))
editor_load_map_button = TextButton(purple_editor_font1, purple_editor_font2, "LOAD MAP", display, (100, 17))
editor_load_image_button = TextButton(purple_editor_font1, purple_editor_font2, "LOAD IMAGE", display, (100, 52))
editor_settings_button = TextButton(purple_editor_font1, purple_editor_font2, "SETTINGS", display, (100, 87))

editor_button_list = (tiles_button, decorations_button, mobs_button, editor_load_map_button, editor_load_image_button, left_arrow_button, right_arrow_button,
                      editor_settings_button)


def load_image(rect_image_dict_, path, new_tile_index, ui_images_):
    """ Loads an image"""
    file_path = askopenfilename()
    basename = os.path.basename(file_path)
    name = basename.split(".")[0]

    if not file_path:
        return rect_image_dict_, new_tile_index, ui_images_

    copyfile(file_path, path + str(basename))
    gap = 5
    image = pygame.image.load(file_path).convert()
    image.set_colorkey(img_colorkey)
    image = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))
    image_rect = image.get_rect()

    if name[0:5] == "enemy":
        tab_ = "mobs"

    elif image_rect.width == 32 and image_rect.height == 32:
        tab_ = "tiles"

    else:
        tab_ = "decorations"

    if len(rect_image_dict_[tab_]) > 0:

        if list(rect_image_dict_[tab_].values())[-1].y + (list(rect_image_dict_[tab_].values())[-1].height * 2) + gap > 1011:
            image_rect.x, image_rect.y, = (list(rect_image_dict_[tab_].values())[-1].x + image_rect.width + gap), 323

        else:
            image_rect.x, image_rect.y, = list(rect_image_dict_[tab_].values())[-1].x, (list(rect_image_dict_[tab_].values())[-1].y +
                                                                                        list(rect_image_dict_[tab_].values())[-1].height) + gap
    else:
        image_rect.x, image_rect.y, = (39, 323)

    for rect in rect_image_dict_[tab_].values():
        if image_rect.colliderect(rect):

            while image_rect.colliderect(rect):
                image_rect.y += 1

            image_rect.y += gap

    new_tile_index[name] = image

    if name in rect_image_dict_[tab_]:
        image_rect.x, image_rect.y, = rect_image_dict_[tab_][name].x, rect_image_dict_[tab_][name].y
        rect_image_dict_[tab_].pop(name)
        rect_image_dict_[tab_][name] = image_rect

    else:
        rect_image_dict_[tab_][name] = image_rect

    new_ui_images = new_tile_index.copy()

    return rect_image_dict_, new_tile_index, new_ui_images


def save_map():
    """Saves map and adds layers to 'all_layers' by looping through 'map' and 'mobs'"""
    layer_list = []
    f = open(map_file_path, "w")

    for chunk_ in tile_map["map"].values():
        for tile_ in chunk_.values():
            for layer_ in tile_:

                if layer_ not in layer_list:
                    layer_list.append(layer_)

    for chunk_ in tile_map["mobs"].values():
        for tile_ in chunk_.values():
            for layer_ in tile_:

                if layer_ not in layer_list:
                    layer_list.append(layer_)

    if "0" not in layer_list:
        layer_list.append("0")

    tile_map["all_layers"] = layer_list
    tile_map["all_layers"].sort(key=int)
    json.dump(tile_map, f)
    f.close()


def load_map(current_map_file_path=None, current_map_file=None, layer_dictionary=None):
    """Loads map"""

    try:
        file_name = askopenfilename(initialdir=settings["maps_path"], filetypes=[("jpeg files", "*.json")], defaultextension="*.json")
        f = open(file_name, 'r')
        data = json.load(f)
        if file_name.endswith(".json") and isinstance(data, dict):

            f.close()
            layer_dict_ = {}

            for i_ in data["all_layers"]:
                layer_dict_[str(i_)] = pygame.Surface(WINDOW_SIZE)
                layer_dict_[str(i_)].set_colorkey(bg_color)

            return data, file_name, None, "editor", layer_dict_  # Returns stuff, except for the error, which is returned to None

        else:
            f.close()
            return tile_map, current_map_file, "Load failed!", "menu", layer_dictionary

    except FileNotFoundError:
        return current_map_file_path, current_map_file, "Load failed!", "menu", layer_dictionary


def calculate_line(x1, y1, x2, y2, fun, _zoom, layer_, offset_, selection_):
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
            fun(_zoom, layer_, offset_, selection_)  # Calls function to either draw or erase tiles

        numerator += shortest

        if not numerator < longest:
            numerator -= longest
            x1 += dx1
            y1 += dy1

        else:
            x1 += dx2
            y1 += dy2

        _i += 1


def draw_tile(_zoom, layer_, offset_, selection_, specific_tile=None):
    """Draws tiles and enemies"""

    if mouse_rect.x > sidebar_img.get_width() or specific_tile is not None:

        old_tile = None
        tile_pos_ = [round(((mouse_rect.x - offset_[0]) + round(scroll[0])) / tile_size),
                     round(((mouse_rect.y - offset_[1]) + round(scroll[1])) / tile_size)]
        chunk_pos_ = str(int((tile_pos_[0]) / 8)) + ";" + str(int((tile_pos_[1]) / 8))
        pos_ = str(tile_pos_[0]) + ";" + str(tile_pos_[1])

        if specific_tile is not None:
            pos_ = specific_tile.split(";")
            pos_[0], pos_[1] = int(pos_[0]), int(pos_[1])
            tile_pos_ = [pos_[0], pos_[1]]
            chunk_pos_ = str(int((tile_pos_[0]) / 8)) + ";" + str(int((tile_pos_[1]) / 8))
            pos_ = str(tile_pos_[0]) + ";" + str(tile_pos_[1])

        if selection_[:5] == "enemy":

            if chunk_pos_ not in tile_map["mobs"]:
                tile_map["mobs"][chunk_pos_] = {}

            if pos_ not in tile_map["mobs"][chunk_pos_]:
                tile_map["mobs"][chunk_pos_][pos_] = {}

            if pos_ in tile_map["mobs"][chunk_pos_] and layer_ in tile_map["mobs"][chunk_pos_][pos_]:
                old_tile = tile_map["mobs"][chunk_pos_][pos_][layer_][-1]

            tile_map["mobs"][chunk_pos_][pos_][layer_] = [selection_]

            if specific_tile is None and [pos_, layer_, "replace", selection, old_tile] not in undo_list and [pos_, layer_, "remove", selection_] not in undo_list:
                if not old_tile == selection_:
                    if old_tile is not None:
                        undo_list.append([pos_, layer_, "replace", selection, old_tile])
                    else:
                        undo_list.append([pos_, layer_, "remove", selection_])

            tile_map["mobs"][chunk_pos_][pos_] = {key_: val for key_, val in sorted(tile_map["mobs"][chunk_pos_][pos_].items(), key=lambda ele: int(ele[0]))}

            for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]),
                            (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

        else:

            if chunk_pos_ not in tile_map["map"]:
                tile_map["map"][chunk_pos_] = {}

            if pos_ not in tile_map["map"][chunk_pos_]:
                tile_map["map"][chunk_pos_][pos_] = {}

            if pos_ in tile_map["map"][chunk_pos_] and layer_ in tile_map["map"][chunk_pos_][pos_]:
                old_tile = tile_map["map"][chunk_pos_][pos_][layer_][-1]

            tile_map["map"][chunk_pos_][pos_][layer_] = [selection_]

            if specific_tile is None and [pos_, layer_, "replace", selection, old_tile] not in undo_list and [pos_, layer_, "remove", selection_] not in undo_list:
                if not old_tile == selection_:  # skips tiles that are the same as selection

                    if old_tile is not None:
                        undo_list.append([pos_, layer_, "replace", selection, old_tile])
                    else:
                        undo_list.append([pos_, layer_, "remove", selection_])

            tile_map["map"][chunk_pos_][pos_] = {key_: val for key_, val in sorted(tile_map["map"][chunk_pos_][pos_].items(), key=lambda ele: int(ele[0]))}

            for i_ in tile_map["map"][chunk_pos_][pos_]:

                if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                    screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]),
                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                else:
                    screen.blit((tile_index["null"]),
                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))


def erase_tile(_zoom, layer_, offset_, selection_=None, specific_tile=None):
    """Erases tiles and enemies"""

    if mouse_rect.x > sidebar_img.get_width() or specific_tile is not None:

        erased = False  # If tile wasn't a normal tile, erase an enemy

        tile_pos_ = [round(((mouse_rect.x - offset_[0]) + round(scroll[0])) / tile_size),
                     round(((mouse_rect.y - offset_[1]) + round(scroll[1])) / tile_size)]

        chunk_pos_ = str(int((tile_pos_[0]) / 8)) + ";" + str(int((tile_pos_[1]) / 8))
        pos_ = str(tile_pos_[0]) + ";" + str(tile_pos_[1])

        if specific_tile is not None:

            pos_ = specific_tile.split(";")
            pos_[0], pos_[1], = int(pos_[0]), int(pos_[1])
            tile_pos_ = [pos_[0], pos_[1]]
            chunk_pos_ = str(int((pos_[0]) / 8)) + ";" + str(int((pos_[1]) / 8))
            pos_ = specific_tile

        if chunk_pos_ in tile_map["map"]:
            if pos_ in tile_map["map"][chunk_pos_]:
                if layer_ in tile_map["map"][chunk_pos_][pos_]:
                    if tile_map["map"][chunk_pos_][pos_][layer_][0] in tile_index:

                        background_surface = tile_index[tile_map["map"][chunk_pos_][pos_][layer_][0]].copy()

                        if specific_tile is None and [pos_, layer_, "add", tile_map["map"][chunk_pos_][pos_][layer_][0]] not in undo_list:
                            undo_list.append([pos_, layer_, "add", tile_map["map"][chunk_pos_][pos_][layer_][0]])

                    else:
                        background_surface = tile_index["null"].copy()

                        if specific_tile is None and [pos_, layer_, "add", "null"] not in undo_list:
                            undo_list.append([pos_, layer_, "add", "null"])

                    background_surface.fill(bg_color)
                    screen.blit(background_surface, (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                    tile_map["map"][chunk_pos_][pos_].pop(layer_)
                    erased = True

                    for i_ in tile_map["map"][chunk_pos_][pos_]:

                        if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                            screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]), (int(tile_pos_[0] * tile_size) - scroll[0],
                                                                                                 int(tile_pos_[1] * tile_size) - scroll[1]))
                        else:
                            screen.blit((tile_index["null"]), (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                    if chunk_pos_ in tile_map["mobs"]:
                        if pos_ in tile_map["mobs"][chunk_pos_]:

                            for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                                screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]),
                                            (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                if chunk_pos_ in tile_map["map"]:
                    if pos_ in tile_map["map"][chunk_pos_]:

                        if not tile_map["map"][chunk_pos_][pos_]:
                            tile_map["map"][chunk_pos_].pop(pos_)

                    if not tile_map["map"][chunk_pos_]:
                        tile_map["map"].pop(chunk_pos_)

        if selection_:  # To remove pycharm "unused variable" error :p
            pass

        if chunk_pos_ in tile_map["mobs"] and erased is False:
            if pos_ in tile_map["mobs"][chunk_pos_]:
                if layer_ in tile_map["mobs"][chunk_pos_][pos_]:
                    if tile_map["mobs"][chunk_pos_][pos_][layer_][0] in tile_index:

                        background_surface = tile_index[tile_map["mobs"][chunk_pos_][pos_][layer_][0]].copy()

                        if specific_tile is None and [pos_, layer_, "add", tile_map["mobs"][chunk_pos_][pos_][layer_][0]] not in undo_list:
                            undo_list.append([pos_, layer_, "add", tile_map["mobs"][chunk_pos_][pos_][layer_][0]])

                    else:
                        background_surface = tile_index["null"].copy()

                        if specific_tile is None and [pos_, layer_, "add", "null"] not in undo_list:
                            undo_list.append([pos_, layer_, "add", "null"])

                    background_surface.fill(bg_color)
                    screen.blit(background_surface, (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))
                    tile_map["mobs"][chunk_pos_][pos_].pop(layer_)

                    for i_ in tile_map["mobs"][chunk_pos_][pos_]:
                        screen.blit((tile_index[tile_map["mobs"][chunk_pos_][pos_][i_][0]]), (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size)
                                                                                              - scroll[1]))
                    if chunk_pos_ in tile_map["map"]:
                        if pos_ in tile_map["map"][chunk_pos_]:
                            for i_ in tile_map["map"][chunk_pos_][pos_]:

                                if tile_map["map"][chunk_pos_][pos_][i_][0] in tile_index:
                                    screen.blit((tile_index[tile_map["map"][chunk_pos_][pos_][i_][0]]),
                                                (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                                else:
                                    screen.blit((tile_index["null"]), (int(tile_pos_[0] * tile_size) - scroll[0], int(tile_pos_[1] * tile_size) - scroll[1]))

                if chunk_pos_ in tile_map["mobs"]:
                    if pos_ in tile_map["mobs"][chunk_pos_]:

                        if not tile_map["mobs"][chunk_pos_][pos_]:
                            tile_map["mobs"][chunk_pos_].pop(pos_)

                    if not tile_map["mobs"][chunk_pos_]:
                        tile_map["mobs"].pop(chunk_pos_)


def scale_tiles(t_index, tile_index_copy, operator=""):
    """Scales every tile image, this is used for zooming the screen in and out, I simply scale every tile image and blit them with certain offset to give the illusion
    of zooming in/out. operator is a string, either '*' for multiplying tile images by zoom or '/' for dividing tile images by zoom"""

    if operator == "*":
        for key_ in tile_index_copy:
            img = tile_index_copy[key_]
            t_index[key_] = pygame.transform.scale(img, (img.get_width() * zoom, img.get_height() * zoom))

    elif operator == "/":
        for key_ in tile_index_copy:
            img = tile_index_copy[key_]
            t_index[key_] = pygame.transform.scale(img, (round(img.get_width() / abs(zoom)), round(img.get_height() / abs(zoom))))

    else:
        for key_ in tile_index_copy:
            img = tile_index_copy[key_]
            t_index[key_] = pygame.transform.scale(img, (img.get_width(), img.get_height()))

    return t_index, tile_index_copy


last_state = "menu"
state = "menu"
running = True
while running:

    # Menu -------------------------------------------------------------------------------------------------------------------------------------------------------------
    if state == "menu":

        left_mouse_button = False
        screen.blit(background_img, (0, 0))

        mouse = pygame.mouse.get_pos()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                left_mouse_button = True

        # Blits buttons
        load_map_button.update(left_mouse_button)
        new_map_button.update(left_mouse_button)
        settings_button.update(left_mouse_button)
        exit_button.update(left_mouse_button)

        if load_map_button.clicked:
            tile_map, map_file_path, error, state, layer_dict = load_map(layer_dictionary=layer_dict)  # Load map

        # Creates new map
        elif new_map_button.clicked:

            try:
                tile_map = asksaveasfile(initialdir=settings["maps_path"], defaultextension=".json", filetypes=[("jpeg files", "*.json")])
                map_file_path = tile_map.name
                file = open(tile_map.name, 'w')
                file.write('{"all_layers": ["0"], "mobs": {}, "map": {}}')
                file.close()
                file = open(tile_map.name, "r")
                tile_map = json.load(file)
                file.close()

                for i in tile_map["all_layers"]:
                    layer_dict[i] = pygame.Surface(WINDOW_SIZE)
                    layer_dict[i].set_colorkey(bg_color)

                state = "editor"

            except AttributeError:
                error = "Failed to create map"

        elif settings_button.clicked:
            state = "settings"
            last_state = "menu"

        elif exit_button.clicked:
            running = False

        if error:
            warning_text.render(error, screen, (screen.get_width() / 2 - warning_text.width(error) / 2, 182))

        if state == "editor":
            update = True

        display.blit(screen, (0, 0))  # Displays screen

    # settings --------------------------------------------------------------------------------------------------------------------------------------------------------

    elif state == "settings":

        left_mouse_button = False
        screen.fill((70, 135, 143))
        jumbo_purple_font.render("SETTINGS", screen, (screen.get_width() / 2 - jumbo_purple_font.width("SETTINGS") / 2, 27))
        mouse = pygame.mouse.get_pos()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                left_mouse_button = True

        # Button updates
        back_button.update(left_mouse_button)
        tiles_path_button.update(left_mouse_button)
        spritesheets_path_button.update(left_mouse_button)
        maps_path_button.update(left_mouse_button)

        # Button logic
        if back_button.clicked:
            state = last_state
            update = True

        if tiles_path_button.clicked:

            p = askdirectory()
            if not p == "":

                settings["tiles_path"] = p
                file = open('data/settings.json', 'w')
                json.dump(settings, file, indent=0)
                file.close()

                tile_index = {"null": null_img}
                rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}
                ui_images = {}

                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict,
                                                                           tile_index)  # Loads all images from spritesheets path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

        if spritesheets_path_button.clicked:

            p = askdirectory()
            if not p == "":

                settings["spritesheets_path"] = p
                file = open('data/settings.json', 'w')
                json.dump(settings, file, indent=0)
                file.close()

                tile_index = {"null": null_img}
                rect_image_dict = {"tiles": {}, "decorations": {}, "mobs": {}}
                ui_images = {}

                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["tiles_path"], rect_image_dict, tile_index)  # Loads all images from tiles path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images(settings["spritesheets_path"] + "/", rect_image_dict,
                                                                           tile_index)  # Loads all images from spritesheets path
                # noinspection PyRedeclaration
                rect_image_dict, tile_index, ui_images = load_saved_images("data/saved images/", rect_image_dict, tile_index)  # Loads images from "saved images" folder

        if maps_path_button.clicked:

            p = askdirectory()
            if not p == "":
                settings["maps_path"] = p
                file = open('data/settings.json', 'w')
                json.dump(settings, file, indent=0)
                file.close()

        display.blit(screen, (0, 0))

    # Editor -----------------------------------------------------------------------------------------------------------------------------------------------------------

    elif state == "editor":
        mouse = pygame.mouse.get_pos()
        left_mouse_button = False

        for event in pygame.event.get():

            # Exits game
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                save_map()
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_u:
                    update = True

                # Resets scroll
                if event.key == pygame.K_SPACE:
                    scroll = [0, 0]
                    update = True

                # Moves screen to the left
                if event.key == pygame.K_LEFT:
                    old_scroll = scroll.copy()
                    old_mouse_rect = mouse_rect.copy()
                    scroll[0] -= 2
                    screen_copy.blit(screen, (0, 0))
                    screen.fill(bg_color)
                    screen.blit(screen_copy, (2, 0))
                    pixels_scrolled[0] += -2

                # Moves screen to the right
                elif event.key == pygame.K_RIGHT:
                    old_scroll = scroll.copy()
                    old_mouse_rect = mouse_rect.copy()
                    scroll[0] -= -2
                    screen_copy.blit(screen, (0, 0))
                    screen.fill(bg_color)
                    screen.blit(screen_copy, (-2, 0))
                    pixels_scrolled[0] += 2

                # Moves screen up
                if event.key == pygame.K_UP:
                    old_scroll = scroll.copy()
                    old_mouse_rect = mouse_rect.copy()
                    scroll[1] -= 2
                    screen_copy.blit(screen, (0, 0))
                    screen.fill(bg_color)
                    screen.blit(screen_copy, (0, 2))
                    pixels_scrolled[1] += -2

                # Moves screen down
                elif event.key == pygame.K_DOWN:
                    old_scroll = scroll.copy()
                    old_mouse_rect = mouse_rect.copy()
                    scroll[1] -= -2
                    screen_copy.blit(screen, (0, 0))
                    screen.fill(bg_color)
                    screen.blit(screen_copy, (0, -2))
                    pixels_scrolled[1] += 2

                elif event.key == pygame.K_i:
                    screen.fill(bg_color)

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_rect.x, mouse_rect.y = mouse[0], mouse[1]

                if event.button == 1:
                    left_mouse_button = True

                    # Tile selection
                    for key in rect_image_dict[tab].keys():
                        if rect_image_dict[tab][key].collidepoint(mouse):
                            selection = key

                tile_position = [round(((mouse[0] - offset[0]) + round(scroll[0]))), round(((mouse[1] - offset[1]) + round(scroll[1])))]

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
                if event.button == 4:

                    if mouse[0] > sidebar_img.get_width():
                        if zoom < 4:
                            zoom += 2

                            if zoom > 0:
                                tile_size = 32 * zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "*")
                                player_img = pygame.transform.scale(orig_player_img, (orig_player_img.get_width() * zoom, orig_player_img.get_height() * zoom))

                                scroll = [((tile_position[0] * 2) - 928 - zoom_mouse_offset[0]),
                                          ((tile_position[1] * 2) - 496 - zoom_mouse_offset[1])]

                                if zoom > 2:
                                    scroll = [(tile_position[0] * 2) - 896 - zoom_mouse_offset[0],
                                              (tile_position[1] * 2) - 464 - zoom_mouse_offset[1]]

                            elif zoom < 0:
                                tile_size = 32 / abs(zoom)
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "/")
                                player_img = pygame.transform.scale(orig_player_img, (round(orig_player_img.get_width() / abs(zoom)), round(orig_player_img.get_height()
                                                                                                                                            / abs(zoom))))
                                scroll = [((tile_position[0] * 2) - 952) - zoom_mouse_offset[0],
                                          ((tile_position[1] * 2) - 520) - zoom_mouse_offset[1]]

                            else:
                                tile_size = 32
                                tile_index, ui_images = scale_tiles(tile_index, ui_images)
                                player_img = orig_player_img.copy()

                                scroll = [((tile_position[0] * 2) - 944 - zoom_mouse_offset[0]),
                                          ((tile_position[1] * 2) - 512 - zoom_mouse_offset[1])]
                            update = True

                # Zoom
                elif event.button == 5:
                    if mouse[0] > sidebar_img.get_width():
                        if zoom > -4:
                            zoom -= 2

                            if zoom > 0:
                                tile_size = 32 * zoom
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "*")
                                player_img = pygame.transform.scale(orig_player_img, (orig_player_img.get_width() * zoom, orig_player_img.get_height() * zoom))

                                scroll = [((tile_position[0] / 2) - 928 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 496 - zoom_mouse_offset[1])]

                            elif zoom < 0:
                                tile_size = 32 / abs(zoom)
                                tile_index, ui_images = scale_tiles(tile_index, ui_images, "/")
                                player_img = pygame.transform.scale(orig_player_img, (round(orig_player_img.get_width() / abs(zoom)), round(orig_player_img.get_height()
                                                                                                                                            / abs(zoom))))
                                scroll = [((tile_position[0] / 2) - 952 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 520 - zoom_mouse_offset[1])]

                                if zoom < -2:
                                    scroll = [((tile_position[0] / 2) - 956 - zoom_mouse_offset[0]),
                                              ((tile_position[1] / 2) - 524 - zoom_mouse_offset[1])]

                            else:
                                tile_size = 32
                                tile_index, ui_images = scale_tiles(tile_index, ui_images)
                                player_img = orig_player_img.copy()

                                scroll = [((tile_position[0] / 2) - 944 - zoom_mouse_offset[0]),
                                          ((tile_position[1] / 2) - 512 - zoom_mouse_offset[1])]
                            update = True

            if event.type == pygame.MOUSEBUTTONUP:
                update = True

            # Scroll
            if pygame.mouse.get_pressed(3)[1]:

                if not old_pressed == pygame.mouse.get_pressed(3)[1]:
                    mouse_rect.x, mouse_rect.y = mouse[0], mouse[1]

                old_scroll = scroll.copy()
                old_mouse_rect = mouse_rect.copy()
                mouse_rect.x, mouse_rect.y, = mouse[0], mouse[1]
                scroll[0] -= (mouse_rect.x - old_mouse_rect.x)
                scroll[1] -= (mouse_rect.y - old_mouse_rect.y)
                screen_copy.blit(screen, (0, 0))
                screen.fill(bg_color)
                screen.blit(screen_copy, (mouse_rect.x - old_mouse_rect.x, mouse_rect.y - old_mouse_rect.y))
                pixels_scrolled[0] += scroll[0] - old_scroll[0]
                pixels_scrolled[1] += scroll[1] - old_scroll[1]

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

                if zoom > 0:

                    tile_range[0] = round(23 / (zoom / 2))
                    tile_range[1] = round(38 / (zoom / 2))

                elif zoom < 0:
                    tile_range[0] = round(38 * abs(zoom))
                    tile_range[1] = round(64 * abs(zoom))

                else:
                    tile_range[0] = 38
                    tile_range[1] = 64

                if not pixels_scrolled[0] == 0:
                    last_tile_pos = ""

                    while True:
                        if pixels_scrolled[0] > 0 or last_tile_pos == "right":
                            tile_pos[0] = round(((((display.get_width() - 0) - pixels_scrolled[0]) - offset[0]) + round(scroll[0])) / tile_size)
                            last_tile_pos = "right"

                        elif pixels_scrolled[0] < 0 or last_tile_pos == "left":
                            tile_pos[0] = round((((0 - offset[0]) - pixels_scrolled[0]) + round(scroll[0])) / tile_size)
                            last_tile_pos = "left"

                        for y in range(tile_range[0]):
                            tile_pos[1] = int((y - 3) + round(scroll[1] / tile_size))
                            chunk_pos = str(int(tile_pos[0] / 8)) + ";" + str(int(tile_pos[1] / 8))

                            # Blits tiles
                            if chunk_pos in tile_map["map"]:
                                tile = str(int(tile_pos[0])) + ";" + str(int((y - 3) + round(scroll[1] / tile_size)))
                                if tile in tile_map["map"][chunk_pos]:
                                    pos = tile.split(";")
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])

                                    for layer in tile_map["map"][chunk_pos][tile]:

                                        if str(tile_map["map"][chunk_pos][tile][layer][0]) in tile_index:
                                            screen.blit((tile_index[str(tile_map["map"][chunk_pos][tile][layer][0])]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                        elif str(tile_map["map"][chunk_pos][tile][layer][0]) not in tile_index:
                                            screen.blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                            # Blits tiles
                            if chunk_pos in tile_map["mobs"]:
                                tile = str(int(tile_pos[0])) + ";" + str(int((y - 3) + round(scroll[1] / tile_size)))
                                if tile in tile_map["mobs"][chunk_pos]:
                                    pos = tile.split(";")
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])

                                    for layer in tile_map["mobs"][chunk_pos][tile]:

                                        if str(tile_map["mobs"][chunk_pos][tile][layer][0]) in tile_index:
                                            screen.blit((tile_index[str(tile_map["mobs"][chunk_pos][tile][layer][0])]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                        elif str(tile_map["mobs"][chunk_pos][tile][layer][0]) not in tile_index:
                                            screen.blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                        if pixels_scrolled[0] == 0:
                            pixels_scrolled[0] = 0
                            break

                        elif pixels_scrolled[0] > 0 - tile_size:
                            pixels_scrolled[0] -= tile_size - 1
                            if pixels_scrolled[0] < 0:
                                pixels_scrolled[0] = 0

                        elif pixels_scrolled[0] < 0 + tile_size:
                            pixels_scrolled[0] += tile_size - 1
                            if pixels_scrolled[0] > 0:
                                pixels_scrolled[0] = 0

                if not pixels_scrolled[1] == 0:

                    last_tile_pos = ""
                    while True:
                        if pixels_scrolled[1] > 0 or last_tile_pos == "bottom":
                            tile_pos[1] = round(((((display.get_height() - 1) - pixels_scrolled[1]) - offset[1]) + round(scroll[1])) / tile_size)
                            last_tile_pos = "bottom"

                        elif pixels_scrolled[1] < 0 or last_tile_pos == "top":
                            tile_pos[1] = round((((0 - offset[1]) + round(scroll[1])) - pixels_scrolled[1]) / tile_size)
                            last_tile_pos = "top"

                        for x in range(tile_range[1]):
                            tile_pos[0] = int((x - 3) + round(scroll[0] / tile_size))
                            chunk_pos = str(int(tile_pos[0] / 8)) + ";" + str(int(tile_pos[1] / 8))

                            # Blits tiles
                            if chunk_pos in tile_map["map"]:
                                tile = str(int((x - 3) + round(scroll[0] / tile_size))) + ";" + str(int(tile_pos[1]))

                                if tile in tile_map["map"][chunk_pos]:
                                    pos = tile.split(";")
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])

                                    for layer in tile_map["map"][chunk_pos][tile]:

                                        if str(tile_map["map"][chunk_pos][tile][layer][0]) in tile_index:
                                            screen.blit((tile_index[str(tile_map["map"][chunk_pos][tile][layer][0])]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                        elif str(tile_map["map"][chunk_pos][tile][layer][0]) not in tile_index:
                                            screen.blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                            # Blits mobs
                            if chunk_pos in tile_map["mobs"]:
                                tile = str(int((x - 3) + round(scroll[0] / tile_size))) + ";" + str(int(tile_pos[1]))

                                if tile in tile_map["mobs"][chunk_pos]:
                                    pos = tile.split(";")
                                    pos[0], pos[1], = int(pos[0]), int(pos[1])

                                    for layer in tile_map["mobs"][chunk_pos][tile]:

                                        if str(tile_map["mobs"][chunk_pos][tile][layer][0]) in tile_index:
                                            screen.blit((tile_index[str(tile_map["mobs"][chunk_pos][tile][layer][0])]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                        elif str(tile_map["mobs"][chunk_pos][tile][layer][0]) not in tile_index:
                                            screen.blit((tile_index["null"]),
                                                        (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                        if pixels_scrolled[1] == 0:
                            break

                        elif pixels_scrolled[1] > 0 - tile_size and not pixels_scrolled[1] == 0:
                            pixels_scrolled[1] -= tile_size - 1
                            if pixels_scrolled[1] < 0:
                                pixels_scrolled[1] = 0
                        elif pixels_scrolled[1] < 0 + tile_size and not pixels_scrolled[1] == 0:
                            pixels_scrolled[1] += tile_size - 1
                            if pixels_scrolled[1] > 0:
                                pixels_scrolled[1] = 10

        # Undo / redo
        current_time = time.time()
        last_holding_down = holding_down

        if pygame.key.get_pressed()[pygame.K_z] and pygame.key.get_pressed()[pygame.K_LCTRL] and pygame.key.get_pressed()[pygame.K_LSHIFT]:
            holding_down = True

            if not last_holding_down:
                current_time = time.time()
                last_time = current_time

            if current_time - last_time >= 0.3:
                undo_redo_flag = True
                last_time = current_time

            if undo_redo_flag or not last_holding_down:

                if not last_holding_down or current_time - last_time >= 0.05:
                    if current_time - last_time >= 0.05:
                        last_time = current_time

                    if len(redo_list) > 0:
                        update = True
                        pos = redo_list[-1][0].split(";")
                        pos[0], pos[1], = int(pos[0]), int(pos[1])

                        if redo_list[-1][2] == "remove":
                            draw_tile(zoom, current_layer, offset, selection_=redo_list[-1][3], specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            undo_list.append(redo_list[-1])
                            redo_list.pop()

                        elif redo_list[-1][2] == "add":
                            erase_tile(zoom, current_layer, offset, specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            undo_list.append(redo_list[-1])
                            redo_list.pop()

                        elif redo_list[-1][2] == "replace":

                            draw_tile(zoom, redo_list[-1][1], offset, selection_=redo_list[-1][3], specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            undo_list.append(redo_list[-1])
                            redo_list.pop()

        # Undo / redo
        elif pygame.key.get_pressed()[pygame.K_z] and pygame.key.get_pressed()[pygame.K_LCTRL]:
            holding_down = True

            if not last_holding_down:
                current_time = time.time()
                last_time = current_time

            if current_time - last_time >= 0.3:
                undo_redo_flag = True
                last_time = current_time

            if undo_redo_flag or not last_holding_down:

                if not last_holding_down or current_time - last_time >= 0.05:
                    if current_time - last_time >= 0.05:
                        last_time = current_time

                    if len(undo_list) > 0:
                        update = True
                        pos = undo_list[-1][0].split(";")
                        pos[0], pos[1], = int(pos[0]), int(pos[1])

                        if undo_list[-1][2] == "remove":
                            erase_tile(zoom, current_layer, offset, specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            redo_list.append(undo_list[-1])
                            undo_list.pop()

                        elif undo_list[-1][2] == "add":
                            draw_tile(zoom, current_layer, offset, selection_=undo_list[-1][3], specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            redo_list.append(undo_list[-1])
                            undo_list.pop()

                        elif undo_list[-1][2] == "replace":
                            draw_tile(zoom, undo_list[-1][1], offset, selection_=undo_list[-1][4], specific_tile=str(pos[0]) + ";" + str(pos[1]))
                            redo_list.append(undo_list[-1])
                            undo_list.pop()

        else:
            undo_redo_flag = False
            holding_down = False

        # Draw tiles
        if pygame.mouse.get_pressed(3)[0]:
            if selection is not None:
                calculate_line(mouse_rect.x, mouse_rect.y, mouse[0], mouse[1], draw_tile, zoom, current_layer, offset, selection)

        # Erases tiles
        elif pygame.mouse.get_pressed(3)[2]:
            calculate_line(mouse_rect.x, mouse_rect.y, mouse[0], mouse[1], erase_tile, zoom, current_layer, offset, selection)

        # Blitting -----------------------------------------------------------------------------------------------------------------------------------------------------
        if update:
            screen.fill(bg_color)
            for i in layer_dict.keys():
                layer_dict[i].fill(bg_color)

            layer_dict["0"].blit(player_img, (int(16 * tile_size) - scroll[0], int(15 * tile_size) - scroll[1]))

            if zoom < 0:
                tile_range = [round(5 * abs(zoom)), 9 * abs(zoom)]

            else:
                tile_range = [7, 9]

            for y in range(tile_range[0]):
                for x in range(tile_range[1]):
                    target_x = x - 1 + int(round(scroll[0] / (8 * tile_size)))
                    target_y = y - 1 + int(round(scroll[1] / (8 * tile_size)))
                    target_chunk = str(target_x) + ';' + str(target_y)

                    # Blits tiles
                    if target_chunk in tile_map["map"]:
                        for tile in tile_map["map"][target_chunk]:
                            for layer in tile_map["map"][target_chunk][tile]:
                                if layer not in layer_dict:
                                    layer_dict[layer] = pygame.Surface(WINDOW_SIZE)
                                    layer_dict[layer].set_colorkey(bg_color)
                                    layer_dict[layer].fill(bg_color)
                                    layer_dict = {key: val for key, val in sorted(layer_dict.items(), key=lambda ele: int(ele[0]))}

                                pos = tile.split(";")
                                pos[0], pos[1], = int(pos[0]), int(pos[1])

                                if str(tile_map["map"][target_chunk][tile][layer][0]) in tile_index:
                                    layer_dict[layer].blit((tile_index[str(tile_map["map"][target_chunk][tile][layer][0])]),
                                                           (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                elif str(tile_map["map"][target_chunk][tile][layer][0]) not in tile_index:
                                    layer_dict[layer].blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                    # Blits mobs
                    if target_chunk in tile_map["mobs"]:
                        for tile in tile_map["mobs"][target_chunk]:
                            for layer in tile_map["mobs"][target_chunk][tile]:

                                if layer not in layer_dict:
                                    layer_dict[layer] = pygame.Surface(WINDOW_SIZE)
                                    layer_dict[layer].set_colorkey(bg_color)
                                    layer_dict[layer].fill(bg_color)
                                    layer_dict = {key: val for key, val in sorted(layer_dict.items(), key=lambda ele: int(ele[0]))}

                                pos = tile.split(";")
                                pos[0], pos[1], = int(pos[0]), int(pos[1])

                                if str(tile_map["mobs"][target_chunk][tile][layer][0]) in tile_index:
                                    layer_dict[layer].blit((tile_index[str(tile_map["mobs"][target_chunk][tile][layer][0])]),
                                                           (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

                                elif str(tile_map["mobs"][target_chunk][tile][layer][0]) not in tile_index:
                                    layer_dict[layer].blit((tile_index["null"]), (int(pos[0] * tile_size) - scroll[0], int(pos[1] * tile_size) - scroll[1]))

            for i in layer_dict.keys():
                screen.blit(layer_dict[i], (0, 0))

            update = False

        display.blit(screen, (0, 0))

        # Blits mouse position text
        tile_position = [round(((mouse[0] - offset[0]) + round(scroll[0])) / tile_size), round(((mouse[1] - offset[1]) + round(scroll[1])) / tile_size)]
        chunk_pos = str(int((tile_position[0]) / 8)) + ":" + str(int((tile_position[1]) / 8))
        chunk_pos = chunk_pos.replace(":", ";")

        # Blits mouse tile
        if not pygame.mouse.get_pressed(3)[2]:
            if mouse[0] > sidebar_img.get_width():
                mouse_scroll = [scroll[0] % tile_size, scroll[1] % tile_size]

                if selection in tile_index:
                    blitted_selection = tile_index[selection].copy()
                    tinted_selection = pygame.Surface((blitted_selection.get_width(), blitted_selection.get_height()))
                    tinted_selection.fill((0, 0, 0))
                    tinted_selection.set_alpha(30)
                    blitted_selection.set_alpha(180)
                    pos = str(tile_position[0]) + ";" + str(tile_position[1])

                    if chunk_pos in tile_map["map"]:
                        if pos in tile_map["map"][chunk_pos]:
                            for layer in tile_map["map"][chunk_pos][pos]:
                                if tile_map["map"][chunk_pos][pos][layer][0] == selection:

                                    blitted_selection.set_alpha(255)
                                    tinted_selection.set_alpha(0)
                                    break

                    blitted_selection.blit(tinted_selection, (0, 0))

                    mouse_tile_flag = True
                    if chunk_pos in tile_map["map"]:
                        if pos in tile_map["map"][chunk_pos]:
                            for layer in tile_map["map"][chunk_pos][pos]:
                                if layer > current_layer and mouse_tile_flag:

                                    display.blit(blitted_selection, (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                                     round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))
                                    mouse_tile_flag = False

                                if tile_map["map"][chunk_pos][pos][layer][0] in tile_index:
                                    display.blit((tile_index[tile_map["map"][chunk_pos][pos][layer][0]]),
                                                 (int(tile_position[0] * tile_size) - scroll[0], int(tile_position[1] * tile_size) - scroll[1]))

                                else:
                                    display.blit((tile_index["null"]), (int(tile_position[0] * tile_size) - scroll[0], int(tile_position[1] * tile_size) - scroll[1]))

                    if mouse_tile_flag:
                        display.blit(blitted_selection, (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                         round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))

                else:
                    if selection is not None:
                        display.blit(tile_index["null"], (round(((mouse[0] - offset[0]) + mouse_scroll[0]) / tile_size) * tile_size - mouse_scroll[0],
                                                          round(((mouse[1] - offset[1]) + mouse_scroll[1]) / tile_size) * tile_size - mouse_scroll[1]))

        # display.blit(sidebar_img, (0, 0))  # Blits sidebar image
        chunk_pos = chunk_pos.replace(";", ":")
        white_font.render("Chunk: " + chunk_pos + "   Tile: " + str(tile_position[0]) + ":" + str(tile_position[1]), display, (420, 2))
        dark_purple_font.render("Layer: " + str(current_layer), display, (46, 197))
        right_arrow_button.position[0] = 47 + (dark_purple_font.width("Layer: " + str(current_layer)))
        display.blit(tiny_mouse_dot_img, mouse_rect)

        # Displays sidebar images
        for key in rect_image_dict[tab].keys():
            if key in ui_images:

                if not rect_image_dict[tab][key].collidepoint(mouse):
                    display.blit(ui_images[key], rect_image_dict[tab][key])

                else:
                    display.blit(ui_images[key], (rect_image_dict[tab][key].x, rect_image_dict[tab][key].y - 5))

            else:
                display.blit(ui_images["null"], rect_image_dict[tab][key])

        # BUTTONS ------------------------------------------------------------------------------------------------------------------------------------------------------

        for button in editor_button_list:
            button.update(left_mouse_button)

        if tiles_button.clicked:
            tab = "tiles"

        if decorations_button.clicked:
            tab = "decorations"

        if mobs_button.clicked:
            tab = "mobs"

        if editor_load_map_button.clicked:
            save_map()
            tile_map, map_file_path, error, _, layer_dict = load_map(tile_map, map_file_path, layer_dict)
            update = True

        if editor_load_image_button.clicked:
            rect_image_dict, tile_index, ui_images = load_image(rect_image_dict, "//data/map editor/saved images/", tile_index, ui_images)

        if left_arrow_button.clicked:
            current_layer = str(int(current_layer) - 1)

        if right_arrow_button.clicked:
            current_layer = str(int(current_layer) + 1)

        if editor_settings_button.clicked:
            state = "settings"
            last_state = "editor"

    clock.tick(1000)
    pygame.display.update()
