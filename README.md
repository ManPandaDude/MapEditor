# MapEditor
A gui tile based map editor.

Uses json files for maps.

# Menu
Can load maps, create new maps, and edit settings for image paths.

# Settings
Can modify paths for loading tile and spritesheet images.
Can also modify the default maps folder to make it easier to load maps.

# Editor
Can place and erase tiles.
Has different tabs for storing tile images: tiles, for 16x16 images, decorations, for everything thats not 16x16, and mobs, for mobs.
Has layer functionality.
Can zoom in with mouse wheel, and use mouse wheel click to move view around.
Map file stores data in chunks, with each chunk having tiles.
Map file stores number of layers, tile map, and mobs separately.

