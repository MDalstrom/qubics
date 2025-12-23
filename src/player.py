def play(surface, world, systems, renderers):
    
    for system in systems:
        for entity in world:
            system(world, entity)

    for renderer in renderers:
        for entity in world:
            renderer(surface, entity)

