import pygame
import sys

from dependencies import export_backend, interactive_backend, get_player

pygame.init()

run = None
if len(sys.argv) > 1 and sys.argv[1] == "export":
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.mp4"
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    run = export_backend(output_file, duration)
else:
    run = interactive_backend()

player = get_player()
run(player)
