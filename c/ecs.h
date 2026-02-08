#ifndef ECS_H
#define ECS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
  size_t stride;
} ComponentDescriptor;

typedef struct {
  ComponentDescriptor **descriptors;
  size_t length;
} Archetype;


struct ChunkContainer;

typedef struct {
  size_t entities_count;
  struct ChunkContainer *container;
  void **buffers;
} Chunk;

typedef struct ChunkContainer {
  Chunk *chunks;
  size_t chunks_count;
  Archetype archetype;
} ChunkContainer;

typedef struct {
  ChunkContainer *containers;
  size_t containers_count;
} World;

typedef struct {
  ChunkContainer **containers;
  size_t count;
} Query;

typedef struct {
  Chunk *chunk;
  size_t idx;
} Entity;

World *world_create();
void world_destroy(World *world);

ComponentDescriptor *component_describe(size_t stride);

Entity entity_create(World *world, Archetype archetype);
void entity_remove(Entity entity);
Entity entity_move(Entity entity, World *world, Archetype *new_archetype);

Query query_create(World *world, Archetype archetype);

#endif // ECS_H
