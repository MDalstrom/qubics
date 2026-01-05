def damage_system(world, entity):
    if 'health' not in entity or 'circle_collider' not in entity:
        return
    
    collider = entity['circle_collider']
    
    for other_idx in collider['collisions']:
        other = world[other_idx]
        if 'damage' in other:
            entity['health']['hp'] -= other['damage']['value']()


def remove_dead_system(world, entity):
    if 'health' in entity and entity['health']['hp'] <= 0:
        entity['destroyed'] = True
