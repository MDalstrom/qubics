def movement_system(_, entity):
    if 'transform' not in entity or 'velocity' not in entity:
        return
    
    transform = entity['transform']
    velocity = entity['velocity']
    
    transform['x'] += velocity['vx']
    transform['y'] += velocity['vy']


def rotation_system(_, entity):
    if 'transform' not in entity or 'velocity' not in entity:
        return
    
    transform = entity['transform']
    velocity = entity['velocity']
    
    transform['angle'] += velocity['angular_velocity']
    velocity['angular_velocity'] *= 0.98
