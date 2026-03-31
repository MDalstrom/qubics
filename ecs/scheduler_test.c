#include "scheduler.h"

#include <assert.h>
#include <stdio.h>

static ComponentDescriptor pos = {sizeof(float) * 3, "pos"};
static ComponentDescriptor vel = {sizeof(float) * 3, "vel"};

static void dummy(void *w, void *c) { (void)w; (void)c; }

static void test_independent(void) {
  // Two systems with no overlapping components: same stage
  ComponentDescriptor *r0[] = {&pos};
  ComponentDescriptor *r1[] = {&vel};
  SystemDescriptor systems[] = {
    {dummy, {1, r0}, {0, NULL}},
    {dummy, {1, r1}, {0, NULL}},
  };
  size_t stage_ends[2];
  size_t n = systems_sort(systems, 2, stage_ends);
  assert(n == 1);
  assert(stage_ends[0] == 2);
  printf("test_independent: OK\n");
}

static void test_read_read_no_conflict(void) {
  // Both read the same component: no conflict, same stage
  ComponentDescriptor *r[] = {&pos};
  SystemDescriptor systems[] = {
    {dummy, {1, r}, {0, NULL}},
    {dummy, {1, r}, {0, NULL}},
  };
  size_t stage_ends[2];
  size_t n = systems_sort(systems, 2, stage_ends);
  assert(n == 1);
  assert(stage_ends[0] == 2);
  printf("test_read_read_no_conflict: OK\n");
}

static void test_write_read_conflict(void) {
  // A writes pos, B reads pos: conflict -> different stages
  ComponentDescriptor *w[] = {&pos};
  ComponentDescriptor *r[] = {&pos};
  SystemDescriptor systems[] = {
    {dummy, {0, NULL}, {1, w}},
    {dummy, {1, r},   {0, NULL}},
  };
  size_t stage_ends[2];
  size_t n = systems_sort(systems, 2, stage_ends);
  assert(n == 2);
  assert(stage_ends[0] == 1);
  assert(stage_ends[1] == 2);
  printf("test_write_read_conflict: OK\n");
}

static void test_write_write_conflict(void) {
  // Both write pos: conflict -> different stages
  ComponentDescriptor *w[] = {&pos};
  SystemDescriptor systems[] = {
    {dummy, {0, NULL}, {1, w}},
    {dummy, {0, NULL}, {1, w}},
  };
  size_t stage_ends[2];
  size_t n = systems_sort(systems, 2, stage_ends);
  assert(n == 2);
  assert(stage_ends[0] == 1);
  assert(stage_ends[1] == 2);
  printf("test_write_write_conflict: OK\n");
}

static void test_grouping(void) {
  // A writes pos, B writes vel -> same stage (no conflict)
  // C reads pos -> conflicts with A, goes to stage 1
  // D reads vel -> conflicts with B, but not C -> stage 1
  ComponentDescriptor *wa[] = {&pos};
  ComponentDescriptor *wb[] = {&vel};
  ComponentDescriptor *rc[] = {&pos};
  ComponentDescriptor *rd[] = {&vel};
  SystemDescriptor systems[] = {
    {dummy, {0, NULL}, {1, wa}},
    {dummy, {0, NULL}, {1, wb}},
    {dummy, {1, rc},   {0, NULL}},
    {dummy, {1, rd},   {0, NULL}},
  };
  size_t stage_ends[4];
  size_t n = systems_sort(systems, 4, stage_ends);
  assert(n == 2);
  assert(stage_ends[0] == 2);
  assert(stage_ends[1] == 4);
  printf("test_grouping: OK\n");
}

int main(void) {
  test_independent();
  test_read_read_no_conflict();
  test_write_read_conflict();
  test_write_write_conflict();
  test_grouping();
  return 0;
}
