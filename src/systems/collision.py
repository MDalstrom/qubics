import numpy as np


def boundary_collision_system(world, entity):
    if 'circle_collider' not in entity or 'transform' not in entity or 'velocity' not in entity:
        return
    
    collider = entity['circle_collider']
    if not (collider['mask'] & (1 << 2)):
        return
    
    bounds = next((e for e in world if 'bounds' in e), None)
    if not bounds:
        return
    
    bounds_rect = bounds['rect']
    transform = entity['transform']
    velocity = entity['velocity']
    radius = collider['radius']
    
    if transform['x'] - radius <= bounds_rect.left or transform['x'] + radius >= bounds_rect.right:
        velocity['vx'] = -velocity['vx']
        transform['x'] = max(bounds_rect.left + radius, min(transform['x'], bounds_rect.right - radius))
    
    if transform['y'] - radius <= bounds_rect.top or transform['y'] + radius >= bounds_rect.bottom:
        velocity['vy'] = -velocity['vy']
        transform['y'] = max(bounds_rect.top + radius, min(transform['y'], bounds_rect.bottom - radius))


def collision_system(world, entity):
    if 'circle_collider' not in entity or 'transform' not in entity:
        return
    
    entities_with_colliders = [(i, e) for i, e in enumerate(world) 
                                if 'circle_collider' in e and 'transform' in e]
    entity_idx = next(i for i, e in entities_with_colliders if e is entity)
    
    collider1 = entity['circle_collider']
    collider1['collisions'] = []
    transform1 = entity['transform']
    
    for i, other in entities_with_colliders:
        if i <= entity_idx:
            continue
        
        collider2 = other['circle_collider']
        if not (collider1['layer'] & collider2['mask']) and not (collider2['layer'] & collider1['mask']):
            continue
        
        transform2 = other['transform']
        dx = transform2['x'] - transform1['x']
        dy = transform2['y'] - transform1['y']
        dist = np.sqrt(dx**2 + dy**2)
        min_dist = collider1['radius'] + collider2['radius']
        
        if dist < min_dist and dist > 0:
            # skip collisions between an entity and its own parent/child (prevent self-damage)
            owner_of_entity = entity['parent']['owner'].index if 'parent' in entity else None
            owner_of_other = other['parent']['owner'].index if 'parent' in other else None
            if owner_of_entity == i or owner_of_other == entity_idx:
                continue

            collider1['collisions'].append(i)
            collider2['collisions'].append(entity_idx)
            
            if 'velocity' in entity and 'velocity' in other:
                nx, ny = dx / dist, dy / dist
                overlap = min_dist - dist
                
                transform1['x'] -= nx * overlap * 0.5
                transform1['y'] -= ny * overlap * 0.5
                transform2['x'] += nx * overlap * 0.5
                transform2['y'] += ny * overlap * 0.5
                
                velocity1 = entity['velocity']
                velocity2 = other['velocity']
                
                dvx = velocity1['vx'] - velocity2['vx']
                dvy = velocity1['vy'] - velocity2['vy']
                dot = dvx * nx + dvy * ny
                
                if dot > 0:
                    velocity1['vx'] -= dot * nx
                    velocity1['vy'] -= dot * ny
                    velocity2['vx'] += dot * nx
                    velocity2['vy'] += dot * ny
                    
                    torque = nx * dvy - ny * dvx
                    velocity1['angular_velocity'] += torque * 0.01
                    velocity2['angular_velocity'] -= torque * 0.01
