#include <stdint.h>
#include <string.h>

#include "api/contract.h"
#include "ecs/ecs.h"

_Static_assert(sizeof(ECS_Entity) == sizeof(Entity), "Entity size mismatch");

#define MAX_QUERY_RESULTS 256

ECS_World *g_world;
ECS_Registry *g_registry;

static void *g_query_buffers[MAX_QUERY_RESULTS];
static size_t g_query_counts[MAX_QUERY_RESULTS];
static Archetype *g_query_archetypes[MAX_QUERY_RESULTS];
static QueryResult g_query_result;

static ECS_Archetype to_ecs(Archetype a) {
  return (ECS_Archetype){
      .generic = (ECS_GenericComponentDescriptor **)a.generic,
      .generic_count = a.generic_count,
      .shared = (ECS_SharedComponentDescriptor **)a.shared,
      .shared_count = a.shared_count,
  };
}

static ComponentDescriptor wrap_register_generic(uint32_t id, size_t stride) {
  return generic_component_register(g_registry, stride, id);
}

static ComponentDescriptor wrap_register_shared(uint32_t id, void *buffer) {
  return shared_component_register(g_registry, buffer, id);
}

static ComponentDescriptor wrap_find(uint32_t id) {
  for (size_t i = 0; i < g_registry->count; i++)
    if (g_registry->descriptors[i]->id == id)
      return g_registry->descriptors[i];
  for (size_t i = 0; i < g_registry->shared_count; i++)
    if (g_registry->shared_descriptors[i]->id == id)
      return g_registry->shared_descriptors[i];
  return NULL;
}

static Entity wrap_create_entity(Archetype archetype) {
  ECS_Entity e = entity_create(g_world, to_ecs(archetype));
  Entity result;
  memcpy(&result, &e, sizeof(Entity));
  return result;
}

static void wrap_remove_entity(Entity entity) {
  ECS_Entity e;
  memcpy(&e, &entity, sizeof(ECS_Entity));
  entity_remove(e);
}

static Entity wrap_move_entity(Entity entity, Archetype new_archetype) {
  ECS_Entity e;
  memcpy(&e, &entity, sizeof(ECS_Entity));
  ECS_Entity moved = entity_move(e, g_world, to_ecs(new_archetype));
  Entity result;
  memcpy(&result, &moved, sizeof(Entity));
  return result;
}

static QueryResult wrap_query(Archetype archetype) {
  static ECS_ChunkContainer *containers[MAX_QUERY_RESULTS];
  size_t count =
      query_chunks(g_world, to_ecs(archetype), containers, MAX_QUERY_RESULTS);
  size_t n = 0;
  for (size_t i = 0; i < count; i++)
    for (size_t j = 0; j < containers[i]->chunks_count && n < MAX_QUERY_RESULTS;
         j++) {
      g_query_buffers[n] = (void *)containers[i]->chunks[j].buffers;
      g_query_counts[n] = containers[i]->chunks[j].entities_count;
      g_query_archetypes[n] = (Archetype *)&containers[i]->archetype;
      n++;
    }
  g_query_result = (QueryResult){
      .count = n,
      .buffers = g_query_buffers,
      .counts = g_query_counts,
      .archetypes = g_query_archetypes,
  };
  return g_query_result;
}

static void *wrap_get_shared_buffer(ComponentDescriptor comp) {
  return ((ECS_SharedComponentDescriptor *)comp)->buffer;
}

const WorldApi g_world_api = {
    .create_entity = wrap_create_entity,
    .remove_entity = wrap_remove_entity,
    .move_entity = wrap_move_entity,
    .query_at_least = wrap_query,
    .get_shared_buffer = wrap_get_shared_buffer,
};

const RegistryApi g_registry_api = {
    .register_generic = wrap_register_generic,
    .register_shared = wrap_register_shared,
    .find = wrap_find,
};
