#include <dirent.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "backend-contracts/contract.h"
#include "ecs/ecs.h"
#include "ecs/scheduler.h"

static struct {
    Registry            *(*registry_create)(void);
    void                 (*registry_destroy)(Registry *);
    ComponentDescriptor *(*component_register)(Registry *, size_t, const char *);
    Scheduler           *(*schedule_create)(void);
    void                 (*schedule_system)(Scheduler *, SystemDescriptor);
    void                 (*schedule_destroy)(Scheduler *);
    Runner              *(*runner_create)(Scheduler *);
    void                 (*runner_destroy)(Runner *);
    void                 (*runner_tick)(Runner *, void *, void *);
    World               *(*world_create)(void);
    void                 (*world_destroy)(World *);
    Entity               (*entity_create)(World *, Archetype);
    void                 (*entity_remove)(Entity);
    Entity               (*entity_move)(Entity, World *, Archetype);
    size_t               (*query_chunks)(World *, Archetype, ChunkContainer **, size_t);
} ecs;

static Runner       *g_runner;
static World        *g_world;
static Registry     *g_registry;
static const char   *g_build_dir;
static time_t        g_stamp_mtime;
static tick_function g_run_fn;

// RegistryApi wrappers — capture g_registry
static ComponentDescriptor *reg_component_register(size_t stride, const char *name) {
    return ecs.component_register(g_registry, stride, name);
}

static const RegistryApi g_registry_api = {
    .component_register = reg_component_register,
};

// WorldApi wrappers — capture g_world
static Entity world_create_entity(Archetype archetype) {
    return ecs.entity_create(g_world, archetype);
}

static void world_remove_entity(Entity entity) {
    ecs.entity_remove(entity);
}

static Entity world_move_entity(Entity entity, Archetype new_archetype) {
    return ecs.entity_move(entity, g_world, new_archetype);
}

static size_t world_query(Archetype archetype, ChunkContainer **out, size_t capacity) {
    return ecs.query_chunks(g_world, archetype, out, capacity);
}

static const WorldApi g_world_api = {
    .create_entity = world_create_entity,
    .remove_entity = world_remove_entity,
    .move_entity   = world_move_entity,
    .query         = world_query,
};

static void load_lib(const char *path, Scheduler *scheduler) {
    fprintf(stderr, "[hot] loading %s\n", path);
    void *lib = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
    if (!lib) { fprintf(stderr, "[hot] dlopen %s: %s\n", path, dlerror()); return; }

    plugin_fn plugin = dlsym(lib, "qubics_plugin");
    if (plugin) {
        PluginState ps = plugin(g_registry_api);
        fprintf(stderr, "[hot] %s: registered %zu system(s)\n", path, ps.count);
        for (size_t i = 0; i < ps.count; i++)
            ecs.schedule_system(scheduler, ps.descriptors[i]);
        free(ps.descriptors);
    }

    if (!g_run_fn) {
        tick_function run = dlsym(lib, "run");
        if (run) {
            fprintf(stderr, "[hot] %s: found 'run'\n", path);
            g_run_fn = run;
        }
    }
}

static int load_systems(void) {
    char path[1024];
    fprintf(stderr, "[hot] scanning %s\n", g_build_dir);
    DIR *dir = opendir(g_build_dir);
    if (!dir) { fprintf(stderr, "opendir %s: failed\n", g_build_dir); return -1; }

    if (g_registry) ecs.registry_destroy(g_registry);
    g_registry = ecs.registry_create();
    Scheduler *scheduler = ecs.schedule_create();

    struct dirent *pkg;
    while ((pkg = readdir(dir)) != NULL) {
        if (pkg->d_name[0] == '.') continue;
        if (strcmp(pkg->d_name, "ecs") == 0) continue;

        char pkg_dir[1024];
        snprintf(pkg_dir, sizeof(pkg_dir), "%s/%s", g_build_dir, pkg->d_name);

        struct stat st;
        if (stat(pkg_dir, &st) != 0 || !S_ISDIR(st.st_mode)) continue;

        fprintf(stderr, "[hot] package dir: %s\n", pkg_dir);
        DIR *inner = opendir(pkg_dir);
        if (!inner) { fprintf(stderr, "[hot] opendir %s: failed\n", pkg_dir); continue; }

        struct dirent *entry;
        while ((entry = readdir(inner)) != NULL) {
            size_t len = strlen(entry->d_name);
            if (len < 6 || strcmp(entry->d_name + len - 6, ".dylib") != 0) continue;

            snprintf(path, sizeof(path), "%s/%s", pkg_dir, entry->d_name);
            load_lib(path, scheduler);
        }
        closedir(inner);
    }
    closedir(dir);

    if (g_runner) ecs.runner_destroy(g_runner);
    if (g_world)  ecs.world_destroy(g_world);

    g_runner = ecs.runner_create(scheduler);
    g_world  = ecs.world_create();

    ecs.schedule_destroy(scheduler);

    fprintf(stderr, "[hot] systems reloaded\n");
    return 0;
}

static int check_stamp(void) {
    char path[1024];
    struct stat st;

    snprintf(path, sizeof(path), "%s/.stamp", g_build_dir);
    if (stat(path, &st) != 0) return 0;

    if (st.st_mtime != g_stamp_mtime) {
        g_stamp_mtime = st.st_mtime;
        return 1;
    }
    return 0;
}

static void tick(void *ctx) {
    if (check_stamp()) load_systems();
    if (g_runner) ecs.runner_tick(g_runner, (void *)&g_world_api, ctx);
}

int main(void) {
    g_build_dir = getenv("QUBICS_PATH");
    if (!g_build_dir) { fprintf(stderr, "QUBICS_PATH not set\n"); return 1; }

    char path[1024];
    snprintf(path, sizeof(path), "%s/ecs/ecs.dylib", g_build_dir);
    void *ecs_lib = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
    if (!ecs_lib) { fprintf(stderr, "dlopen ecs: %s\n", dlerror()); return 1; }

    ecs.registry_create    = dlsym(ecs_lib, "registry_create");
    ecs.registry_destroy   = dlsym(ecs_lib, "registry_destroy");
    ecs.component_register = dlsym(ecs_lib, "component_register");
    ecs.schedule_create    = dlsym(ecs_lib, "schedule_create");
    ecs.schedule_system    = dlsym(ecs_lib, "schedule_system");
    ecs.schedule_destroy   = dlsym(ecs_lib, "schedule_destroy");
    ecs.runner_create      = dlsym(ecs_lib, "runner_create");
    ecs.runner_destroy     = dlsym(ecs_lib, "runner_destroy");
    ecs.runner_tick        = dlsym(ecs_lib, "runner_tick");
    ecs.world_create       = dlsym(ecs_lib, "world_create");
    ecs.world_destroy      = dlsym(ecs_lib, "world_destroy");
    ecs.entity_create      = dlsym(ecs_lib, "entity_create");
    ecs.entity_remove      = dlsym(ecs_lib, "entity_remove");
    ecs.entity_move        = dlsym(ecs_lib, "entity_move");
    ecs.query_chunks       = dlsym(ecs_lib, "query_chunks");

    if (load_systems() != 0) return 1;
    if (!g_run_fn) { fprintf(stderr, "no backend found (no dylib exports 'run')\n"); return 1; }

    check_stamp();
    g_run_fn(tick);

    ecs.runner_destroy(g_runner);
    ecs.world_destroy(g_world);
    ecs.registry_destroy(g_registry);
    return 0;
}
