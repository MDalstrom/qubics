import math


def parent_system(world, entity):
    if 'parent' not in entity or 'transform' not in entity:
        return
    
    parent_data = entity['parent']
    owner = world[parent_data['owner'].index]
    
    if not owner or 'transform' not in owner:
        return
    
    owner_transform = owner['transform']
    angle = owner_transform['angle'] + parent_data['offset_angle']
    distance = parent_data['offset_distance']
    
    entity['transform']['x'] = owner_transform['x'] + distance * math.cos(angle)
    entity['transform']['y'] = owner_transform['y'] + distance * math.sin(angle)
