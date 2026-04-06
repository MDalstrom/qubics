#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stddef.h>

#define SCHEDULER_THREADS 4

typedef struct { const void **tags; size_t count; } ComponentSet;

typedef struct Scheduler Scheduler;
typedef struct Runner Runner;

Scheduler *scheduler_create();
void scheduler_destroy(Scheduler *scheduler);

void scheduler_add(Scheduler *scheduler, void (*fn)(void *world, void *ctx),
                   ComponentSet reads, ComponentSet writes);

Runner *runner_create(Scheduler *scheduler);
void runner_tick(Runner *runner, void *world, void *ctx);
void runner_destroy(Runner *runner);

#endif // SCHEDULER_H
