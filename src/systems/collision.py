import numpy as np
from components import CircleCollider, Transform, Rigidbody, Health, Parent, Bounds, Destroyed
from infrastructure.world import World, Entity, for_each


def boundary_collision_system(world: World):
    bounds = world.query_one(Bounds)
    if not bounds:
        return

    @for_each
    def inner(_: World, __: Entity, collider: CircleCollider, transform: Transform, rigidbody: Rigidbody) -> None:
        bounds_rect = bounds.rect
        radius = collider.radius
        
        x, y = transform.get_world_position()
        
        if x - radius <= bounds_rect.left:
            rigidbody.vx = -rigidbody.vx
            penetration = bounds_rect.left - (x - radius)
            x = bounds_rect.left + radius + penetration
        elif x + radius >= bounds_rect.right:
            rigidbody.vx = -rigidbody.vx
            penetration = (x + radius) - bounds_rect.right
            x = bounds_rect.right - radius - penetration
        
        if y - radius <= bounds_rect.top:
            rigidbody.vy = -rigidbody.vy
            penetration = bounds_rect.top - (y - radius)
            y = bounds_rect.top + radius + penetration
        elif y + radius >= bounds_rect.bottom:
            rigidbody.vy = -rigidbody.vy
            penetration = (y + radius) - bounds_rect.bottom
            y = bounds_rect.bottom - radius - penetration
        
        transform.set_world_position(x, y)

    inner(world)


def collision_system(world: World) -> None:
    entities_with_colliders = [(i, e) for i, e in enumerate(world) 
                                if e.get_component(CircleCollider) 
                                and e.get_component(Transform)
                                and not e.get_component(Destroyed)]
    
    for entity_idx, entity in entities_with_colliders:
        collider1 = entity.get_component(CircleCollider)
        assert(collider1)
        transform1 = entity.get_component(Transform)
        assert(transform1)
        
        collider1.collisions = []
        
        for i, other in entities_with_colliders:
            if i <= entity_idx:
                continue
            
            collider2 = other.get_component(CircleCollider)
            assert(collider2)
            transform2 = other.get_component(Transform)
            assert(transform2)
            
            def should_collide(a: Entity, b: Entity) -> bool:
                parent_a = a.get_component(Parent)
                parent_b = b.get_component(Parent)
                
                if parent_a:
                    health_b = b.get_component(Health)
                    return health_b is not None and b is not world[parent_a.owner.index]
                if parent_b:
                    health_a = a.get_component(Health)
                    return health_a is not None and a is not world[parent_b.owner.index]
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
                parent_e = entity.get_component(Parent)
                parent_o = other.get_component(Parent)
                owner_of_entity = parent_e.owner.index if parent_e else None
                owner_of_other = parent_o.owner.index if parent_o else None
                if owner_of_entity == i or owner_of_other == entity_idx:
                    continue

                collider1.collisions.append(i)
                collider2.collisions.append(entity_idx)
                
                rigidbody1 = entity.get_component(Rigidbody)
                rigidbody2 = other.get_component(Rigidbody)
                
                if rigidbody1 and rigidbody2:
                    nx, ny = dx / dist, dy / dist
                    overlap = min_dist - dist
                    
                    transform1.set_world_position(x1 - nx * overlap * 0.5, y1 - ny * overlap * 0.5)
                    transform2.set_world_position(x2 + nx * overlap * 0.5, y2 + ny * overlap * 0.5)
                    
                    # Combined properties
                    restitution = min(rigidbody1.restitution, rigidbody2.restitution)
                    friction = (rigidbody1.friction + rigidbody2.friction) * 0.5
                    
                    dvx = rigidbody1.vx - rigidbody2.vx
                    dvy = rigidbody1.vy - rigidbody2.vy
                    
                    # Normal impulse
                    dot = dvx * nx + dvy * ny
                    
                    if dot > 0:
                        impulse_scalar = (1 + restitution) * dot
                        
                        # Apply normal impulse
                        rigidbody1.vx -= impulse_scalar * nx * 0.5
                        rigidbody1.vy -= impulse_scalar * ny * 0.5
                        rigidbody2.vx += impulse_scalar * nx * 0.5
                        rigidbody2.vy += impulse_scalar * ny * 0.5
                        
                        # Apply friction/torque
                        tx, ty = -ny, nx  # Tangent vector
                        vt = dvx * tx + dvy * ty
                        
                        # Friction impulse
                        friction_impulse = vt * friction
                        
                        rigidbody1.vx -= friction_impulse * tx * 0.5
                        rigidbody1.vy -= friction_impulse * ty * 0.5
                        rigidbody2.vx += friction_impulse * tx * 0.5
                        rigidbody2.vy += friction_impulse * ty * 0.5
                        
                        # Torque from collision
                        # Lever arm is radius
                        r1 = collider1.radius
                        r2 = collider2.radius
                        
                        # Simple torque model: force at surface causes rotation
                        # Tangential force creates torque
                        torque_force = friction_impulse
                        rigidbody1.angular_velocity -= torque_force * (1.0 / r1) * 2.0 
                        rigidbody2.angular_velocity += torque_force * (1.0 / r2) * 2.0
