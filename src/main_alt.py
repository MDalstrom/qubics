import sys, os
# Ensure 'src' directory is on sys.path so imports work when running this file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from alt.dependencies.config import get_config
from alt.dependencies.scenario import get_scenario_baker
from alt.dependencies.core import get_world

config = get_config()
baker = get_scenario_baker()

world = get_world()
baker(world)

running = True

import pygame
from alt.application.background import fill_background, bounds_render_system
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 

    fill_background(world)
    bounds_render_system(world)
    pygame.display.flip()

