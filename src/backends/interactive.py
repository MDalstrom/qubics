"""
Interactive pygame backend - renders to screen in real-time.
Pure rendering backend, no simulation logic.
"""
import pygame


class InteractiveBackend:
    """Pygame window backend for real-time interactive rendering."""
    
    def __init__(self, width: int, height: int, bg_color: tuple[int, int, int], fps: int, title: str = "Game"):
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.bg_color = bg_color
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = True
    
    def begin_frame(self) -> None:
        """Clear screen and handle events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        
        self.screen.fill(self.bg_color)
    
    def get_surface(self):
        """Get drawing surface."""
        return self.screen
    
    def end_frame(self) -> None:
        """Display frame and limit FPS."""
        pygame.display.flip()
        self.clock.tick(self.fps)
    
    def should_quit(self) -> bool:
        """Check if user wants to quit."""
        return not self.running
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        pygame.quit()

