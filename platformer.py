#!/usr/bin/env python3
"""
A simple platformer game by Ross Watts
"""

import pygame
import os

from pygame.constants import *

# 16:9 aspect ratio
# Native resolution of 100
SIZE = 100 # Monitor = 105
WIDTH = 16 * SIZE
HEIGHT = 9 * SIZE
MOVETHRESHOLD = int(SIZE)

# Units pixels per 1/60 seconds

SPEED = 7 # 420 pixels / second
JUMPSPEED = 9 # 540 pixels / second

GRAVITY = 20 # 1200 pixels / second / second

# 8-bit Platformer SFX commissioned by Mark McCorkle for OpenGameArt.org ( http://opengameart.org )
JUMPSOUNDFILE = "./sounds/jump.ogg"
SELECTSOUNDFILE = "./sounds/select.ogg"
POWERUPSOUNDFILE = "./sounds/powerup.ogg"

TILEFILES = ["./images/grass.png","./images/grassc.png","./images/grassp.png",
             "./images/dirt.png",
             "./images/metal.png","./images/metalc.png","./images/metalp.png",
             "./images/metala.png","./images/plate.png"]

UIBUTTON = "./images/button.png"
UIBUTTONSMALL = "./images/smallbutton.png"
UISLIDER = "./images/slider.png"
UIKNOB = "./images/knob.png"

# Colours

WHITE = (255,255,255)
GREEN = (255,0,0)


class World():
    def __init__(self,level: str,blockSize: int,colour: tuple):
        """ Load the level (a list of lines of text) onto the screen. """
        self.items = []
        self.colour = colour
        self.blockSize = blockSize
        self.relx = 0
        self.rely = 0

        self.width = level.index("\n")
        self.height = len(level) // self.width
        self.scrollWidth = self.width * self.blockSize
        self.scrollHeight = self.height * self.blockSize

        # Prepare all the tiles in the game.

        # Start and End (0,1)
        self.tiles = [[pygame.surface.Surface([self.blockSize,self.blockSize])],
                      [pygame.surface.Surface([self.blockSize,self.blockSize])]]
        self.tiles[0][0].fill((0,255,0))
        self.tiles[1][0].fill((0,255,0))
        # 6 Placeholders (2,3,4,5,6,7)
        self.tiles += [[pygame.surface.Surface([self.blockSize,self.blockSize])]] * 6
        # 8 Grass tile variations (8)
        self.tiles += [[self.load_image(TILEFILES[0])]]
        self.tiles[8] += [pygame.transform.rotate(self.tiles[8][0],-90),
                          pygame.transform.rotate(self.tiles[8][0],-180),
                          pygame.transform.rotate(self.tiles[8][0],-270)]

        self.tiles[8] += [self.load_image(TILEFILES[1])]
        self.tiles[8] += [pygame.transform.rotate(self.tiles[8][4],-90)]
        self.tiles[8] += [self.load_image(TILEFILES[2])]
        self.tiles[8] += [pygame.transform.rotate(self.tiles[8][6],-90)]
        # 1 Dirt tile (9)
        self.tiles += [[self.load_image(TILEFILES[3])]]
        # 8 Metal tile variations (10)
        self.tiles += [[self.load_image(TILEFILES[4])]]
        self.tiles[10] += [pygame.transform.rotate(self.tiles[10][0],-90),
                          pygame.transform.rotate(self.tiles[10][0],-180),
                          pygame.transform.rotate(self.tiles[10][0],-270)]

        self.tiles[10] += [self.load_image(TILEFILES[5])]
        self.tiles[10] += [pygame.transform.rotate(self.tiles[10][4],-90)]
        self.tiles[10] += [self.load_image(TILEFILES[6])]
        self.tiles[10] += [pygame.transform.rotate(self.tiles[10][6],-90)]
        # 1 Metal tile (11)
        self.tiles += [[self.load_image(TILEFILES[7])]]
        # 1 Plate tile (12)
        self.tiles += [[self.load_image(TILEFILES[8])]]

        

        self.tiles = list(map(lambda t: list(map(lambda i:i.convert_alpha(),t)),
                              self.tiles))
        
        tiles0 = self.parse_tile(level,"0")
            

        # Non-directionals
        for i,block in enumerate(level):
            x = i % (self.width + 1)
            y = i // (self.width + 1)

            if not block in [" ","\n"]:
                direction = ord(tiles0[i]) - 48 if block == "0" else 0
                self.items.append({"type":ord(block) - 32,
                                   "dir":direction,
                                   "collision":self.has_collisions(level,i),
                                   "rect":pygame.Rect(
                                       x*self.blockSize,
                                       y*self.blockSize,
                                       self.blockSize,self.blockSize),
                                   })

        if self.scrollHeight > HEIGHT:
            self.move_y(-(self.scrollHeight-HEIGHT))
            self.rely = 0
    @property
    def start(self):
        """ The start tile of the level."""
        return next(filter(lambda i: i["type"] == 8,self.items))["rect"]

    @property
    def end(self):
        """ The end tile of the level."""
        return next(filter(lambda i: i["type"] == 9,self.items))["rect"]

    def has_collisions(self,level,i):
        """ Return whether a tile should be able to be collided with. """
        above = level[i - (self.width + 1)] if i - (self.width + 1) > 0 else "\x00"
        left = level[i - 1] if i - 1 > 0 else "\x00"
        below = level[i + (self.width + 1)] if i + (self.width + 1) < len(level) else "\x00"
        right = level[i + 1] if i + 1 < len(level) else "\x00"

        if ord(level[i]) - 32 < 0x10:
            return False
        elif any(map(lambda x: x in ["\x00"," ","(",")"],[above,left,below,right])):
            return True
        else:
            return False

    def parse_tile(self,level,tile):
        """ Return the orientation of directional tiles. """
        leveltiles = "".join(map(lambda x: x if x == tile else " ",level))

        for i,block in enumerate(leveltiles):
            if block != " ":
                above = leveltiles[i - (self.width + 1)] if i - (self.width + 1) > 0 else "\x00"
                left = leveltiles[i - 1] if i - 1 > 0 else "\x00"
                below = leveltiles[i + (self.width + 1)] if i + (self.width + 1) < len(leveltiles) else "\x00"
                right = leveltiles[i + 1] if i + 1 < len(leveltiles) else "\x00"
                
                if below == "0" and right == "0":
                    leveltiles = leveltiles[:i] + "4" + leveltiles[i + 1:]
                elif below == "0" and left == "0":
                    leveltiles = leveltiles[:i] + "5" + leveltiles[i + 1:]
                elif above == "4" or above == "3":
                    if left in list(map(str,range(8))):
                        leveltiles = leveltiles[:i] + "6" + leveltiles[i + 1:]
                    else:
                        leveltiles = leveltiles[:i] + "3" + leveltiles[i + 1:]
                elif above == "5" or above == "1":
                    if right in list(map(str,range(8))):
                        leveltiles = leveltiles[:i] + "7" + leveltiles[i + 1:]
                    else:
                        leveltiles = leveltiles[:i] + "1" + leveltiles[i + 1:]

        return leveltiles
        

    def load_image(self,file) -> pygame.Surface:
        """ Return a correctly scaled image. """
        return pygame.transform.scale(pygame.image.load(file),
                                      (self.blockSize,self.blockSize),
                                      )

    def collided(self, player: pygame.Rect):
        """ Return the rectangle the player rectangle is colliding with. """
        blocks = list(map(lambda i: i["rect"],
                          filter(lambda b: b["collision"],
                                 self.items)))
        index = player.collidelist(blocks)
        if index != -1:
            return blocks[index]

        barriers = [pygame.Rect(-SIZE,0,SIZE,HEIGHT),
                    pygame.Rect(WIDTH,0,SIZE,HEIGHT),
                    pygame.Rect(0,HEIGHT,WIDTH,SIZE)]
        index = player.collidelist(barriers)
        if index != -1:
            return barriers[index]
        
        return False
    
    def move_x(self,dist: int):
        """ Move the world in the x axis by dist pixels. """
        self.relx -= int(dist)
        for block in self.items:
            block["rect"].move_ip(dist,0)

    def move_y(self,dist: int):
        """ Move the world in the y axis by dist pixels. """
        self.rely -= int(dist)
        for block in self.items:
            block["rect"].move_ip(0,dist)
    

    def valid_rect(self,block,types=range(0x8,0x20)):
        """Check if a block is a certain type and return the infomation for blitting. """
        if pygame.Rect(-SIZE,-SIZE,WIDTH+SIZE+MOVETHRESHOLD,
                       HEIGHT+SIZE+MOVETHRESHOLD).contains(block["rect"]) and \
           block["type"] in types:
            return (self.tiles[block["type"] - 0x8][block["dir"]],block["rect"].topleft)
        else:
            return False    

    def update(self,screen: pygame.Surface):
        """ Draw the world onto the screen. """
        screen.blits(list(filter(None,map(self.valid_rect,self.items))))

class Player(pygame.sprite.Sprite):
    def __init__(self,rect: pygame.Rect,world: World):
        """ Draw and control the player with realistic physics. """
        super().__init__()
        self.rect = rect
        self.world = world

        self.image = pygame.surface.Surface([rect.width,rect.height]).convert()
        self.image.fill((255,0,0))

        # Start time
        self.startTime = pygame.time.get_ticks()
        self.time = 1

        # 60 fps frame duration
        self.framedur = 16

        # Initial velocity
        self.velocity = 0

    @property
    def y_change(self) -> float:
        """ Calculate the player's movement. """
        
        return scale_val(GRAVITY * self.time - self.velocity)

    def right(self):
        """ Move the player right. """
        
        collision = self.world.collided(self.rect.move(scale_val(SPEED * self.framedur // 16),0))
        if collision:
            movement = collision.left - self.rect.right
        else:
            movement = scale_val(SPEED * self.framedur // 16)
        
        if self.rect.centerx > (WIDTH // 2) + MOVETHRESHOLD and \
           self.world.scrollWidth - WIDTH > self.world.relx:
            self.world.move_x(-movement)
        else:
            self.rect.move_ip(movement,0)
                
    def left(self):
        """ Move the player left. """
        
        collision = self.world.collided(self.rect.move(scale_val(-SPEED * self.framedur // 16),0))
        if collision:
            movement = self.rect.left - collision.right
        else:
            movement = scale_val(SPEED * self.framedur // 16)
        
        if self.rect.centerx < (WIDTH // 2) - MOVETHRESHOLD and \
           self.world.relx > 0:
            self.world.move_x(movement)
        else:
            self.rect.move_ip(-movement,0)

    def gravity(self):
        """ Apply the force of gravity onto the player. """
        
        # Check if the player is moving upwards.
        if self.velocity > 0:
            # Check if the peak point has been reached.
            collision = self.world.collided(self.rect.move(0,self.y_change))
            if self.time >= -(JUMPSPEED / -GRAVITY) or collision:
                self.velocity = 0
                self.startTime = pygame.time.get_ticks()

        self.time = (pygame.time.get_ticks() - self.startTime) / (62.5 * self.framedur)
        
        # Calculate if a block will be hit.
        collision = self.world.collided(self.rect.move(0,self.y_change))
        if collision:
            self.startTime = pygame.time.get_ticks()
            movement = collision.top - self.rect.bottom
        else:
            movement = self.y_change

        if self.rect.centery < (HEIGHT // 2) - MOVETHRESHOLD and \
           self.world.scrollHeight - HEIGHT > self.world.rely and \
           movement < 0:
            self.world.move_y(-movement)
        elif self.rect.centery > (HEIGHT // 2) + MOVETHRESHOLD and \
             self.world.rely < 0 and \
             movement > 0:
            self.world.move_y(-movement)
        else:
            self.rect.move_ip(0,movement)

class Game():
    def __init__(self):
        """ Control the UI of the game. """
        # The current function to run every update.
        self.update = self.startloop
        # The previous function that was run each update.
        self.previous = self.startloop
        self.screen = pygame.display.get_surface()
        
        # Graphics
        self.level = 1
        self.load_level("./levels/level{}.txt".format(self.level))

        self.mousepos = None

        # Sounds
        self.jumpSound = pygame.mixer.Sound(JUMPSOUNDFILE)
        self.selectSound = pygame.mixer.Sound(SELECTSOUNDFILE)
        self.powerupSound = pygame.mixer.Sound(POWERUPSOUNDFILE)

        # UI images

        # Button
        self.button = self.load_image(UIBUTTON).convert_alpha()
        self.buttonrect = self.button.get_rect()

        # Small Button
        self.smallButton = self.load_image(UIBUTTONSMALL).convert_alpha()
        self.smallButtonrect = self.smallButton.get_rect()

        # Slider
        self.slider = self.load_image(UISLIDER,0.7).convert_alpha()
        self.slidervalue = 0.9
        self.sliderrect = self.slider.get_rect()

        # Knob
        self.knob = self.load_image(UIKNOB,0.7).convert_alpha()
        self.knobrect = self.knob.get_rect()
        self.knobrect.move_ip(self.slidervalue * self.sliderrect.width,0)
        
        # UI text

        self.txt = {"label":{"font":pygame.font.SysFont("Arial",int(scale_val(40))),
                             "colour":WHITE,"anti-alias":True,
                             "Sound: ":None},
                    "button":{"font":pygame.font.SysFont("Arial",int(scale_val(60))),
                              "colour":WHITE,"anti-alias":True,
                              "Play":None,"Options":None,"Back":None,"Exit":None},
                    "title":{"font":pygame.font.SysFont("Arial",int(scale_val(200)),
                                                        bold=True),
                             "colour":(51,255,0),"anti-alias":True,
                             "Retro Parkourer":None},
                    "subtitle":{"font":pygame.font.SysFont("Arial",int(scale_val(100)),
                                                           bold=True),
                                "colour":WHITE,"anti-alias":True,
                                "Options":None,"Pause":None}}

        for key in self.txt:
            for msg in self.txt[key]:
                if self.txt[key][msg] == None:
                    self.txt[key][msg] = self.txt[key]["font"].render(msg,
                                                                      self.txt[key]["anti-alias"],
                                                                      self.txt[key]["colour"])

    def load_image(self,filename,scale=1) -> pygame.Surface:
        """ Return the image scaled to the correct dimensions. """
        img = pygame.image.load(filename)
        return pygame.transform.scale(img,
                                      (int(scale_val(img.get_width()) * scale),
                                       int(scale_val(img.get_height()) * scale)))

    def load_level(self,file):
        with open(file,"r") as f:
            level = f.read()

        self.world = World(level,SIZE // 2,WHITE)
        self.player = Player(pygame.Rect(self.world.start.x,
                                         self.world.start.y+SIZE // 3,
                                         SIZE // 3,SIZE // 3),
                             self.world)
        self.playerPlain = pygame.sprite.RenderPlain(self.player)

    def startloop(self):
        """ Draw the start screen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Title
        self.screen.blit(self.txt["title"]["Retro Parkourer"],
                         (scale_val(800) - \
                          self.txt["title"]["Retro Parkourer"].get_rect().centerx,
                          scale_val(150) - \
                          self.txt["title"]["Retro Parkourer"].get_rect().centery))

        # Buttons
        playButton = self.screen.blit(self.button,
                                      (scale_val(800) - self.buttonrect.centerx,
                                       scale_val(450) - self.buttonrect.centery))
        self.screen.blit(self.txt["button"]["Play"],
                         (scale_val(800) - \
                          self.txt["button"]["Play"].get_rect().centerx,
                          scale_val(450) - \
                          self.txt["button"]["Play"].get_rect().centery))

        optbutton = self.screen.blit(self.button,
                                      (scale_val(800) - self.buttonrect.centerx,
                                       scale_val(600) - self.buttonrect.centery))
        self.screen.blit(self.txt["button"]["Options"],
                         (scale_val(800) - \
                          self.txt["button"]["Options"].get_rect().centerx,
                          scale_val(600) - \
                          self.txt["button"]["Options"].get_rect().centery))
        
        if pygame.mouse.get_pressed()[0]:
            if playButton.collidepoint(pygame.mouse.get_pos()):
                self.player.startTime = pygame.time.get_ticks()
                self.selectSound.play()
                self.update = self.levelloop
                self.previous = self.startloop
            elif optbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                self.update = self.optionsloop
                self.previous = self.startloop
    
    def optionsloop(self):
        """ Draw the options screen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        self.screen.blit(self.txt["subtitle"]["Options"],
                         (scale_val(800) - \
                          self.txt["subtitle"]["Options"].get_rect().centerx,
                          scale_val(60) - \
                          self.txt["subtitle"]["Options"].get_rect().centery))

        backButton = self.screen.blit(self.smallButton,(scale_val(16),scale_val(9)))
        self.screen.blit(self.txt["button"]["Back"],
                         (scale_val(22) + self.txt["button"]["Back"].get_rect().centerx,
                          scale_val(4) + self.txt["button"]["Back"].get_rect().centery))

        slider = self.screen.blit(self.slider,(scale_val(800) - self.sliderrect.centerx,
                                               scale_val(180) - self.sliderrect.centery))
        self.screen.blit(self.txt["label"]["Sound: "],
                         (scale_val(727) - \
                          self.txt["label"]["Sound: "].get_rect().centerx - self.sliderrect.centerx,
                          scale_val(180) - self.txt["label"]["Sound: "].get_rect().centery))
        soundKnob = self.screen.blit(self.knob,(scale_val(800) - self.sliderrect.centerx + self.knobrect.x,
                                                scale_val(180) - self.knobrect.centery))
        
        if pygame.mouse.get_pressed()[0]:
             if backButton.collidepoint(pygame.mouse.get_pos()):
                 self.selectSound.play()
                 self.update = self.previous
                 self.previous = self.optionsloop
             elif soundKnob.collidepoint(pygame.mouse.get_pos()):
                 if self.mousepos:
                     dx = pygame.mouse.get_pos()[0] - self.mousepos[0]
                     if self.sliderrect.contains(self.knobrect.move(dx,0)):
                         self.knobrect.move_ip(dx,0)
                
                 self.mousepos = pygame.mouse.get_pos()
                 
                 self.slidervalue = self.knobrect.x / self.sliderrect.width
                 self.jumpSound.set_volume(self.slidervalue * 1.121)
                 self.selectSound.set_volume(self.slidervalue * 1.121)
        else:
            self.mousepos = None

    def levelloop(self):
        """ Draw the level and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))
        
        # Check for held keys
        key_state = pygame.key.get_pressed()

        if key_state[K_LEFT]:
            self.player.left()
        elif key_state[K_RIGHT]:
            self.player.right()

        if key_state[K_UP] and \
           self.world.collided(self.player.rect.move(0,GRAVITY)) and \
           self.player.velocity == 0:

            self.player.startTime = pygame.time.get_ticks()
            self.player.velocity = JUMPSPEED

            self.jumpSound.play()

        self.player.gravity()

        # Draw the world and player
        self.world.update(self.screen)
        self.playerPlain.draw(self.screen)

        if self.world.end.contains(self.player.rect):
            self.powerupSound.play()
            self.level += 1
            if self.level > 3:
                self.level = 1
                self.load_level("./levels/level{}.txt".format(self.level))
                self.update = self.startloop
            else:
                self.load_level("./levels/level{}.txt".format(self.level))

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_p:
                    self.update = self.pauseloop
                    self.previous = self.levelloop

    def pauseloop(self):
        """ Draw the pausescreen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Draw the world and player
        self.world.update(self.screen)
        self.playerPlain.draw(self.screen)

        self.screen.blit(self.txt["subtitle"]["Pause"],
                         (scale_val(800) - \
                          self.txt["subtitle"]["Pause"].get_rect().centerx,
                          scale_val(60) - \
                          self.txt["subtitle"]["Pause"].get_rect().centery))

        playButton = self.screen.blit(self.button,
                                      (scale_val(800) - self.buttonrect.centerx,
                                       scale_val(225) - self.buttonrect.centery))
        self.screen.blit(self.txt["button"]["Play"],
                         (scale_val(800) - \
                          self.txt["button"]["Play"].get_rect().centerx,
                          scale_val(225) - \
                          self.txt["button"]["Play"].get_rect().centery))

        optbutton = self.screen.blit(self.button,
                                      (scale_val(800) - self.buttonrect.centerx,
                                       scale_val(375) - self.buttonrect.centery))
        self.screen.blit(self.txt["button"]["Options"],
                         (scale_val(800) - \
                          self.txt["button"]["Options"].get_rect().centerx,
                          scale_val(375) - \
                          self.txt["button"]["Options"].get_rect().centery))

        exitbutton = self.screen.blit(self.button,
                                      (scale_val(800) - self.buttonrect.centerx,
                                       scale_val(525) - self.buttonrect.centery))

        self.screen.blit(self.txt["button"]["Exit"],
                         (scale_val(800) - \
                          self.txt["button"]["Exit"].get_rect().centerx,
                          scale_val(525) - \
                          self.txt["button"]["Exit"].get_rect().centery))

        
        self.player.startTime = pygame.time.get_ticks() - \
                                (self.player.time * (62.5*self.player.framedur))

        if pygame.mouse.get_pressed()[0]:
            if playButton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.update = self.levelloop
                self.previous = self.pauseloop
            elif optbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.update = self.optionsloop
                self.previous = self.pauseloop
            elif exitbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.level = 1
                self.load_level("./levels/level{}.txt".format(self.level))
                
                self.update = self.startloop
                self.previous = self.pauseloop

        # Check for keys
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_p:
                    self.update = self.levelloop
                    self.previous = self.pauseloop

def scale_val(value) -> int:
    return int(value / 100 * SIZE)

def main():
    # Sounds
    pygame.mixer.pre_init(44100,-16,8,2048)
    pygame.mixer.init()

    # Window
    pygame.init()
    
    pygame.display.set_caption("Platformer")
    pygame.display.set_mode((WIDTH,HEIGHT),DOUBLEBUF)

    # Fonts
    pygame.font.init()

    game = Game()
    
    clock = pygame.time.Clock()
    
    run = True
    windowed = True
    pygame.event.set_allowed([QUIT, KEYDOWN])
    
    while run:
        # Check for keypresses
        for event in pygame.event.get():
            if event.type == QUIT: 
                run = False # Close the window
            elif event.type == KEYDOWN:
                if event.key == K_q and event.mod & KMOD_CTRL:
                    run = False # Close the window
                elif event.key == K_F11: # Toggle fullscreen
                    windowed ^= pygame.display.toggle_fullscreen()
                elif event.key == K_ESCAPE and not windowed: # Exit fullscreen
                    windowed ^= pygame.display.toggle_fullscreen()

        game.update()
        pygame.display.update()
        game.player.framedur = clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
