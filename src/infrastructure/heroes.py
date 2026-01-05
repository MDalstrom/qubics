COLLISION_LAYER_SPHERE = 1 << 0
COLLISION_LAYER_WEAPON = 1 << 1
COLLISION_LAYER_BOUNDS = 1 << 2


def add_transform(entity, x, y, angle=0.0):
    entity['transform'] = {'x': x, 'y': y, 'angle': angle}


def add_velocity(entity, vx, vy, angular_velocity=0.0):
    entity['velocity'] = {'vx': vx, 'vy': vy, 'angular_velocity': angular_velocity}


def add_health(entity, hp):
    entity['health'] = {'hp': hp}


def add_damage(entity, damage_value):
    entity['damage'] = {'value': lambda: damage_value}


def add_circle_collider(entity, radius, layer, mask):
    entity['circle_collider'] = {
        'radius': radius,
        'layer': layer,
        'mask': mask,
        'collisions': []
    }


def add_renderable(entity, shape, color, **params):
    entity['renderable'] = {'shape': shape, 'color': color, **params}


def add_parent(entity, owner_ref, offset_distance=0, offset_angle=0):
    entity['parent'] = {
        'owner': owner_ref,
        'offset_distance': offset_distance,
        'offset_angle': offset_angle
    }


def create_armer(world, hp, x, y, radius, color, vx, vy):
    armer = {}
    add_transform(armer, x, y)
    add_velocity(armer, vx, vy)
    add_health(armer, hp)
    add_damage(armer, 5)
    add_circle_collider(armer, radius, COLLISION_LAYER_SPHERE, COLLISION_LAYER_SPHERE | COLLISION_LAYER_BOUNDS)
    add_renderable(armer, 'circle', color, radius=radius)
    
    return world.add(armer)


def create_swordsman(world, hp, x, y, radius, color, vx, vy):
    swordsman = {}
    add_transform(swordsman, x, y)
    add_velocity(swordsman, vx, vy, angular_velocity=0.05)
    add_health(swordsman, hp)
    add_circle_collider(swordsman, radius, COLLISION_LAYER_SPHERE, COLLISION_LAYER_SPHERE | COLLISION_LAYER_BOUNDS)
    add_renderable(swordsman, 'circle', color, radius=radius)
    
    swordsman_ref = world.add(swordsman)
    
    sword = {}
    add_transform(sword, 0, 0)
    add_damage(sword, 10)
    add_circle_collider(sword, 10, COLLISION_LAYER_WEAPON, COLLISION_LAYER_SPHERE)
    add_renderable(sword, 'circle', (50, 50, 50), radius=10)
    add_parent(sword, swordsman_ref, offset_distance=radius + 10, offset_angle=0)
    world.add(sword)
    
    return swordsman_ref
