#ifndef API_H
#define API_H

#include <stddef.h>
#include <stdint.h>

struct RenderingContext;

typedef void *ComponentDescriptor;
typedef struct {
  uint8_t _opaque[16];
} Entity;

typedef struct {
  ComponentDescriptor *generic;
  size_t generic_count;
  ComponentDescriptor *shared;
  size_t shared_count;
} Archetype;

typedef struct {
  size_t count;
  void **buffers;
  size_t *counts;
  Archetype **archetypes;
} QueryResult;

typedef struct {
  Entity (*create_entity)(Archetype archetype);
  void (*remove_entity)(Entity entity);
  Entity (*move_entity)(Entity entity, Archetype new_archetype);
  QueryResult (*query_at_least)(Archetype archetype);
  void *(*get_shared_buffer)(ComponentDescriptor comp);
} WorldApi;

typedef void (*BakeSystem)(WorldApi *world);

typedef struct {
  float delta_time;
  float elapsed;
} SimulationState;

typedef void (*SimulationSystem)(WorldApi *world, SimulationState state);

typedef void (*RenderingSystem)(WorldApi *world,
                                struct RenderingContext *context);

typedef struct {
  void (*fn)(void *);
  Archetype reads;
  Archetype writes;
} SystemDescriptor;

typedef struct {
  ComponentDescriptor (*register_generic)(uint32_t id, size_t stride);
  ComponentDescriptor (*register_shared)(uint32_t id, void *buffer);
  ComponentDescriptor (*find)(uint32_t id);
} RegistryApi;

typedef struct {
  SystemDescriptor *bake;
  size_t bake_count;
  SystemDescriptor *simulation;
  size_t simulation_count;
  SystemDescriptor *render;
  size_t render_count;
} PluginState;

typedef PluginState (*plugin_fn)(RegistryApi api);

#endif // API_H
