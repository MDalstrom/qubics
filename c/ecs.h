#ifndef ECS_H
#define ECS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Core component-related structs
typedef struct {
	float x, y, z, w;
} Vector4;

typedef struct {
	Vector4 m0, m1, m2, m3;
} Matrix4x4;

typedef struct {
	Matrix4x4 matrix;
} Transform;

typedef struct {
    int value;
} TestComponent;

// --- ECS Core Structs ---

typedef struct {
	uint64_t* bitmasks;
	size_t length;
  size_t popcount;
} ComponentMask;

typedef struct {
	const char* name;
  size_t stride; 
} ComponentDescriptor;

typedef struct {
	ComponentDescriptor* descriptors;
	size_t length;
} ComponentStorage;

struct Archetype;

typedef struct Chunk {
	void** data;
	size_t entities_count;

	struct Chunk* next;
	struct Archetype* archetype;
} Chunk;

typedef struct Archetype {
	Chunk* tail_chunk;
	ComponentMask mask;
} Archetype;

typedef struct {
  Chunk* chunk;
  size_t idx;
} Entity;

typedef struct {
	Archetype* archetypes;
	size_t archetypes_count;
	size_t archetypes_capacity;

  ComponentStorage component_storage;
} World;


// --- Function Prototypes ---

Archetype* archetype_create(ComponentMask mask);
void archetype_destroy(Archetype* archetype);

World* world_create(size_t capacity);
void world_destroy(World* world);

size_t world_register_component(World* world, const char* name, size_t stride);
Archetype* world_get_or_create_archetype(World* world, size_t* component_ids, size_t count);

Entity entity_create(World* world, Archetype* archetype);
void* entity_get_component_data_ptr(World* world, Entity entity, size_t component_id);
void entity_remove(World* world, Entity entity);
Entity entity_move(Entity entity, World* world, Archetype* new_archetype);
size_t get_data_idx(ComponentMask mask, size_t component_id);


#endif // ECS_H