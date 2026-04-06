#ifndef ECS_H
#define ECS_H

#include <stddef.h>
#include <stdint.h>

typedef void* ECS_Buffer;

typedef struct {
  size_t stride;
  uint32_t id;
} ECS_GenericComponentDescriptor;

typedef struct {
  ECS_Buffer buffer;
  uint32_t id;
} ECS_SharedComponentDescriptor;

typedef struct {
  ECS_GenericComponentDescriptor **generic;
  size_t generic_count;
  ECS_SharedComponentDescriptor **shared;
  size_t shared_count;
} ECS_Archetype;

typedef struct {
  size_t count;
  ECS_GenericComponentDescriptor **descriptors;
  size_t shared_count;
  ECS_SharedComponentDescriptor **shared_descriptors;
} ECS_Registry;

typedef struct {
  size_t entities_count;
  struct ECS_ChunkContainer *container;
  void **buffers;
} ECS_Chunk;

typedef struct ECS_ChunkContainer {
  ECS_Archetype archetype;
  size_t chunks_count;
  ECS_Chunk *chunks;
} ECS_ChunkContainer;

typedef struct {
  ECS_Chunk *chunk;
  size_t idx;
} ECS_Entity;

typedef struct {
  size_t containers_count;
  ECS_ChunkContainer *containers;
} ECS_World;

ECS_Registry *registry_create();
void registry_destroy(ECS_Registry *registry);

ECS_GenericComponentDescriptor *generic_component_register(ECS_Registry *registry, size_t stride, uint32_t id);
ECS_SharedComponentDescriptor *shared_component_register(ECS_Registry *registry, void *buffer, uint32_t id);

ECS_World *world_create();
void world_destroy(ECS_World *world);

ECS_Entity entity_create(ECS_World *world, ECS_Archetype archetype);
void entity_remove(ECS_Entity entity);
ECS_Entity entity_move(ECS_Entity entity, ECS_World *world, ECS_Archetype new_archetype);

size_t query_chunks(ECS_World *world, ECS_Archetype archetype, ECS_ChunkContainer **out, size_t capacity);

#endif // ECS_H
