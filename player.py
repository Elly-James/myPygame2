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
        self.sprite_img = pygame.image.load("assets/img_player.png").convert_alpha()
        
        # Collision detection
        self.width = 0.5  # Width of the car (normalized)
    
    def init(self):
        """Initialize player settings"""
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