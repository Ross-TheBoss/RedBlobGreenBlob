"""
A simple platformer game by Ross Watts
"""

import pygame
import time

from pygame.constants import *

# 16:9 aspect ratio
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

TILEFILES = ["./images/grass.png","./images/grassc.png","./images/grassp.png"]

UIBUTTON = "./images/button.png"


class World():
    def __init__(self,level: list,blockSize: int,colour: tuple):
        """ Load the level (a list of lines of text) onto the screen. """
        self.items = []
        self.colour = colour
        self.blockSize = blockSize
        self.start = (0,0)
        self.end = (0,0)
        self.relx = 0

        self.height = len(level)
        self.width = len(level[0][:-1]) 
        self.scrollwidth = self.width * self.blockSize

        # Prepare all the tiles in the game.
        
        self.tiles = [pygame.surface.Surface([self.blockSize,self.blockSize]),
                      pygame.surface.Surface([self.blockSize,self.blockSize])]
        self.tiles[0].fill((0,255,0))
        self.tiles[1].fill((0,255,0))
        self.tiles += [pygame.surface.Surface([self.blockSize,self.blockSize])] * 6
        
        self.tiles += [self.load_image(TILEFILES[0])]
        self.tiles += [pygame.transform.rotate(self.tiles[8],-90),
                       pygame.transform.rotate(self.tiles[8],-180),
                       pygame.transform.rotate(self.tiles[8],-270)]

        self.tiles += [self.load_image(TILEFILES[1])]
        self.tiles += [pygame.transform.rotate(self.tiles[12],-90),
                       self.load_image(TILEFILES[2])]
        self.tiles += [pygame.transform.rotate(self.tiles[14],-90)]

        self.tiles = list(map(lambda t: t.convert_alpha(),self.tiles))
        
        
        for y,line in enumerate(level):
            for x,block in enumerate(line):
                if block == "(": # Start
                    self.start = (x*self.blockSize,y*(self.blockSize-1))
                elif block == ")": # End
                    self.end = (x*self.blockSize,y*self.blockSize)
                
                if not block in [" ","\n"]:
                    self.items.append({"type":ord(block) - 32,
                                       "rect":pygame.Rect(
                                           x*self.blockSize,
                                           y*self.blockSize,
                                           self.blockSize,self.blockSize),
                                       })

    def load_image(self,file):
        return pygame.transform.scale(pygame.image.load(file),
                                      (self.blockSize,self.blockSize),
                                      )

    def collided(self, player: pygame.Rect):
        """ Return the rectangle the player rectangle is colliding with. """
        blocks = list(map(lambda i: i["rect"],
                          filter(lambda b: b["type"] in range(0x10,0x20),
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

    def move(self,dist: int):
        """ Move the world in the x axis by dist pixels. """
        self.relx -= dist
        for block in self.items:
            block["rect"].move_ip(dist,0)

    def valid_rect(self,block,types=range(0x8,0x20)):
        """Check if a block is a certain type and return the infomation for blitting. """
        if pygame.Rect(-SIZE,-SIZE,WIDTH+SIZE+MOVETHRESHOLD,
                       HEIGHT+SIZE+MOVETHRESHOLD).contains(block["rect"]) and \
           block["type"] in types:
            return (self.tiles[block["type"] - 0x8],block["rect"].topleft)
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
    def y_change(self):
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
           self.world.scrollwidth - WIDTH > self.world.relx:
            self.world.move(-movement)
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
            self.world.move(movement)
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
        if not collision:
            self.rect.move_ip(0,self.y_change)
        else:
            self.startTime = pygame.time.get_ticks()
            self.rect.move_ip(0,collision.top - self.rect.bottom)

class Game():
    def __init__(self):
        # The current function to run every update.
        self.update = self.startloop
        self.screen = pygame.display.get_surface()
        
        # Graphics
        with open("./levels/level1.txt","r") as f:
            level = f.readlines()

        self.world = World(level,SIZE // 2,(255,255,255))
        self.player = Player(pygame.Rect(self.world.start[0],
                                         self.world.start[1]+SIZE // 3,
                                         SIZE // 3,SIZE // 3),
                             self.world)
        self.playerPlain = pygame.sprite.RenderPlain(self.player)

        self.jumpSound = pygame.mixer.Sound(JUMPSOUNDFILE)
        self.selectSound = pygame.mixer.Sound(SELECTSOUNDFILE)

        self.button = pygame.image.load(UIBUTTON)
        self.button = pygame.transform.scale(self.button,
                                             (int(scale_val(self.button.get_width())),
                                              int(scale_val(self.button.get_height())))
                                             ).convert_alpha()
        self.buttonrect = self.button.get_rect()

        self.txtplay = pygame.font.SysFont("Arial",
                                           int(scale_val(60))).render("Play",
                                                                        False,
                                                                        (255,255,255))
        self.txtplayrect = self.txtplay.get_rect()

    def startloop(self):
        # Clear the screen
        self.screen.fill((0,0,0))

        playbutton = self.screen.blit(self.button,
                                      (WIDTH // 2 - self.buttonrect.centerx,
                                       HEIGHT // 2 - self.buttonrect.centery))
        
        if pygame.mouse.get_pressed()[0] and \
           playbutton.collidepoint(pygame.mouse.get_pos()):
            self.player.startTime = pygame.time.get_ticks()
            self.selectSound.play()
            self.update = self.levelloop
            
        
        self.screen.blit(self.txtplay,(WIDTH // 2 - self.txtplayrect.centerx,
                                       HEIGHT // 2 - self.txtplayrect.centery))

    def levelloop(self):
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

def scale_val(value):
    return value / 100 * SIZE

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
            elif event.type == pygame.KEYDOWN:
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
