from math import tan

from numpy import cross
from application.collisions.components import Collider
from application.math import clamp
from application.physics.velocity import Velocity
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


class Body():
    def __init__(self, mass, inertia, restitution, friction) -> None:
        self.inv_mass = 1.0 / mass
        self.inv_inertia = 1.0 / inertia
        self.restitution = restitution
        self.friction = friction

def correct(world: World):
    cache = set()
    @for_each
    def a(world: World, a: Entity, a_collider: Collider, a_velocity: Velocity, a_body: Body, a_transform: Transform):
        for collision in a_collider.collisions:
            b = collision.other

            hash = id(a) ^ id(b)
            if hash in cache:
                return
            cache.add(hash)

            b_transform = b.get_component(Transform)
            assert b_transform
            b_body = b.get_component(Body)
            assert b_body
            correction = collision.penetration / (a_body.inv_mass + b_body.inv_mass)

            a_transform.position += collision.normal * correction * a_body.inv_mass
            b_transform.position -= collision.normal * correction * b_body.inv_mass
    a(world)
    ...

def apply(world: World):
    cache = set()
    @for_each
    def a(world: World, a: Entity, a_collider: Collider, a_velocity: Velocity, a_body: Body, a_transform: Transform):
        for collision in a_collider.collisions:
            b = collision.other

            hash = id(a) ^ id(b)
            if hash in cache:
                return
            cache.add(hash)

            b_body = b.get_component(Body)
            if not b_body:
                return

            b_transform = b.get_component(Transform)
            assert b_transform
            b_velocity = b.get_component(Velocity)
            assert b_velocity
            b_body = b.get_component(Body)
            assert b_body

            ra = collision.contact_point - a_transform.position
            va = a_velocity.linear + ra.cross_scalar(a_velocity.angular)

            rb = collision.contact_point - b_transform.position
            vb = b_velocity.linear + rb.cross_scalar(b_velocity.angular)

            vr = va - vb
            vn = vr.dot(collision.normal)

            if vn > 0:
                return
            
            restitution = max(a_body.restitution, b_body.restitution)
            j = -(1 + restitution) * vn / (
                a_body.inv_mass + b_body.inv_mass +
                (ra.cross(collision.normal))**2 * a_body.inv_inertia + 
                (rb.cross(collision.normal))**2 * b_body.inv_inertia
            )

            impulse = j * collision.normal
            a_velocity.linear += impulse * a_body.inv_mass
            b_velocity.linear -= impulse * b_body.inv_mass
            a_velocity.angular += ra.cross(impulse) * a_body.inv_inertia
            b_velocity.angular -= rb.cross(impulse) * b_body.inv_inertia
            tangent = vr - (vn * collision.normal)

            tangent = tangent.normalized()
            vt = vr.dot(tangent)
            jt = -vt / (
                a_body.inv_mass + b_body.inv_mass + 
                (ra.cross(tangent))**2 * a_body.inv_inertia +
                (rb.cross(tangent))**2 * b_body.inv_inertia
            )

            friction = min(a_body.friction, b_body.friction)
            frictionImpulse = clamp(jt, -j * friction, j * friction) * tangent
            a_velocity.linear += frictionImpulse * a_body.inv_mass
            b_velocity.linear -= frictionImpulse * b_body.inv_mass
            a_velocity.angular += ra.cross(frictionImpulse) * a_body.inv_inertia
            b_velocity.angular -= rb.cross(frictionImpulse) * b_body.inv_inertia
        ...
    a(world)

# # Tangent direction (perpendicular to normal)
# tangent = vRel - (vRel.dot(normal) * normal)
# tangent = tangent.normalized()
#
# # Velocity along tangent
# vT = vRel.dot(tangent)
#
# # Tangent impulse magnitude
# jt = -vT / (
#     invMassA + invMassB + 
#     (rA.cross(tangent))**2 * invInertiaA + 
#     (rB.cross(tangent))**2 * invInertiaB
# )
#
# # Coulomb friction: |friction| ≤ μ * |normal_force|
# frictionImpulse = clamp(jt, -j * friction, j * friction) * tangent
#
# # Apply friction
# bodyA.velocity += frictionImpulse * invMassA
# bodyB.velocity -= frictionImpulse * invMassB
# bodyA.angular_velocity += rA.cross(frictionImpulse) * invInertiaA
# bodyB.angular_velocity -= rB.cross(frictionImpulse) * invInertiaB
