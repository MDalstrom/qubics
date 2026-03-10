#ifndef METAL_H
#define METAL_H

typedef void (*tick_function)(void* render_context);

void run(tick_function tick_fn);

#endif /* METAL_H */
