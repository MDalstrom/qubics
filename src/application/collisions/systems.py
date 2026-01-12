from application.collisions.components import CircleCollider, EdgeCollider, BoxCollider, Collider, CollisionInfo, CollisionMatrix
from application.math import Vector
from application.transform import Transform
from application.physics import Rigidbody
from ecs.world import World
from ecs.entity import Entity
from ecs.system import for_each, singleton
import math


@for_each
def clear_collisions(_: World, __: Entity, collider: Collider) -> None:
    collider.collisions = []

@singleton
def collision_detection_system(world: World, _: Entity, collision_matrix: CollisionMatrix):

    @for_each
    def _circle_vs_circle(
        _: World,
        a_entity: Entity,
        a_collider: CircleCollider,
        a_collider_comp: Collider,
        a_transform: Transform,
    ):
        @for_each
        def inner(
            _: World,
            b_entity: Entity,
            b_collider: CircleCollider,
            b_collider_comp: Collider,
            b_transform: Transform,
        ):
            if id(a_entity) >= id(b_entity):
                return
            
            # Check collision matrix
            if not collision_matrix[(a_collider_comp.layer, b_collider_comp.layer)]:
                return

            ax, ay = a_transform.get_world_position()
            bx, by = b_transform.get_world_position()
            
            dx = bx - ax
            dy = by - ay
            dist_sq = dx * dx + dy * dy
            
            radius_sum = a_collider.radius + b_collider.radius
            
            if dist_sq < radius_sum * radius_sum:
                dist = math.sqrt(dist_sq)
                
                if dist > 0:
                    normal = Vector(dx / dist, dy / dist)
                    penetration = radius_sum - dist
                    
                    a_collider_comp.collisions.append(CollisionInfo(b_entity, Vector(-normal.x, -normal.y), penetration))
                    b_collider_comp.collisions.append(CollisionInfo(a_entity, normal, penetration))

        inner(world)

    _circle_vs_circle(world)

    @for_each
    def _circle_vs_edge(
        _: World,
        edge_entity: Entity,
        edge_collider: EdgeCollider,
        edge_collider_comp: Collider,
        edge_transform: Transform,
    ):
        @for_each
        def inner(
            _: World,
            circle_entity: Entity,
            circle_collider: CircleCollider,
            circle_collider_comp: Collider,
            circle_transform: Transform,
        ):
            if circle_entity == edge_entity:
                return
            
            if not collision_matrix[(circle_collider_comp.layer, edge_collider_comp.layer)]:
                return

            edge_x, edge_y = edge_transform.get_world_position()
            edge_angle = edge_transform.get_world_angle()
            
            edge_start_x = edge_x - edge_collider.length * math.cos(edge_angle)
            edge_start_y = edge_y - edge_collider.length * math.sin(edge_angle)
            edge_end_x = edge_x + edge_collider.length * math.cos(edge_angle)
            edge_end_y = edge_y + edge_collider.length * math.sin(edge_angle)
            
            circle_x, circle_y = circle_transform.get_world_position()
            radius = circle_collider.radius
            
            edge_dx = edge_end_x - edge_start_x
            edge_dy = edge_end_y - edge_start_y
            edge_length_sq = edge_dx * edge_dx + edge_dy * edge_dy
            
            if edge_length_sq == 0:
                return
            
            to_circle_x = circle_x - edge_start_x
            to_circle_y = circle_y - edge_start_y
            
            t = max(0, min(1, (to_circle_x * edge_dx + to_circle_y * edge_dy) / edge_length_sq))
            
            closest_x = edge_start_x + t * edge_dx
            closest_y = edge_start_y + t * edge_dy
            
            dist_x = circle_x - closest_x
            dist_y = circle_y - closest_y
            dist_sq = dist_x * dist_x + dist_y * dist_y
            
            if dist_sq < radius * radius:
                dist = math.sqrt(dist_sq)
                penetration = radius - dist
                
                if dist > 0:
                    normal = Vector(dist_x / dist, dist_y / dist)
                else:
                    edge_len = math.sqrt(edge_length_sq)
                    edge_normal = Vector(-edge_dy / edge_len, edge_dx / edge_len)
                    side = to_circle_x * (-edge_dy) + to_circle_y * edge_dx
                    normal = edge_normal if side >= 0 else Vector(-edge_normal.x, -edge_normal.y)
                
                circle_collider_comp.collisions.append(CollisionInfo(edge_entity, normal, penetration))
                
                circle_transform.set_world_position(
                    circle_x + normal.x * penetration,
                    circle_y + normal.y * penetration
                )

        inner(world)

    _circle_vs_edge(world)


    @for_each
    def _circle_vs_box(
        world: World,
        box_entity: Entity,
        box_collider: BoxCollider,
        box_collider_comp: Collider,
        box_transform: Transform,
    ):
        @for_each
        def inner(
            _: World,
            circle_entity: Entity,
            circle_collider: CircleCollider,
            circle_collider_comp: Collider,
            circle_transform: Transform,
        ):
            if circle_entity == box_entity:
                return
            
            # Check collision matrix
            if not collision_matrix[(circle_collider_comp.layer, box_collider_comp.layer)]:
                return
            
            # Get box transform
            box_x, box_y = box_transform.get_world_position()
            box_angle = box_transform.get_world_angle()
            
            # Get circle position
            circle_x, circle_y = circle_transform.get_world_position()
            radius = circle_collider.radius
            
            # Transform circle into box's local space
            dx = circle_x - box_x
            dy = circle_y - box_y
            cos_a = math.cos(-box_angle)
            sin_a = math.sin(-box_angle)
            local_x = dx * cos_a - dy * sin_a
            local_y = dx * sin_a + dy * cos_a
            
            # Find closest point on box (in local space)
            half_w = box_collider.width / 2
            half_h = box_collider.height / 2
            closest_x = max(-half_w, min(half_w, local_x))
            closest_y = max(-half_h, min(half_h, local_y))
            
            # Distance from circle center to closest point
            dist_x = local_x - closest_x
            dist_y = local_y - closest_y
            dist_sq = dist_x * dist_x + dist_y * dist_y
            
            if dist_sq < radius * radius:
                dist = math.sqrt(dist_sq)
                
                cos_a = math.cos(box_angle)
                sin_a = math.sin(box_angle)
                contact_world = Vector(
                    box_x + closest_x * cos_a - closest_y * sin_a,
                    box_y + closest_x * sin_a + closest_y * cos_a
                )
                
                if dist > 0:
                    local_normal_x = dist_x / dist
                    local_normal_y = dist_y / dist
                    
                    normal = Vector(
                        local_normal_x * cos_a - local_normal_y * sin_a,
                        local_normal_x * sin_a + local_normal_y * cos_a
                    )
                    penetration = radius - dist
                else:
                    if abs(closest_x) > abs(closest_y):
                        local_normal_x = 1.0 if closest_x > 0 else -1.0
                        local_normal_y = 0.0
                    else:
                        local_normal_x = 0.0
                        local_normal_y = 1.0 if closest_y > 0 else -1.0
                    
                    normal = Vector(
                        local_normal_x * cos_a - local_normal_y * sin_a,
                        local_normal_x * sin_a + local_normal_y * cos_a
                    )
                    penetration = radius
                
                circle_collider_comp.collisions.append(CollisionInfo(box_entity, normal, penetration, contact_world))
                box_collider_comp.collisions.append(CollisionInfo(circle_entity, Vector(-normal.x, -normal.y), penetration, contact_world))
        
        inner(world)

    _circle_vs_box(world)

    @for_each
    def _box_vs_edge(
        _: World,
        edge_entity: Entity,
        edge_collider: EdgeCollider,
        edge_collider_comp: Collider,
        edge_transform: Transform,
    ):
        @for_each
        def inner(
            _: World,
            box_entity: Entity,
            box_collider: BoxCollider,
            box_collider_comp: Collider,
            box_transform: Transform,
        ):
            if box_entity == edge_entity:
                return
            
            if not collision_matrix[(box_collider_comp.layer, edge_collider_comp.layer)]:
                return
            
            edge_matrix = edge_transform.get_world_matrix()
            e0 = edge_matrix @ Vector(-edge_collider.length, 0)
            e1 = edge_matrix @ Vector(edge_collider.length, 0)
            edge_dir = (e1 - e0).normalized()
            edge_normal = Vector(edge_dir.y, -edge_dir.x)

            box_matrix = box_transform.get_world_matrix()
            box_vertices = [box_matrix @ vertex for vertex in [
                Vector(-box_collider.width, -box_collider.height),
                Vector(box_collider.width, -box_collider.height),
                Vector(box_collider.width, box_collider.height),
                Vector(-box_collider.width, box_collider.height),
            ]]

            min_dist = float('inf')
            hit = None
            for vertex in box_vertices:
                delta = (vertex - e0).dot(edge_normal)
                if delta < min_dist:
                    min_dist = delta
                    hit = vertex
            
            if not hit:
                return

            directed = (hit - e0).dot(edge_dir)
            if directed < 0 or directed > edge_collider.length * 2:
                return

            if min_dist < 0:
                penetration = -min_dist
                collision = CollisionInfo(box_entity, edge_normal, penetration)
                box_collider_comp.collisions.append(collision)

        inner(world)
    
    _box_vs_edge(world)


@for_each
def collision_response_system(
    _: World,
    __: Entity,
    collider: Collider,
    rigidbody: Rigidbody,
    transform: Transform,
) -> None:
    if len(collider.collisions) == 0:
        return

    for collision in collider.collisions:
        normal = collision.normal

        velocity_along_normal = rigidbody.vx * normal.x + rigidbody.vy * normal.y
        if velocity_along_normal < 0:
            impulse_mag = -(1 + rigidbody.restitution) * velocity_along_normal * rigidbody.mass
            rigidbody.vx += (impulse_mag / rigidbody.mass) * normal.x
            rigidbody.vy += (impulse_mag / rigidbody.mass) * normal.y
            
            if collision.contact_point is not None:
                cx, cy = transform.get_world_position()
                rx = collision.contact_point.x - cx
                ry = collision.contact_point.y - cy
                torque = rx * (impulse_mag * normal.y) - ry * (impulse_mag * normal.x)
                rigidbody.angular_velocity += torque / rigidbody.inertia

