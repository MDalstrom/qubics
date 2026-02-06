#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>

typedef struct {
	float x, y, z, w;
} Vector4;

typedef struct {
	Vector4 m0, m1, m2, m3;
} Matrix4x4;

typedef struct {
	Matrix4x4 matrices[];
} Transform;

///
///
///

typedef struct {
	uint64_t i;
} ComponentId;

typedef struct {
	uint64_t* masks;
	size_t length;
} ComponentMask;

typedef struct {
	size_t size; 
	const char* name;
} ComponentDescriptor;

typedef struct {
	ComponentDescriptor* descriptors;
	size_t length;
} ComponentStorage;

typedef struct {
	void** data;
	size_t entities;
} Chunk;

typedef struct {
	Chunk* chunks;
	ComponentMask mask;
} Archetype;

bool contains(ComponentMask bigger, ComponentMask smaller) {
	if (smaller.length > bigger.length) {
		return false;
	}

	for (size_t i = 0; i < smaller.length; i++) {
		uint64_t mask = smaller.masks[i];
		if ((bigger.masks[i] & mask) != mask) {
			return false;
		}
	}

	return true;
}

typedef struct {

} Query;

typedef struct {
	Archetype* archetypes;
	size_t archetypes_count;
	size_t archetypes_capacity;

	size_t component_id_next;
} World;

World* world_create(size_t capacity) {
	World *result = malloc(sizeof(World));

	result->archetypes_capacity = capacity;
	result->archetypes_count = 0;
	result->archetypes = malloc(capacity * sizeof(Chunk));

	result->component_id_next = 0;

	return result;
}

void world_destroy(World* world) {
	for (size_t i = 0; i < world->archetypes_count; i++) {
		Archetype archetype = world->archetypes[i];

	}
	free(world->archetypes);
	free(world);
}


int main() {
}

