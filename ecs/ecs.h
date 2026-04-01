#ifndef ECS_H
#define ECS_H

#include <stddef.h>
#include "api.h"

typedef struct {
  size_t count;
  ComponentDescriptor **descriptors;
} Registry;

typedef struct {
  size_t containers_count;
  ChunkContainer *containers;
} World;

Registry *registry_create();
void registry_destroy(Registry *registry);

ComponentDescriptor *component_register(Registry *registry, size_t stride, const char* name);

World *world_create();
void world_destroy(World *world);

Entity entity_create(World *world, Archetype archetype);
void entity_remove(Entity entity);
Entity entity_move(Entity entity, World *world, Archetype new_archetype);

size_t query_chunks(World *world, Archetype archetype, ChunkContainer **out, size_t capacity);

#endif // ECS_H
