#include "ecs.h"

#include <_stdio.h>
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ENTITIES_PER_CHUNK 4

int archetype_matches(Archetype a, Archetype b) {
  if (a.length != b.length) {
    return 0;
  }

  for (size_t i = 0; i < a.length; i++) {
    if (a.descriptors[i] != b.descriptors[i]) return 0;
  }

  return 1;
}

Registry *registry_create() {
  Registry *registry = malloc(sizeof(Registry));
  registry->descriptors = NULL;
  registry->count = 0;
  return registry;
}

void registry_destroy(Registry *registry) {
  for (size_t i = 0; i < registry->count; i++) {
    free(registry->descriptors[i]);
  }
  free(registry->descriptors);
  free(registry);
}

World *world_create() {
  World *result = malloc(sizeof(World));
  result->containers = NULL;
  result->containers_count = 0;
  return result;
}

void world_destroy(World *world) {
  for (size_t i = 0; i < world->containers_count; i++) {
    ChunkContainer *container = world->containers + i;
    for (size_t j = 0; j < container->chunks_count; j++) {
      Chunk *chunk = container->chunks + j;
      for (size_t k = 0; k < container->archetype.length; k++) {
        free(chunk->buffers[k]);
      }
      free(chunk->buffers);
    }
    free(container->chunks);
    free(container->archetype.descriptors);
  }
  free(world->containers);
  free(world);
}

ComponentDescriptor *component_register(Registry *registry, size_t stride, const char* name) {
  ComponentDescriptor *descriptor = malloc(sizeof(ComponentDescriptor));
  printf("stride\n");
  descriptor->stride = stride;
  descriptor->name = name;

  registry->descriptors = realloc(registry->descriptors, ++registry->count * sizeof(ComponentDescriptor*));
  registry->descriptors[registry->count - 1] = descriptor;

  return descriptor;
}

void init_chunk(Chunk *chunk, ChunkContainer* container) {
chunk->container = container;
  chunk->entities_count = 0;
  chunk->buffers = malloc(container->archetype.length * sizeof(void*));
  for (size_t i = 0; i < container->archetype.length; i++) {
    size_t buffer_size = container->archetype.descriptors[i]->stride * ENTITIES_PER_CHUNK;
    chunk->buffers[i] = malloc(buffer_size);
  }
}

Entity entity_create(World *world, Archetype archetype) { 
  ChunkContainer *target;
  for (size_t i = 0; i < world->containers_count; i++) {
    Archetype candidate = world->containers[i].archetype;
    if (archetype_matches(archetype, candidate)) {
      target = world->containers + i;
      goto skip_creating_container;
    }
  }

  world->containers = realloc(world->containers, ++world->containers_count * sizeof(ChunkContainer));
  target = world->containers + world->containers_count - 1;
  target->archetype.length = archetype.length;
  target->archetype.descriptors = malloc(archetype.length * sizeof(ComponentDescriptor*));
  memcpy(target->archetype.descriptors, archetype.descriptors, archetype.length * sizeof(ComponentDescriptor*));
  target->chunks_count = 1;
  target->chunks = malloc(1 * sizeof(Chunk));

  Chunk *chunk = target->chunks + 0; 
  init_chunk(chunk, target);
  goto create_entity;

skip_creating_container:
  if (target->chunks[target->chunks_count - 1].entities_count == ENTITIES_PER_CHUNK) {
    target->chunks = realloc(target->chunks, ++target->chunks_count * sizeof(Chunk));
    init_chunk(target->chunks + target->chunks_count - 1, target);
  }
  chunk = target->chunks + target->chunks_count - 1;

create_entity: 
  return (Entity) { chunk, chunk->entities_count++ };
}

void entity_remove(Entity entity) {
  ChunkContainer* container = entity.chunk->container;
  Chunk* last = container->chunks + container->chunks_count - 1;
  while (last->entities_count == 0) {
    last--;
  }

  size_t last_entity_idx = last->entities_count - 1;
  Archetype* archetype = &container->archetype;
  for (size_t i = 0; i < archetype->length; i++) {
    size_t stride = archetype->descriptors[i]->stride;
    memcpy(
        entity.chunk->buffers[i] + stride * entity.idx,
        last->buffers[i] + stride * last_entity_idx,
        stride
    );
  }
  entity.chunk++;
  last->entities_count--;
}

Entity entity_move(Entity entity, World *world, Archetype new_archetype) {
  entity_remove(entity);
  return entity_create(world, new_archetype);
}

size_t query_chunks(World *world, Archetype archetype, ChunkContainer **out, size_t capacity) {
  size_t count = 0;
  for (size_t i = 0; i < world->containers_count && count < capacity; i++) {
    if (archetype_matches(archetype, world->containers[i].archetype)) {
      out[count++] = world->containers + i;
    }
  }
  return count;
}

