import unittest

from application.collisions.components import Collider, CollisionInfo
from application.math import Vector
from application.physics.rigidbody import Rigidbody, apply_collisions_forces
from application.transform import Transform
from ecs.entity import Entity
from ecs.world import World


class PhysicsSystemTest(unittest.TestCase):
    def test_offcenter_collision_applies_impulse_and_friction(self):
        world = World(timestep=1.0)

        a = Entity("a")
        a_transform = Transform()
        a_rigidbody = Rigidbody(
            velocity=Vector(3.0, -2.0),
            center_of_mass=Vector(0.0, 0.0),
            mass=1.0,
            angular_velocity=0.0,
            angular_damping=0.0,
            inertia=1.0,
            friction=1.0,
            restitution=1.0,
        )
        a_collider = Collider()
        a.add_component(a_transform)
        a.add_component(a_rigidbody)
        a.add_component(a_collider)

        b = Entity("b")
        b_transform = Transform()
        b_rigidbody = Rigidbody(
            velocity=Vector(0.0, 0.0),
            center_of_mass=Vector(0.0, 0.0),
            mass=0.0,
            angular_velocity=0.0,
            angular_damping=0.0,
            inertia=0.0,
            friction=0.0,
            restitution=1.0,
        )
        b_collider = Collider()
        b.add_component(b_transform)
        b.add_component(b_rigidbody)
        b.add_component(b_collider)

        collision = CollisionInfo(
            other=b,
            normal=Vector(0.0, 1.0),
            penetration=0.0,
            contact_point=Vector(1.0, 0.0),
        )
        a_collider.collisions.append(collision)

        world.add(a)
        world.add(b)

        apply_collisions_forces(world)

        self.assertAlmostEqual(a_rigidbody.velocity.x, 2.0, places=5)
        self.assertAlmostEqual(a_rigidbody.velocity.y, 0.0, places=5)
        self.assertAlmostEqual(a_rigidbody.angular_velocity, 2.0, places=5)
        self.assertAlmostEqual(b_rigidbody.velocity.x, 0.0, places=5)
        self.assertAlmostEqual(b_rigidbody.velocity.y, 0.0, places=5)
        self.assertAlmostEqual(b_rigidbody.angular_velocity, 0.0, places=5)

    def test_head_on_collision_swaps_velocities(self):
        world = World(timestep=1.0)

        a = Entity("a")
        a_transform = Transform()
        a_rigidbody = Rigidbody(
            velocity=Vector(1.0, 0.0),
            center_of_mass=Vector(0.0, 0.0),
            mass=1.0,
            angular_velocity=0.0,
            angular_damping=0.0,
            inertia=1.0,
            friction=0.0,
            restitution=1.0,
        )
        a_collider = Collider()
        a.add_component(a_transform)
        a.add_component(a_rigidbody)
        a.add_component(a_collider)

        b = Entity("b")
        b_transform = Transform()
        b_rigidbody = Rigidbody(
            velocity=Vector(-1.0, 0.0),
            center_of_mass=Vector(0.0, 0.0),
            mass=1.0,
            angular_velocity=0.0,
            angular_damping=0.0,
            inertia=1.0,
            friction=0.0,
            restitution=1.0,
        )
        b_collider = Collider()
        b.add_component(b_transform)
        b.add_component(b_rigidbody)
        b.add_component(b_collider)

        collision = CollisionInfo(
            other=b,
            normal=Vector(1.0, 0.0),
            penetration=0.0,
            contact_point=Vector(0.0, 0.0),
        )
        a_collider.collisions.append(collision)

        world.add(a)
        world.add(b)

        apply_collisions_forces(world)

        self.assertAlmostEqual(a_rigidbody.velocity.x, -1.0, places=5)
        self.assertAlmostEqual(b_rigidbody.velocity.x, 1.0, places=5)
        self.assertAlmostEqual(a_rigidbody.angular_velocity, 0.0, places=5)
        self.assertAlmostEqual(b_rigidbody.angular_velocity, 0.0, places=5)

    def test_penetration_correction_moves_entities_apart(self):
        world = World(timestep=1.0)

        a = Entity("a")
        a_transform = Transform()
        a_rigidbody = Rigidbody(
            velocity=Vector.zero(),
            center_of_mass=Vector.zero(),
            mass=1.0,
            angular_velocity=0.0,
            inertia=1.0,
            friction=0.0,
            restitution=0.0,
        )
        a_collider = Collider()
        a.add_component(a_transform)
        a.add_component(a_rigidbody)
        a.add_component(a_collider)

        b = Entity("b")
        b_transform = Transform()
        b_rigidbody = Rigidbody(
            velocity=Vector.zero(),
            center_of_mass=Vector.zero(),
            mass=1.0,
            angular_velocity=0.0,
            inertia=1.0,
            friction=0.0,
            restitution=0.0,
        )
        b_collider = Collider()
        b.add_component(b_transform)
        b.add_component(b_rigidbody)
        b.add_component(b_collider)

        collision = CollisionInfo(
            other=b,
            normal=Vector(0.0, 1.0),
            penetration=0.1,
            contact_point=Vector.zero(),
        )
        a_collider.collisions.append(collision)

        world.add(a)
        world.add(b)

        apply_collisions_forces(world)

        ax, ay = a_transform.get_world_position()
        bx, by = b_transform.get_world_position()
        self.assertLess(ay, 0.0)
        self.assertGreater(by, 0.0)


if __name__ == "__main__":
    unittest.main()
