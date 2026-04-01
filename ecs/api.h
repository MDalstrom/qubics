#ifndef API_H
#define API_H

#include <stddef.h>

struct WorldApi;

typedef void (*SystemFn)(struct WorldApi *world, void *ctx);

typedef struct {
  size_t stride;
  const char* name;
} ComponentDescriptor;

typedef struct {
  size_t length;
  ComponentDescriptor **descriptors;
} Archetype;

typedef struct {
  SystemFn run;
  Archetype reads;
  Archetype writes;
} SystemDescriptor;

typedef struct {
  size_t entities_count;
  struct ChunkContainer *container;
  void **buffers;
} Chunk;

typedef struct ChunkContainer {
  Archetype archetype;
  size_t chunks_count;
  Chunk *chunks;
} ChunkContainer;

typedef struct {
  Chunk *chunk;
  size_t idx;
} Entity;

typedef struct WorldApi {
  Entity (*create_entity)(Archetype archetype);
  void (*remove_entity)(Entity entity);
  Entity (*move_entity)(Entity entity, Archetype new_archetype);
  size_t (*query)(Archetype archetype, ChunkContainer **out, size_t capacity);
} WorldApi;

typedef struct {
  ComponentDescriptor* (*component_register)(size_t stride, const char* name);
} RegistryApi;

typedef struct {
    SystemDescriptor *descriptors;
    size_t count;
} PluginState;

typedef PluginState (*plugin_fn)(RegistryApi registry);

#endif // API_H
