from alt.dependencies.scheduler import get_loop
loop = get_loop()

running = True

while running:
    loop()

