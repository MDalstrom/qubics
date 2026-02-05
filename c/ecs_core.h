#ifndef ECS_CORE_H
#define ECS_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Entity is just an ID */
typedef uint32_t Entity;

/* Component type identifier */
typedef uint32_t ComponentTypeId;

/* Component metadata - describes a component type */
typedef struct {
    ComponentTypeId type_id;
    const char* name;      /* For debugging */
} ComponentType;

/* Component buffer - holds a single FlatBuffer blob for all entities in chunk */
typedef struct {
    void* data;            /* Pointer to FlatBuffer blob */
    size_t size;           /* Current size of blob */
    size_t capacity;       /* Allocated capacity */
} ComponentBuffer;

/* Archetype - describes a unique combination of component types */
typedef struct {
    ComponentType** component_types;  /* Array of pointers to component types */
    uint32_t component_count;
    uint64_t hash;                    /* Hash of component type IDs for fast lookup */
    uint64_t component_mask;          /* Bitmask of component type IDs */
    
    /* Per-archetype chunk tracking for fast iteration */
    struct Chunk** chunks;            /* Chunks with this archetype */
    uint32_t chunk_count;
    uint32_t chunk_capacity;
} Archetype;

/* Chunk - contiguous storage for entities with the same archetype */
typedef struct Chunk {
    Archetype* archetype;
    uint32_t capacity;        /* Maximum entities this chunk can hold */
    uint32_t count;           /* Current number of entities */
    
    Entity* entities;         /* Array of entity IDs [capacity] */
    ComponentBuffer* buffers; /* Array of FlatBuffer blobs [component_count] */
} Chunk;

/* Entity location - where an entity is stored */
typedef struct {
    Chunk* chunk;
    uint32_t index;  /* Index within the chunk */
} EntityLocation;

/* Chunk iterator - for system queries */
typedef struct {
    Chunk** chunks;
    uint32_t count;
} ChunkIterator;

/* World - manages all entities and chunks */
typedef struct {
    /* Entity management */
    Entity next_entity_id;
    EntityLocation* entity_locations;  /* Sparse array mapping Entity -> Location */
    uint32_t entity_locations_capacity;
    
    /* Archetype management */
    Archetype** archetypes;
    uint32_t archetype_count;
    uint32_t archetype_capacity;
    
    /* Component type registry */
    ComponentType** component_types;
    uint32_t component_type_count;
    uint32_t component_type_capacity;
    
    /* Default chunk capacity */
    uint32_t default_chunk_capacity;
} World;

/* ===== World API ===== */

/* Create and destroy world */
World* world_create(uint32_t default_chunk_capacity);
void world_destroy(World* world);

/* Register component types (must be done before use) */
ComponentTypeId world_register_component_type(World* world, const char* name);

/* Entity management */
Entity world_create_entity(World* world, ComponentTypeId* component_types, uint32_t component_count);
void world_destroy_entity(World* world, Entity entity);
bool world_entity_exists(World* world, Entity entity);

/* Query chunks by component types (for systems) */
ChunkIterator world_query_chunks(World* world, ComponentTypeId* component_types, uint32_t component_count);
void chunk_iterator_free(ChunkIterator* iterator);

/* ===== Chunk API ===== */

/* Get component buffer (FlatBuffer blob) for a chunk - PRIMARY API */
void* chunk_get_component_buffer(Chunk* chunk, ComponentTypeId type_id);

/* Get chunk entity count */
uint32_t chunk_get_count(Chunk* chunk);

/* Set component buffer (used when initializing/updating FlatBuffer data) */
bool chunk_set_component_buffer(Chunk* chunk, ComponentTypeId type_id, void* data, size_t size);

/* Add entity to chunk - returns false if full */
bool chunk_add_entity(Chunk* chunk, Entity entity);

/* Remove entity from chunk (swapback - caller must update FlatBuffers accordingly) */
void chunk_remove_entity(Chunk* chunk, uint32_t index);

/* ===== Archetype API ===== */

/* Find component index in archetype (-1 if not found) */
int archetype_find_component(Archetype* archetype, ComponentTypeId type_id);

/* ===== Helper Functions ===== */

/* Compute hash for component type array (for archetype matching) */
uint64_t compute_component_hash(ComponentTypeId* types, uint32_t count);

size_t chunk_get_component_buffer_size(Chunk* chunk, ComponentTypeId type_id);

#endif /* ECS_CORE_H */
