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
            OBJ_CAR: pygame.image.load("assets/img_car.png").convert_alpha(),
            OBJ_TRUCK: pygame.image.load("assets/img_racing_car.png").convert_alpha()
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
        """Create obstacles (cars) that are clearly visible"""
        self.obstacles = []
        
        # Leave the first 20% of the track clear for the player
        safe_zone = self.total_segments * 0.2
        remaining_track = self.total_segments - safe_zone
        
        # Calculate number of cars based on density
        num_cars = int(self.total_segments * (self.obstacle_density / 100))
        
        # Place cars at regular intervals with some randomness
        for i in range(num_cars):
            # Calculate a position that ensures cars are spread out
            position_percent = (i / num_cars) * 0.8  # Use 80% of the remaining track
            segment_index = int(safe_zone + (remaining_track * position_percent))
            
            # Add some randomness to the position
            segment_index += random.randint(-5, 5)
            
            # Ensure segment_index is within valid range
            segment_index = max(int(safe_zone), min(segment_index, self.total_segments - 1))
            
            # Determine car type (75% regular cars, 25% trucks)
            obj_type = OBJ_CAR if random.random() > 0.25 else OBJ_TRUCK
            
            # Assign to a lane (-1: left, 0: center, 1: right)
            lane = random.randint(-1, 1)
            
            # Set speed factor (50-80% of player's speed)
            speed_factor = random.uniform(0.5, 0.8)
            
            # Add car
            self.obstacles.append({
                'z': segment_index * self.segment_length,
                'type': obj_type,
                'lane': lane,
                'speed': speed_factor,
                'active': True
            })
    
    def update_obstacles(self, player_z, dt, player_speed):
        """Update positions of all obstacles"""
        player_segment = int(player_z / self.segment_length)
        
        for car in self.obstacles:
            # Update car position based on its speed
            car_speed = car['speed'] * player_speed
            car['z'] += car_speed * dt
            
            # If car reaches end of track, loop it back
            if car['z'] >= self.road_length:
                car['z'] -= self.road_length
            
            # Check if this car should be reactivated (if it's far behind player)
            car_segment = int(car['z'] / self.segment_length)
            segment_diff = (car_segment - player_segment + self.total_segments) % self.total_segments
            
            # Mark cars as active if they are ahead of the player or close behind
            car['active'] = (segment_diff < self.visible_segments) or (segment_diff > self.total_segments - 50)
    
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
        """Render all cars on the road with simplified approach"""
        # Get all segments the player can see
        base_segment = self.get_segment(camera.z)
        base_index = base_segment['index']
        
        # Draw active cars
        for car in self.obstacles:
            # Skip inactive cars
            if not car['active']:
                continue
                
            # Calculate relative position to camera
            relative_z = car['z'] - camera.z
            
            # Handle looping around the track
            if relative_z < 0:
                relative_z += self.road_length
            
            # Skip if too far or behind camera
            if relative_z <= 0 or relative_z > self.visible_segments * self.segment_length:
                continue
                
            # Get the segment the car is on
            car_segment = self.get_segment(car['z'])
            car_segment_index = car_segment['index']
            
            # Calculate offset for looping
            offset_z = self.road_length if car_segment_index < base_index else 0
            
            # Create a temporary point for the car's position
            car_point = {
                'world': {
                    'x': car['lane'] * (self.road_width / 3),  # Distribute across lanes
                    'y': 0,
                    'z': car['z']
                },
                'screen': {'x': 0, 'y': 0, 'w': 0},
                'scale': -1
            }
            
            # Project the car's position
            self.project_3d(car_point, camera.x, camera.y, camera.z - offset_z, camera.dist_to_plane)
            
            # Only render if point has valid scale
            if car_point['scale'] <= 0:
                continue
                
            # Draw the car at the projected position
            car_image = self.obstacle_images[car['type']]
            
            # Calculate size based on distance (scale)
            scale = min(1.0, car_point['scale'] * 0.8)  # Limit maximum size
            
            if scale > 0.1:  # Only draw if not too small
                car_width = int(car_image.get_width() * scale)
                car_height = int(car_image.get_height() * scale)
                
                # Only draw if dimensions are valid
                if car_width > 1 and car_height > 1:
                    # Scale image
                    try:
                        scaled_car = pygame.transform.scale(car_image, (car_width, car_height))
                        
                        # Draw car at projected position
                        car_x = car_point['screen']['x'] - car_width // 2
                        car_y = car_point['screen']['y'] - car_height
                        
                        # Make sure car is in visible area
                        if 0 <= car_x < SCREEN_WIDTH and 0 <= car_y < SCREEN_HEIGHT:
                            screen.blit(scaled_car, (car_x, car_y))
                    except pygame.error:
                        # Skip if scaling fails
                        pass
    
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