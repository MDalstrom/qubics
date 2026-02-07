#include "ecs.h"

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

// Define some components
typedef struct {
    float x, y;
} Position;

typedef struct {
    float dx, dy;
} Velocity;

int main() {
    printf("Starting ECS test...\n");

    // 1. Create a world
    World* world = world_create(16);
    assert(world != NULL);
    assert(world->archetypes_count == 0);
    assert(world->archetypes_capacity == 16);

    printf("World created.\n");

    // 2. Register components
    world_register_component(world, "Position", sizeof(Position));
    world_register_component(world, "Velocity", sizeof(Velocity));
    assert(world->component_storage.length == 2);
    printf("Components registered.\n");

    // 3. Create component masks
    uint64_t pos_only_mask_bits[] = {1};
    ComponentMask pos_only_mask = {pos_only_mask_bits, 1, 1};

    uint64_t pos_vel_mask_bits[] = {3};
    ComponentMask pos_vel_mask = {pos_vel_mask_bits, 1, 2};

    // 4. Create archetypes
    Archetype* pos_arch_template = archetype_create(pos_only_mask);
    world->archetypes[world->archetypes_count++] = *pos_arch_template;
    free(pos_arch_template);

    Archetype* pos_vel_arch_template = archetype_create(pos_vel_mask);
    world->archetypes[world->archetypes_count++] = *pos_vel_arch_template;
    free(pos_vel_arch_template);

    printf("Archetypes created.\n");

    Archetype* pos_arch = &world->archetypes[0];
    Archetype* pos_vel_arch = &world->archetypes[1];

    // 5. Create entities
    Entity e1 = entity_create(world, pos_vel_arch);
    assert(e1.chunk != NULL);
    assert(e1.idx == 0);
    assert(pos_vel_arch->tail_chunk->entities_count == 1);

    Entity e2 = entity_create(world, pos_vel_arch);
    assert(e2.idx == 1);
    assert(pos_vel_arch->tail_chunk->entities_count == 2);

    printf("Entities created.\n");

    // 6. Set component data
    size_t pos_data_idx = get_data_idx(pos_vel_mask, 0);
    size_t vel_data_idx = get_data_idx(pos_vel_mask, 1);

    Position* pos_data = (Position*)e1.chunk->data[pos_data_idx];
    pos_data[e1.idx] = (Position){1.0f, 2.0f};

    Velocity* vel_data = (Velocity*)e1.chunk->data[vel_data_idx];
    vel_data[e1.idx] = (Velocity){0.1f, 0.2f};

    pos_data[e2.idx] = (Position){3.0f, 4.0f};
    vel_data[e2.idx] = (Velocity){0.3f, 0.4f};

    printf("Component data set.\n");


    // 7. Move an entity
    Entity e1_moved = entity_move(e1, world, pos_arch);
    assert(e1_moved.chunk != NULL);
    assert(pos_vel_arch->tail_chunk->entities_count == 1);
    assert(pos_arch->tail_chunk->entities_count == 1);
    printf("Entity moved.\n");

    // 8. Check data after move
    size_t moved_pos_data_idx = get_data_idx(pos_only_mask, 0);
    Position* moved_pos_data = (Position*)e1_moved.chunk->data[moved_pos_data_idx];
    assert(moved_pos_data[e1_moved.idx].x == 1.0f);
    assert(moved_pos_data[e1_moved.idx].y == 2.0f);
    printf("Data checked after move.\n");

    // 9. Remove an entity
    entity_remove(world, e2);
    assert(pos_vel_arch->tail_chunk->entities_count == 0);
    printf("Entity removed.\n");

    // 10. Destroy the world
    world_destroy(world);
    printf("World destroyed.\n");

    printf("ECS test finished successfully!\n");

    return 0;
}
