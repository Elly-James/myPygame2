import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_CX, SCREEN_CY
from circuit import Circuit
from camera import Camera
from player import Player
from settings import Settings

# Level definitions
class Level:
    def __init__(self, name, speed, obstacle_density):
        self.name = name
        self.speed = speed
        self.obstacle_density = obstacle_density

LEVELS = {
    'easy': Level('Easy', 500, 10),
    'medium': Level('Medium', 1000, 20),
    'hard': Level('Hard', 1500, 30)
}

def countdown(screen, settings):
    """Display a 3, 2, 1 countdown before the game starts."""
    for i in range(3, 0, -1):
        screen.fill((0, 0, 0))
        settings.show_countdown(i)
        pygame.display.flip()
        pygame.time.wait(1000)

def select_level(screen, settings):
    """Allow the user to select a level (easy, medium, hard)."""
    options = ["Easy", "Medium", "Hard"]
    selected = 0

    while True:
        screen.fill((0, 0, 0))
        settings.show_level_selection(options, selected)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_RETURN:
                    return options[selected].lower()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pseudo-3D Racer")
    clock = pygame.time.Clock()

    # Initialize settings
    settings = Settings(screen)

    # Level selection
    selected_level = select_level(screen, settings)
    level = LEVELS[selected_level]

    # Initialize game objects
    circuit = Circuit()
    camera = Camera()
    player = Player()
    
    # Adjust player speed based on the selected level
    player.max_speed = level.speed
    circuit.obstacle_density = level.obstacle_density

    # Initialize game
    camera.init()
    player.init()
    circuit.create()  # Create the road first
    circuit.create_obstacles()  # Then create obstacles

    # Countdown before starting
    countdown(screen, settings)

    # Game state
    paused = False
    game_over = False
    won = False
    start_time = pygame.time.get_ticks()

    # Main game loop
    while True:
        dt = clock.tick(60) / 1000  # Amount of seconds between each loop

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

        # Update game logic
        if not paused and not game_over and not won:
            player.update(dt, circuit)
            camera.update(player, circuit)
            
            # Update obstacles
            circuit.update_obstacles(player.z, dt, player.max_speed)

            # Increment score based on distance traveled
            settings.score = int(player.z / 100)

            # Check for collisions
            if player.check_collision(circuit):
                game_over = True
                settings.time = (pygame.time.get_ticks() - start_time) // 1000  # Stop the timer

            # Check if the player has crossed the finishing line
            elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
            if elapsed_time >= 90:  # 1 minute and 30 seconds
                won = True

        # Render the game
        screen.fill((0, 0, 0))

        # Draw sky background
        sky_image = pygame.image.load("assets/img_sky.png")
        screen.blit(sky_image, (0, 0))

        # Draw city background
        city_image = pygame.image.load("assets/img_city.png")
        screen.blit(city_image, (0, SCREEN_HEIGHT - city_image.get_height()))

        # Draw road and obstacles
        circuit.render_3d(screen, camera)

        # Draw player car
        player.render(screen)

        # Draw score and time
        settings.update_time(start_time)
        settings.show_score()

        # Show game over or win message
        if game_over:
            settings.show_game_over()
        elif won:
            settings.show_win()

        # Show paused message
        if paused:
            settings.show_pause()

        # Update the display
        pygame.display.flip()

if __name__ == "__main__":
    main()