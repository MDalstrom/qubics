import pygame

def run(player, *, config):
    screen = pygame.display.set_mode((config['width'], config['height']))
    pygame.display.set_caption("Bouncing Spheres")
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill(config['bg_color'])
        player(screen)
        pygame.display.flip()
        clock.tick(config['fps'])
    
    pygame.quit()
