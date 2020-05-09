import random
import time
from abc import ABC, abstractmethod

import pygame

FRAME_REFRESH_RATE = 30

DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 600

# Set up colours
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND = BLACK
FONT = 'space_invaders.ttf'

BACKGROUND_IMAGE = 'background.jpg'

# Gunship global (constants)
GUNSHIP_IMAGE_FILE = 'gunship.png'
GUNSHIP_SPEED = 20
LASER_SPEED = 20

BOMB_SPEED = 15
INVADER_SPEED = 5
SAUCER_SPEED = 10

NEW_BOMB_CYCLE_INTERVAL = 30
EXPLOSION_REFRESH_CYCLE = 10

BARRIER_POSITION = 450
INVADER_AREA_TOP = 50

INVADER_START_Y = INVADER_AREA_TOP
INVADER_START_X = 50
INVADER_MOVE_DOWN = 2

INVADER_TYPE_1 = ("invader1.png", 'explosion1.png', 10)
INVADER_TYPE_2 = ("invader2.png", 'explosion2.png', 20)
INVADER_TYPE_3 = ("invader3.png", 'explosion3.png', 30)
INVADER_SAUCER = ("saucer.png", 100)
LASER = 'laser.png'
BOMB = 'bomb.png'

UP = 'U'
DOWN = 'D'

LEFT = 'L'
RIGHT = 'R'

MAX_INVADERS_IN_ROW = 9
LIVES_Y_POSITION = 3

SOUNDS = {}


class Player:

    def __init__(self, game):
        self.lives = 3
        self.life1 = Life(game, DISPLAY_WIDTH - 120, LIVES_Y_POSITION)
        self.life2 = Life(game, DISPLAY_WIDTH - 90, LIVES_Y_POSITION)
        self.life3 = Life(game, DISPLAY_WIDTH - 60, LIVES_Y_POSITION)
        self.score = 0
        self.game = game
        self.scoreText = Text(FONT, 15, 'Score', WHITE, 5, 5)
        self.livesText = Text(FONT, 15, 'Lives ', WHITE, DISPLAY_WIDTH - 180, LIVES_Y_POSITION + 4)

    def draw(self):
        """ draw the game object at the
            current x, y coordinates """
        self.livesText.draw(self.game.display_surface)
        if self.lives == 3:
            self.game.display_surface.blit(self.life1.image, (self.life1.x, self.life1.y))
        if self.lives >= 2:
            self.game.display_surface.blit(self.life2.image, (self.life2.x, self.life2.y))
        if self.lives >= 1:
            self.game.display_surface.blit(self.life3.image, (self.life3.x, self.life3.y))

        score_value_text = Text(FONT, 15, str(self.score), GREEN, 85, 5)
        self.scoreText.draw(self.game.display_surface)
        score_value_text.draw(self.game.display_surface)

    def remove_a_life(self):
        self.lives = self.lives - 1
        if self.lives == 0:
            print('Game Over')
            self.game.game_over()

    def add_to_score(self, value):
        self.score = self.score + value


class GameObject(ABC):
    pass


class DrawableGameObject(GameObject):

    def __init__(self, game):
        self.game = game

    @abstractmethod
    def draw(self):
        pass


class ImageGameObject(DrawableGameObject):

    def __init__(self, game, filename):
        super().__init__(game)
        self.filename = filename
        self.load_image(filename)

    def load_image(self, filename):
        self.image = pygame.image.load(filename).convert()
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def draw(self):
        """ draw the game object at the
            current x, y coordinates """
        self.game.display_surface.blit(self.image, (self.x, self.y))


class Life(ImageGameObject):
    def __init__(self, game, x, y):
        super().__init__(game, 'gunship.png')
        self.image = pygame.transform.scale(self.image, (23, 23))
        self.x = x
        self.y = y


class Text(object):
    def __init__(self, text_font, size, message, color, xpos, ypos):
        self.font = pygame.font.Font(text_font, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class Barrier(DrawableGameObject):
    """ Represents a barrier wall """

    def __init__(self, game):
        super().__init__(game)


class MoveableGameObject(ImageGameObject):

    def __init__(self, game, filename, speed):
        super().__init__(game, filename)
        self.speed = speed
        self.x = 0
        self.y = 0

    def move_right(self):
        """ moves the object right across the screen """
        self.x = self.x + self.speed

    def move_left(self):
        """ Move the object left across the screen """
        self.x = self.x - self.speed

    def rect(self):
        """ Generates a rectangle representing the objects location
        and dimensions """
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Bullet(MoveableGameObject):

    def __init__(self, game, filename, x, y, direction, speed):
        super().__init__(game, filename, speed)
        self.direction = direction
        self.x = x
        self.y = y
        self.sound = load_sound_file('shoot.wav')

    def move(self):
        if self.direction == UP:
            self.move_up()
        else:
            self.move_down()

    def move_up(self):
        """ Move the starship up the screen """
        self.y = self.y - self.speed
        if self.y < INVADER_AREA_TOP:
            self.remove()

    def move_down(self):
        """ Move the starship down the screen """
        self.y = self.y + self.speed
        if self.y + self.height > DISPLAY_HEIGHT:
            self.remove()

    def play(self):
        self.sound.play()

    @abstractmethod
    def remove(self):
        pass


class Laser(Bullet):
    def __init__(self, game, x, y):
        super().__init__(game, LASER, x, y, UP, LASER_SPEED)
        self.persistent = False

    def remove(self):
        self.game.lasers.remove(self)


class Bomb(Bullet):
    def __init__(self, game, x, y):
        super().__init__(game, BOMB, x, y, DOWN, BOMB_SPEED)
        self.sound = load_sound_file('bomb.wav')

    def remove(self):
        self.game.bombs.remove(self)


class Gunship(MoveableGameObject):
    """ Represents a Gunship"""

    def __init__(self, game):
        super().__init__(game, GUNSHIP_IMAGE_FILE, GUNSHIP_SPEED)
        self.x = int(DISPLAY_WIDTH / 2)
        self.y = int(DISPLAY_HEIGHT - 40)

    def fire_laser(self):
        laser = Laser(self.game, self.x + (self.width / 2), self.y)
        self.game.add_laser(laser)
        laser.play()

    def __str__(self):
        return 'Gunship(' + str(self.x) + ', ' + str(self.y) + ')'

class Saucer(MoveableGameObject):
    def __init__(self, game):
        super().__init__(game, INVADER_SAUCER[0], SAUCER_SPEED)
        self.value = INVADER_SAUCER[1]
        self.x = 0
        self.y = INVADER_AREA_TOP - 20
        self.exploded = False
        self.explosion = load_sound_file('saucer.wav')

    def move(self):
        if self.x + self.width > DISPLAY_WIDTH:
            self.game.remove_saucer(self)
        else:
            self.move_right()


class Invader(MoveableGameObject):
    """ Represents a type of Space Invader in the Game """

    def __init__(self, game, row, type, x, column):
        super().__init__(game, type[0], INVADER_SPEED)
        self.explosion_image = type[1]
        self.value = type[2]
        self.row = row
        self.x = x
        self.column = column
        self.exploded = False
        self.explosion = load_sound_file('invader_explosion.wav')

    def drop_bomb(self):
        bomb = Bomb(self.game, self.x + (self.width / 2), self.row.y)
        self.game.add_bomb(bomb)
        bomb.play()

    def move(self):
        # Make the move
        if self.row.direction() == LEFT:
            self.move_left()
        else:
            self.move_right()

    def rect(self):
        """ Generates a rectangle representing the objects location
        and dimensions """
        return pygame.Rect(self.x, self.row.y, self.width, self.height)

    def draw(self):
        """ draw the game object at the
            current x, y coordinates """
        self.game.display_surface.blit(self.image, (self.x, self.row.y))

    def check_for_collion(self):
        for laser in self.game.lasers:
            if self.rect().colliderect(laser.rect()):
                # A laser hit the alien ship
                self.image = pygame.image.load(self.explosion_image).convert()
                self.exploded = True
                self.explosion.play()
                self.game.add_to_player(self.value)
                if self.game.remove_laser(laser):
                    break

    def __str__(self):
        return 'Invader(' + str(self.x) + ', ' + str(self.row.y) + ')'


class InvaderRow:

    def __init__(self, game, squadren, index, type):
        self.game = game
        self.invaders = []
        self.index = index
        self.type = type
        self.setup()
        self.squadren = squadren
        self.y = INVADER_START_Y + (self.index * 45)

    def setup(self):
        for column in range(MAX_INVADERS_IN_ROW):
            x = INVADER_START_X + (column * 50)
            invader = Invader(self.game, self, self.type, x, column)
            self.invaders.append(invader)

    def get_number_of_invaders(self):
        return len(self.invaders)

    def select_invader_for_bomb(self):
        position = random.randint(0, self.get_number_of_invaders()) - 1
        self.invaders[position].drop_bomb()

    def move(self):
        for invader in self.invaders:
            invader.move()

    def move_down(self):
        self.y = self.y + INVADER_MOVE_DOWN

    def check_for_collisions(self):
        for invader in self.invaders:
            invader.check_for_collion()

    def remove_invaders_if_exploded(self):
        for invader in self.invaders:
            if invader.exploded:
                self.invaders.remove(invader)

    def is_empty(self):
        return len(self.invaders) == 0

    def direction(self):
        return self.squadren.direction

    # Iterable protocol
    def __iter__(self):
        return self.invaders.__iter__()


class InvaderSquadren:

    def __init__(self, game):
        self.game = game
        self.rows = [InvaderRow(game, self, 0, INVADER_TYPE_1),
                     InvaderRow(game, self, 1, INVADER_TYPE_1),
                     InvaderRow(game, self, 2, INVADER_TYPE_2),
                     InvaderRow(game, self, 3, INVADER_TYPE_2),
                     InvaderRow(game, self, 4, INVADER_TYPE_3),
                     InvaderRow(game, self, 5, INVADER_TYPE_3)]
        self.direction = RIGHT

    def get_row_count(self):
        return len(self.rows)

    def select_invader_row_for_bomb(self):
        row = random.randint(0, self.get_row_count()) - 1
        self.rows[row].select_invader_for_bomb()

    def remove_invaders_if_exploded(self):
        for row in self.rows:
            row.remove_invaders_if_exploded()
            if row.is_empty():
                self.remove_row(row)

    def remove_row(self, row):
        self.rows.remove(row)

    def check_for_collisions(self):
        for row in self.rows:
            row.check_for_collisions()

    def determine_direction(self):
        for row in self.rows:
            for invader in row:
                # Determine the next cycles direction
                if invader.x + invader.width > DISPLAY_WIDTH:
                    self.change_direction(LEFT)
                    break
                elif invader.x <= 0:
                    self.change_direction(RIGHT)

    def change_direction(self, new_direction):
        self.direction = new_direction
        for row in self.rows:
            row.move_down()

    # Iterable protocol
    def __iter__(self):
        return self.rows.__iter__()


def load_sound_file(filename):
    sound = None
    if filename in SOUNDS:
        sound = SOUNDS[filename]
    else:
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(0.2)
        SOUNDS[filename] = sound
    return sound


class Game:
    """ Represents the game itself, holds the main game playing loop """

    def __init__(self):
        self.__setup_game()

    def __setup_game(self):
        pygame.init()
        # Set up execution state
        self.is_running = True
        # Set up the display
        self.display_surface = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption('Pyvaders!')
        # Set up the background image
        self.background = pygame.image.load(BACKGROUND_IMAGE).convert()
        self.display_surface.blit(self.background, (0, 0))
        # Used for timing within the program.
        self.clock = pygame.time.Clock()
        # Set up the gunship
        self.gunship = Gunship(self)
        # Set up the invaders
        self.invaders = InvaderSquadren(self)
        # set up lasers
        self.lasers = []
        # set up bombs
        self.bombs = []
        # Game over flag
        self.game_over = False
        # Player object
        self.player = Player(self)
        # Saucer object
        self.saucer = None

    def __display_message(self, message):
        """ Displays a message to the user on the screen """
        text_font = pygame.font.Font('freesansbold.ttf', 48)
        text_surface = text_font.render(message, True, BLUE, WHITE)
        text_rectangle = text_surface.get_rect()
        text_rectangle.center = (DISPLAY_WIDTH / 2, DISPLAY_HEIGHT / 2)
        self.display_surface.fill(WHITE)
        self.display_surface.blit(text_surface, text_rectangle)

    def __pause(self):
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        paused = False
                        break

    def _draw_display(self):
        # Clear the screen of current contents
        self.display_surface.blit(self.background, (0, 0))

        # Draw player detials
        self.player.draw()

        # Draw the invaders and the gunship
        self.gunship.draw()
        for row in self.invaders.rows:
            for invader in row.invaders:
                invader.draw()

        # Draw the lasers
        for laser in self.lasers:
            laser.draw()

        # Draw the bombs
        for bomb in self.bombs:
            bomb.draw()

        # Draw the saucer
        if self.saucer is not None:
            self.saucer.draw()

        # Update the display
        pygame.display.update()

    def _check_can_fire(self):
        return len(self.lasers) == 0

    def _display_player_details(self):
        pass

    def _handle_user_input(self):
        # Work out what the user wants to do
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                # Check to see which key is pressed
                if event.key == pygame.K_RIGHT:
                    # Right arrow key has been pressed
                    # move the player right
                    self.gunship.move_right()
                elif event.key == pygame.K_LEFT:
                    # Left arrow has been pressed
                    # move the player left
                    self.gunship.move_left()
                elif event.key == pygame.K_SPACE:
                    if self._check_can_fire():
                        self.gunship.fire_laser()
                elif event.key == pygame.K_p:
                    self.__pause()
                elif event.key == pygame.K_q:
                    self.is_running = False

    def _move_game_objects(self):

        # Move the laser
        for laser in self.lasers:
            laser.move()

        # Move the bombs
        for bomb in self.bombs:
            bomb.move()

        if self.saucer is not None:
            self.saucer.move()

        # Move the invaders
        for invader_row in self.invaders:
            invader_row.move()

        self.invaders.determine_direction()

    def remove_saucer(self, saucer):
        self.saucer = None

    def add_to_player(self, value):
        self.player.add_to_score(value)

    def remove_laser(self, laser):
        if not laser.persistent:
            self.lasers.remove(laser)
            return True
        return False

    def detect_collisions(self):
        self.invaders.check_for_collisions()

    def add_bomb(self, bomb):
        self.bombs.append(bomb)

    def add_laser(self, laser):
        self.lasers.append(laser)

    def game_over(self):
        self.game_over = True

    def play(self):
        cycle_count = 0
        while self.is_running and not self.game_over:
            cycle_count += 1

            self._handle_user_input()

            if cycle_count % EXPLOSION_REFRESH_CYCLE == 0:
                self.invaders.remove_invaders_if_exploded()

            if cycle_count % NEW_BOMB_CYCLE_INTERVAL == 0:
                self.invaders.select_invader_row_for_bomb()

            self._display_player_details()

            self._move_game_objects()

            self.detect_collisions()

            self._draw_display()

            # Defines the frame rate. The number is number of frames per second
            # Should be called once per frame (but only once)
            self.clock.tick(FRAME_REFRESH_RATE)

        self.__display_message("Game Over")
        self._draw_display()

        time.sleep(1)
        # Let pygame shutdown gracefully
        pygame.quit()


def main():
    print('Starting Game')
    game = Game()
    game.play()
    print('Game Over')


if __name__ == '__main__':
    main()
