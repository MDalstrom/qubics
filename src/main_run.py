import pygame

from infrastructure.dependencies import interactive_backend, get_player

pygame.init()

run = interactive_backend()
player = get_player()
run(player)
