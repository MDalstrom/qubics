#ifndef MESH2D_H
#define MESH2D_H

#include <stddef.h>

#define MESH2D_MAX_POINTS 64

typedef struct {
    float x;
    float y;
} Point2D;

typedef struct {
    Point2D points[MESH2D_MAX_POINTS];
    size_t  point_count;
    float   r, g, b, a;
} Mesh2D;

#endif /* MESH2D_H */
