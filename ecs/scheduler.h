#ifndef SCHEDULER_H
#define SCHEDULER_H

#include "ecs.h"
#include <stddef.h>

#define SCHEDULER_THREADS 4

typedef void (*SystemFn)(void *world, void *ctx);

typedef struct {
  SystemFn run;
  Archetype reads;
  Archetype writes;
} SystemDescriptor;

typedef struct {
  size_t count;
  SystemDescriptor *descriptors;
} Scheduler;

typedef struct {
  SystemFn *stages;
  size_t count;
  size_t *stage_ends;
  size_t stages_count;
} Runner;

Scheduler *schedule_create();
void schedule_destroy(Scheduler *scheduler);

void schedule_system(Scheduler *scheduler, SystemDescriptor descriptor);

Runner *runner_create(Scheduler *scheduler);
void runner_tick(Runner *runner, World *world, void *ctx);
void runner_destroy(Runner *runner);

#endif // SCHEDULER_H
