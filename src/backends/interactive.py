import pygame

def run(player, *, config):
    screen = pygame.display.set_mode((config['width'], config['height']))
    pygame.display.set_caption("Bouncing Spheres")
    clock = pygame.time.Clock()
    
    current_time = pygame.time.get_ticks() / 1000.0
    accumulator = 0.0
    
    running = True
    while running:
        new_time = pygame.time.get_ticks() / 1000.0
        frame_time = new_time - current_time
        if frame_time > 0.25:
            frame_time = 0.25
            
        current_time = new_time
        accumulator += frame_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        while accumulator >= config['delta_time']:
            player(screen, dt=config['delta_time'])
            accumulator -= config['delta_time']
            
        alpha = accumulator / config['delta_time']
        
        screen.fill(config['bg_color'])
        player(screen, dt=0, alpha=alpha)
        pygame.display.flip()
        
        clock.tick(config['fps'])
    
    pygame.quit()
