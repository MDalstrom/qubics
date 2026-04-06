#include "ecs.h"

#include <assert.h>
#include <stdlib.h>
#include <string.h>

#define ENTITIES_PER_CHUNK 4

int archetype_matches(ECS_Archetype a, ECS_Archetype b) {
  if (a.generic_count != b.generic_count || a.shared_count != b.shared_count) {
    return 0;
  }

  for (size_t i = 0; i < a.generic_count; i++) {
    if (a.generic[i] != b.generic[i]) return 0;
  }

  for (size_t i = 0; i < a.shared_count; i++) {
    if (a.shared[i] != b.shared[i]) return 0;
  }

  return 1;
}

ECS_Registry *registry_create() {
  ECS_Registry *registry = malloc(sizeof(ECS_Registry));
  registry->descriptors = NULL;
  registry->count = 0;
  registry->shared_descriptors = NULL;
  registry->shared_count = 0;
  return registry;
}

void registry_destroy(ECS_Registry *registry) {
  for (size_t i = 0; i < registry->count; i++) {
    free(registry->descriptors[i]);
  }
  free(registry->descriptors);
  for (size_t i = 0; i < registry->shared_count; i++) {
    free(registry->shared_descriptors[i]);
  }
  free(registry->shared_descriptors);
  free(registry);
}

ECS_World *world_create() {
  ECS_World *result = malloc(sizeof(ECS_World));
  result->containers = NULL;
  result->containers_count = 0;
  return result;
}

void world_destroy(ECS_World *world) {
  for (size_t i = 0; i < world->containers_count; i++) {
    ECS_ChunkContainer *container = world->containers + i;
    for (size_t j = 0; j < container->chunks_count; j++) {
      ECS_Chunk *chunk = container->chunks + j;
      for (size_t k = 0; k < container->archetype.generic_count; k++) {
        free(chunk->buffers[k]);
      }
      free(chunk->buffers);
    }
    free(container->chunks);
    free(container->archetype.generic);
    free(container->archetype.shared);
  }
  free(world->containers);
  free(world);
}

ECS_GenericComponentDescriptor *generic_component_register(ECS_Registry *registry, size_t stride, uint32_t id) {
  ECS_GenericComponentDescriptor *descriptor = malloc(sizeof(ECS_GenericComponentDescriptor));
  descriptor->stride = stride;
  descriptor->id = id;

  registry->descriptors = realloc(registry->descriptors, ++registry->count * sizeof(ECS_GenericComponentDescriptor*));
  registry->descriptors[registry->count - 1] = descriptor;

  return descriptor;
}

ECS_SharedComponentDescriptor *shared_component_register(ECS_Registry *registry, void *buffer, uint32_t id) {
  ECS_SharedComponentDescriptor *descriptor = malloc(sizeof(ECS_SharedComponentDescriptor));
  descriptor->buffer = buffer;
  descriptor->id = id;

  registry->shared_descriptors = realloc(registry->shared_descriptors, ++registry->shared_count * sizeof(ECS_SharedComponentDescriptor*));
  registry->shared_descriptors[registry->shared_count - 1] = descriptor;

  return descriptor;
}

void init_chunk(ECS_Chunk *chunk, ECS_ChunkContainer* container) {
chunk->container = container;
  chunk->entities_count = 0;
  chunk->buffers = malloc(container->archetype.generic_count * sizeof(void*));
  for (size_t i = 0; i < container->archetype.generic_count; i++) {
    size_t buffer_size = container->archetype.generic[i]->stride * ENTITIES_PER_CHUNK;
    chunk->buffers[i] = malloc(buffer_size);
  }
}

ECS_Entity entity_create(ECS_World *world, ECS_Archetype archetype) { 
  ECS_ChunkContainer *target;
  for (size_t i = 0; i < world->containers_count; i++) {
    ECS_Archetype candidate = world->containers[i].archetype;
    if (archetype_matches(archetype, candidate)) {
      target = world->containers + i;
      goto skip_creating_container;
    }
  }

  world->containers = realloc(world->containers, ++world->containers_count * sizeof(ECS_ChunkContainer));
  target = world->containers + world->containers_count - 1;

  target->archetype.generic_count = archetype.generic_count;
  target->archetype.generic = malloc(archetype.generic_count * sizeof(ECS_GenericComponentDescriptor*));
  memcpy(target->archetype.generic, archetype.generic, archetype.generic_count * sizeof(ECS_GenericComponentDescriptor*));

  target->archetype.shared_count = archetype.shared_count;
  target->archetype.shared = malloc(archetype.shared_count * sizeof(ECS_SharedComponentDescriptor*));
  memcpy(target->archetype.shared, archetype.shared, archetype.shared_count * sizeof(ECS_SharedComponentDescriptor*));

  target->chunks_count = 1;
  target->chunks = malloc(1 * sizeof(ECS_Chunk));

  ECS_Chunk *chunk = target->chunks + 0; 
  init_chunk(chunk, target);
  goto create_entity;

skip_creating_container:
  if (target->chunks[target->chunks_count - 1].entities_count == ENTITIES_PER_CHUNK) {
    target->chunks = realloc(target->chunks, ++target->chunks_count * sizeof(ECS_Chunk));
    init_chunk(target->chunks + target->chunks_count - 1, target);
  }
  chunk = target->chunks + target->chunks_count - 1;

create_entity: 
  return (ECS_Entity) { chunk, chunk->entities_count++ };
}

void entity_remove(ECS_Entity entity) {
  ECS_ChunkContainer* container = entity.chunk->container;
  ECS_Chunk* last = container->chunks + container->chunks_count - 1;
  while (last->entities_count == 0) {
    last--;
  }

  size_t last_entity_idx = last->entities_count - 1;
  ECS_Archetype* archetype = &container->archetype;
  for (size_t i = 0; i < archetype->generic_count; i++) {
    size_t stride = archetype->generic[i]->stride;
    memcpy(
        entity.chunk->buffers[i] + stride * entity.idx,
        last->buffers[i] + stride * last_entity_idx,
        stride
    );
  }
  entity.chunk++;
  last->entities_count--;
}

ECS_Entity entity_move(ECS_Entity entity, ECS_World *world, ECS_Archetype new_archetype) {
  entity_remove(entity);
  return entity_create(world, new_archetype);
}

size_t query_chunks(ECS_World *world, ECS_Archetype archetype, ECS_ChunkContainer **out, size_t capacity) {
  size_t count = 0;
  for (size_t i = 0; i < world->containers_count && count < capacity; i++) {
    if (archetype_matches(archetype, world->containers[i].archetype)) {
      out[count++] = world->containers + i;
    }
  }
  return count;
}

