import pygame

def run(player, *, config):
    screen = pygame.display.set_mode((config['width'], config['height']))
    pygame.display.set_caption("Bouncing Spheres")
    clock = pygame.time.Clock()
    
    accumulator = 0.0
    
    running = True
    while running:
        frame_time = clock.tick(config['fps'])
        accumulator += frame_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        while accumulator >= config['delta_time']:
            player(screen, dt=config['delta_time'])
            accumulator -= config['delta_time']
        
        screen.fill(config['bg_color'])
        player(screen, dt=0)
        pygame.display.flip()
    
    pygame.quit()
