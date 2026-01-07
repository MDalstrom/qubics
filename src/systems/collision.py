import numpy as np
from components import CircleCollider, Transform, Velocity, Health, Parent, Bounds
from infrastructure.world import World, Entity


def boundary_collision_system(world: World, entity: Entity) -> None:
    # Only spheres (entities with health) collide with bounds
    collider = entity.get_component(CircleCollider)
    transform = entity.get_component(Transform)
    velocity = entity.get_component(Velocity)
    health = entity.get_component(Health)
    
    if not collider or not transform or not velocity or not health:
        return
    
    # Find bounds entity
    bounds_entity = None
    for e in world:
        if e.get_component(Bounds):
            bounds_entity = e
            break
    
    if not bounds_entity:
        return
    
    bounds_component = bounds_entity.get_component(Bounds)
    bounds_rect = bounds_component.rect
    radius = collider.radius
    
    x, y = transform.get_world_position()
    
    if x - radius <= bounds_rect.left or x + radius >= bounds_rect.right:
        velocity.vx = -velocity.vx
        x = max(bounds_rect.left + radius, min(x, bounds_rect.right - radius))
    
    if y - radius <= bounds_rect.top or y + radius >= bounds_rect.bottom:
        velocity.vy = -velocity.vy
        y = max(bounds_rect.top + radius, min(y, bounds_rect.bottom - radius))
    
    transform.set_world_position(x, y)


def collision_system(world: World, entity: Entity) -> None:
    collider1 = entity.get_component(CircleCollider)
    transform1 = entity.get_component(Transform)
    
    if not collider1 or not transform1:
        return
    
    entities_with_colliders = [(i, e) for i, e in enumerate(world) 
                                if e.get_component(CircleCollider) and e.get_component(Transform)]
    entity_idx = next(i for i, e in entities_with_colliders if e is entity)
    
    collider1.collisions = []
    
    for i, other in entities_with_colliders:
        if i <= entity_idx:
            continue
        
        collider2 = other.get_component(CircleCollider)
        transform2 = other.get_component(Transform)
        
        # Decide collision rules based on components
        def should_collide(a: Entity, b: Entity) -> bool:
            parent_a = a.get_component(Parent)
            parent_b = b.get_component(Parent)
            
            # if a is child/weapon (has parent), it collides with health-bearing entities except its owner
            if parent_a:
                health_b = b.get_component(Health)
                return health_b is not None and b is not world[parent_a.owner.index]
            if parent_b:
                health_a = a.get_component(Health)
                return health_a is not None and a is not world[parent_b.owner.index]
            # otherwise, collide spheres with spheres
            return a.get_component(Health) is not None and b.get_component(Health) is not None

        if not should_collide(entity, other):
            continue

        x1, y1 = transform1.get_world_position()
        x2, y2 = transform2.get_world_position()
        dx = x2 - x1
        dy = y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        min_dist = collider1.radius + collider2.radius
        
        if dist < min_dist and dist > 0:
            # skip collisions between an entity and its own parent/child (prevent self-damage)
            parent_e = entity.get_component(Parent)
            parent_o = other.get_component(Parent)
            owner_of_entity = parent_e.owner.index if parent_e else None
            owner_of_other = parent_o.owner.index if parent_o else None
            if owner_of_entity == i or owner_of_other == entity_idx:
                continue

            collider1.collisions.append(i)
            collider2.collisions.append(entity_idx)
            
            velocity1 = entity.get_component(Velocity)
            velocity2 = other.get_component(Velocity)
            
            if velocity1 and velocity2:
                nx, ny = dx / dist, dy / dist
                overlap = min_dist - dist
                
                transform1.set_world_position(x1 - nx * overlap * 0.5, y1 - ny * overlap * 0.5)
                transform2.set_world_position(x2 + nx * overlap * 0.5, y2 + ny * overlap * 0.5)
                
                dvx = velocity1.vx - velocity2.vx
                dvy = velocity1.vy - velocity2.vy
                dot = dvx * nx + dvy * ny
                
                if dot > 0:
                    velocity1.vx -= dot * nx
                    velocity1.vy -= dot * ny
                    velocity2.vx += dot * nx
                    velocity2.vy += dot * ny
                    
                    torque = nx * dvy - ny * dvx
                    velocity1.angular_velocity += torque * 0.01
                    velocity2.angular_velocity -= torque * 0.01
