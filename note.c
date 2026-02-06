#include <stddef.h>

typedef struct {
	float x;
	float y;
	float z;
	float w;
} Vector4;

typedef struct {
	Vector4 positions[];
} Transform;



typedef struct {
	void **ptrs;
	size_t *sizes;
} Chunk;

// chunk:
// - World Matrix (Matrix4x4)
// - Velocity (Vector3)

