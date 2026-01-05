def play(surface, world, systems, renderers):
    
    for system in systems:
        for entity in world:
            if entity.get('destroyed'):
                continue
            system(world, entity)

    for renderer in renderers:
        for entity in world:
            if entity.get('destroyed'):
                continue
            renderer(surface, entity)

