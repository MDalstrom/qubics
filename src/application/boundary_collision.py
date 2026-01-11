from application.collision import CircleCollider, BoundsCollider
from application.transform import Transform
from application.physics import Rigidbody
from ecs.world import World
from ecs.entity import Entity
from ecs.system import for_each


def boundary_collision_system(world: World):
    bounds = world.query_one(BoundsCollider)
    if not bounds:
        return

    @for_each
    def inner(_: World, __: Entity, collider: CircleCollider, transform: Transform, rigidbody: Rigidbody) -> None:
        bounds_rect = bounds.rect
        radius = collider.radius
        
        x, y = transform.get_world_position()
        
        # Helper for applying friction/torque
        def apply_friction(nx: float, ny: float):
            # Tangent vector (rotate normal 90 deg)
            tx, ty = -ny, nx
            
            # Surface velocity at contact point
            # r vector from center to contact point is -radius * normal
            rx, ry = -radius * nx, -radius * ny
            
            # v_point = v_cm + omega x r
            # 2D cross product: omega * (-ry, rx) ? No.
            # v_rot_x = -omega * ry
            # v_rot_y = omega * rx
            vx_rot = -rigidbody.angular_velocity * ry
            vy_rot = rigidbody.angular_velocity * rx
            
            # Relative velocity at contact point (wall is static)
            vrx = rigidbody.vx + vx_rot
            vry = rigidbody.vy + vy_rot
            
            # Project onto tangent
            vt = vrx * tx + vry * ty
            
            # Friction impulse
            # Assume wall friction matches rigidbody friction for now, or use a constant
            friction = rigidbody.friction 
            
            impulse = vt * friction
            
            # Apply to linear velocity
            rigidbody.vx -= impulse * tx
            rigidbody.vy -= impulse * ty
            
            # Apply to angular velocity
            # Torque = r x F. Force F = -impulse * tangent
            # Fx = -impulse * tx, Fy = -impulse * ty
            # Torque = rx * Fy - ry * Fx
            fx = -impulse * tx
            fy = -impulse * ty
            torque = rx * fy - ry * fx
            
            # I = 0.5 * m * r^2. Mass m=1.
            inertia = 0.5 * radius * radius
            rigidbody.angular_velocity += torque / inertia

        if x - radius <= bounds_rect.left:
            if rigidbody.vx < 0:
                rigidbody.vx = -rigidbody.vx * rigidbody.restitution
                penetration = bounds_rect.left - (x - radius)
                x = bounds_rect.left + radius + penetration
                apply_friction(1, 0)
        elif x + radius >= bounds_rect.right:
            if rigidbody.vx > 0:
                rigidbody.vx = -rigidbody.vx * rigidbody.restitution
                penetration = (x + radius) - bounds_rect.right
                x = bounds_rect.right - radius - penetration
                apply_friction(-1, 0)
        
        if y - radius <= bounds_rect.top:
            if rigidbody.vy < 0:
                rigidbody.vy = -rigidbody.vy * rigidbody.restitution
                penetration = bounds_rect.top - (y - radius)
                y = bounds_rect.top + radius + penetration
                apply_friction(0, 1)
        elif y + radius >= bounds_rect.bottom:
            if rigidbody.vy > 0:
                rigidbody.vy = -rigidbody.vy * rigidbody.restitution
                penetration = (y + radius) - bounds_rect.bottom
                y = bounds_rect.bottom - radius - penetration
                apply_friction(0, -1)
        
        transform.set_world_position(x, y)

    inner(world)


