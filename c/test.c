#include "ecs.h"
#include "network.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void test_create_and_remove_single_entity() {
  printf("Running test: %s\n", __FUNCTION__);
  World *world = world_create();
  assert(world != NULL);
  assert(world->containers_count == 0);

  ComponentDescriptor *pos = component_describe(sizeof(float) * 2);
  Archetype archetype = {.descriptors = &pos, .length = 1};

  Entity e = entity_create(world, archetype);
  assert(world->containers_count == 1);
  assert(world->containers[0].chunks_count == 1);
  assert(world->containers[0].chunks[0].entities_count == 1);
  assert(e.chunk == world->containers[0].chunks);
  assert(e.idx == 0);

  entity_remove(e);
  assert(world->containers[0].chunks[0].entities_count == 0);

  world_destroy(world);
  printf("Passed test: %s\n", __FUNCTION__);
}

void test_create_entity_fills_chunk() {
  printf("Running test: %s\n", __FUNCTION__);
  World *world = world_create();
  ComponentDescriptor *cd = component_describe(sizeof(int));
  Archetype archetype = {.descriptors = &cd, .length = 1};

  for (int i = 0; i < 4; i++) {
    entity_create(world, archetype);
  }

  assert(world->containers_count == 1);
  assert(world->containers[0].chunks_count == 1);
  assert(world->containers[0].chunks[0].entities_count == 4);

  world_destroy(world);
  printf("Passed test: %s\n", __FUNCTION__);
}

void test_create_entity_creates_new_chunk() {
  printf("Running test: %s\n", __FUNCTION__);
  World *world = world_create();
  ComponentDescriptor *cd = component_describe(sizeof(int));
  Archetype archetype = {.descriptors = &cd, .length = 1};

  for (int i = 0; i < 5; i++) {
    entity_create(world, archetype);
  }

  assert(world->containers_count == 1);
  assert(world->containers[0].chunks_count == 2);
  assert(world->containers[0].chunks[0].entities_count == 4);
  assert(world->containers[0].chunks[1].entities_count == 1);

  world_destroy(world);
  printf("Passed test: %s\n", __FUNCTION__);
}

void test_create_multiple_archetypes() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();

    ComponentDescriptor* pos = component_describe(sizeof(float) * 2);
    Archetype archetype_pos = { .descriptors = &pos, .length = 1 };
    entity_create(world, archetype_pos);

    ComponentDescriptor* vel = component_describe(sizeof(float) * 2);
    Archetype archetype_vel = { .descriptors = &vel, .length = 1 };
    entity_create(world, archetype_vel);

    assert(world->containers_count == 2);
    assert(world->containers[0].chunks_count == 1);
    assert(world->containers[0].chunks[0].entities_count == 1);
    assert(world->containers[1].chunks_count == 1);
    assert(world->containers[1].chunks[0].entities_count == 1);

    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_world_create_initializes_empty() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    assert(world != NULL);
    assert(world->containers_count == 0);
    assert(world->containers == NULL);
    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_create_entity_with_no_components() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    Archetype archetype = {.descriptors = NULL, .length = 0};

    Entity e = entity_create(world, archetype);
    assert(world->containers_count == 1);
    assert(world->containers[0].chunks_count == 1);
    assert(world->containers[0].chunks[0].entities_count == 1);
    assert(e.chunk == world->containers[0].chunks);
    assert(e.idx == 0);

    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_remove_and_add_entity() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();
    ComponentDescriptor* cd = component_describe(sizeof(int));
    Archetype archetype = { .descriptors = &cd, .length = 1 };

    Entity entities;
    entities = entity_create(world, archetype);

    entity_remove(entities);

    assert(world->containers[0].chunks[0].entities_count == 0);

    Entity new_entity = entity_create(world, archetype);
    assert(world->containers[0].chunks[0].entities_count == 1);
    assert(new_entity.idx == 0);

    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_create_and_remove_entity_with_no_components() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    Archetype archetype = {.descriptors = NULL, .length = 0};

    Entity e = entity_create(world, archetype);
    entity_remove(e);

    assert(world->containers_count == 1);
    assert(world->containers[0].chunks_count == 1);
    assert(world->containers[0].chunks[0].entities_count == 0);

    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_query_empty_world() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();
    ComponentDescriptor* cd = component_describe(sizeof(int));
    Archetype archetype = { .descriptors = &cd, .length = 1 };

    Query q = query_create(world, archetype);
    assert(q.count == 0);
    free(q.containers);

    world_destroy(world);
    free(cd);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_query_no_match() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();

    ComponentDescriptor* pos = component_describe(sizeof(float) * 2);
    Archetype archetype_pos = { .descriptors = &pos, .length = 1 };
    entity_create(world, archetype_pos);

    ComponentDescriptor* vel = component_describe(sizeof(float) * 2);
    Archetype archetype_vel = { .descriptors = &vel, .length = 1 };

    Query q = query_create(world, archetype_vel);
    assert(q.count == 0);
    free(q.containers);

    world_destroy(world);
    free(pos);
    free(vel);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_query_single_match() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();

    ComponentDescriptor* pos = component_describe(sizeof(float) * 2);
    Archetype archetype_pos = { .descriptors = &pos, .length = 1 };
    entity_create(world, archetype_pos);

    ComponentDescriptor* vel = component_describe(sizeof(float) * 2);
    Archetype archetype_vel = { .descriptors = &vel, .length = 1 };
    entity_create(world, archetype_vel);

    Query q = query_create(world, archetype_pos);
    assert(q.count == 1);
    free(q.containers);

    world_destroy(world);
    free(pos);
    free(vel);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_query_multiple_components_archetype() {
    printf("Running test: %s\n", __FUNCTION__);
    World* world = world_create();

    ComponentDescriptor* pos = component_describe(sizeof(float) * 2);
    ComponentDescriptor* vel = component_describe(sizeof(float) * 2);
    ComponentDescriptor* descriptors[] = {pos, vel};
    Archetype archetype_pv = { .descriptors = descriptors, .length = 2 };
    entity_create(world, archetype_pv);

    Query q = query_create(world, archetype_pv);
    assert(q.count == 1);
    free(q.containers);

    world_destroy(world);
    free(pos);
    free(vel);
    printf("Passed test: %s\n", __FUNCTION__);
}

ComponentDescriptor *test_pos_descriptor = NULL;
ComponentDescriptor *test_vel_descriptor = NULL;

const char* test_path_resolver(ComponentDescriptor* desc) {
    if (desc == test_pos_descriptor) {
        return "test.Position";
    } else if (desc == test_vel_descriptor) {
        return "test.Velocity";
    }
    return "unknown";
}

ComponentDescriptor* test_path_lookup(const char* path) {
    if (strcmp(path, "test.Position") == 0) {
        return component_describe(sizeof(float) * 2);
    } else if (strcmp(path, "test.Velocity") == 0) {
        return component_describe(sizeof(float) * 2);
    }
    return NULL;
}

void test_buffer_create_and_destroy() {
    printf("Running test: %s\n", __FUNCTION__);
    Buffer *buf = buffer_create(1024);
    assert(buf != NULL);
    assert(buf->data != NULL);
    assert(buf->size == 0);
    assert(buf->capacity == 1024);
    buffer_destroy(buf);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_serialize_empty_world() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    Buffer *buf = buffer_create(1024);
    
    world_serialize(world, buf, test_path_resolver);
    assert(buf->size == 0);
    
    buffer_destroy(buf);
    world_destroy(world);
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_serialize_world_with_entities() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    
    test_pos_descriptor = component_describe(sizeof(float) * 2);
    Archetype archetype = {.descriptors = &test_pos_descriptor, .length = 1};
    
    Entity e = entity_create(world, archetype);
    float *pos_data = (float*)e.chunk->buffers[0] + e.idx * 2;
    pos_data[0] = 1.0f;
    pos_data[1] = 2.0f;
    
    Buffer *buf = buffer_create(1024);
    world_serialize(world, buf, test_path_resolver);
    
    assert(buf->size > 0);
    
    buffer_destroy(buf);
    world_destroy(world);
    component_destroy(test_pos_descriptor);
    test_pos_descriptor = NULL;
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_serialize_deserialize_roundtrip() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world1 = world_create();
    
    test_pos_descriptor = component_describe(sizeof(float) * 2);
    Archetype archetype = {.descriptors = &test_pos_descriptor, .length = 1};
    
    Entity e1 = entity_create(world1, archetype);
    float *pos1 = (float*)(e1.chunk->buffers[0]) + e1.idx * 2;
    pos1[0] = 3.5f;
    pos1[1] = 7.2f;
    
    Entity e2 = entity_create(world1, archetype);
    float *pos2 = (float*)(e2.chunk->buffers[0]) + e2.idx * 2;
    pos2[0] = 10.0f;
    pos2[1] = 20.0f;
    
    Buffer *buf = buffer_create(1024);
    world_serialize(world1, buf, test_path_resolver);
    
    World *world2 = world_deserialize(buf, test_path_lookup);
    assert(world2 != NULL);
    assert(world2->containers_count == 1);
    assert(world2->containers[0].chunks[0].entities_count == 2);
    
    float *des_pos1 = (float*)(world2->containers[0].chunks[0].buffers[0]);
    assert(des_pos1[0] == 3.5f);
    assert(des_pos1[1] == 7.2f);
    assert(des_pos1[2] == 10.0f);
    assert(des_pos1[3] == 20.0f);
    
    buffer_destroy(buf);
    world_destroy(world1);
    world_destroy(world2);
    component_destroy(test_pos_descriptor);
    test_pos_descriptor = NULL;
    printf("Passed test: %s\n", __FUNCTION__);
}

void test_serialize_multiple_archetypes() {
    printf("Running test: %s\n", __FUNCTION__);
    World *world = world_create();
    
    test_pos_descriptor = component_describe(sizeof(float) * 2);
    test_vel_descriptor = component_describe(sizeof(float) * 2);
    
    Archetype archetype_pos = {.descriptors = &test_pos_descriptor, .length = 1};
    Entity e1 = entity_create(world, archetype_pos);
    float *pos = (float*)(e1.chunk->buffers[0]) + e1.idx * 2;
    pos[0] = 1.0f;
    pos[1] = 2.0f;
    
    Archetype archetype_vel = {.descriptors = &test_vel_descriptor, .length = 1};
    Entity e2 = entity_create(world, archetype_vel);
    float *vel = (float*)(e2.chunk->buffers[0]) + e2.idx * 2;
    vel[0] = 0.5f;
    vel[1] = 0.25f;
    
    Buffer *buf = buffer_create(1024);
    world_serialize(world, buf, test_path_resolver);
    assert(buf->size > 0);
    
    World *world2 = world_deserialize(buf, test_path_lookup);
    assert(world2 != NULL);
    assert(world2->containers_count == 2);
    
    buffer_destroy(buf);
    world_destroy(world);
    world_destroy(world2);
    component_destroy(test_pos_descriptor);
    component_destroy(test_vel_descriptor);
    test_pos_descriptor = NULL;
    test_vel_descriptor = NULL;
    printf("Passed test: %s\n", __FUNCTION__);
}

int main() {
  test_create_and_remove_single_entity();
  test_create_entity_fills_chunk();
  test_create_entity_creates_new_chunk();
  test_create_multiple_archetypes();
  test_world_create_initializes_empty();
  test_create_entity_with_no_components();
  test_remove_and_add_entity();
  test_create_and_remove_entity_with_no_components();
  test_query_empty_world();
  test_query_no_match();
  test_query_single_match();
  test_query_multiple_components_archetype();
  
  test_buffer_create_and_destroy();
  test_serialize_empty_world();
  test_serialize_world_with_entities();
  test_serialize_deserialize_roundtrip();
  test_serialize_multiple_archetypes();
  
  return 0;
}
