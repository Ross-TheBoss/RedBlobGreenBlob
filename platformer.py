#!/usr/bin/env python3
"""
Retro Parkourer

A simple platformer game by Ross Watts.
"""

import pygame
import random
import os
import configparser

from pygame.constants import *
# 16:9 aspect ratio
# Native resolution of 100
SIZE = 105 # Monitor = 105
WIDTH = 16 * SIZE
HEIGHT = 9 * SIZE
MOVETHRESHOLD = int(SIZE)

# Units pixels per 1/60 seconds

# Velocity
SPEED = 7 # 420 pixels / second
JUMPSPEED = 9 # 540 pixels / second

# Acceleration
GRAVITY = 20 # 1200 pixels / second / second

# Directories

SOUNDDIR = "sounds"
IMGDIR = "images"
LEVELDIR = "levels"

# 8-bit Platformer SFX commissioned by Mark McCorkle for OpenGameArt.org ( http://opengameart.org )
JUMPSOUNDFILE = os.path.join(SOUNDDIR,"jump.ogg")
SELECTSOUNDFILE = os.path.join(SOUNDDIR,"select.ogg")
POWERUPSOUNDFILE = os.path.join(SOUNDDIR,"powerup.ogg")
DESTROYSOUNDFILE = os.path.join(SOUNDDIR,"destroy.ogg") # Orginally Explosion.wav

EXPLODEDPLAYER = os.path.join(IMGDIR,"exploded.png")

PLATETILE = 0
TOPTILE = 1
ANITILE = 2
VARTILE = 3

TILECOLLIDE = 0b1
TILEDEADLY = 0b10
TILEALPHA = 0b100

TILES = [{"type":TOPTILE,"flags":TILECOLLIDE,"files":["grass.png","grassc.png","grassp.png"]},
         {"type":PLATETILE,"flags":TILECOLLIDE,"files":["dirt.png"]},
         {"type":TOPTILE,"flags":TILECOLLIDE,"files":["metal.png","metalc.png","metalp.png"]},
         {"type":PLATETILE,"flags":TILECOLLIDE,"files":["metala.png"]},
         {"type":PLATETILE,"flags":TILECOLLIDE,"files":["plate.png"]},
         {"type":ANITILE,"flags":TILEDEADLY | TILEALPHA,
          "files":["lava.png","lava1.png","lava2.png","lava3.png","lava4.png"]},
         {"type":VARTILE,"flags":TILECOLLIDE,"files":["stone.png","stone1.png","stone2.png"]}]

for tile in TILES:
    tile.update({"files":list(map(lambda name: os.path.join(IMGDIR,name),tile["files"]))})

UIBUTTON = os.path.join(IMGDIR,"button.png")
UIBUTTONSMALL = os.path.join(IMGDIR,"smallbutton.png")
UIBUTTONMINI = os.path.join(IMGDIR,"minibutton.png")
UISLIDER = os.path.join(IMGDIR,"slider.png")
UIKNOB = os.path.join(IMGDIR,"knob.png")
UION = os.path.join(IMGDIR,"on.png")
UIOFF = os.path.join(IMGDIR,"off.png")

BACKGROUND = os.path.join(IMGDIR,"background.png")

# Colours

WHITE = (255,255,255)
GREEN = (255,0,0)
        


class World():
    def __init__(self,level: str,blockSize: int,colour: tuple):
        """ Load the level (a list of lines of text) onto the screen. """
        self.items = []
        self.colour = colour
        self.blockSize = blockSize

        # Relative x and y coordinates.
        self.relx = 0
        self.rely = 0

        # Checkpoint scrolling x and y coordinates.
        self.checkx = 0
        self.checky = 0

        self.width = level.index("\n")
        self.height = len(level) // self.width
        self.scrollWidth = self.width * self.blockSize
        self.scrollHeight = self.height * self.blockSize

        # Prepare all the tiles in the game.

        # Start, End and Checkpoint (0,1,2)
        self.tiles = [[pygame.surface.Surface([self.blockSize,self.blockSize])],
                      [pygame.surface.Surface([self.blockSize,self.blockSize])],
                      [pygame.surface.Surface([self.blockSize,self.blockSize])]]
        self.tiles[0][0].fill((0,255,0))
        self.tiles[1][0].fill((0,255,0))
        self.tiles[2][0].fill((0,200,0))
        # 5 Placeholders (2,3,4,5,6,7)
        self.tiles += [[pygame.surface.Surface([self.blockSize,self.blockSize])]] * 5
        # 8 Grass tile variations (8)
        self.tiles += [self.load_tile(TILES[0])]
        # 1 Dirt tile (9)
        self.tiles += [self.load_tile(TILES[1])]
        # 8 Metal tile variations (10)
        self.tiles += [self.load_tile(TILES[2])]
        # 1 Metal tile (11)
        self.tiles += [self.load_tile(TILES[3])]
        # 1 Plate tile (12)
        self.tiles += [self.load_tile(TILES[4])]
        # 3 Lava tiles (13)
        self.tiles += [self.load_tile(TILES[5])]
        # 1 Stone tiles (14)
        self.tiles += [self.load_tile(TILES[6])]

        # Orientations of directional tiles
        dirtiles = list(map(lambda x: self.parse_tile(level,chr(x[0] + 48)) if x[1]["type"] == TOPTILE else None,
                            enumerate(TILES)))

        # Tiles that won't be collided with. (air, background decor, etc. )
        bgtiles = list(filter(None,map(lambda x: False if x[1]["flags"] & TILECOLLIDE else chr(x[0] + 48),
                                       enumerate(TILES))))
            

        # Non-directionals
        for i,block in enumerate(level):
            x = i % (self.width + 1)
            y = i // (self.width + 1)

            if not block in [" ","\n"]:
                if ord(block) - 48 >= 0 and TILES[ord(block) - 48]["type"] == TOPTILE:
                    direction = int(dirtiles[ord(block) - 48][i])
                else:
                    direction = 0
                
                self.items.append({"type":ord(block) - 32,
                                   "dir":direction,
                                   "collision":self.has_collisions(bgtiles,level,i),
                                   "rect":pygame.Rect(
                                       x*self.blockSize,
                                       y*self.blockSize,
                                       self.blockSize,self.blockSize),
                                   })

        self.animate(VARTILE)
        self.animate()

        # The checkpoint
        self.check = self.start

        if self.start.x > (WIDTH // 2 + MOVETHRESHOLD):
            self.move_x(-(self.start.x - (WIDTH // 2 + MOVETHRESHOLD)))
            self.checkx = self.relx

        if self.scrollHeight - self.start.y > (HEIGHT // 2 + MOVETHRESHOLD):
            self.move_y((self.scrollHeight - self.start.y)-\
                        (HEIGHT // 2 + MOVETHRESHOLD))
            self.checky = self.rely
        
        if self.scrollHeight > HEIGHT:
            self.move_y(-(self.scrollHeight-HEIGHT))
            self.rely = self.rely - (self.scrollHeight-HEIGHT)
            
    @property
    def start(self):
        """ The start tile of the level."""
        return next(filter(lambda i: i["type"] == 8,self.items))["rect"]

    @property
    def end(self):
        """ The end tile of the level."""
        return next(filter(lambda i: i["type"] == 9,self.items))["rect"]

    def has_collisions(self,bgtiles,level,i):
        """ Return whether a tile should be able to be collided with. """
        above = level[i - (self.width + 1)] if i - (self.width + 1) > 0 else "\x00"
        left = level[i - 1] if i - 1 > 0 else "\x00"
        below = level[i + (self.width + 1)] if i + (self.width + 1) < len(level) else "\x00"
        right = level[i + 1] if i + 1 < len(level) else "\x00"

        if ord(level[i]) - 32 < 0x10 or \
           not (TILES[max(0,ord(level[i]) - 48)]["flags"] & TILECOLLIDE):
            return False
        elif any(map(lambda x: x in ["\x00"," ","(",")","*"] + bgtiles,
                     [above,left,below,right])):
            return True
        else:
            return False

    def load_tile(self,tile):
        """ Return a all of a tile variations. """
        if tile["type"] == PLATETILE:
            imgs = [self.load_image(tile["files"][0])]
        elif tile["type"] == TOPTILE:
            imgs = [self.load_image(tile["files"][0])]
            imgs += [pygame.transform.rotate(imgs[0],-90),
                     pygame.transform.rotate(imgs[0],-180),
                     pygame.transform.rotate(imgs[0],-270)]
            imgs += [self.load_image(tile["files"][1])]
            imgs += [pygame.transform.rotate(imgs[4],-90)]
            imgs += [self.load_image(tile["files"][2])]
            imgs += [pygame.transform.rotate(imgs[6],-90)]
        elif tile["type"] == ANITILE or tile["type"] == VARTILE:
            imgs = list(map(self.load_image,tile["files"]))

        if tile["flags"] & TILEALPHA:
            imgs = list(map(lambda i:i.convert_alpha(),imgs))
        else:
            imgs = list(map(lambda i:i.convert(),imgs))

        return imgs

    def parse_tile(self,level,tile):
        """ Return the orientation of directional tiles. """
        leveltiles = "".join(map(lambda x: "0" if x == tile else " ",level))

        for i,block in enumerate(leveltiles):
            if block != " ":
                above = leveltiles[i - (self.width + 1)] if i - (self.width + 1) > 0 else "\x00"
                left = leveltiles[i - 1] if i - 1 > 0 else "\x00"
                below = leveltiles[i + (self.width + 1)] if i + (self.width + 1) < len(leveltiles) else "\x00"
                right = leveltiles[i + 1] if i + 1 < len(leveltiles) else "\x00"
                
                if below == "0" and right in ["0","6"]:
                    leveltiles = leveltiles[:i] + "4" + leveltiles[i + 1:]
                elif below == "0" and left in ["0","7"]:
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
        

    def load_image(self, file) -> pygame.Surface:
        """ Return a correctly scaled image. """
        return pygame.transform.scale(pygame.image.load(file),
                                      (self.blockSize,self.blockSize),
                                      )

    def get_movement(self, player: pygame.Rect, movement: int):
        """ Return how far the rect can be moved (in the x-axis) before colliding or reaching max. """
        collision = self.collided(player.move(movement,0))
        if collision:
            if movement > 0:
                # Moving right
                movement = collision.left - player.right
            else:
                # Moving left
                movement =  collision.right - player.left

        return movement
        
    def collided(self, player: pygame.Rect):
        """ Return the rectangle the player rectangle is colliding with. """
        
        blocks = list(map(lambda i: i["rect"],
                          filter(lambda b: b["collision"],
                                 self.items)))
        index = player.collidelist(blocks)
        if index != -1:
            return blocks[index]

        barriers = [pygame.Rect(-SIZE*100,0,SIZE*100,HEIGHT),
                    pygame.Rect(WIDTH,0,SIZE*100,HEIGHT)]
        index = player.collidelist(barriers[:2])
        if index != -1:
            return barriers[index]
        
        return False
        

    def failed(self,player: pygame.Rect):
        """ Return whether the player collided with a deadly object. """
        void = pygame.Rect(0,HEIGHT,WIDTH,SIZE)
        blocks = list(map(lambda i: i["rect"],
                          filter(lambda b: b["type"] - 16 >= 0 and \
                                 TILES[b["type"] - 16]["flags"] & TILEDEADLY,
                                 self.items)))
        
        if player.collidelist([void] + blocks) != -1:
            return True
        else:
            return False

    def at_checkpoint(self,player: pygame.Rect):
        blocks = list(map(lambda i: i["rect"],
                          filter(lambda b: b["type"] == 10,
                                 self.items)))

        i = player.collidelist(blocks)
        if i != -1 and self.check != blocks[i]:
            self.checkx = self.relx
            self.checky = self.rely

            self.check = blocks[i]
            return True
        else:
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
            return (self.tiles[block["type"] - 0x8][block["dir"]],
                    block["rect"].topleft)
        else:
            return False

    def animate(self,_type=ANITILE):
        """ Animate the tiles. """
        for i,v in enumerate(self.items):
            if TILES[max(v["type"] - 0x10,0)]["type"] == _type:
                self.items[i]["dir"] = random.randint(0,len(TILES[v["type"] - 0x10]["files"])-1)
        
    def update(self,screen: pygame.Surface):
        """ Draw the world onto the screen. """
        screen.blits(list(filter(None,map(self.valid_rect,self.items))))

class Player(pygame.sprite.Sprite):
    def __init__(self,rect: pygame.Rect,world: World):
        """ Draw and control the player with realistic physics. """
        super().__init__()
        self.rect = rect
        self.world = world
        self.particles = []

        self.image = pygame.surface.Surface([rect.width,rect.height]).convert()
        self.image.fill((255,0,0))

        # Ground time (time when the player had ground beneath them.)
        self.groundTime = pygame.time.get_ticks()

        # 60 fps frame duration
        self.framedur = 16

        # Initial velocity for gravity
        self.gravVel = 0

    def get_velocity(self, acceleration: float, time: float, velocity: float) -> int:
        """
        Return the velocity given the acceleration, initial velocity and time.
        Uses the equation - v = a * dt + u 
        """
        return scale_val((acceleration * get_interval(time) + velocity) \
                         * self.framedur / 16)

    def right(self, m):
        """ Move the player right by the magnetude (m). """
        movement = self.world.get_movement(self.rect,
                                           scale_val(m * self.framedur / 16))

        # Camera scrolling
        
        if self.rect.centerx > (WIDTH // 2) + MOVETHRESHOLD and \
           self.world.scrollWidth - WIDTH > self.world.relx:
            self.world.move_x(-movement)
            self.particles = list(map(lambda p: p.move(-movement,0),
                                      self.particles))
        else:
            self.rect.move_ip(movement,0)

        if self.world.collided(self.rect.move(0,1)) and movement > (SPEED / 2):
            for i in range(2):
                size = scale_val(random.randint(7,10))
                self.particles.append(pygame.Rect(self.rect.centerx+(i*movement)/2,
                                                  self.rect.bottom,size,size))
                
    def left(self, m):
        """ Move the player left by the magnetude (m). """
        movement = self.world.get_movement(self.rect,
                                           scale_val(-m * self.framedur / 16))

        # Camera scrolling
        
        if self.rect.centerx < (WIDTH // 2) - MOVETHRESHOLD and \
           self.world.relx > 0:
            self.world.move_x(-movement)
            self.particles = list(map(lambda p: p.move(-movement,0),
                                      self.particles))
        else:
            self.rect.move_ip(movement,0)

        if self.world.collided(self.rect.move(0,1)) and movement < (-SPEED / 2):
            for i in range(2):
                size = scale_val(random.randint(7,10))
                self.particles.append(pygame.Rect(self.rect.centerx+(i*movement)/2,
                                                  self.rect.bottom,size,size))

       

    def move_x(self, m):
        """ Move the player in the x axis by the magnetude (m) considering collisions. """
        movement = self.world.get_movement(self.rect,
                                           scale_val(m * self.framedur / 16))

        if m > 0:
            if self.rect.centerx > (WIDTH // 2) + MOVETHRESHOLD and \
               self.world.scrollWidth - WIDTH > self.world.relx:
                self.world.move_x(-movement)
            else:
                self.rect.move_ip(movement,0)
        else:
             if self.rect.centerx < (WIDTH // 2) - MOVETHRESHOLD and \
                self.world.relx > 0:
                 self.world.move_x(-movement)
             else:
                self.rect.move_ip(movement,0)
        
    def gravity(self):
        """ Apply the force of gravity onto the player. """
        dy = self.get_velocity(GRAVITY,self.groundTime,-self.gravVel)
        
        # Check if the player is moving upwards.
        if self.gravVel > 0:
            # Check if the peak point has been reached.
            collision = self.world.collided(self.rect.move(0,dy))
            if get_interval(self.groundTime) >= -(self.gravVel / -GRAVITY):
                self.gravVel = 0
                self.groundTime = pygame.time.get_ticks()
                dy = 0
            elif collision:
                self.gravVel = 0
                self.groundTime = pygame.time.get_ticks()
                dy = collision.bottom - self.rect.top
        
        # Calculate if a block will be hit.
        collision = self.world.collided(self.rect.move(0,dy))
        if collision:
            self.groundTime = pygame.time.get_ticks()
            movement = collision.top - self.rect.bottom
        else:
            movement = dy

        if self.rect.centery < (HEIGHT // 2) - MOVETHRESHOLD and \
           self.world.scrollHeight - HEIGHT > self.world.rely and \
           movement < 0:
            self.world.move_y(-movement)
            self.particles = list(map(lambda p: p.move(0,-movement),
                                      self.particles))
        elif self.rect.centery > (HEIGHT // 2) + MOVETHRESHOLD and \
             self.world.rely < 0 and \
             movement > 0:
            self.world.move_y(-movement)
            self.particles = list(map(lambda p: p.move(0,-movement),
                                      self.particles))
        else:
            self.rect.move_ip(0,movement)

    def draw_particles(self,screen: pygame.Surface):
        """ Draw particles under the player. """
        for i,particle in enumerate(self.particles):
                if particle.width != 0:
                    shade = max(0,200 - (len(self.particles)-i)*8)
                    self.particles[i].width *= 0.95
                    self.particles[i].height *= 0.95
                    pygame.draw.rect(screen,(shade,0,0),particle)

class Game():
    LEVELLOCATION = "./levels/level{}.txt"
    def __init__(self,config: configparser.ConfigParser):
        """ Control the UI of the game. """
        # Config file
        self.config = config
        
        # The current function to run every update.
        self.update = self.startloop
        # The previous function that was run each update.
        self.previous = self.startloop
        self.screen = pygame.display.get_surface()
        
        # Graphics
        self.lvl = 1
        self.deaths = 0
        self.load_level(self.LEVELLOCATION.format(self.lvl))
        

        self.mousepos = None

        self.failclock = 0
        self.pausetime = 0

        # Sounds
        self.jumpSound = pygame.mixer.Sound(JUMPSOUNDFILE)
        self.selectSound = pygame.mixer.Sound(SELECTSOUNDFILE)
        self.powerupSound = pygame.mixer.Sound(POWERUPSOUNDFILE)
        self.destroySound = pygame.mixer.Sound(DESTROYSOUNDFILE)

        self.jumpChl = pygame.mixer.Channel(1)

        # Images

        # Player

        self.expPlayer = self.load_image(EXPLODEDPLAYER,1/1.5)
        self.expPlayerrect = self.expPlayer.get_rect()

        # Background - streched to cover the screen.

        self.background = pygame.transform.scale(pygame.image.load(BACKGROUND),
                                                 (WIDTH,HEIGHT)).convert()
        
        # UI

        # Button
        self.button, self.buttonrect = self.load_ui(UIBUTTON,alpha=True)

        # Small Button
        self.smallButton, self.smallButtonrect = self.load_ui(UIBUTTONSMALL,
                                                              alpha=True)

        # Mini Button
        self.miniButton, self.miniButtonrect = self.load_ui(UIBUTTONMINI,
                                                            alpha=True)
        
        # Slider
        self.slider, self.sliderrect = self.load_ui(UISLIDER,scale=0.7,
                                                    alpha=True)
        self.slidervalue = (self.config["DEFAULT"].getint("volume",100) / 100)

        self.jumpSound.set_volume(self.slidervalue)
        self.selectSound.set_volume(self.slidervalue)
        self.destroySound.set_volume(self.slidervalue)
        self.powerupSound.set_volume(self.slidervalue)
        
        # Switch on
        self.switchOn, self.switchOnrect = self.load_ui(UION,scale=0.7,
                                                        alpha=True)

        # Switch off
        self.switchOff, self.switchOffrect = self.load_ui(UIOFF,scale=0.7,
                                                          alpha=True)
        self.timerBool = self.config["DEFAULT"].getboolean("timer",True)
        self.particleBool = self.config["DEFAULT"].getboolean("particles",True)

        # Knob
        self.knob, self.knobrect = self.load_ui(UIKNOB,scale=0.7,alpha=True)
        self.knobrect.move_ip(self.slidervalue / 1.121 * self.sliderrect.width,0)
        
        # UI text

        self.txt = {"label":{"font":pygame.font.SysFont("Arial",int(scale_val(40))),
                             "colour":WHITE,"anti-alias":True,
                             "Sound: ":None,"Timer: ":None,"Particles: ":None},
                    "button":{"font":pygame.font.SysFont("Arial",int(scale_val(60))),
                              "colour":WHITE,"anti-alias":True,
                              "Play":None,"Options":None,"Back":None,"Exit":None,
                              "Level Select":None,"Save":None,"Continue":None,
                              "Restart":None,"Deaths: ":None,"Time: ":None},
                    "title":{"font":pygame.font.SysFont("Arial",int(scale_val(200)),
                                                        bold=True),
                             "colour":(51,255,0),"anti-alias":True,
                             "Retro Parkourer":None},
                    "subtitle":{"font":pygame.font.SysFont("Arial",int(scale_val(100)),
                                                           bold=True),
                                "colour":WHITE,"anti-alias":True,
                                "Options":None,"Pause":None,"Level Select":None,
                                "Level Complete":None}}
        
        for i in range(len(os.listdir(LEVELDIR))):
            self.txt["button"][str(i+1)] = None
        
        for key in self.txt:
            for msg in self.txt[key]:
                if self.txt[key][msg] == None:
                    self.txt[key][msg] = self.txt[key]["font"].render(msg,
                                                                      self.txt[key]["anti-alias"],
                                                                      self.txt[key]["colour"])

        # Timer
        self.timertxt = self.txt["button"]["font"].render("0",
                                                         self.txt["button"]["anti-alias"],
                                                         self.txt["button"]["colour"])
        # Deaths
        self.deathtxt = self.txt["button"]["font"].render("0",
                                                          self.txt["button"]["anti-alias"],
                                                          self.txt["button"]["colour"])
    def blit_centered(self,surface: pygame.Surface,x,y):
        """ Blit the surface to the screen centered around x and y. """
        return self.screen.blit(surface,(scale_val(x) - surface.get_rect().centerx,
                                         scale_val(y) - surface.get_rect().centery))
        
    def load_ui(self,filename,scale=1,alpha=False):
        """ Return the image and assiated rect for the image. """
        element = self.load_image(filename,scale)
        if alpha:
            element = element.convert_alpha()
        else:
            element = element.convert()
        
        return element, element.get_rect()

        

    def load_image(self,filename,scale=1) -> pygame.Surface:
        """ Return the image scaled to the correct dimensions. """
        img = pygame.image.load(filename)
        return pygame.transform.scale(img,
                                      (int(scale_val(img.get_width()) * scale),
                                       int(scale_val(img.get_height()) * scale)))

    def load_level(self,file):
        with open(file,"r") as f:
            level = f.read()

        self.deaths = 0
        self.levelclock = pygame.time.get_ticks()
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

        # Background
        self.screen.blit(self.background,(0,0))

        # Title
        self.blit_centered(self.txt["title"]["Retro Parkourer"],800,150)

        # Play button
        playButton = self.blit_centered(self.button,800,450)
        self.blit_centered(self.txt["button"]["Play"],800,450)

        # Options button
        optbutton = self.blit_centered(self.button,800,600)
        self.blit_centered(self.txt["button"]["Options"],800,600)
        
        # Level selection button
        levelbutton = self.blit_centered(self.button,800,750)
        self.blit_centered(self.txt["button"]["Level Select"],800,750)
        
        if pygame.mouse.get_pressed()[0]:
            if playButton.collidepoint(pygame.mouse.get_pos()):
                self.load_level(self.LEVELLOCATION.format(self.lvl))
                self.player.groundTime = pygame.time.get_ticks()
                self.levelclock = pygame.time.get_ticks()
                self.selectSound.play()
                self.update = self.level
                self.previous = self.startloop
            elif optbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                self.update = self.options
                self.previous = self.startloop
            elif levelbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                self.update = self.levelselect
                self.previous = self.startloop
    
    def options(self):
        """ Draw the options screen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        if self.previous == self.startloop:
            # Background
            self.screen.blit(self.background,(0,0))

        # Title
        self.blit_centered(self.txt["subtitle"]["Options"],800,60)

        # Back button
        backButton = self.screen.blit(self.smallButton,(scale_val(16),scale_val(9)))
        self.screen.blit(self.txt["button"]["Back"],
                         (scale_val(22) + self.txt["button"]["Back"].get_rect().centerx,
                          scale_val(4) + self.txt["button"]["Back"].get_rect().centery))

        # Save button
        # Unscale the height and take 104 away from it -
        # the save button is positioned based on
        # where the bottom of the screen is.
        saveButton = self.blit_centered(self.button,800,
                                        (HEIGHT / SIZE * 100) - 104)
        self.blit_centered(self.txt["button"]["Save"],800,
                           (HEIGHT / SIZE * 100) - 104)
        
        # Options - Starting at x=392,y=136
        
        # Sound slider
        slider = self.screen.blit(self.slider,(scale_val(800) - self.sliderrect.centerx,
                                               scale_val(180) - self.sliderrect.centery))
        self.screen.blit(self.txt["label"]["Sound: "],
                         (scale_val(392) - \
                          self.txt["label"]["Sound: "].get_rect().right,
                          scale_val(180) - self.txt["label"]["Sound: "].get_rect().centery))
        soundKnob = self.screen.blit(self.knob,(scale_val(800) - self.sliderrect.centerx + self.knobrect.x,
                                                scale_val(180) - self.knobrect.centery))

        # Turn on/off timer
        if self.timerBool:
            timerSwitch = self.screen.blit(self.switchOn,(scale_val(392),
                                                          scale_val(285) - self.switchOnrect.centery))
        else:
            timerSwitch = self.screen.blit(self.switchOff,(scale_val(392),
                                                           scale_val(285) - self.switchOnrect.centery))
        self.screen.blit(self.txt["label"]["Timer: "],
                         (scale_val(392) - self.txt["label"]["Timer: "].get_rect().right,
                          scale_val(285) - self.txt["label"]["Timer: "].get_rect().centery))
        
        # Turn on/off particles
        if self.particleBool:
            particleSwitch = self.screen.blit(self.switchOn,(scale_val(792),
                                                             scale_val(285) - self.switchOnrect.centery))
        else:
            particleSwitch = self.screen.blit(self.switchOff,(scale_val(792),
                                                              scale_val(285) - self.switchOnrect.centery))

        self.screen.blit(self.txt["label"]["Particles: "],
                         (scale_val(792) - self.txt["label"]["Particles: "].get_rect().right,
                          scale_val(285) - self.txt["label"]["Particles: "].get_rect().centery))

        # Check if buttons have been clicked.
        if pygame.mouse.get_pressed()[0]:
             if backButton.collidepoint(pygame.mouse.get_pos()):
                 # Back button clicked - go to main menu.
                 self.selectSound.play()
                 self.update = self.previous
                 self.previous = self.options
             elif saveButton.collidepoint(pygame.mouse.get_pos()):
                 # Save button clicked - save the settings the config file.
                 self.selectSound.play()
                 with open("options.ini","w") as conf:
                     self.config.write(conf)
                 pygame.time.wait(100)
                
             elif soundKnob.collidepoint(pygame.mouse.get_pos()):
                 # Sound knob clicked - slide the sound slider.
                 if self.mousepos:
                     dx = pygame.mouse.get_pos()[0] - self.mousepos[0]
                     if self.sliderrect.contains(self.knobrect.move(dx,0)):
                         self.knobrect.move_ip(dx,0)
                
                 self.mousepos = pygame.mouse.get_pos()
                 
                 self.slidervalue = (self.knobrect.x / self.sliderrect.width) * 1.121
                 
                 self.jumpSound.set_volume(self.slidervalue)
                 self.selectSound.set_volume(self.slidervalue)
                 self.destroySound.set_volume(self.slidervalue)
                 self.powerupSound.set_volume(self.slidervalue)

                 self.config["DEFAULT"]["volume"] = str(int(self.slidervalue * 100))
                 
             elif timerSwitch.collidepoint(pygame.mouse.get_pos()):
                 # Timer switch clicked - toggle whether to show the timer.
                 self.selectSound.play()
                 self.timerBool ^= True
                 self.config["DEFAULT"]["timer"] = str(self.timerBool).lower()
                 pygame.time.wait(100)
             elif particleSwitch.collidepoint(pygame.mouse.get_pos()):
                 # Particles switch clicked - toggle whether to show particles.
                 self.selectSound.play()
                 self.particleBool ^= True
                 self.config["DEFAULT"]["particles"] = str(self.timerBool).lower()
                 pygame.time.wait(100)
        else:
            self.mousepos = None

    def level(self):
        """ Draw the level and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Check for held keys
        key_state = pygame.key.get_pressed()

        # Left and Right movement and particles.
        if key_state[K_LEFT]:
            mv = self.player.left(SPEED)
        elif key_state[K_RIGHT]:
            mv = self.player.right(SPEED)
        else:
            self.player.particles.extend([pygame.Rect(0,0,0,0)])

        self.player.particles = self.player.particles[-20:]


        if key_state[K_UP]:
            if self.player.gravVel == 0:
                if self.world.collided(self.player.rect.move(0,1)):
                    self.player.groundTime = pygame.time.get_ticks()
                    self.player.gravVel = JUMPSPEED

                    if not self.jumpChl.get_busy():
                        self.jumpChl.play(self.jumpSound)
                

        # Draw the player and world
        self.world.update(self.screen)
        
        if self.failclock == 0:
            if self.world.failed(self.player.rect):
                self.player.gravity()
                 
                self.failclock = 1
                self.player.groundTime = pygame.time.get_ticks()
                self.player.gravVel = 0
            else:
                self.player.gravity()
                
                self.playerPlain.draw(self.screen)
        else:
            self.screen.blit(pygame.transform.rotate(self.expPlayer,random.randint(0,359)),
                                 (self.player.rect.x - self.expPlayerrect.centerx + \
                                  scale_val(random.randint(0,10)),
                                  self.player.rect.y - self.expPlayerrect.centery + \
                                  scale_val(random.randint(0,10))))

        if self.particleBool:
            self.player.draw_particles(self.screen)

        # Update the timer
        self.timertxt = self.txt["button"]["font"].render(str(round(get_interval(self.levelclock),1)),
                                                         self.txt["button"]["anti-alias"],
                                                         self.txt["button"]["colour"])
        if self.timerBool:
            self.screen.blit(self.timertxt,(0,0))
        

        # Play the sound when a checkpoint is reached.
        if self.world.at_checkpoint(self.player.rect):
            self.powerupSound.play()

        # Animate the world.
        if pygame.time.get_ticks() % 300 < self.player.framedur:
            self.world.animate()

        # Advance to the next level.
        if self.world.end.contains(self.player.rect):
            self.powerupSound.play()

            self.deathtxt = self.txt["button"]["font"].render(str(self.deaths),
                                                              self.txt["button"]["anti-alias"],
                                                              self.txt["button"]["colour"])
            self.update = self.levelcomplete
            self.previous = self.level

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_p:
                    self.pausetime = pygame.time.get_ticks()
                    self.update = self.pause
                    self.previous = self.level

        if self.failclock == 1:
            self.destroySound.play()
            self.player.groundTime = pygame.time.get_ticks()
            self.player.gravVel = 0
            self.deaths += 1
            self.failclock += 1
        elif 5 > self.failclock > 1:
            self.player.groundTime = pygame.time.get_ticks()
            self.player.gravVel = 0
            self.failclock += 1
        elif self.failclock == 5:
            self.failclock = 0
            pygame.time.delay(80)

            # Reset the world scrolling
            self.world.move_x(self.world.relx-self.world.checkx)
            self.world.move_y(self.world.rely-self.world.checky)
            
            # Reset the player
            self.player = Player(pygame.Rect(self.world.check.x,
                                             self.world.check.y+SIZE // 3,
                                             SIZE // 3,SIZE // 3),
                                 self.world)
            self.playerPlain = pygame.sprite.RenderPlain(self.player)

    def levelselect(self):
        """ Draw the level selection screen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Background
        self.screen.blit(self.background,(0,0))

        # Title
        self.blit_centered(self.txt["subtitle"]["Level Select"],800,60)

        # Back button
        backButton = self.screen.blit(self.smallButton,(scale_val(16),scale_val(9)))
        self.screen.blit(self.txt["button"]["Back"],
                         (scale_val(22) + self.txt["button"]["Back"].get_rect().centerx,
                          scale_val(4) + self.txt["button"]["Back"].get_rect().centery))
        
        gen = zip(*iter((x,y) for y in range(0,750,150) for x in range(0,900,150)))
        
        for x,y,lvl in zip(*gen,range(1,len(os.listdir(LEVELDIR))+1)):
            lvlButton = self.screen.blit(self.miniButton,(scale_val(350 + x),scale_val(158 + y)))
            self.screen.blit(self.txt["button"][str(lvl)],
                     (scale_val(378 + x) + self.txt["button"][str(lvl)].get_rect().centerx,
                      scale_val(154 + y) + self.txt["button"][str(lvl)].get_rect().centery))

            if pygame.mouse.get_pressed()[0] and \
               lvlButton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.lvl = lvl
                self.load_level(self.LEVELLOCATION.format(self.lvl))
                
                self.update = self.level
                self.previous = self.levelselect


        if pygame.mouse.get_pressed()[0]:
             if backButton.collidepoint(pygame.mouse.get_pos()):
                 self.selectSound.play()
                 
                 self.update = self.previous
                 self.previous = self.levelselect

    def levelcomplete(self):
        """ Draw the level completion screen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Draw the world and player
        self.world.update(self.screen)
        self.playerPlain.draw(self.screen)

        # Particles
        if self.particleBool:
            self.player.draw_particles(self.screen)

        # Title
        self.blit_centered(self.txt["subtitle"]["Level Complete"],800,60)

        # Time and Deaths displays
        self.screen.blit(self.txt["button"]["Deaths: "],
                         (scale_val(840) - (self.buttonrect.w / 2),
                          scale_val(200) - self.txt["button"]["Deaths: "].get_rect().centery))
        self.screen.blit(self.deathtxt,
                         (scale_val(1070) - (self.buttonrect.w / 2),
                          scale_val(200) - self.deathtxt.get_rect().centery))
        
        self.screen.blit(self.txt["button"]["Time: "],
                         (scale_val(1240) - (self.buttonrect.w / 2),
                          scale_val(200) - self.txt["button"]["Time: "].get_rect().centery))
        self.screen.blit(self.timertxt,
                         (scale_val(1420) - (self.buttonrect.w / 2),
                          scale_val(200) - self.timertxt.get_rect().centery))
        
        

        # Continue button
        continueButton = self.blit_centered(self.button,800,350)
        self.blit_centered(self.txt["button"]["Continue"],800,350)

        # Restart button
        restartButton = self.blit_centered(self.button,800,500)
        self.blit_centered(self.txt["button"]["Restart"],800,500)

        # Options button
        optbutton = self.blit_centered(self.button,800,650)
        self.blit_centered(self.txt["button"]["Options"],800,650)

        # Exit button
        exitbutton = self.blit_centered(self.button,800,800)
        self.blit_centered(self.txt["button"]["Exit"],800,800)

        if pygame.mouse.get_pressed()[0]:
            if continueButton.collidepoint(pygame.mouse.get_pos()):
                # Go to next level
                self.selectSound.play()
                
                self.lvl += 1
                if self.lvl > len(os.listdir(LEVELDIR)):
                    self.lvl = 1
                    self.load_level(self.LEVELLOCATION.format(self.lvl))
                    self.update = self.startloop
                    self.previous = self.levelcomplete
                else:
                    self.load_level(self.LEVELLOCATION.format(self.lvl))
                    self.update = self.level
                    self.previous = self.levelcomplete
            elif restartButton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()

                self.load_level(self.LEVELLOCATION.format(self.lvl))

                self.update = self.level
                self.previous = self.levelcomplete
            elif optbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.update = self.options
                self.previous = self.levelcomplete
            elif exitbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.lvl = 1
                self.load_level(self.LEVELLOCATION.format(self.lvl))
                
                self.update = self.startloop
                self.previous = self.levelcomplete

        # Check for keys
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    # Go to next level
                    
                    self.lvl += 1
                    if self.lvl > len(os.listdir(LEVELDIR)):
                        self.lvl = 1
                        self.load_level(self.LEVELLOCATION.format(self.lvl))
                        self.update = self.startloop
                        self.previous = self.levelcomplete
                    else:
                        self.load_level(self.LEVELLOCATION.format(self.lvl))
                        self.update = self.level
                        self.previous = self.levelcomplete
        
                 
        

    def pause(self):
        """ Draw the pausescreen and handle events. """
        # Clear the screen
        self.screen.fill((0,0,0))

        # Draw the world and player
        self.world.update(self.screen)
        self.playerPlain.draw(self.screen)

        # Timer
        if self.timerBool:
            self.screen.blit(self.timertxt,(0,0))
        # Particles
        if self.particleBool:
            self.player.draw_particles(self.screen)

        # Title
        self.blit_centered(self.txt["subtitle"]["Pause"],800,60)

        # Play button
        playButton = self.blit_centered(self.button,800,225)
        self.blit_centered(self.txt["button"]["Play"],800,225)

        # Restart button
        restartButton = self.blit_centered(self.button,800,375)
        self.blit_centered(self.txt["button"]["Restart"],800,375)

        # Options button
        optbutton = self.blit_centered(self.button,800,525)
        self.blit_centered(self.txt["button"]["Options"],800,525)

        # Exit button
        exitbutton = self.blit_centered(self.button,800,675)
        self.blit_centered(self.txt["button"]["Exit"],800,675)

        if pygame.mouse.get_pressed()[0]:
            if playButton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()

                self.player.groundTime += 1000 * get_interval(self.pausetime)
                self.levelclock += 1000 * get_interval(self.pausetime)
                
                self.update = self.level
                self.previous = self.pause
            elif restartButton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()

                self.load_level(self.LEVELLOCATION.format(self.lvl))

                self.update = self.level
                self.previous = self.pause
            elif optbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.update = self.options
                self.previous = self.pause
            elif exitbutton.collidepoint(pygame.mouse.get_pos()):
                self.selectSound.play()
                
                self.lvl = 1
                self.load_level(self.LEVELLOCATION.format(self.lvl))
                
                self.update = self.startloop
                self.previous = self.pause

        # Check for keys
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_p or event.key == K_RETURN:
                    self.player.groundTime += 1000 * get_interval(self.pausetime)
                    self.levelclock += 1000 * get_interval(self.pausetime)
                    
                    self.update = self.level
                    self.previous = self.pause
    

def scale_val(value) -> int:
    return round(value / 100 * SIZE)

def get_interval(ticks: int) -> float:
    """ Get how much time has passed in seconds. """
    return (pygame.time.get_ticks() - ticks) / 1000

def main():
    global WIDTH, HEIGHT
    
    # Configuration for options
    config = configparser.ConfigParser()
    config.read("options.ini")
    # Sounds
    pygame.mixer.pre_init(44100,-16,8,2048)
    pygame.mixer.init()

    # Window
    pygame.init()

    screenInfo = pygame.display.Info()
    pygame.display.set_caption("Platformer")
    pygame.display.set_mode((WIDTH,HEIGHT),DOUBLEBUF | RESIZABLE | HWSURFACE)

    # Fonts
    pygame.font.init()

    game = Game(config)
    
    clock = pygame.time.Clock()
    
    run = True
    windowed = True
    pygame.event.set_allowed([QUIT, KEYDOWN, VIDEORESIZE])
    
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
                    resizeEvent = pygame.event.Event(VIDEORESIZE,
                                                     size=(screenInfo.current_w,
                                                           screenInfo.current_h))
                    pygame.event.post(resizeEvent)
                elif event.key == K_ESCAPE and not windowed: # Exit fullscreen
                    windowed ^= pygame.display.toggle_fullscreen()
            elif event.type == VIDEORESIZE:
                WIDTH, HEIGHT = event.size
                if windowed:
                    pygame.display.set_mode(event.size,
                                            DOUBLEBUF | RESIZABLE | HWSURFACE)
                else:
                    pygame.display.set_mode(event.size,
                                            DOUBLEBUF | RESIZABLE | HWSURFACE | FULLSCREEN)
                game.background = pygame.transform.scale(game.background,
                                                         (WIDTH,HEIGHT)).convert()
        game.update()
        pygame.display.update()
        game.player.framedur = clock.tick(60)
        fps = clock.get_fps()
    ## print(fps)
    
    pygame.quit()

if __name__ == "__main__":
    main()
