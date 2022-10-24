#!/usr/bin/env python3
"""
RedBlobGreenBlob level loader.
"""

import pygame
import os
import random

from RedBlobGreenBlob.constants import *
from RedBlobGreenBlob.player import Player

PLATETILE = 0
TOPTILE = 1
ANITILE = 2
VARTILE = 3

TILECOLLIDE = 0b1
TILEDEADLY = 0b10
TILEALPHA = 0b100

# Starting at tile 40.
TILES = [
    {"type": PLATETILE, "flags": 0, "files": ["start.png"]},
    {"type": PLATETILE, "flags": 0, "files": ["end.png"]},
    {"type": PLATETILE, "flags": 0, "files": ["checkpoint.png"]},
    {},
    {},
    {},
    {},
    {},
    {"type": TOPTILE, "flags": TILECOLLIDE,
     "files": ["grass.png", "grassc.png", "grassp.png"]},
    {"type": PLATETILE, "flags": TILECOLLIDE, "files": ["dirt.png"]},
    {"type": TOPTILE, "flags": TILECOLLIDE,
     "files": ["metal.png", "metalc.png", "metalp.png"]},
    {"type": PLATETILE, "flags": TILECOLLIDE, "files": ["metala.png"]},
    {"type": PLATETILE, "flags": TILECOLLIDE, "files": ["plate.png"]},
    {"type": ANITILE, "flags": TILEDEADLY | TILEALPHA,
     "files": ["lava.png", "lava1.png", "lava2.png", "lava3.png", "lava4.png"]},
    {"type": VARTILE, "flags": TILECOLLIDE,
     "files": ["stone.png", "stone1.png", "stone2.png"]}
]

for tile in TILES:
    if "files" in tile:
        tile.update(
            {"files": list(map(lambda file: os.path.join(IMGDIR, file), tile["files"]))})


class Tile(pygame.sprite.Sprite):
    """ Tile sprite """
    animationFrame = 300

    def __init__(self, x, y, tile, size: int = 100, file: int = 0, *groups):
        """ Load the tile given its x and y, tile dictionary, size and file number. """
        super().__init__(*groups)
        self.size = size
        self.images = tile["files"]
        self.type = tile["type"]
        self.file = file

        self.image = self.images[self.file]
        self.aniTicks = pygame.time.get_ticks()

        self.rect = pygame.Rect(x, y, size, size)

        if self.type == VARTILE:
            self.animate()

    def animate(self):
        self.file = random.randint(0, len(self.images) - 1)
        self.image = self.images[self.file]

    def update(self):
        if self.type == ANITILE and \
                (pygame.time.get_ticks() - self.aniTicks) > self.animationFrame:
            self.aniTicks = pygame.time.get_ticks()
            self.animate()


class Border(pygame.sprite.Sprite):
    """ Border sprite that acts as an invisible barrier. """

    def __init__(self, rect, *groups):
        super().__init__(*groups)
        self.rect = rect
        self.image = pygame.surface.Surface((self.rect.width, self.rect.height))


class Level(pygame.sprite.AbstractGroup):
    def __init__(self, file, size):
        super().__init__()
        with open(file, "r") as f:
            content = f.read()

        self.size = size
        self.width = content.index("\n") + 1
        self.height = len(content) // content.index("\n")
        self.start = None
        self.end = None

        # Store the order in which checkpoints are activated.
        self.checkpoint = pygame.sprite.OrderedUpdates()

        # Groups for collision detection.
        self.hitboxes = pygame.sprite.Group()
        self.deadly = pygame.sprite.Group()
        self.checkpoints = pygame.sprite.Group()

        # Orientations of directional tiles
        dirtiles = list(
            map(lambda x: self.parse_tile(content, chr(x[0] + 40)) if x[1].get("type",
                                                                               -1) == TOPTILE else None,
                enumerate(TILES)))

        # Tiles that won't be collided with. (air, background decor, etc. )
        bgtiles = list(filter(None, map(lambda x: False if x[1].get("flags",
                                                                    0) & TILECOLLIDE else chr(
            x[0] + 40),
                                        enumerate(TILES))))

        self.tiles = list(map(dict, TILES))
        for tile in self.tiles:
            if "files" in tile:
                tile.update({"files": self.load_tile(tile)})

        for i, block in enumerate(content):
            x = i % self.width
            y = i // self.width
            if not block in [" ", "\n"]:
                if ord(block) - 40 >= 0 and self.tiles[ord(block) - 40].get("type",
                                                                            -1) == TOPTILE:
                    direction = int(dirtiles[ord(block) - 40][i])
                else:
                    direction = 0

                tile = dict(self.tiles[ord(block) - 40])
                if tile["flags"] & TILECOLLIDE:
                    tile["flags"] = (tile["flags"] - TILECOLLIDE) | \
                                    (TILECOLLIDE & int(
                                        self.has_collisions(bgtiles, content, i)))

                spriteTile = Tile(x * self.size, y * self.size, tile, self.size,
                                  direction)

                if tile["flags"] & TILECOLLIDE:
                    self.hitboxes.add(spriteTile)
                elif tile["flags"] & TILEDEADLY:
                    self.deadly.add(spriteTile)

                if ord(block) - 40 == 0:
                    self.start = spriteTile
                    self.checkpoint.add(spriteTile)
                if ord(block) - 40 == 1:
                    self.end = spriteTile
                elif ord(block) - 40 == 2:
                    self.checkpoints.add(spriteTile)

                self.add(spriteTile)

        # Left border
        self.hitboxes.add(Border(pygame.Rect(-self.size, 0,
                                             self.size, self.height * self.size)))
        # Right border
        self.hitboxes.add(Border(pygame.Rect((self.width - 1) * self.size, 0,
                                             self.size, self.height * self.size)))

    def load_image(self, file):
        """ Load a tile image scaled to the appropriate size. """
        return pygame.transform.scale(pygame.image.load(file),
                                      (self.size, self.size))

    def load_tile(self, tile):
        """ Return a all of a tile variations. """
        if tile["type"] == PLATETILE:
            images = [self.load_image(tile["files"][0])]
        elif tile["type"] == TOPTILE:
            images = [self.load_image(tile["files"][0])]
            images += [pygame.transform.rotate(images[0], -90),
                       pygame.transform.rotate(images[0], -180),
                       pygame.transform.rotate(images[0], -270)]
            images += [self.load_image(tile["files"][1])]
            images += [pygame.transform.rotate(images[4], -90)]
            images += [self.load_image(tile["files"][2])]
            images += [pygame.transform.rotate(images[6], -90)]
        elif tile["type"] == ANITILE or tile["type"] == VARTILE:
            images = list(map(self.load_image, tile["files"]))

        if tile["flags"] & TILEALPHA:
            return list(map(lambda i: i.convert_alpha(), images))
        else:
            return list(map(lambda i: i.convert(), images))

    def has_collisions(self, bgtiles, content, i):
        """ Return whether a tile should be able to be collided with. """
        above = content[i - self.width] if i - self.width > 0 else "\x00"
        left = content[i - 1] if i - 1 > 0 else "\x00"
        below = content[i + self.width] if i + self.width < len(content) else "\x00"
        right = content[i + 1] if i + 1 < len(content) else "\x00"

        if not (self.tiles[max(0, ord(content[i]) - 40)]["flags"] & TILECOLLIDE):
            return False
        elif any(map(lambda x: x in list(["\x00", " "] + bgtiles),
                     [above, left, below, right])):
            return True
        else:
            return False

    def parse_tile(self, content, tile):
        """ Return the orientation of directional tiles. """
        leveltiles = "".join(map(lambda x: "0" if x == tile else " ", content))

        for i, block in enumerate(leveltiles):
            if block != " ":
                above = leveltiles[i - self.width] if i - self.width > 0 else "\x00"
                left = leveltiles[i - 1] if i - 1 > 0 else "\x00"
                below = leveltiles[i + self.width] if i + self.width < len(
                    leveltiles) else "\x00"
                right = leveltiles[i + 1] if i + 1 < len(leveltiles) else "\x00"

                if below == "0" and right in ["0", "6"]:
                    leveltiles = leveltiles[:i] + "4" + leveltiles[i + 1:]
                elif below == "0" and left in ["0", "7"]:
                    leveltiles = leveltiles[:i] + "5" + leveltiles[i + 1:]
                elif above == "4" or above == "3":
                    if left in list(map(str, range(8))):
                        leveltiles = leveltiles[:i] + "6" + leveltiles[i + 1:]
                    else:
                        leveltiles = leveltiles[:i] + "3" + leveltiles[i + 1:]
                elif above == "5" or above == "1":
                    if right in list(map(str, range(8))):
                        leveltiles = leveltiles[:i] + "7" + leveltiles[i + 1:]
                    else:
                        leveltiles = leveltiles[:i] + "1" + leveltiles[i + 1:]

        return leveltiles

    def at_checkpoint(self, player: pygame.sprite.Sprite):
        """ Return and set the checkpoint the player has collided with. """
        collision = pygame.sprite.spritecollideany(player, self.checkpoints)
        if collision and not collision == self.checkpoint.sprites()[-1]:
            # Add the checkpoint into the group regardless of whether
            # there is already the same checkpoint in the group.
            self.checkpoint.add_internal(collision)
            collision.add_internal(self)
            return True
        else:
            return False

    def failed(self, player: pygame.sprite.Sprite):
        """ Return whether the player has collided with a deadly object."""
        if pygame.sprite.spritecollideany(player, self.deadly):
            return True
        elif player.rect.bottom > self.height * self.size:
            return True
        else:
            return False

    def goto_checkpoint(self, player: pygame.sprite.Sprite):
        """ Move the player to the last checkpoint."""
        player.rect.x = self.checkpoint.sprites()[-1].rect.x
        player.rect.bottom = self.checkpoint.sprites()[-1].rect.bottom


class Camera(pygame.sprite.Group):
    """
    Camera(x, y, width, height, scrollWidth, scrollHeight, moveThreshold) -> Camera
    
    RedBlobGreenBlob camera.

    This camera is a group that allows for scrolling.
    It used to scroll through the level's therefore ensuring the player is always in view.
    """
    delay = 1

    def __init__(self, x, y, width, height, sWidth, sHeight, moveThreshold):
        """
        Initialise the camera with its (x,y) position, width, height, scroll width, scroll height and move threshold. 
        """
        super().__init__(self)
        self.x = x
        self.y = y
        self.scrollWidth = sWidth
        self.scrollHeight = sHeight
        self.width = width
        self.height = height
        self.moveThreshold = moveThreshold

    def draw(self, surface):
        sprites = self.sprites()
        surface_blit = surface.blit
        for spr in sprites:
            self.spritedict[spr] = surface_blit(spr.image,
                                                spr.rect.move(-self.x, self.y))
        self.lostsprites = []

    def scroll(self, player: Player, delay=None):
        """scroll so that the sprite is in view."""
        delay = delay if delay else self.delay

        rect = player.rect.move(-self.x, self.y)

        # Right
        if rect.centerx > (self.width // 2) + self.moveThreshold:
            self.x += (rect.centerx - ((self.width // 2) + self.moveThreshold)) / delay

        # Left
        if rect.centerx < (self.width // 2) - self.moveThreshold:
            self.x -= (((self.width // 2) - self.moveThreshold) - rect.centerx) / delay

        # Up
        if rect.centery < (self.height // 2) - self.moveThreshold:
            self.y += (((self.height // 2) - self.moveThreshold) - rect.centery) / delay

        # Down
        if rect.centery > (self.height // 2) + self.moveThreshold:
            self.y -= (rect.centery - ((self.height // 2) + self.moveThreshold)) / delay

        self.x = min(max(0, self.x), self.scrollWidth - self.width)

        # No minimum y value. 
        self.y = max(self.y, self.height - self.scrollHeight)


def main():
    pygame.init()

    pygame.display.set_mode((1920, 1080))
    screen = pygame.display.get_surface()

    level = Level("./levels/level1.txt", 20)
    print(pygame.time.get_ticks())
    g = pygame.sprite.RenderPlain(*iter(level))
    print(pygame.time.get_ticks())

    run = True

    while run:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        g.draw(screen)

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
