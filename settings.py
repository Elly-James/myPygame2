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