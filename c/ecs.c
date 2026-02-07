#include "ecs.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

Archetype* archetype_create(ComponentMask mask) {
  Archetype* result = malloc(sizeof(Archetype));
  result->tail_chunk = NULL;
  result->mask.length = mask.length;
  result->mask.popcount = mask.popcount;
  result->mask.bitmasks = malloc(mask.length * sizeof(uint64_t));
  memcpy(result->mask.bitmasks, mask.bitmasks, mask.length * sizeof(uint64_t));
  return result;
}

void archetype_destroy(Archetype* archetype) {
  Chunk* chunk = archetype->tail_chunk;
  size_t n = archetype->mask.popcount;
  while (chunk != NULL) {
    for (size_t i = 0; i < n; i++) {
      free(chunk->data[i]);
    }
    free(chunk->data);
    Chunk* next_chunk = chunk->next;
    free(chunk);
    chunk = next_chunk;
  }

  free(archetype->mask.bitmasks);
}


World* world_create(size_t capacity) {
	World* result = malloc(sizeof(World));

	result->archetypes_capacity = capacity;
	result->archetypes_count = 0;
	result->archetypes = malloc(capacity * sizeof(Archetype));

  result->component_storage.descriptors = NULL;
  result->component_storage.length = 0;

	return result;
}

size_t world_register_component(World* world, const char* name, size_t stride) {
    world->component_storage.length++;
    world->component_storage.descriptors = realloc(world->component_storage.descriptors, world->component_storage.length * sizeof(ComponentDescriptor));
    world->component_storage.descriptors[world->component_storage.length - 1] = (ComponentDescriptor){name, stride};
    return world->component_storage.length - 1; // Return the ID (index) of the new component
}

Archetype* world_get_or_create_archetype(World* world, size_t* component_ids, size_t count) {
    // 1. Construct ComponentMask
    size_t max_id = 0;
    for (size_t i = 0; i < count; i++) {
        if (component_ids[i] > max_id) {
            max_id = component_ids[i];
        }
    }
    size_t mask_len = (max_id / 64) + 1;
    uint64_t* bitmasks = calloc(mask_len, sizeof(uint64_t));
    size_t popcount = 0;
    for (size_t i = 0; i < count; i++) {
        size_t id = component_ids[i];
        size_t mask_idx = id / 64;
        uint64_t bit = 1ULL << (id % 64);
        if ((bitmasks[mask_idx] & bit) == 0) {
            bitmasks[mask_idx] |= bit;
            popcount++;
        }
    }
    ComponentMask mask = {bitmasks, mask_len, popcount};

    // 2. Search for existing archetype
    for (size_t i = 0; i < world->archetypes_count; i++) {
        Archetype* arch = &world->archetypes[i];
        if (arch->mask.length == mask.length && memcmp(arch->mask.bitmasks, mask.bitmasks, mask.length * sizeof(uint64_t)) == 0) {
            free(bitmasks); // Mask already exists, free the temporary one
            return arch;
        }
    }

    // 3. If not found, create a new one
    if (world->archetypes_count == world->archetypes_capacity) {
        world->archetypes_capacity *= 2;
        world->archetypes = realloc(world->archetypes, world->archetypes_capacity * sizeof(Archetype));
    }
    
    Archetype* new_archetype_ptr = archetype_create(mask);
    world->archetypes[world->archetypes_count] = *new_archetype_ptr;
    free(new_archetype_ptr); // free the temporary archetype pointer, we copied the value
    
    // The mask was moved to the new archetype, so we shouldn't free it here
    
    return &world->archetypes[world->archetypes_count++];
}


void world_destroy(World* world) {
	for (size_t i = 0; i < world->archetypes_count; i++) {
    archetype_destroy(&world->archetypes[i]);
	}
	free(world->archetypes);
  if (world->component_storage.descriptors) {
    free(world->component_storage.descriptors);
  }
	free(world);
}



#define ENTITIES_PER_CHUNK 12
static Chunk* chunk_create(ComponentStorage storage, ComponentMask mask, struct Archetype* archetype) {
  Chunk* new_chunk = malloc(sizeof(Chunk));
  new_chunk->archetype = archetype;
  new_chunk->entities_count = 0;
  new_chunk->next = NULL;

  new_chunk->data = malloc(mask.popcount * sizeof(void*));
  size_t data_idx = 0;
  size_t component_idx = 0;
  for (size_t ordinal = 0; ordinal < mask.length; ordinal++) {
    size_t piece = mask.bitmasks[ordinal];
    while (piece > 0) {
      if ((piece & 1) == 1) {
        ComponentDescriptor descriptor = storage.descriptors[component_idx];
        size_t length = descriptor.stride * ENTITIES_PER_CHUNK;

        new_chunk->data[data_idx++] = malloc(length);
        if (data_idx == mask.popcount) {
          return new_chunk;
        }
      }
      piece >>= 1;
      component_idx++;
    }
  }
  
  assert(mask.popcount == data_idx);
  return new_chunk;
}

Entity entity_create(World* world, Archetype* archetype) {
  if (archetype->tail_chunk == NULL || archetype->tail_chunk->entities_count == ENTITIES_PER_CHUNK) {
    Chunk* new_chunk = chunk_create(world->component_storage, archetype->mask, archetype);
    new_chunk->next = archetype->tail_chunk;
    archetype->tail_chunk = new_chunk;
  }
  Entity result = { archetype->tail_chunk, archetype->tail_chunk->entities_count++ };
  return result;
}

size_t get_data_idx(ComponentMask mask, size_t component_id) {
    size_t data_idx = 0;
    size_t max_ord = component_id / 64;
    for (size_t ord = 0; ord < max_ord; ord++) {
      data_idx += __builtin_popcountll(mask.bitmasks[ord]);
    }
    uint64_t final_piece = mask.bitmasks[max_ord] & ((1ULL << (component_id % 64)) - 1);
    data_idx += __builtin_popcountll(final_piece);
    return data_idx;
}

void* entity_get_component_data_ptr(World* world, Entity entity, size_t component_id) {
    Archetype* archetype = entity.chunk->archetype;
    bool in_archetype = (archetype->mask.bitmasks[component_id / 64] >> (component_id % 64)) & 1;
    if (!in_archetype) {
        return NULL;
    }

    size_t data_idx = get_data_idx(archetype->mask, component_id);
    size_t stride = world->component_storage.descriptors[component_id].stride;

    if (stride == 0) {
        return NULL; // Or a special value for zero-sized components
    }

    return (char*)entity.chunk->data[data_idx] + entity.idx * stride;
}

void entity_remove(World* world, Entity entity) {
    Chunk* chunk = entity.chunk;
    size_t entity_idx_to_remove = entity.idx;
    size_t last_entity_idx = --chunk->entities_count;

    if (entity_idx_to_remove == last_entity_idx) {
        return;
    }

    Archetype* archetype = chunk->archetype;

    for (size_t comp_id = 0; comp_id < world->component_storage.length; comp_id++) {
        bool in_archetype = (archetype->mask.bitmasks[comp_id / 64] >> (comp_id % 64)) & 1;
        if (in_archetype) {
            size_t data_idx = get_data_idx(archetype->mask, comp_id);
            size_t stride = world->component_storage.descriptors[comp_id].stride;

            if (stride > 0) {
                void* dst_ptr = (char*)chunk->data[data_idx] + entity_idx_to_remove * stride;
                void* src_ptr = (char*)chunk->data[data_idx] + last_entity_idx * stride;
                memcpy(dst_ptr, src_ptr, stride);
            }
        }
    }
    
}

Entity entity_move(Entity entity, World* world, Archetype* new_archetype) {
  Archetype* source_archetype = entity.chunk->archetype;


  Entity new_entity = entity_create(world, new_archetype);

  for (size_t comp_id = 0; comp_id < world->component_storage.length; comp_id++) {
    bool in_source = (source_archetype->mask.bitmasks[comp_id / 64] >> (comp_id % 64)) & 1;
    bool in_target = (new_archetype->mask.bitmasks[comp_id / 64] >> (comp_id % 64)) & 1;

    if (in_source && in_target) {
      size_t source_data_idx = get_data_idx(source_archetype->mask, comp_id);
      size_t target_data_idx = get_data_idx(new_archetype->mask, comp_id);
      size_t stride = world->component_storage.descriptors[comp_id].stride;

      if (stride > 0) {
        void* src_ptr = (char*)entity.chunk->data[source_data_idx] + entity.idx * stride;
        void* dst_ptr = (char*)new_entity.chunk->data[target_data_idx] + new_entity.idx * stride;
        memcpy(dst_ptr, src_ptr, stride);
      }
    }
  }
  
  entity_remove(world, entity);

  return new_entity;
}
