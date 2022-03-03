#!/usr/bin/python3.4
import pygame


def clip(surf, x, y, x_size, y_size):
    handle_surf = surf.copy()
    _clip_rect = pygame.Rect(x, y, x_size, y_size)
    handle_surf.set_clip(_clip_rect)
    image = surf.subsurface(handle_surf.get_clip())
    return image.copy()


def clip_rect(x, y, x_size, y_size):
    _clip_rect = pygame.Rect(x, y, x_size, y_size)
    return _clip_rect


def swap_color(img, old_c, new_c, colorkey):
    """Swaps old_c with new_c
    Swaps color by erasing old_color from surface1 by setting it as colorkey, copies surface1 as surface2,
    fills surface1 with new_color, and pastes surface2 on surface1"""
    img.set_colorkey(old_c)
    surf = img.copy()
    surf.fill(new_c)
    surf.blit(img, (0, 0))
    surf.set_colorkey(colorkey)
    try:
        self.color = new_c
    except Exception:
        pass
    return surf


def load_font_img(path, font_color, colorkey, scale=1):
    font_fg_color = (255, 0, 0)

    font_img = pygame.image.load(path).convert()
    font_img = swap_color(font_img, font_fg_color, font_color, colorkey)
    last_x = 0
    letters = []
    letter_spacing = []
    for x in range(font_img.get_width()):
        if font_img.get_at((x, 0))[0] == 127:
            letters.append(clip(font_img, last_x, 0, x - last_x, font_img.get_height()))
            letter_spacing.append(x - last_x)
            last_x = x + 1
        x += 1
    for letter in letters:
        letters[letters.index(letter)] = pygame.transform.scale(letter, (letter.get_width() * scale, letter.get_height() * scale))
        letter.set_colorkey(colorkey)
    return letters, letter_spacing, font_img.get_height(),


class Font:
    def __init__(self, path, color, colorkey, scale_multiplier=1, spacing_x=1, spacing_y=1, ):
        self.letters, self.letter_spacing, self.line_height, = \
            load_font_img(path, color, colorkey, scale_multiplier)
        self.font_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                           'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                           'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '.', '-',
                           ',', ':', '+', '\'', '!', '?', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '(', ')',
                           '/', '_', '=', '\\', '[', ']', '*', '"', '<', '>', ';']
        self.space_width = self.letter_spacing[0] - self.letter_spacing[0] / 2
        self.base_spacing = spacing_x
        self.line_spacing = spacing_y * 2
        self.color = color
        self.scale = scale_multiplier

    def width(self, text):
        text_width = 0
        for char in text:

            if char not in ['\n', ' ']:
                text_width += self.letters[self.font_order.index(char)].get_width() + self.base_spacing * self.scale
            elif char == ' ':
                text_width += (self.space_width + self.base_spacing) * self.scale
            elif char == '\n':
                text_width -= self.base_spacing * self.scale

        text_width -= self.base_spacing * self.scale
        return text_width

    def height(self, text):
        height = 0
        for char in text:
            if char in ['g', 'j', 'p', 'q', 'y']:
                height = self.letters[0].get_height()
            elif char not in ['\n', ' ']:
                height = self.letters[0].get_height() - 4 * self.scale
        return height

    def render(self, text, surf, loc, line_width=0):
        i = 0
        iterate = 0
        x_offset = 0
        y_offset = 0
        if line_width != 0:
            spaces = []
            x = 0

            for i, char in enumerate(text):
                if char == ' ':
                    spaces.append((x, i))
                    x += self.space_width + self.base_spacing
                else:
                    x += self.letter_spacing[self.font_order.index(char)] + self.base_spacing
            line_offset = 0
            for i, space in enumerate(spaces):
                if (space[0] - line_offset) > line_width:
                    line_offset += spaces[i - 1][0] - line_offset
                    if i != 0:
                        text = text[:spaces[i - 1][1]] + '\n' + text[spaces[i - 1][1] + 1:]
        for char in text:
            if char not in ['\n', ' ']:
                surf.blit(self.letters[self.font_order.index(char)], ((loc[0] + x_offset * self.scale), loc[1] + y_offset * self.scale))
                x_offset += self.letter_spacing[self.font_order.index(char)] + self.base_spacing
            elif char == ' ':
                x_offset += self.space_width + self.base_spacing
            elif char == '\n':
                iterate += 1
                y_offset += self.line_spacing + self.line_height
                x_offset = 0
