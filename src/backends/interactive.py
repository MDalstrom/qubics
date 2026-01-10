import pygame
from loop import step_simulation, render_frame


def run(game, *, config):
    update, render = game
    screen = pygame.display.set_mode((config['width'], config['height']))
    pygame.display.set_caption("Balls Fight")
    clock = pygame.time.Clock()
    
    current_time = pygame.time.get_ticks() / 1000.0
    accumulator = 0.0
    
    running = True
    while running:
        # Measure elapsed time
        new_time = pygame.time.get_ticks() / 1000.0
        frame_time = new_time - current_time
        if frame_time > 0.25:  # Cap at 250ms to prevent spiral of death
            frame_time = 0.25
        current_time = new_time
        accumulator += frame_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update simulation (independent of rendering)
        accumulator, alpha = step_simulation(update, accumulator, config['delta_time'])
        
        # Render (only difference between backends)
        render_frame(render, screen, config['bg_color'], alpha)
        pygame.display.flip()
        
        clock.tick(config['fps'])
    
    pygame.quit()

