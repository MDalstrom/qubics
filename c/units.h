typedef struct {
	float x, y, z, w;
} Vector4;

typedef struct {
	float x, y, z;
} Vector3;

typedef struct {
	float x, y;
} Vector2;

typedef struct {
	Vector4 m0, m1, m2, m3;
} Matrix4x4;

typedef struct {
	Vector3 m0, m1, m2;
} Matrix3x3;

typedef struct {
	Matrix4x4 wm;
} Transform3D;

typedef struct {
  Matrix3x3 wm;
} Transform2D;

