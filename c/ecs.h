#ifndef ECS_H
#define ECS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
  size_t stride;
} ComponentDescriptor;

typedef struct {
  size_t length;
  ComponentDescriptor **descriptors;
} Archetype;


struct ChunkContainer;

typedef struct {
  size_t entities_count;
  struct ChunkContainer *container;
  void **buffers;
} Chunk;

typedef struct ChunkContainer {
  Archetype archetype;
  size_t chunks_count;
  Chunk *chunks;
} ChunkContainer;

typedef struct {
  size_t containers_count;
  ChunkContainer *containers;
} World;

typedef struct {
  size_t count;
  ChunkContainer **containers;
} Query;

typedef struct {
  Chunk *chunk;
  size_t idx;
} Entity;

World *world_create();
void world_destroy(World *world);

ComponentDescriptor *component_describe(size_t stride);
void component_destroy(ComponentDescriptor* descriptor);

Entity entity_create(World *world, Archetype archetype);
void entity_remove(Entity entity);
Entity entity_move(Entity entity, World *world, Archetype new_archetype);

Query query_create(World *world, Archetype archetype);

#endif // ECS_H
