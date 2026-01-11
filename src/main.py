import pygame
pygame.init()


from infrastructure.config import get_config
from infrastructure.scheduler import get_loop

print(get_config())
loop = get_loop()

running = True

accumulator = 0.0
while running:
    try:
        accumulator = loop(accumulator)
    except (ValueError, KeyboardInterrupt):
        running = False
