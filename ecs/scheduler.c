#include "scheduler.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

static bool descriptors_overlap(Archetype *a, Archetype *b) {
  for (size_t i = 0; i < a->length; i++) {
    for (size_t j = 0; j < b->length; j++) {
      if (a->descriptors[i] == b->descriptors[j]) return true;
    }
  }
  return false;
}

static bool systems_conflict(SystemDescriptor *a, SystemDescriptor *b) {
  return descriptors_overlap(&a->writes, &b->reads) ||
         descriptors_overlap(&b->writes, &a->reads) ||
         descriptors_overlap(&a->writes, &b->writes);
}

static size_t systems_sort(SystemDescriptor *systems, size_t count, size_t *stage_ends) {
  size_t assignment[count];
  size_t stages_count = 0;

  for (size_t i = 0; i < count; i++) {
    size_t stage = 0;
    for (; stage < stages_count; stage++) {
      bool conflicts = false;
      for (size_t j = 0; j < i; j++) {
        if (assignment[j] == stage && systems_conflict(&systems[i], &systems[j])) {
          conflicts = true;
          break;
        }
      }
      if (!conflicts) break;
    }
    assignment[i] = stage;
    if (stage == stages_count) stages_count++;
  }

  for (size_t i = 1; i < count; i++) {
    SystemDescriptor sys = systems[i];
    size_t stage = assignment[i];
    size_t j = i;
    while (j > 0 && assignment[j - 1] > stage) {
      systems[j] = systems[j - 1];
      assignment[j] = assignment[j - 1];
      j--;
    }
    systems[j] = sys;
    assignment[j] = stage;
  }

  size_t s = 0;
  for (size_t i = 0; i < count; i++) {
    if (i == count - 1 || assignment[i] != assignment[i + 1]) {
      stage_ends[s++] = i + 1;
    }
  }

  return stages_count;
}

Scheduler *schedule_create() {
  Scheduler *scheduler = malloc(sizeof(Scheduler));
  scheduler->count = 0;
  scheduler->descriptors = NULL;
  return scheduler;
}

void schedule_destroy(Scheduler *scheduler) {
  free(scheduler->descriptors);
  free(scheduler);
}

void schedule_system(Scheduler *scheduler, SystemDescriptor descriptor) {
  scheduler->descriptors = realloc(
      scheduler->descriptors,
      ++scheduler->count * sizeof(SystemDescriptor)
  );
  scheduler->descriptors[scheduler->count - 1] = descriptor;
}

Runner *runner_create(Scheduler *scheduler) {
  size_t count = scheduler->count;

  SystemDescriptor *sorted = malloc(count * sizeof(SystemDescriptor));
  memcpy(sorted, scheduler->descriptors, count * sizeof(SystemDescriptor));

  size_t *stage_ends = malloc(count * sizeof(size_t));
  size_t stages_count = systems_sort(sorted, count, stage_ends);

  SystemFn *stages = malloc(count * sizeof(SystemFn));
  for (size_t i = 0; i < count; i++) {
    stages[i] = sorted[i].run;
  }
  free(sorted);

  Runner *runner = malloc(sizeof(Runner));
  runner->stages = stages;
  runner->count = count;
  runner->stage_ends = stage_ends;
  runner->stages_count = stages_count;
  return runner;
}

typedef struct {
  Runner *runner;
  World *world;
  void *ctx;
  size_t stage_start;
  size_t stage_end;
  atomic_size_t *cursor;
} TickArgs;

static void *tick_thread(void *arg) {
  TickArgs *a = arg;
  size_t i;
  while ((i = atomic_fetch_add(a->cursor, 1)) < a->stage_end) {
    a->runner->stages[i](a->world, a->ctx);
  }
  return NULL;
}

void runner_tick(Runner *runner, World *world, void *ctx) {
  pthread_t threads[SCHEDULER_THREADS];
  TickArgs args[SCHEDULER_THREADS];
  atomic_size_t cursor;

  size_t start = 0;
  for (size_t s = 0; s < runner->stages_count; s++) {
    size_t end = runner->stage_ends[s];
    atomic_init(&cursor, start);

    for (int t = 0; t < SCHEDULER_THREADS; t++) {
      args[t] = (TickArgs){ runner, world, ctx, start, end, &cursor };
      pthread_create(&threads[t], NULL, tick_thread, &args[t]);
    }
    for (int t = 0; t < SCHEDULER_THREADS; t++) {
      pthread_join(threads[t], NULL);
    }

    start = end;
  }
}

void runner_destroy(Runner *runner) {
  free(runner->stages);
  free(runner->stage_ends);
  free(runner);
}
