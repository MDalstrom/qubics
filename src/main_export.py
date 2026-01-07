import pygame

from infrastructure.dependencies import export_backend, get_player

pygame.init()

run = export_backend()
player = get_player()
run(player)
