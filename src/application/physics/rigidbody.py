from dataclasses import dataclass
from application.math import Vector
from application.transform import Transform
from application.collisions.components import Collider
from ecs.entity import Entity
from ecs.world import World
from ecs.system import for_each


@dataclass
class Rigidbody:
    velocity: Vector
    center_of_mass: Vector
    friction: float = 0.0
    mass: float = 1.0
    angular_velocity: float = 0.0
    angular_damping: float = 0.5
    inertia: float = 1000.0
    restitution: float = 1.0
    
    @property
    def inv_mass(self) -> float:
        return 1.0 / self.mass if self.mass > 0 else 0.0
    
    @property
    def inv_inertia(self) -> float:
        return 1.0 / self.inertia if self.inertia > 0 else 0.0

@dataclass
class Kinematic:
    pass


@dataclass
class Acceleration:
    ax: float = 0.0
    ay: float = 0.0


def apply_collisions_forces(world: World):
    cache = set()

    def cross(a: Vector, b: Vector) -> float:
        return a.x * b.y - a.y * b.x

    def perpendicular(v: Vector) -> Vector:
        return Vector(-v.y, v.x)
    
    def resolve_rigidbody_collision(a: Entity, a_rigidbody: Rigidbody, a_transform: Transform, a_wm, a_com, 
                                     b: Entity, b_rigidbody: Rigidbody, b_transform: Transform, collision):
        b_wm = b_transform.get_world_matrix()
        b_com = b_wm @ b_rigidbody.center_of_mass
        
        a_delta = collision.contact_point - a_com
        a_delta_cross = cross(a_delta, collision.normal)
        a_effective_velocity = a_rigidbody.velocity + a_rigidbody.angular_velocity * perpendicular(a_delta)
        b_delta = collision.contact_point - b_com
        b_delta_cross = cross(b_delta, collision.normal)
        b_effective_velocity = b_rigidbody.velocity + b_rigidbody.angular_velocity * perpendicular(b_delta)
        
        # impulse
        relative_velocity = b_effective_velocity - a_effective_velocity 
        normal_velocity = relative_velocity.dot(collision.normal) 

        restitution = max(a_rigidbody.restitution, b_rigidbody.restitution)
        eff_mass = a_rigidbody.inv_mass + b_rigidbody.inv_mass + a_delta_cross * a_delta_cross * a_rigidbody.inv_inertia + b_delta_cross * b_delta_cross * b_rigidbody.inv_inertia
        if eff_mass == 0:
            return
        impulse_mag = -(1 + restitution) * normal_velocity / eff_mass
        
        impulse = collision.normal * impulse_mag

        # friction
        friction_direction = relative_velocity - (relative_velocity.dot(collision.normal) * collision.normal)
        if friction_direction.length_squared() > 0:
            friction_direction = friction_direction.normalized()
            tan_velocity = relative_velocity.dot(friction_direction)
        else:
            friction_direction = Vector.zero()
            tan_velocity = 0.0

        friction_impulse_mag = -tan_velocity / eff_mass
        mutual_friction = (a_rigidbody.friction + b_rigidbody.friction) / 2
        friction_impulse_max = mutual_friction * abs(impulse_mag)
        friction_impulse_mag = min(max(friction_impulse_mag, -friction_impulse_max), friction_impulse_max)
        friction = friction_direction * friction_impulse_mag

        # apply 
        acc = impulse + friction 
        a_rigidbody.velocity -= acc * a_rigidbody.inv_mass
        b_rigidbody.velocity += acc * b_rigidbody.inv_mass
        a_rigidbody.angular_velocity -= cross(a_delta, acc) * a_rigidbody.inv_inertia
        b_rigidbody.angular_velocity += cross(b_delta, acc) * b_rigidbody.inv_inertia
        
        # # correction
        # acc_mass = a_rigidbody.inv_mass + b_rigidbody.inv_mass
        #
        # a_correction = max(collision.penetration - a_rigidbody.slop, 0)
        # a_c = collision.normal * a_correction / acc_mass * a_rigidbody.inv_mass
        # a_x, a_y = Transform.get_position(a_wm) - a_c
        # a_transform.set_world_position(a_x, a_y)
        #
        # b_correction = max(collision.penetration - b_rigidbody.slop, 0)
        # b_c = collision.normal * b_correction / acc_mass * b_rigidbody.inv_mass
        # b_x, b_y = Transform.get_position(b_wm) + b_c
        # b_transform.set_world_position(b_x, b_y)
    
    def resolve_kinematic_collision(a: Entity, a_rigidbody: Rigidbody, a_transform: Transform, a_wm, a_com,
                                      b: Entity, b_kinematic: Kinematic, b_transform: Transform, collision):
        b_com = b_transform.get_world_matrix() @ Vector.zero()
        b_velocity = Vector.zero()
        b_angular_velocity = 0.0
        
        a_delta = collision.contact_point - a_com
        a_delta_cross = cross(a_delta, collision.normal)
        a_effective_velocity = a_rigidbody.velocity + a_rigidbody.angular_velocity * perpendicular(a_delta)
        b_delta = collision.contact_point - b_com
        b_effective_velocity = b_velocity + b_angular_velocity * perpendicular(b_delta)
        
        # impulse
        relative_velocity = b_effective_velocity - a_effective_velocity 
        normal_velocity = relative_velocity.dot(collision.normal) 

        restitution = a_rigidbody.restitution
        eff_mass = a_rigidbody.inv_mass + a_delta_cross * a_delta_cross * a_rigidbody.inv_inertia
        if eff_mass == 0:
            return
        impulse_mag = -(1 + restitution) * normal_velocity / eff_mass
        
        impulse = collision.normal * impulse_mag

        # friction
        friction_direction = relative_velocity - (relative_velocity.dot(collision.normal) * collision.normal)
        if friction_direction.length_squared() > 0:
            friction_direction = friction_direction.normalized()
            tan_velocity = relative_velocity.dot(friction_direction)
        else:
            friction_direction = Vector.zero()
            tan_velocity = 0.0

        friction_impulse_mag = -tan_velocity / eff_mass
        mutual_friction = a_rigidbody.friction
        friction_impulse_max = mutual_friction * abs(impulse_mag)
        friction_impulse_mag = min(max(friction_impulse_mag, -friction_impulse_max), friction_impulse_max)
        friction = friction_direction * friction_impulse_mag

        # apply (kinematic doesn't move)
        acc = impulse + friction 
        a_rigidbody.velocity -= acc * a_rigidbody.inv_mass
        a_rigidbody.angular_velocity -= cross(a_delta, acc) * a_rigidbody.inv_inertia

    @for_each
    def apply_collisions_forces(_: World, a: Entity, a_collider: Collider, a_rigidbody: Rigidbody, a_transform: Transform):
        a_wm = a_transform.get_world_matrix()
        a_com = a_wm @ a_rigidbody.center_of_mass

        for collision in a_collider.collisions:
            b = collision.other
            
            hash = (id(a) ^ id(b))
            if hash in cache:
                continue
            cache.add(hash)

            b_transform = b.get_component(Transform)
            assert(b_transform)

            b_rigidbody = b.get_component(Rigidbody)
            b_kinematic = b.get_component(Kinematic)
            
            if b_rigidbody:
                resolve_rigidbody_collision(a, a_rigidbody, a_transform, a_wm, a_com, b, b_rigidbody, b_transform, collision)
            elif b_kinematic:
                resolve_kinematic_collision(a, a_rigidbody, a_transform, a_wm, a_com, b, b_kinematic, b_transform, collision)

    apply_collisions_forces(world)

@for_each
def acceleration_system(
    world: World, _: Entity, rigidbody: Rigidbody, acceleration: Acceleration, collider: Collider
) -> None:
    rigidbody.velocity.x += acceleration.ax * world.timestep
    rigidbody.velocity.y += acceleration.ay * world.timestep

@for_each
def velocity_system(
    world: World, _: Entity, transform: Transform, rigidbody: Rigidbody
) -> None:
    wx, wy = transform.get_world_position()
    wx += rigidbody.velocity.x * world.timestep
    wy += rigidbody.velocity.y * world.timestep
    transform.set_world_position(wx, wy)
    
    angle = transform.get_world_angle()
    angle += rigidbody.angular_velocity * world.timestep
    transform.set_world_angle(angle)


@for_each
def angular_damping_system(
    world: World, _: Entity, rigidbody: Rigidbody
) -> None:
    rigidbody.angular_velocity *= 1.0 - rigidbody.angular_damping
