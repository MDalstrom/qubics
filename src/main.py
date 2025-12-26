import pygame
import sys

from dependencies import export_backend, interactive_backend, get_player

pygame.init()
run = None

if len(sys.argv) > 1 and sys.argv[1] == "export":
    run = export_backend()
else:
    run = interactive_backend()

player = get_player()
run(player)
