from . import rigidbody
from . import velocity, body, acceleration, damping

systems = [
    rigidbody.acceleration_system,
    rigidbody.velocity_system,
    rigidbody.angular_damping_system,
]

alt = [
    acceleration.apply,

    body.apply,
    body.correct,
    
    damping.apply_linear,
    damping.apply_angular,

    velocity.apply_linear,
    velocity.apply_angular,
]
