#ifndef MESH2D_H
#define MESH2D_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    float matrix[16];
} Transform;

typedef struct {
    float left, right, bottom, top;
    float near_z, far_z;
} Viewport;

typedef struct {
    void    *vertex_buffer;
    uint32_t vertex_count;
    float    color[4];
} Mesh2DShared;

#endif /* MESH2D_H */
