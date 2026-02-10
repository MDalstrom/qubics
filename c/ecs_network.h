#ifndef ECS_NETWORK_H
#define ECS_NETWORK_H

#include "ecs.h"
#include <stdint.h>

typedef struct {
  uint8_t *data;
  size_t size;
  size_t capacity;
} Buffer;

typedef const char* (*ComponentPathResolver)(ComponentDescriptor*);
typedef ComponentDescriptor* (*ComponentPathLookup)(const char* path);

Buffer* buffer_create(size_t initial_capacity);
void buffer_destroy(Buffer *buf);

void world_serialize(World *world, Buffer *buf, ComponentPathResolver path_resolver);
World* world_deserialize(Buffer *buf, ComponentPathLookup path_lookup);

int network_create_server(const char *host, int port);
int network_accept_client(int server_fd);
int network_send_world(int client_fd, World *world, ComponentPathResolver path_resolver);
int network_connect_client(const char *host, int port);
int network_receive_data(int sockfd, Buffer *buf);
void network_close(int fd);

#endif // ECS_NETWORK_H
