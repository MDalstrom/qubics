from . import velocity, body, acceleration, damping

systems = [
    acceleration.apply,

    body.apply,
    body.correct,
    
    damping.apply_linear,
    damping.apply_angular,

    velocity.apply_linear,
    velocity.apply_angular,
]

