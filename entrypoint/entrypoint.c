#include <dirent.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

#include "api/contract.h"
#include "ecs/ecs.h"
#include "scheduler/scheduler.h"

#define FIXED_DT (1.0f / 60.0f)
#define MAX_DELTA 0.25

typedef void (*tick_fn)(void *ctx);
typedef void (*run_fn)(tick_fn);

extern ECS_World *g_world;
extern ECS_Registry *g_registry;
extern const WorldApi g_world_api;
extern const RegistryApi g_registry_api;

static Runner *g_sim_runner;
static Runner *g_render_runner;
static const char *g_build_dir;
static time_t g_stamp_mtime;
static run_fn g_run_fn;

static double g_accumulator;
static float g_elapsed;
static struct timespec g_last_tick;

static void load_lib(const char *path, BakeSystem **bake_fns, size_t *bake_count, Scheduler *sim, Scheduler *render) {
  void *lib = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
  if (!lib)
    return;

  plugin_fn plugin = dlsym(lib, "qubics_plugin");
  if (plugin) {
    PluginState ps = plugin(g_registry_api);

    *bake_fns =
        realloc(*bake_fns, (*bake_count + ps.bake_count) * sizeof(**bake_fns));
    for (size_t i = 0; i < ps.bake_count; i++)
      (*bake_fns)[(*bake_count)++] = (BakeSystem)ps.bake[i].fn;

    for (size_t i = 0; i < ps.simulation_count; i++)
      scheduler_add(
          sim, (void (*)(void *, void *))ps.simulation[i].fn,
          (ComponentSet){(const void **)ps.simulation[i].reads.generic,
                         ps.simulation[i].reads.generic_count},
          (ComponentSet){(const void **)ps.simulation[i].writes.generic,
                         ps.simulation[i].writes.generic_count});

    for (size_t i = 0; i < ps.render_count; i++)
      scheduler_add(render, (void (*)(void *, void *))ps.render[i].fn,
                    (ComponentSet){(const void **)ps.render[i].reads.generic,
                                   ps.render[i].reads.generic_count},
                    (ComponentSet){(const void **)ps.render[i].writes.generic,
                                   ps.render[i].writes.generic_count});

    free(ps.bake);
    free(ps.simulation);
    free(ps.render);
  }

  if (!g_run_fn) {
    run_fn run = dlsym(lib, "run");
    if (run)
      g_run_fn = run;
  }
}

static int load_systems(void) {
  DIR *dir = opendir(g_build_dir);
  if (!dir)
    return -1;

  if (g_registry)
    registry_destroy(g_registry);
  g_registry = registry_create();

  BakeSystem *bake_fns = NULL;
  size_t bake_count = 0;
  Scheduler *sim = scheduler_create();
  Scheduler *render = scheduler_create();

  struct dirent *pkg;
  while ((pkg = readdir(dir)) != NULL) {
    if (pkg->d_name[0] == '.')
      continue;

    char pkg_dir[1024];
    snprintf(pkg_dir, sizeof(pkg_dir), "%s/%s", g_build_dir, pkg->d_name);

    struct stat st;
    if (stat(pkg_dir, &st) != 0 || !S_ISDIR(st.st_mode))
      continue;

    DIR *inner = opendir(pkg_dir);
    if (!inner)
      continue;

    struct dirent *entry;
    while ((entry = readdir(inner)) != NULL) {
      size_t len = strlen(entry->d_name);
      if (len < 6 || strcmp(entry->d_name + len - 6, ".dylib") != 0)
        continue;
      char path[1024];
      snprintf(path, sizeof(path), "%s/%s", pkg_dir, entry->d_name);
      load_lib(path, &bake_fns, &bake_count, sim, render);
    }
    closedir(inner);
  }
  closedir(dir);

  if (g_sim_runner)
    runner_destroy(g_sim_runner);
  if (g_render_runner)
    runner_destroy(g_render_runner);
  if (g_world)
    world_destroy(g_world);

  g_sim_runner = runner_create(sim);
  g_render_runner = runner_create(render);
  g_world = world_create();

  scheduler_destroy(sim);
  scheduler_destroy(render);

  for (size_t i = 0; i < bake_count; i++)
    bake_fns[i]((WorldApi *)&g_world_api);
  free(bake_fns);

  g_accumulator = 0.0;
  g_elapsed = 0.0f;
  clock_gettime(CLOCK_MONOTONIC, &g_last_tick);

  return 0;
}

static int check_stamp(void) {
  char path[1024];
  struct stat st;
  snprintf(path, sizeof(path), "%s/.stamp", g_build_dir);
  if (stat(path, &st) != 0)
    return 0;
  if (st.st_mtime != g_stamp_mtime) {
    g_stamp_mtime = st.st_mtime;
    return 1;
  }
  return 0;
}

static void tick(void *ctx) {
  if (check_stamp())
    load_systems();
  if (!g_sim_runner || !g_render_runner)
    return;

  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  double delta = (now.tv_sec - g_last_tick.tv_sec) +
                 (now.tv_nsec - g_last_tick.tv_nsec) * 1e-9;
  g_last_tick = now;

  if (delta > MAX_DELTA)
    delta = MAX_DELTA;
  g_accumulator += delta;

  while (g_accumulator >= FIXED_DT) {
    g_elapsed += FIXED_DT;
    g_accumulator -= FIXED_DT;
    SimulationState state = {.delta_time = FIXED_DT, .elapsed = g_elapsed};
    runner_tick(g_sim_runner, (void *)&g_world_api, &state);
  }

  runner_tick(g_render_runner, (void *)&g_world_api, ctx);
}

int main(void) {
  g_build_dir = getenv("QUBICS_PATH");
  if (!g_build_dir)
    return 1;

  if (load_systems() != 0)
    return 1;
  printf("qubics set\n");
  if (!g_run_fn)
    return 1;

  check_stamp();
  g_run_fn(tick);

  runner_destroy(g_sim_runner);
  runner_destroy(g_render_runner);
  world_destroy(g_world);
  registry_destroy(g_registry);
  return 0;
}
