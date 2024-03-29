"""
RedBlobGreenBlob

A platformer game by Ross Watts - the sequel to RetroParkourer.
"""

import pygame
import os
import configparser

from pygame.constants import *
from RedBlobGreenBlob.level import *
from RedBlobGreenBlob.player import *
from RedBlobGreenBlob.constants import *

UIBUTTON = os.path.join(IMGDIR, "button.png")
UIBUTTONSMALL = os.path.join(IMGDIR, "smallbutton.png")
UIBUTTONMINI = os.path.join(IMGDIR, "minibutton.png")
UISLIDER = os.path.join(IMGDIR, "slider.png")
UIKNOB = os.path.join(IMGDIR, "knob.png")
UION = os.path.join(IMGDIR, "on.png")
UIOFF = os.path.join(IMGDIR, "off.png")

BACKGROUND = os.path.join(IMGDIR, "background.png")

# Colours

WHITE = (255, 255, 255)
GREEN = (51, 255, 0)
RED = (255, 51, 0)
# Golden ratio gold - GoldenWolf79 (https://www.color-hex.com/color/ffda00)
GOLD = (255, 218, 0)

TOP, LEFT = 0, 0
CENTER = 1
BOTTOM, RIGHT = 2, 2


class UI(Camera):
    """
    UI(displayInfo) -> UI

    Create the user interface for red blob green blob.
    """
    LEVELLOCATION = os.path.join(LEVELDIR, "level{}.txt")

    def __init__(self, display_info: pygame.display.Info,
                 options: configparser.ConfigParser):
        self.display_info = display_info
        super().__init__(0, 0, self.display_info.current_w, self.display_info.current_h,
                         self.display_info.current_w, self.display_info.current_h,
                         self.size)
        self.player = None
        self.level = None
        self.overlay = None
        self.background = None
        self.previous = None  # Previous screen.
        self.options = options
        self.mixer = {"select": pygame.mixer.Sound(SELECTSOUNDFILE),
                      "jump": pygame.mixer.Sound(JUMPSOUNDFILE),
                      "powerup": pygame.mixer.Sound(POWERUPSOUNDFILE),
                      "destroy": pygame.mixer.Sound(DESTROYSOUNDFILE)}

        for sound in self.mixer:
            self.mixer[sound].set_volume(int(self.options["DEFAULT"]["volume"]) / 100)

        # A group for drawing static objects.
        self.static = pygame.sprite.Group()

        self.lvl = 1
        self.lvlTimes = []

        # A function that handles all the global keyboard events.
        self.event_handler = None

        # Text
        size_percent = self.size / 100

        self.fonts = {
            "label": [pygame.font.SysFont("Arial", int(40 * size_percent)), True, WHITE],
            "button": [pygame.font.SysFont("Arial", int(60 * size_percent)), True, WHITE],
            "gold button": [pygame.font.SysFont("Arial", int(60 * size_percent)), True,
                            GOLD],
            "title green": [
                pygame.font.SysFont("Arial", int(150 * size_percent), bold=True),
                True, GREEN],
            "title red": [
                pygame.font.SysFont("Arial", int(150 * size_percent), bold=True),
                True, RED],
            "subtitle": [pygame.font.SysFont("Arial", int(100 * size_percent), bold=True),
                         True, WHITE]}

        self.images = {"button": self.load_image(UIBUTTON),
                       "smallbutton": self.load_image(UIBUTTONSMALL),
                       "minibutton": self.load_image(UIBUTTONMINI),
                       "switch on": self.load_image(UION, 0.7),
                       "switch off": self.load_image(UIOFF, 0.7),
                       "slider": self.load_image(UISLIDER, 0.7),
                       "knob": self.load_image(UIKNOB, 0.7),
                       "background": pygame.transform.scale(pygame.image.load(BACKGROUND),
                                                            (self.width, self.height))
                       }

        self.load_start()

    def render_text(self, fontname, text) -> pygame.surface.Surface:
        """ Return the surface of the rendered text using a pre-defined font. """
        font, antialias, colour = self.fonts[fontname]
        return font.render(text, antialias, colour).convert_alpha()

    def get_static(self, x, y) -> pygame.Vector2:
        """ Translate the fraction of the width and height to the actual value. """
        return pygame.Vector2(self.width * x,
                              self.height * y)

    def make_button(self, text, image="button") -> tuple:
        """ Return the position arguments used to make a button. """
        return (self.images[image].copy(),
                self.render_text("button", text),
                self.mixer)

    def no_scrolling(self):
        """ Remove the scrolling from the camera. """
        self.scrollWidth = self.display_info.current_w
        self.scrollHeight = self.display_info.current_h
        self.x = 0
        self.y = 0

    # Setting and saving options.
    def set_volume(self, value):
        """ Set the volume. """
        self.options["DEFAULT"]["volume"] = str(int(value * 100))
        for sound in self.mixer:
            self.mixer[sound].set_volume(int(self.options["DEFAULT"]["volume"]) / 100)

    def set_options_bool(self, value, name):
        """ Set an options boolean. """
        self.options["DEFAULT"][name] = str(value).lower()

    def save_options(self):
        """ Save the options to the file. """
        with open(os.path.join(ROOTDIR, "options.ini"), "w") as file:
            self.options.write(file)

    @property
    def size(self) -> int:
        """ The size of the tiles - 10th of the current height. """
        # Size = 10th of the current height.
        return self.display_info.current_h // 10

    # Event Handlers
    def level_handler(self, event):
        """ Event handler for the level screen - handle the event. """
        if event.type == KEYDOWN:
            if event.key == K_p:
                self.load_pause()
            elif event.key == K_F1:  # TODO: For testing
                self.load_levelcomplete()

    def pause_handler(self, event):
        """ Event handler for the pause screen - handle the event. """
        if event.type == KEYDOWN:
            if event.key in [K_p, K_RETURN]:
                self.unpause()
            elif event.key == K_BACKSPACE:
                # Restart level
                self.load_world(self.lvl)

    def unpause(self):
        """ Unpause the screen by removing the pause overlay. """
        self.static.remove(*iter(self.overlay))
        self.event_handler = self.level_handler
        self.player.paused = False
        self.timer.paused = False
        self.previous = self.load_world

    def complete_handler(self, event):
        """ Event handler for the level complete screen - handle the event. """
        if event.type == KEYDOWN:
            if event.key == K_RETURN:
                # Next level
                self.load_world(self.lvl + 1)
            elif event.key == K_BACKSPACE:
                # Restart level
                self.load_world(self.lvl)

    def options_handler(self, event):
        """ Event handler for the options screen - handle the event. """
        if event.type == KEYDOWN:
            if event.key == K_BACKSPACE:
                # Go back - same as pressing the back button.
                self.previous()
            elif event.key == K_RETURN:
                # Save options
                self.save_options()

    # Loaders
    def load_image(self, filename, scale=1.) -> pygame.Surface:
        """ Return the image scaled to the correct dimensions. """
        img = pygame.image.load(filename)
        return pygame.transform.scale(img,
                                      (int(img.get_width() * self.size / 100 * scale),
                                       int(img.get_height() * self.size / 100 * scale))).convert_alpha()

    def load_start(self):
        """ Load the start screen. """
        # Screen
        self.event_handler = lambda event: None
        self.empty()

        self.no_scrolling()

        self.background = Widget(self.get_static(0, 0),
                                 self.images["background"],
                                 self)

        titleR = Widget(self.get_static(0.5, 0),
                        self.render_text("title red", "RedBlob"),
                        self, anchor=(CENTER, TOP))
        titleG = Widget(self.get_static(0.5, 0.15),
                        self.render_text("title green", "GreenBlob"),
                        self, anchor=(CENTER, TOP))

        play_button = Button(self.get_static(0.5, 0.42),
                            lambda: self.load_world(1),
                            *self.make_button("Play"),
                            self, anchor=(CENTER, CENTER))

        opt_button = Button(self.get_static(0.5, 0.58),
                           self.load_options,
                           *self.make_button("Options"),
                           self, anchor=(CENTER, CENTER))

        select_button = Button(self.get_static(0.5, 0.75),
                              self.load_levelselect,
                              *self.make_button("Level Select"),
                              self, anchor=(CENTER, CENTER))

        self.previous = self.load_start

    def load_world(self, lvl):
        """ Load the game world. """
        # Screen
        if lvl not in range(1, len(os.listdir(LEVELDIR)) + 1):
            return self.load_start()

        self.event_handler = self.level_handler

        self.empty()
        self.background = None

        # Setup camera and level.
        self.lvl = lvl
        self.level = Level(self.LEVELLOCATION.format(str(lvl)), self.size // 2)
        self.x = 0
        self.y = 0
        self.scrollWidth = (self.level.width - 1) * self.level.size
        self.scrollHeight = self.level.height * self.level.size
        self.add(*iter(self.level))

        if self.level.height * self.level.size > self.height:
            self.y = self.height - (self.level.height * self.level.size)

        self.timer = Timer(self.get_static(0, 0),
                           self.render_text, args=("button",))

        if self.options["DEFAULT"].getboolean("timer"):
            self.static.add(self.timer)

        # Setup player.
        self.player = Player(self.level, self, self.mixer, self.size)

        self.scroll(self.player, 1)

        self.previous = self.load_world

    def load_levelselect(self):
        """ Load the level selection screen. """
        # Screen
        self.event_handler = lambda event: None

        self.empty()
        self.no_scrolling()

        if self.background:
            self.add(self.background)

        title = Widget(self.get_static(0.5, 0),
                       self.render_text("subtitle", "Level Select"),
                       self, anchor=(CENTER, TOP))

        back_button = Button(self.get_static(0.01, 0.01),
                            self.load_start,
                            self.images["smallbutton"].copy(),
                            self.render_text("button", "Back"),
                            self.mixer, self)

        self.buttons = []

        sep = self.get_static(0.09375, 0)[0]
        coords = self.get_static(0.23625, 0.17)
        gen = list(zip(*iter((x, y) for y in range(0, int(sep * 5), int(sep)) for x in
                             range(0, int(sep * 6), int(sep)))))

        for x, y, lvl in zip(*gen, range(1, len(os.listdir(LEVELDIR)) + 1)):
            self.buttons.append(
                Button(coords + pygame.Vector2(x, y),
                       self.load_world,
                       self.images["minibutton"].copy(),
                       self.render_text("button", str(lvl)),
                       self.mixer, self, args=(int(lvl),))
            )

        self.previous = self.load_levelselect

    def load_levelcomplete(self):
        """ Load the level completion screen. """
        # Overlay
        if self.previous != self.load_world:
            self.empty()
            self.add(*iter(self.level))
            self.add(self.player)
            if self.options["DEFAULT"].getboolean("timer"):
                self.static.add(self.timer)
        else:
            self.completionTicks = self.timer.calc_time()
            self.player.paused = True
            self.timer.paused = True

            # Record the time in milliseconds.
            # Rewrite the entire times file.
            with open(os.path.join(ROOTDIR, "times.csv"), "r+") as file:
                content = file.readlines()
                if len(content) < self.lvl:
                    content.extend(["\n"] * (self.lvl - len(content)))

                content[self.lvl - 1] = "{}{}, \n".format(content[self.lvl - 1][:-1],
                                                          self.completionTicks)

                # Update the level times.
                self.lvlTimes = []
                for line in content:
                    self.lvlTimes.append(list(map(int, line[:-1].split(", ")[:-1])))

                file.seek(0, 0)
                file.writelines(content)

        # Calculate the best time for the level.
        bestTime = min(self.lvlTimes[self.lvl - 1])

        self.event_handler = self.complete_handler

        self.overlay = pygame.sprite.Group()

        title = Widget(self.get_static(0.5, 0),
                       self.render_text("subtitle", "Level Complete"),
                       self.overlay, anchor=(CENTER, TOP))

        timer_label = Widget(self.get_static(0.521, 0.22),
                            self.render_text("button", "Time: "),
                            self.overlay, anchor=(LEFT, CENTER))

        # Turn gold if the time is the best time on the level.
        timer = Widget(self.get_static(0.646, 0.22),
                       self.render_text(
                           "gold button" if bestTime == self.completionTicks else "button",
                           str(round(self.completionTicks / 1000, 1))),
                       self.overlay, anchor=(LEFT, CENTER))

        deaths_label = Widget(self.get_static(0.271, 0.22),
                             self.render_text("button", "Deaths: "),
                             self.overlay, anchor=(LEFT, CENTER))

        deaths = Widget(self.get_static(0.415, 0.22),
                        self.render_text("button", str(self.player.deaths)),
                        self.overlay, anchor=(LEFT, CENTER))

        # Buttons
        continue_button = Button(self.get_static(0.5, 0.39),
                                lambda: self.load_world(self.lvl + 1),
                                *self.make_button("Continue"),
                                self.overlay, anchor=(CENTER, CENTER))

        restart_button = Button(self.get_static(0.5, 0.56),
                               lambda: self.load_world(self.lvl),
                               *self.make_button("Restart"),
                               self.overlay, anchor=(CENTER, CENTER))

        opt_button = Button(self.get_static(0.5, 0.72),
                           self.load_options, *self.make_button("Options"),
                           self.overlay, anchor=(CENTER, CENTER))

        exit_button = Button(self.get_static(0.5, 0.89),
                            self.load_start,
                            *self.make_button("Exit"),
                            self.overlay, anchor=(CENTER, CENTER))

        self.static.add(*iter(self.overlay))

        self.previous = self.load_levelcomplete

    def load_options(self):
        """ Load the options screen. """
        # Screen
        self.event_handler = self.options_handler

        self.empty()

        if self.background:
            self.add(self.background)

        title = Widget(self.get_static(0.5, 0),
                       self.render_text("subtitle", "Options"),
                       self.static, anchor=(CENTER, TOP))

        back_button = Button(self.get_static(0.01, 0.01),
                            self.previous,
                            self.images["smallbutton"].copy(),
                            self.render_text("button", "Back"), self.mixer,
                            self.static)

        # Sound slider and label
        slider = Slider(self.get_static(0.5, 0.2),
                        self.images["slider"].copy(),
                        self.images["knob"].copy(),
                        self.set_volume, self.static,
                        anchor=(CENTER, CENTER),
                        value=int(self.options["DEFAULT"]["volume"]) / 100)

        sound_label = Widget((slider.rect.x, slider.rect.centery),
                            self.render_text("label", "Sound: "),
                            self.static, anchor=(RIGHT, CENTER))

        # Timer switch and label
        timer = Switch(self.get_static(0.27125, 0.32),
                       [self.images["switch off"].copy(),
                        self.images["switch on"].copy()],
                       self.set_options_bool, self.mixer,
                       self.static, anchor=(LEFT, CENTER), args=("timer",),
                       value=self.options["DEFAULT"].getboolean("timer"))

        timer_label = Widget((timer.rect.x, timer.rect.centery),
                            self.render_text("label", "Timer: "),
                            self.static, anchor=(RIGHT, CENTER))

        # Particles switch and label
        particles = Switch(self.get_static(0.52125, 0.32),
                           [self.images["switch off"].copy(),
                            self.images["switch on"].copy()],
                           self.set_options_bool, self.mixer,
                           self.static, anchor=(LEFT, CENTER), args=("particles",),
                           value=self.options["DEFAULT"].getboolean("particles"))

        particles_label = Widget((particles.rect.x, particles.rect.centery),
                                self.render_text("label", "Particles: "),
                                self.static, anchor=(RIGHT, CENTER))

        save_button = Button(self.get_static(0.5, 0.884),
                            self.save_options,
                            *self.make_button("Save"),
                            self.static, anchor=(CENTER, CENTER))

        self.previous = self.load_options

    def load_pause(self):
        """ Load the pause overlay. """
        # Overlay
        if self.previous != self.load_world:
            self.empty()
            self.add(*iter(self.level))
            self.add(self.player)
            if self.options["DEFAULT"].getboolean("timer"):
                self.static.add(self.timer)
        else:
            self.player.paused = True
            self.timer.paused = True

        self.event_handler = self.pause_handler

        self.overlay = pygame.sprite.Group()

        title = Widget(self.get_static(0.5, 0),
                       self.render_text("subtitle", "Pause"),
                       self.overlay, anchor=(CENTER, TOP))

        play_button = Button(self.get_static(0.5, 0.25),
                            self.unpause,
                            *self.make_button("Play"),
                            self.overlay, anchor=(CENTER, CENTER))

        restart_button = Button(self.get_static(0.5, 0.42),
                               lambda: self.load_world(self.lvl),
                               *self.make_button("Restart"),
                               self.overlay, anchor=(CENTER, CENTER))

        opt_button = Button(self.get_static(0.5, 0.58),
                           self.load_options, *self.make_button("Options"),
                           self.overlay, anchor=(CENTER, CENTER))

        exit_button = Button(self.get_static(0.5, 0.75),
                            self.load_start,
                            *self.make_button("Exit"),
                            self.overlay, anchor=(CENTER, CENTER))

        self.static.add(*iter(self.overlay))

        self.previous = self.load_pause

    def empty(self):
        super().empty()
        self.static.empty()

    def update(self):
        super().update()
        self.static.update()

    def draw(self, screen):
        super().draw(screen)
        self.static.draw(screen)


class Widget(pygame.sprite.Sprite):
    """
    Widget(pos, image, *groups, anchor) -> Widget
    
    The Widget class adds extra method to allow sprites to be aligned and
    know their actual rect on screen when placed in a camera that edits where
    sprites are drawn.
    """

    def __init__(self, pos: tuple, image: pygame.surface.Surface,
                 *groups, anchor: tuple = (0, 0)):
        """Initialise the Widget using its (x,y) position (pos), image, groups and anchor."""
        self.image = image

        # Finding smallest rect that encapsulates all opaque pixels.
        self.rect = image.get_bounding_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]

        self.anchor = anchor
        self.align(*self.anchor)

        # The actual position of the widget on screen.
        self.realrect = self.rect.copy()

        super().__init__(*groups)

    def move(self, pos: tuple):
        """ Move the widget to a new position. """
        self.rect = self.image.get_bounding_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]

        self.align(*self.anchor)

    def add_internal(self, group):
        super().add_internal(group)

        if isinstance(group, Camera):
            self.cam = group
            self.realrect = self.rect.move(-self.cam.x, self.cam.y)

    def align(self, alignx, aligny):
        if alignx == 0:
            # Left - default alignment
            pass
        elif alignx == 1:
            # Center
            self.rect.x -= self.image.get_rect().centerx
        elif alignx == 2:
            # Right
            self.rect.x -= self.image.get_rect().right

        if aligny == 0:
            # Top - default alignment
            pass
        elif aligny == 1:
            # Center
            self.rect.y -= self.image.get_rect().centery
        elif aligny == 2:
            # Bottom
            self.rect.y -= self.image.get_rect().bottom


class Button(Widget):
    # default: image, text, mixer
    # variable: args-(pos, method) kwargs=(args, anchor)
    def __init__(self, pos: tuple, method,
                 image: pygame.surface.Surface, text: pygame.surface.Surface,
                 mixer, *groups, args: tuple = (), anchor: tuple = (0, 0)):
        image.blit(text, (image.get_rect().centerx - text.get_rect().centerx,
                          image.get_rect().centery - text.get_rect().centery))

        self.method = method
        self.args = args
        self.mixer = mixer

        super().__init__(pos, image, *groups, anchor=anchor)

    def update(self):
        if pygame.mouse.get_pressed()[0]:
            if self.realrect.collidepoint(pygame.mouse.get_pos()):
                self.mixer["select"].play()
                self.method(*self.args)

        super().update()


class Switch(Widget):
    def __init__(self, pos: tuple, images: list,
                 method, mixer, *groups, args: tuple = (), anchor: tuple = (0, 0),
                 value: bool = False):
        self.method = method
        self.args = args
        self.mixer = mixer

        self.images = images
        self.value = value

        super().__init__(pos, self.images[int(self.value)], *groups, anchor=anchor)

    def update(self):
        if pygame.mouse.get_pressed()[0]:
            if self.realrect.collidepoint(pygame.mouse.get_pos()):
                self.mixer["select"].play()
                self.value = not self.value
                self.image = self.images[int(self.value)]
                self.method(self.value, *self.args)

        super().update()


class Slider(Widget):
    def __init__(self, pos, slider, knob, method, *groups, args=(), anchor=(0, 0),
                 value=0):
        self.max = slider.get_rect().right - knob.get_rect().width

        self.slider = slider
        self.knob = knob

        super().__init__(pos, slider, *groups, anchor=anchor)
        self.method = method
        self.args = args

        self.value = value
        self.update()

    def update(self):
        self.image = self.slider.copy()

        self.image.blit(self.knob, (max(0, min(self.slider.get_rect().x +
                                               (self.slider.get_width() * self.value),
                                               self.max)),
                                    self.slider.get_rect().centery - self.knob.get_rect().centery))

        if pygame.mouse.get_pressed()[0]:
            if self.realrect.collidepoint(pygame.mouse.get_pos()):
                self.value = (pygame.mouse.get_pos()[
                                  0] - self.rect.x - self.knob.get_width()) / \
                             self.image.get_width() * \
                             ((self.image.get_width() + 2 * self.knob.get_width()) /
                              self.image.get_width())

                self.value = max(0, min(self.value, 1))
                self.method(self.value, *self.args)

        super().update()
        pygame.time.wait(100)


class Timer(Widget):
    def __init__(self, pos: tuple, method,
                 *groups, args: tuple = (), anchor: tuple = (0, 0)):
        self.timer_ticks = pygame.time.get_ticks()

        self.method = method
        self.args = args
        self._paused = False
        super().__init__(pos, self.method(*self.args, "0"),
                         *groups, anchor=anchor)

    @property
    def paused(self) -> bool:
        return self._paused

    @paused.setter
    def paused(self, value: bool):
        if not value:
            self.timer_ticks += pygame.time.get_ticks() - self.pause_ticks
        else:
            self.pause_ticks = pygame.time.get_ticks()

        self._paused = value

    def calc_time(self):
        return pygame.time.get_ticks() - self.timer_ticks

    def update(self):
        if not self.paused:
            self.image = self.method(*self.args,
                                     str(round(self.calc_time() / 1000, 1)))
        super().update()


def main():
    global ui  # For testing
    # Sounds
    pygame.mixer.pre_init(44100, -16, 8, 2048)
    pygame.mixer.init()

    # Window
    pygame.init()

    # pygame.display.set_mode((800,450))
    screenInfo = pygame.display.Info()
    # Size - 10th of the current height.
    size = screenInfo.current_h // 10
    height = screenInfo.current_h
    width = screenInfo.current_w

    pygame.display.set_caption("RedBlobGreenBlob")
    pygame.display.set_mode((width, height), RESIZABLE)

    screen = pygame.display.get_surface()

    options = configparser.ConfigParser()
    options.read(os.path.join(ROOTDIR, "options.ini"))

    ui = UI(screenInfo, options)

    clock = pygame.time.Clock()

    # Mainloop
    run = True
    windowed = True
    while run:
        screen.fill((0, 0, 0))

        # Check for keypresses
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False  # Close the window
            elif event.type == KEYDOWN:
                if event.key == K_q and event.mod & KMOD_CTRL:
                    run = False  # Close the window
                elif event.key == K_F11:  # Toggle fullscreen
                    windowed ^= pygame.display.toggle_fullscreen()
                    resize_event = pygame.event.Event(VIDEORESIZE,
                                                      size=(screenInfo.current_w,
                                                            screenInfo.current_h))
                    pygame.event.post(resize_event)
                elif event.key == K_ESCAPE and not windowed:  # Exit fullscreen
                    windowed ^= pygame.display.toggle_fullscreen()
                else:
                    ui.event_handler(event)
            else:
                ui.event_handler(event)

        if ui.player:
            ui.player.frameTicks = min(100, clock.tick(60))

        ui.update()
        ui.draw(screen)
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
