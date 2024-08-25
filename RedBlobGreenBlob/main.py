import asyncio
import configparser

import pygame
from pygame.constants import *

from ui import UI

# Sounds
pygame.mixer.pre_init(44100, -16, 8, 2048)
pygame.mixer.init()

# Window
pygame.init()

screenInfo = pygame.display.Info()

height = screenInfo.current_h
width = screenInfo.current_w

pygame.display.set_caption("RedBlobGreenBlob")
pygame.display.set_mode((width, height), RESIZABLE)

screen = pygame.display.get_surface()

options = configparser.ConfigParser()
options.read("options.ini")

ui = UI(screenInfo, options)

clock = pygame.time.Clock()


async def main():
    # Mainloop
    run = True
    while run:
        screen.fill((0, 0, 0))

        # Check for keypresses
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False  # Close the window
            else:
                ui.event_handler(event)

        if ui.player:
            ui.player.frameTicks = min(100, clock.tick(60))

        ui.update()
        ui.draw(screen)
        pygame.display.update()
        await asyncio.sleep(0)


asyncio.run(main())
