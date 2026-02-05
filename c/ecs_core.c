#include "ecs_core.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define ARCHETYPE_MAP_SIZE 256

static void insertion_sort_component_ids(ComponentTypeId* arr, uint32_t count) {
    for (uint32_t i = 1; i < count; i++) {
        ComponentTypeId key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}

uint64_t compute_component_hash(ComponentTypeId* types, uint32_t count) {
    if (count == 0) return 0;
    
    ComponentTypeId sorted[32];
    if (count <= 32) {
        memcpy(sorted, types, sizeof(ComponentTypeId) * count);
        insertion_sort_component_ids(sorted, count);
    } else {
        return 0;
    }
    
    uint64_t hash = 14695981039346656037ULL;
    for (uint32_t i = 0; i < count; i++) {
        hash ^= sorted[i];
        hash *= 1099511628211ULL;
    }
    
    return hash;
}

static Archetype* archetype_create(ComponentType** component_types, uint32_t component_count, uint64_t hash) {
    Archetype* archetype = (Archetype*)malloc(sizeof(Archetype));
    if (!archetype) return NULL;
    
    archetype->component_count = component_count;
    archetype->hash = hash;
    archetype->component_types = (ComponentType**)malloc(sizeof(ComponentType*) * component_count);
    
    if (!archetype->component_types) {
        free(archetype);
        return NULL;
    }
    
    memcpy(archetype->component_types, component_types, sizeof(ComponentType*) * component_count);
    
    archetype->component_mask = 0;
    for (uint32_t i = 0; i < component_count; i++) {
        ComponentTypeId type_id = component_types[i]->type_id;
        if (type_id < 64) {
            archetype->component_mask |= (1ULL << type_id);
        }
    }
    
    archetype->chunks = NULL;
    archetype->chunk_count = 0;
    archetype->chunk_capacity = 0;
    
    return archetype;
}

static void archetype_destroy(Archetype* archetype) {
    if (!archetype) return;
    
    for (uint32_t i = 0; i < archetype->chunk_count; i++) {
        Chunk* chunk = archetype->chunks[i];
        
        for (uint32_t j = 0; j < chunk->archetype->component_count; j++) {
            free(chunk->buffers[j].data);
        }
        free(chunk->buffers);
        free(chunk->entities);
        free(chunk);
    }
    
    free(archetype->chunks);
    free(archetype->component_types);
    free(archetype);
}

int archetype_find_component(Archetype* archetype, ComponentTypeId type_id) {
    for (uint32_t i = 0; i < archetype->component_count; i++) {
        if (archetype->component_types[i]->type_id == type_id) {
            return (int)i;
        }
    }
    return -1;
}

static void archetype_add_chunk(Archetype* archetype, Chunk* chunk) {
    if (archetype->chunk_count >= archetype->chunk_capacity) {
        uint32_t new_capacity = archetype->chunk_capacity == 0 ? 4 : archetype->chunk_capacity * 2;
        archetype->chunks = (Chunk**)realloc(archetype->chunks, sizeof(Chunk*) * new_capacity);
        archetype->chunk_capacity = new_capacity;
    }
    
    archetype->chunks[archetype->chunk_count++] = chunk;
}

static Chunk* chunk_create(Archetype* archetype, uint32_t capacity) {
    Chunk* chunk = (Chunk*)malloc(sizeof(Chunk));
    if (!chunk) return NULL;
    
    chunk->archetype = archetype;
    chunk->capacity = capacity;
    chunk->count = 0;
    
    chunk->entities = (Entity*)malloc(sizeof(Entity) * capacity);
    if (!chunk->entities) {
        free(chunk);
        return NULL;
    }
    
    chunk->buffers = (ComponentBuffer*)calloc(archetype->component_count, sizeof(ComponentBuffer));
    if (!chunk->buffers) {
        free(chunk->entities);
        free(chunk);
        return NULL;
    }
    
    for (uint32_t i = 0; i < archetype->component_count; i++) {
        chunk->buffers[i].data = NULL;
        chunk->buffers[i].size = 0;
        chunk->buffers[i].capacity = 0;
    }
    
    archetype_add_chunk(archetype, chunk);
    
    return chunk;
}

bool chunk_add_entity(Chunk* chunk, Entity entity) {
    if (chunk->count >= chunk->capacity) {
        return false;
    }
    
    chunk->entities[chunk->count++] = entity;
    
    return true;
}

void chunk_remove_entity(Chunk* chunk, uint32_t index) {
    assert(index < chunk->count);
    
    if (chunk->count == 0) return;
    
    uint32_t last_index = chunk->count - 1;
    
    if (index != last_index) {
        chunk->entities[index] = chunk->entities[last_index];
    }
    
    chunk->count--;
}

void* chunk_get_component_buffer(Chunk* chunk, ComponentTypeId type_id) {
    int comp_index = archetype_find_component(chunk->archetype, type_id);
    if (comp_index < 0) return NULL;
    
    return chunk->buffers[comp_index].data;
}

bool chunk_set_component_buffer(Chunk* chunk, ComponentTypeId type_id, void* data, size_t size) {
    int comp_index = archetype_find_component(chunk->archetype, type_id);
    if (comp_index < 0) return false;
    
    void* buffer_copy = malloc(size);
    if (!buffer_copy) return false;
    
    memcpy(buffer_copy, data, size);
    
    if (chunk->buffers[comp_index].data) {
        free(chunk->buffers[comp_index].data);
    }
    
    chunk->buffers[comp_index].data = buffer_copy;
    chunk->buffers[comp_index].size = size;
    chunk->buffers[comp_index].capacity = size;
    
    return true;
}

size_t chunk_get_component_buffer_size(Chunk* chunk, ComponentTypeId type_id) {
    int comp_index = archetype_find_component(chunk->archetype, type_id);
    if (comp_index < 0) return 0;
    return chunk->buffers[comp_index].size;
}


World* world_create(uint32_t default_chunk_capacity) {
    World* world = (World*)malloc(sizeof(World));
    if (!world) return NULL;
    
    world->next_entity_id = 1;
    world->default_chunk_capacity = default_chunk_capacity;
    
    world->entity_locations_capacity = 1024;
    world->entity_locations = (EntityLocation*)calloc(world->entity_locations_capacity, sizeof(EntityLocation));
    
    world->archetype_capacity = 16;
    world->archetype_count = 0;
    world->archetypes = (Archetype**)malloc(sizeof(Archetype*) * world->archetype_capacity);
    
    world->component_type_capacity = 32;
    world->component_type_count = 0;
    world->component_types = (ComponentType**)malloc(sizeof(ComponentType*) * world->component_type_capacity);
    
    return world;
}

void world_destroy(World* world) {
    if (!world) return;
    
    for (uint32_t i = 0; i < world->archetype_count; i++) {
        archetype_destroy(world->archetypes[i]);
    }
    free(world->archetypes);
    
    for (uint32_t i = 0; i < world->component_type_count; i++) {
        free(world->component_types[i]);
    }
    free(world->component_types);
    
    free(world->entity_locations);
    free(world);
}

ComponentTypeId world_register_component_type(World* world, const char* name) {
    if (world->component_type_count >= world->component_type_capacity) {
        world->component_type_capacity *= 2;
        world->component_types = (ComponentType**)realloc(
            world->component_types,
            sizeof(ComponentType*) * world->component_type_capacity
        );
    }
    
    ComponentType* type = (ComponentType*)malloc(sizeof(ComponentType));
    type->type_id = world->component_type_count;
    type->name = name;
    
    world->component_types[world->component_type_count] = type;
    return world->component_type_count++;
}

static bool archetype_matches(Archetype* arch, ComponentTypeId* type_ids, uint32_t count) {
    if (arch->component_count != count) return false;
    
    for (uint32_t i = 0; i < count; i++) {
        bool found = false;
        for (uint32_t j = 0; j < arch->component_count; j++) {
            if (arch->component_types[j]->type_id == type_ids[i]) {
                found = true;
                break;
            }
        }
        if (!found) return false;
    }
    return true;
}

static Archetype* world_get_or_create_archetype(
    World* world,
    ComponentTypeId* component_type_ids,
    uint32_t component_count
) {
    uint64_t hash = compute_component_hash(component_type_ids, component_count);
    
    for (uint32_t i = 0; i < world->archetype_count; i++) {
        if (world->archetypes[i]->hash == hash) {
            if (archetype_matches(world->archetypes[i], component_type_ids, component_count)) {
                return world->archetypes[i];
            }
        }
    }
    
    ComponentType** comp_types = (ComponentType**)malloc(sizeof(ComponentType*) * component_count);
    for (uint32_t i = 0; i < component_count; i++) {
        comp_types[i] = world->component_types[component_type_ids[i]];
    }
    
    Archetype* new_archetype = archetype_create(comp_types, component_count, hash);
    free(comp_types);
    
    if (world->archetype_count >= world->archetype_capacity) {
        world->archetype_capacity *= 2;
        world->archetypes = (Archetype**)realloc(
            world->archetypes,
            sizeof(Archetype*) * world->archetype_capacity
        );
    }
    world->archetypes[world->archetype_count++] = new_archetype;
    
    return new_archetype;
}

static Chunk* world_get_or_create_chunk(World* world, Archetype* archetype) {
    for (uint32_t i = 0; i < archetype->chunk_count; i++) {
        Chunk* chunk = archetype->chunks[i];
        if (chunk->count < chunk->capacity) {
            return chunk;
        }
    }
    
    Chunk* new_chunk = chunk_create(archetype, world->default_chunk_capacity);
    
    return new_chunk;
}

Entity world_create_entity(World* world, ComponentTypeId* component_types, uint32_t component_count) {
    Entity entity = world->next_entity_id++;
    
    if (entity >= world->entity_locations_capacity) {
        uint32_t new_capacity = world->entity_locations_capacity * 2;
        world->entity_locations = (EntityLocation*)realloc(
            world->entity_locations,
            sizeof(EntityLocation) * new_capacity
        );
        memset(
            &world->entity_locations[world->entity_locations_capacity],
            0,
            sizeof(EntityLocation) * (new_capacity - world->entity_locations_capacity)
        );
        world->entity_locations_capacity = new_capacity;
    }
    
    Archetype* archetype = world_get_or_create_archetype(world, component_types, component_count);
    
    Chunk* chunk = world_get_or_create_chunk(world, archetype);
    
    uint32_t index = chunk->count;
    chunk_add_entity(chunk, entity);
    
    world->entity_locations[entity].chunk = chunk;
    world->entity_locations[entity].index = index;
    
    return entity;
}

void world_destroy_entity(World* world, Entity entity) {
    if (entity >= world->entity_locations_capacity) return;
    
    EntityLocation* location = &world->entity_locations[entity];
    if (!location->chunk) return;
    
    chunk_remove_entity(location->chunk, location->index);
    
    if (location->index < location->chunk->count) {
        Entity swapped_entity = location->chunk->entities[location->index];
        world->entity_locations[swapped_entity].index = location->index;
    }
    
    location->chunk = NULL;
    location->index = 0;
}

bool world_entity_exists(World* world, Entity entity) {
    if (entity >= world->entity_locations_capacity) return false;
    return world->entity_locations[entity].chunk != NULL;
}

ChunkIterator world_query_chunks(World* world, ComponentTypeId* component_types, uint32_t component_count) {
    uint64_t query_mask = 0;
    for (uint32_t i = 0; i < component_count; i++) {
        if (component_types[i] < 64) {
            query_mask |= (1ULL << component_types[i]);
        }
    }
    
    uint32_t total_chunk_count = 0;
    for (uint32_t i = 0; i < world->archetype_count; i++) {
        total_chunk_count += world->archetypes[i]->chunk_count;
    }
    
    if (total_chunk_count == 0) {
        return (ChunkIterator){NULL, 0};
    }
    
    Chunk** matching_chunks = (Chunk**)malloc(sizeof(Chunk*) * total_chunk_count);
    uint32_t matching_count = 0;
    
    for (uint32_t i = 0; i < world->archetype_count; i++) {
        Archetype* archetype = world->archetypes[i];
        
        if ((archetype->component_mask & query_mask) == query_mask) {
            for (uint32_t j = 0; j < archetype->chunk_count; j++) {
                matching_chunks[matching_count++] = archetype->chunks[j];
            }
        }
    }
    
    if (matching_count == 0) {
        free(matching_chunks);
        return (ChunkIterator){NULL, 0};
    }
    
    if (matching_count < total_chunk_count) {
        matching_chunks = (Chunk**)realloc(matching_chunks, sizeof(Chunk*) * matching_count);
    }
    
    return (ChunkIterator){matching_chunks, matching_count};
}

void chunk_iterator_free(ChunkIterator* iterator) {
    if (iterator && iterator->chunks) {
        free(iterator->chunks);
        iterator->chunks = NULL;
        iterator->count = 0;
    }
}
