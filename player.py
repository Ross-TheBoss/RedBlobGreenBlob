"""
RedBlobGreenBlob player.
"""

import pygame
import random
import os

from pygame.constants import *

# Directories
SOUNDDIR = "sounds"
IMGDIR = "images"
LEVELDIR = "levels"

# 8-bit Platformer SFX commissioned by Mark McCorkle for OpenGameArt.org ( http://opengameart.org )
JUMPSOUNDFILE = os.path.join(SOUNDDIR,"jump.ogg")
SELECTSOUNDFILE = os.path.join(SOUNDDIR,"select.ogg")
POWERUPSOUNDFILE = os.path.join(SOUNDDIR,"powerup.ogg")
DESTROYSOUNDFILE = os.path.join(SOUNDDIR,"destroy.ogg") # Orginally Explosion.wav

UIPLAYER = os.path.join(IMGDIR,"player.png")
UIEXPLODED = os.path.join(IMGDIR,"exploded.png")

class Player(pygame.sprite.Sprite):
    speed = 7 * 60
    jumpSpeed = 9 * 60
    gravity = 20 * 60

    kayoteTicks = 50
    deathDuration = 100
    
    def __init__(self, level, camera, mixer, scale: int=100):
        """ Draw and control the player with realistic physics. """
        super().__init__(camera)

        # Sounds
        self.mixer = mixer
        self.jumpChl = pygame.mixer.Channel(1)

        # Images
        self.rect = pygame.Rect(0,0,scale//3,scale//3)

        self.images = {"player":pygame.transform.scale(pygame.image.load(UIPLAYER),
                                                      [self.rect.width,
                                                       self.rect.height]),
                       "exploded":pygame.transform.scale(pygame.image.load(UIEXPLODED),
                                                         [self.rect.width*3,
                                                          self.rect.height*3])}
        
        # Convert the images as they are set to self.image.
        self.image = self.images["player"].convert()
        
        self.scale = scale

        # Particles
        self.particles = []
        
        # Level for collision detection.
        self.level = level

        # Number of deaths on the current level.
        self.deaths = 0
        # Number of ticks in a frame
        self.frameTicks = 0
        # Time since last death.
        self.deathTicks = 0
        # Time since change in y = 0.
        self.yTicks = pygame.time.get_ticks()
        # Time since touching ground.
        self.groundTicks = pygame.time.get_ticks()
        
         # Velocity - pixels per second.
        self.velocity = pygame.Vector2(0,0)
        # Left / Right thrust - pixels per second
        self.thrust = 0

        self._paused = False

        self.rect.x = self.level.start.rect.x
        self.rect.bottom = self.level.start.rect.bottom

    @property
    def paused(self) -> bool:
        return self._paused
    @paused.setter
    def paused(self, value: bool):
        if not value:
            self.yTicks += pygame.time.get_ticks() - self.pauseTicks
            self.groundTicks += pygame.time.get_ticks() - self.pauseTicks
        else:
            # Set pause timer.
            self.pauseTicks = pygame.time.get_ticks()

        self._paused = value

    def get_velocity(self, acceleration: float, ticks: int, velocity: float):
        """
        Return the velocity given the acceleration, initial velocity and time.
        Uses the equation - v = a * dt + u 
        """
        return (acceleration * ((pygame.time.get_ticks() - ticks) / 1000) + \
               velocity)

    def convert_value(self,value):
        """ Convert a value from pixels per second to the scaled pixels per frame value. """
        return round(value * (self.frameTicks / 960) * (self.scale / 100))

    def get_collisions(self,velx,vely) -> tuple:
        """ Return the sprite the player has collided with and the axis that it occured in. """
        collision = pygame.sprite.spritecollideany(self,self.level.hitboxes)
        collisionY = False
        collisionX = False
        
        if collision:
            # Collisions in the y axis.
            if self.rect.bottom > collision.rect.top and vely > 0: # Down
                collisionY = True
            elif self.rect.top < collision.rect.bottom and vely < 0: # Up
                collisionY = True
            
            # Collisions in the x axis.
            if self.rect.right > collision.rect.left and velx > 0: # Right
                collisionX = True
            elif self.rect.left < collision.rect.right and velx < 0: # Left
                collisionX = True

        return collision, collisionX, collisionY

    def calc_gravity(self):
        """ Calculate gravity and return the change in y. """
        vely = self.convert_value(self.get_velocity(self.gravity,self.yTicks,
                                                    self.velocity.y))

        # Moving upwards
        if self.velocity.y < 0:
            self.rect.y += vely
            collision, collisionX, collisionY = self.get_collisions(0,vely)
            self.rect.y -= vely
            # Peak point has been reached.
            if (pygame.time.get_ticks() - self.yTicks) / \
               1000 >= -(self.velocity.y / self.gravity):
                self.velocity.y = 0
                self.yTicks = pygame.time.get_ticks()
                vely = 0
            elif collisionY: # Touching a roof.
                self.velocity.y = 0
                self.yTicks = pygame.time.get_ticks()
                vely = collision.rect.bottom - self.rect.top

        self.rect.y += vely
        collision, collisionX, collisionY = self.get_collisions(0,vely)
        self.rect.y -= vely
        # Touching the floor.
        if collisionY:
            self.groundTicks = pygame.time.get_ticks()
            self.yTicks = pygame.time.get_ticks()
            vely = collision.rect.top - self.rect.bottom

        return vely

    def calc_collisions(self,velx,vely):
        """ Calculate how collisions will affect the player's position. """
        collision, collisionX, collisionY = self.get_collisions(velx,vely)
        if collisionX:
            # Collisions in the x axis.
            if self.rect.right > collision.rect.left and velx > 0: # Right
                self.rect.right -= self.rect.right - collision.rect.left
            elif self.rect.left < collision.rect.right and velx < 0: # Left
                self.rect.left += collision.rect.right - self.rect.left
        
        if self.velocity.y > 0:
            if (pygame.time.get_ticks() - self.yTicks) / \
               1000 >= -(self.velocity.y / self.gravity):
                self.velocity.y = 0
                self.yTicks = pygame.time.get_ticks()

    def update_particles(self, velx, vely):
        """ Update the particles. """
        
        # Add particle
        if (pygame.time.get_ticks() - self.groundTicks) < self.kayoteTicks and velx != 0:
            for i in range(2):
                particle = pygame.sprite.Sprite()
                size = random.randint(int((self.scale // 10) * 0.7),(self.scale // 10))
                if velx > 0:
                    particle.rect = pygame.Rect(self.rect.right - size - i * (velx / 2),
                                                self.rect.bottom,size,size)
                else:
                    particle.rect = pygame.Rect(self.rect.left - i * (velx / 2),
                                                self.rect.bottom,size,size)
                
                particle.image = pygame.surface.Surface((particle.rect.width,
                                                         particle.rect.height))
                particle.image.fill((200,0,0))
                    
                self.particles.append(particle)
                self.ui.add(self.particles[-1])

        # Update existing particles.
        for i, particle in enumerate(self.particles):
            if particle.rect.width != 0:
                shade = max(0,200 - (len(self.particles)-i)*8)
                self.particles[i].rect.width *= 0.95
                self.particles[i].rect.height *= 0.95
                self.particles[i].image = pygame.surface.Surface((self.particles[i].rect.width,
                                                                  self.particles[i].rect.height))
                self.particles[i].image.fill((shade,0,0))
            else:
                self.ui.remove(self.particles[i])
                self.particles.pop(i)
        
    def update(self):
        """ Handle events and gravity. """        
        if not self.paused:
            # Events
            key_state = pygame.key.get_pressed()

            if key_state[K_RIGHT]:
                self.thrust = self.speed
            elif key_state[K_LEFT]:
                self.thrust = -self.speed

            if key_state[K_UP]:
                self.jump(self.jumpSpeed)

            if self.level.end.rect.contains(self.rect):
                self.mixer["powerup"].play()
                self.ui.load_levelcomplete()
                return

            if self.deathTicks > 0:
                self.ui.scroll(self,1)
                if (pygame.time.get_ticks() - self.deathTicks) > self.deathDuration:
                   self.yTicks = pygame.time.get_ticks()
                   self.groundTicks = pygame.time.get_ticks()
                   self.level.goto_checkpoint(self)
                   self.deathTicks = 0
                   self.image = self.images["player"].convert()

            # Movement
            # Left and right movement - instant - add to normal velocity.
            velx = self.convert_value(self.velocity.x + self.thrust)
            vely = self.calc_gravity()
            
            self.rect.y += vely
            self.rect.x += velx

            # Check for collisions.
            self.calc_collisions(velx,vely)
            self.thrust = 0

            # Particles
            if self.ui.options["DEFAULT"].getboolean("particles"):
                self.update_particles(velx,vely)

            # Checkpoints and failure
            if self.level.at_checkpoint(self):
                self.mixer["powerup"].play()

            if self.deathTicks == 0:
                if self.level.failed(self):
                    self.deaths += 1
                    self.deathTicks = pygame.time.get_ticks()
                    self.mixer["destoy"].play()
                    self.image = self.images["exploded"].convert_alpha()
                else:
                    self.ui.scroll(self)
            else:
                if 0 < (pygame.time.get_ticks() - self.deathTicks) < self.deathDuration:
                    self.image = pygame.transform.rotate(self.images["exploded"],
                                                         random.randint(0,359)).convert_alpha()

    def add_internal(self,group):
        """Add the UI group to the player - assume only a UI group will be added."""
        super().add_internal(group)
        self.ui = self.groups()[0]

    def jump(self,value):
        """ Jump with an initial velocity of value. """
        if (pygame.time.get_ticks() - self.groundTicks) < self.kayoteTicks:
            if not self.jumpChl.get_busy():
                self.jumpChl.play(self.mixer["jump"])
            self.velocity.y = -value
            self.yTicks = pygame.time.get_ticks()
            self.groundTicks -= self.kayoteTicks - (pygame.time.get_ticks() - self.groundTicks)
