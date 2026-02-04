import numpy as np


def sphere(radius, segments, stacks):
    vertices = []

    for i in range(stacks):
        phi1 = np.pi / 2 - i * np.pi / stacks
        phi2 = np.pi / 2 - (i + 1) * np.pi / stacks

        for j in range(segments):
            theta1 = j * 2 * np.pi / segments
            theta2 = (j + 1) * 2 * np.pi / segments

            def to_cartesian(phi, theta):
                x = radius * np.cos(phi) * np.cos(theta)
                y = radius * np.sin(phi)
                z = radius * np.cos(phi) * np.sin(theta)
                return [x, y, z, 1.0]

            v1 = to_cartesian(phi1, theta1)
            v2 = to_cartesian(phi2, theta1)
            v3 = to_cartesian(phi2, theta2)
            v4 = to_cartesian(phi1, theta2)

            vertices.append(v1)
            vertices.append(v2)
            vertices.append(v4)

            vertices.append(v2)
            vertices.append(v3)
            vertices.append(v4)

    return np.array(vertices, dtype=np.float32)
