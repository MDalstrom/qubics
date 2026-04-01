#ifndef BACKEND_CONTRACT_H
#define BACKEND_CONTRACT_H

typedef void (*tick_function)(void *render_context);

void run(tick_function tick_fn);

#endif /* BACKEND_CONTRACT_H */
