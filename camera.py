from constants import *

class Camera:
    def __init__(self):
        # Camera world coordinates
        self.x = 0
        self.y = 1000  # Height above road
        self.z = 0
        
        # Z-distance between camera and player
        self.dist_to_player = 500
        
        # Z-distance between camera and normalized projection plane
        self.dist_to_plane = None
    
    def init(self):
        """Initialize camera (must be called when initializing game or changing settings)"""
        self.dist_to_plane = 1 / (self.y / self.dist_to_player)
    
    def update(self, player, circuit):
        """Update camera position to follow the player"""
        # Since player X is normalized within [-1, 1], camera X must be multiplied by road width
        self.x = player.x * circuit.road_width
        
        # Place the camera behind the player at the desired distance
        self.z = player.z - self.dist_to_player
        
        # Don't let camera Z go negative
        if self.z < 0:
            self.z += circuit.road_length









# circuit.py
import pygame
import random
from constants import *

class Circuit:
    def __init__(self):
        # Road segments
        self.segments = []
        
        # Segment length and road parameters
        self.segment_length = SEGMENT_LENGTH
        self.total_segments = None
        self.visible_segments = VISIBLE_SEGMENTS
        self.rumble_segments = RUMBLE_SEGMENTS
        self.road_lanes = ROAD_LANES
        self.road_width = ROAD_WIDTH
        self.road_length = None
        
        # Obstacles (only cars)
        self.obstacles = []
        self.obstacle_density = 15  # Default, will be overridden by level
        self.obstacle_images = {}
        
        # Load obstacle images (only cars)
        self._load_obstacle_images()
    
    def _load_obstacle_images(self):
        """Load obstacle images (only cars)"""
        self.obstacle_images = {
            OBJ_CAR: pygame.image.load("assets/img_cars.png"),
            OBJ_TRUCK: pygame.image.load("assets/img_trucks.png")
        }
    
    def create(self):
        """Creates the entire road environment"""
        # Clear arrays
        self.segments = []
        
        # Create a road
        self.create_road()
        
        # Colorize first segments in starting color, and last segments in finishing color
        for n in range(self.rumble_segments):
            self.segments[n]['color']['road'] = (255, 255, 255)  # Start line
            self.segments[-n-1]['color']['road'] = (34, 34, 34)  # Finish line
        
        # Store the total number of segments
        self.total_segments = len(self.segments)
        
        # Calculate the road length
        self.road_length = self.total_segments * self.segment_length
    
    def create_road(self):
        """Creates the road sections"""
        self.create_section(1000)  # Create a straight road with 1000 segments
    
    def create_section(self, n_segments):
        """Creates a road section with the specified number of segments"""
        for i in range(n_segments):
            self.create_segment()
    
    def create_segment(self):
        """Creates a new road segment"""
        # Get the current number of segments
        n = len(self.segments)
        
        # Add new segment
        self.segments.append({
            'index': n,
            'point': {
                'world': {'x': 0, 'y': 0, 'z': n * self.segment_length},
                'screen': {'x': 0, 'y': 0, 'w': 0},
                'scale': -1
            },
            # Alternately color the groups of segments dark and light
            'color': COLORS['DARK'] if (n // self.rumble_segments) % 2 else COLORS['LIGHT']
        })
    
    def create_obstacles(self):
        """Create obstacles (only cars)"""
        self.obstacles = []
        
        # Leave the first 20% of the track clear for the player
        safe_zone = self.total_segments * 0.2
        
        # Distribute cars
        for i in range(int(self.total_segments * (self.obstacle_density / 100))):
            # Randomize placement
            segment_index = int(safe_zone + random.random() * (self.total_segments - safe_zone))
            
            # Create a car on the road
            obj_type = OBJ_CAR if random.random() > 0.25 else OBJ_TRUCK  # 25% trucks
            lane = random.randint(-1, 1)  # -1: left lane, 0: center, 1: right lane
            
            # Add car
            self.obstacles.append({
                'z': segment_index * self.segment_length,
                'type': obj_type,
                'lane': lane  # Position across the road
            })
    
    def get_segment(self, position_z):
        """Returns a segment at the given Z position"""
        if position_z < 0:
            position_z += self.road_length
        index = int(position_z / self.segment_length) % self.total_segments
        return self.segments[index]
    
    def project_3d(self, point, camera_x, camera_y, camera_z, camera_depth):
        """Projects a point from world coordinates to screen coordinates"""
        # Translating world coordinates to camera coordinates
        trans_x = point['world']['x'] - camera_x
        trans_y = point['world']['y'] - camera_y
        trans_z = point['world']['z'] - camera_z
        
        # Scaling factor based on the law of similar triangles
        if trans_z <= 0:
            point['scale'] = 0.001  # Avoid division by zero
        else:
            point['scale'] = camera_depth / trans_z
        
        # Projecting camera coordinates onto a normalized projection plane
        projected_x = point['scale'] * trans_x
        projected_y = point['scale'] * trans_y
        projected_w = point['scale'] * self.road_width
        
        # Scaling projected coordinates to the screen coordinates
        point['screen']['x'] = int((1 + projected_x) * SCREEN_CX)
        point['screen']['y'] = int((1 - projected_y) * SCREEN_CY)
        point['screen']['w'] = int(projected_w * SCREEN_CX)
    
    def render_3d(self, screen, camera):
        """Renders the road by drawing segment by segment"""
        # Define the clipping bottom line to render only segments above it
        clip_bottom_line = SCREEN_HEIGHT
        
        # Get the base segment
        base_segment = self.get_segment(camera.z)
        base_index = base_segment['index']
        
        # Draw each segment in the view
        for n in range(self.visible_segments):
            # Get the current segment
            curr_index = (base_index + n) % self.total_segments
            curr_segment = self.segments[curr_index]
            
            # Get the camera offset-Z to loop back the road
            offset_z = self.road_length if curr_index < base_index else 0
            
            # Project the segment to the screen space
            self.project_3d(curr_segment['point'], camera.x, camera.y, camera.z - offset_z, camera.dist_to_plane)
            
            # Draw this segment only if it is above the clipping bottom line
            curr_bottom_line = curr_segment['point']['screen']['y']
            
            if n > 0 and curr_bottom_line < clip_bottom_line:
                prev_index = curr_index - 1 if curr_index > 0 else self.total_segments - 1
                prev_segment = self.segments[prev_index]
                
                p1 = prev_segment['point']['screen']
                p2 = curr_segment['point']['screen']
                
                # Draw the road segment
                self.draw_segment(
                    screen,
                    p1['x'], p1['y'], p1['w'],
                    p2['x'], p2['y'], p2['w'],
                    curr_segment['color']
                )
                
                # Move the clipping bottom line up
                clip_bottom_line = curr_bottom_line
        
        # Render cars after the road
        self.render_obstacles(screen, camera)
    
    def render_obstacles(self, screen, camera):
        """Render all cars on the road"""
        # Sort cars by z-depth to render far to near
        cars_to_render = sorted(
            self.obstacles, 
            key=lambda obj: obj['z'], 
            reverse=True
        )
        
        for car in cars_to_render:
            # Only render cars in front of the camera
            relative_z = car['z'] - camera.z
            if relative_z <= 0:
                relative_z += self.road_length
            
            # Skip if too far or too close
            if relative_z > self.visible_segments * self.segment_length:
                continue
            
            # Get the segment the car is on
            segment = self.get_segment(car['z'])
            segment_point = segment['point']
            
            # Project the car's position
            self.project_3d(segment_point, camera.x, camera.y, camera.z, camera.dist_to_plane)
            
            # Calculate the car's screen position
            car_x = segment_point['screen']['x'] + (car['lane'] * segment_point['screen']['w'])
            car_y = segment_point['screen']['y']
            
            # Draw the car
            car_image = self.obstacle_images[car['type']]
            screen.blit(car_image, (car_x - car_image.get_width() // 2, car_y))
    
    def draw_segment(self, screen, x1, y1, w1, x2, y2, w2, color):
        """Draws a road segment"""
        # Draw grass
        pygame.draw.rect(screen, color['grass'], (0, y2, SCREEN_WIDTH, y1 - y2))
        
        # Draw road
        self.draw_polygon(screen, [
            (x1 - w1, y1),
            (x1 + w1, y1),
            (x2 + w2, y2),
            (x2 - w2, y2)
        ], color['road'])
        
        # Draw rumble strips
        rumble_w1 = w1 / 5
        rumble_w2 = w2 / 5
        self.draw_polygon(screen, [
            (x1 - w1 - rumble_w1, y1),
            (x1 - w1, y1),
            (x2 - w2, y2),
            (x2 - w2 - rumble_w2, y2)
        ], color['rumble'])
        self.draw_polygon(screen, [
            (x1 + w1 + rumble_w1, y1),
            (x1 + w1, y1),
            (x2 + w2, y2),
            (x2 + w2 + rumble_w2, y2)
        ], color['rumble'])
        
        # Draw lanes
        if 'lane' in color:
            line_w1 = (w1 / 20) / 2
            line_w2 = (w2 / 20) / 2
            
            lane_w1 = (w1 * 2) / self.road_lanes
            lane_w2 = (w2 * 2) / self.road_lanes
            
            lane_x1 = x1 - w1
            lane_x2 = x2 - w2
            
            for i in range(1, self.road_lanes):
                lane_x1 += lane_w1
                lane_x2 += lane_w2
                
                self.draw_polygon(screen, [
                    (lane_x1 - line_w1, y1),
                    (lane_x1 + line_w1, y1),
                    (lane_x2 + line_w2, y2),
                    (lane_x2 - line_w2, y2)
                ], color['lane'])
    
    def draw_polygon(self, screen, points, color):
        """Draws a polygon with the given points and color"""
        pygame.draw.polygon(screen, color, points)







# constants.py
# Screen dimensions
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_CX = SCREEN_WIDTH // 2
SCREEN_CY = SCREEN_HEIGHT // 2

# Game states
STATE_INIT = 1
STATE_RESTART = 2
STATE_PLAY = 3
STATE_GAMEOVER = 4
STATE_WON = 5
STATE_PAUSED = 6

# Colors
COLORS = {
    'LIGHT': {'road': (136, 136, 136), 'grass': (66, 147, 82), 'rumble': (184, 49, 46)},
    'DARK': {'road': (102, 102, 102), 'grass': (57, 125, 70), 'rumble': (221, 221, 221), 'lane': (255, 255, 255)}
}

# Road parameters
SEGMENT_LENGTH = 100
ROAD_WIDTH = 1000
RUMBLE_SEGMENTS = 5
ROAD_LANES = 3
VISIBLE_SEGMENTS = 200

# Object types
OBJ_CAR = 0
OBJ_TRUCK = 1
OBJ_BILLBOARD = 2
OBJ_TREE = 3
OBJ_SIGN = 4








# main.py
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
    """
    Display a 3, 2, 1 countdown before the game starts.
    """
    for i in range(3, 0, -1):
        screen.fill((0, 0, 0))
        settings.show_countdown(i)
        pygame.display.flip()
        pygame.time.wait(1000)

def select_level(screen, settings):
    """
    Allow the user to select a level (easy, medium, hard).
    """
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








# player.py
import pygame
from constants import *

class Player:
    def __init__(self):
        # Player world coordinates (x is normalized between -1 and 1)
        self.x = 0  # Position on road (0 = center)
        self.y = 0
        self.z = 0
        
        # Player screen coordinates
        self.screen = {'x': 0, 'y': 0, 'w': 0, 'h': 0}
        
        # Driving parameters
        self.speed = 0
        self.max_speed = 1000  # Default speed (will be adjusted based on level)
        self.acceleration = 0.1
        self.deceleration = 0.3
        self.turning_speed = 3.0
        self.centrifugal_force = 0.3
        
        # Car sprite
        self.sprite_img = None
        self.sprite = None
        
        # Collision detection
        self.width = 0.5  # Width of the car (normalized)
    
    def init(self):
        """Initialize player settings"""
        # Load player image
        self.sprite_img = pygame.image.load("assets/img_player.png")
        
        # Set screen coordinates
        self.screen['w'] = self.sprite_img.get_width()
        self.screen['h'] = self.sprite_img.get_height()
        self.screen['x'] = SCREEN_CX
        self.screen['y'] = SCREEN_HEIGHT - self.screen['h'] // 2
    
    def restart(self):
        """Reset player for a new game"""
        self.x = 0
        self.y = 0
        self.z = 0
        self.speed = self.max_speed / 2  # Start at half max speed
    
    def update(self, dt, circuit):
        """Update player position based on input and physics"""
        # Handle keyboard input
        keys = pygame.key.get_pressed()
        
        # Accelerate/decelerate
        if keys[pygame.K_UP]:
            self.speed += self.acceleration * self.max_speed * dt
        elif keys[pygame.K_DOWN]:
            self.speed -= self.deceleration * self.max_speed * dt
        
        # Limit speed
        self.speed = max(0, min(self.speed, self.max_speed))
        
        # Steering left/right
        if keys[pygame.K_LEFT]:
            self.x -= dt * self.turning_speed * (self.speed / self.max_speed)
        elif keys[pygame.K_RIGHT]:
            self.x += dt * self.turning_speed * (self.speed / self.max_speed)
        
        # Limit player x position to stay on the road
        self.x = max(-1, min(1, self.x))
        
        # Update z position based on speed
        self.z += self.speed * dt
        
        # Keep within the circuit length
        if self.z >= circuit.road_length:
            self.z -= circuit.road_length
    
    def check_collision(self, circuit):
        """Check for collisions with cars"""
        # Get current segment the player is on
        segment = circuit.get_segment(self.z)
        segment_index = segment['index']
        
        # Check all cars in nearby segments
        for car in circuit.obstacles:
            # Only check cars in the current segment or the next one
            if car['z'] > self.z and car['z'] < self.z + 200:
                # Convert player x position (normalized -1 to 1) to lane position for comparison
                player_lane = self.x * 0.5 + 0.5  # Convert to 0 to 1 range
                
                # Calculate horizontal distance
                car_lane_position = car['lane'] * 0.5 + 0.5  # Convert to 0 to 1 range
                distance = abs(player_lane - car_lane_position)
                
                # If they're close enough horizontally and vertically
                if distance < 0.25:  # Horizontal collision threshold
                    return True
        
        return False
    
    def render(self, screen):
        """Draw the player on the screen"""
        # Player is always drawn at the same position on screen
        screen.blit(self.sprite_img, 
                   (self.screen['x'] - self.screen['w'] // 2, 
                    self.screen['y'] - self.screen['h']))









import pygame
from constants import SCREEN_CX, SCREEN_CY, SCREEN_WIDTH, SCREEN_HEIGHT

class Settings:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.score = 0
        self.time = 0
        self.start_time = 0
        self.paused = False
        self.game_over = False
        self.won = False

    def update_time(self, start_time):
        """Update the elapsed time in seconds."""
        self.time = (pygame.time.get_ticks() - start_time) // 1000

    def show_score(self):
        """Display the current score and elapsed time on the screen."""
        score_text = self.font.render(f"Score: {self.score} Time: {self.time}s", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

    def show_pause(self):
        """Display the pause message on the screen."""
        pause_text = self.font.render("PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(SCREEN_CX, SCREEN_CY))
        self.screen.blit(pause_text, text_rect)

    def show_game_over(self):
        """Display the game over message on the screen."""
        game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(SCREEN_CX, SCREEN_CY))
        self.screen.blit(game_over_text, text_rect)

    def show_win(self):
        """Display the win message on the screen."""
        win_text = self.font.render("YOU WON!", True, (0, 255, 0))
        text_rect = win_text.get_rect(center=(SCREEN_CX, SCREEN_CY))
        self.screen.blit(win_text, text_rect)

    def show_level_selection(self, options, selected):
        """Display the level selection menu on the screen."""
        self.screen.fill((0, 0, 0))  # Clear the screen
        title_text = self.font.render("Select Level", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_CX, SCREEN_CY - 100))
        self.screen.blit(title_text, title_rect)

        for i, level in enumerate(options):
            color = (255, 255, 255) if i == selected else (128, 128, 128)
            level_text = self.font.render(level, True, color)
            level_rect = level_text.get_rect(center=(SCREEN_CX, SCREEN_CY + i * 50))
            self.screen.blit(level_text, level_rect)

    def show_countdown(self, count):
        """Display a countdown before the game starts."""
        count_text = self.font.render(str(count), True, (255, 255, 255))
        text_rect = count_text.get_rect(center=(SCREEN_CX, SCREEN_CY))
        self.screen.blit(count_text, text_rect)

    def reset(self):
        """Reset all settings for a new game."""
        self.score = 0
        self.time = 0
        self.start_time = 0
        self.paused = False
        self.game_over = False
        self.won = False