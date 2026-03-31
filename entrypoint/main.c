#include <dirent.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "backend-contracts/contract.h"
#include "bridge-contracts/contract.h"
#include "ecs/ecs.h"
#include "ecs/scheduler.h"

static struct {
    Registry  *(*registry_create)(void);
    void       (*registry_destroy)(Registry *);
    Scheduler *(*schedule_create)(void);
    void       (*schedule_system)(Scheduler *, SystemDescriptor);
    void       (*schedule_destroy)(Scheduler *);
    Runner    *(*runner_create)(Scheduler *);
    void       (*runner_destroy)(Runner *);
    void       (*runner_tick)(Runner *, World *, void *);
    World     *(*world_create)(void);
    void       (*world_destroy)(World *);
} ecs;

static Runner          *g_runner;
static World           *g_world;
static const char      *g_build_dir;
static time_t           g_stamp_mtime;
static tick_function    g_run_fn;

static void load_lib(const char *path, Registry *registry, Scheduler *scheduler) {
    fprintf(stderr, "[hot] loading %s\n", path);
    void *lib = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
    if (!lib) { fprintf(stderr, "[hot] dlopen %s: %s\n", path, dlerror()); return; }

    plugin_fn plugin = dlsym(lib, "qubics_plugin");
    if (plugin) {
        PluginSystems ps = plugin(registry);
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

    Registry  *registry  = ecs.registry_create();
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
            if (strcmp(entry->d_name + len - 6, ".dylib") != 0) continue;

            snprintf(path, sizeof(path), "%s/%s", pkg_dir, entry->d_name);
            load_lib(path, registry, scheduler);
        }
        closedir(inner);
    }
    closedir(dir);

    if (g_runner) ecs.runner_destroy(g_runner);
    if (g_world)  ecs.world_destroy(g_world);

    g_runner = ecs.runner_create(scheduler);
    g_world  = ecs.world_create();

    ecs.schedule_destroy(scheduler);
    ecs.registry_destroy(registry);

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
    if (g_runner) ecs.runner_tick(g_runner, g_world, ctx);
}

int main(void) {
    g_build_dir = getenv("QUBICS_PATH");
    if (!g_build_dir) { fprintf(stderr, "QUBICS_PATH not set\n"); return 1; }

    char path[1024];
    snprintf(path, sizeof(path), "%s/ecs/ecs.dylib", g_build_dir);
    void *ecs_lib = dlopen(path, RTLD_NOW | RTLD_GLOBAL);
    if (!ecs_lib) { fprintf(stderr, "dlopen ecs: %s\n", dlerror()); return 1; }

    ecs.registry_create  = dlsym(ecs_lib, "registry_create");
    ecs.registry_destroy = dlsym(ecs_lib, "registry_destroy");
    ecs.schedule_create  = dlsym(ecs_lib, "schedule_create");
    ecs.schedule_system  = dlsym(ecs_lib, "schedule_system");
    ecs.schedule_destroy = dlsym(ecs_lib, "schedule_destroy");
    ecs.runner_create    = dlsym(ecs_lib, "runner_create");
    ecs.runner_destroy   = dlsym(ecs_lib, "runner_destroy");
    ecs.runner_tick      = dlsym(ecs_lib, "runner_tick");
    ecs.world_create     = dlsym(ecs_lib, "world_create");
    ecs.world_destroy    = dlsym(ecs_lib, "world_destroy");

    if (load_systems() != 0) return 1;
    if (!g_run_fn) { fprintf(stderr, "no backend found (no dylib exports 'run')\n"); return 1; }

    check_stamp();
    g_run_fn(tick);

    ecs.runner_destroy(g_runner);
    ecs.world_destroy(g_world);
    return 0;
}
