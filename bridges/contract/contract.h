#ifndef BRIDGE_CONTRACT_H
#define BRIDGE_CONTRACT_H

#include <stddef.h>
#include "ecs/scheduler.h"

typedef struct {
    SystemDescriptor *descriptors;
    size_t count;
} PluginSystems;

typedef PluginSystems (*plugin_fn)(Registry *registry);

#endif /* BRIDGE_CONTRACT_H */
