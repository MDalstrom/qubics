import numpy as np

def move(_, entity):
    if 'x' in entity and 'vx' in entity:
        entity['x'] += entity['vx']
    if 'y' in entity and 'vy' in entity:
        entity['y'] += entity['vy']

def collide_boundary(world, entity):
    if 'radius' not in entity:
        return

    bounds = next(
        e for e in world
        if 'bounds' in e
    )
    bounds = bounds['rect']

    if 'x' in entity:
        if entity['x'] - entity['radius'] <= bounds.left or entity['x'] + entity['radius'] >= bounds.right:
            entity['vx'] = -entity['vx']
            entity['x'] = max(bounds.left + entity['radius'], min(entity['x'], bounds.right - entity['radius']))
    if 'y' in entity:
        if entity['y'] - entity['radius'] <= bounds.top or entity['y'] + entity['radius'] >= bounds.bottom:
            entity['vy'] = -entity['vy']
            entity['y'] = max(bounds.top + entity['radius'], min(entity['y'], bounds.bottom - entity['radius']))


def clean_collisions(_, entity):
    if 'collisions' in entity:
        entity['collisions'] = []


def collide_spheres(world, entity):
    if 'radius' not in entity:
        return
    
    spheres = [e for e in world if 'radius' in e]
    entity_idx = spheres.index(entity)
    
    for i, other in enumerate(spheres):
        if i <= entity_idx:
            continue
            
        dx = other['x'] - entity['x']
        dy = other['y'] - entity['y']
        dist = np.sqrt(dx**2 + dy**2)
        min_dist = entity['radius'] + other['radius']
        
        if dist < min_dist and dist > 0:
            nx, ny = dx / dist, dy / dist
            overlap = min_dist - dist
            
            entity['x'] -= nx * overlap * 0.5
            entity['y'] -= ny * overlap * 0.5
            other['x'] += nx * overlap * 0.5
            other['y'] += ny * overlap * 0.5
            
            dvx = entity['vx'] - other['vx']
            dvy = entity['vy'] - other['vy']
            dot = dvx * nx + dvy * ny
            
            if dot > 0:
                entity['vx'] -= dot * nx
                entity['vy'] -= dot * ny
                other['vx'] += dot * nx
                other['vy'] += dot * ny
                
                entity['collisions'].append(i)
                other['collisions'].append(entity_idx)


