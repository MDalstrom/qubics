#include "ecs.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

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
  return 0;
}
