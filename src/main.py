from infrastructure.scheduler import get_loop

loop = get_loop()

running = True

while running:
    try:
        loop()
    except (ValueError, KeyboardInterrupt):
        running = False
