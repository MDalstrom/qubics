#include "ecs_network.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

Buffer* buffer_create(size_t initial_capacity) {
  Buffer *buf = malloc(sizeof(Buffer));
  buf->data = malloc(initial_capacity);
  buf->size = 0;
  buf->capacity = initial_capacity;
  return buf;
}

void buffer_ensure_capacity(Buffer *buf, size_t additional) {
  if (buf->size + additional > buf->capacity) {
    while (buf->size + additional > buf->capacity) {
      buf->capacity *= 2;
    }
    buf->data = realloc(buf->data, buf->capacity);
  }
}

void buffer_append(Buffer *buf, const void *data, size_t len) {
  buffer_ensure_capacity(buf, len);
  memcpy(buf->data + buf->size, data, len);
  buf->size += len;
}

void buffer_append_u32(Buffer *buf, uint32_t value) {
  buffer_append(buf, &value, sizeof(uint32_t));
}

void buffer_destroy(Buffer *buf) {
  free(buf->data);
  free(buf);
}

void world_serialize(World *world, Buffer *buf, ComponentPathResolver path_resolver) {
  for (size_t i = 0; i < world->containers_count; i++) {
    ChunkContainer *container = world->containers + i;
    Archetype *archetype = &container->archetype;
    
    buffer_append_u32(buf, (uint32_t)archetype->length);
    
    for (size_t j = 0; j < archetype->length; j++) {
      const char *component_path = path_resolver(archetype->descriptors[j]);
      uint32_t path_len = strlen(component_path);
      buffer_append_u32(buf, path_len);
      buffer_append(buf, component_path, path_len);
    }
    
    size_t total_entities = 0;
    for (size_t j = 0; j < container->chunks_count; j++) {
      total_entities += container->chunks[j].entities_count;
    }
    buffer_append_u32(buf, (uint32_t)total_entities);
    
    for (size_t k = 0; k < archetype->length; k++) {
      for (size_t j = 0; j < container->chunks_count; j++) {
        Chunk *chunk = container->chunks + j;
        size_t data_len = archetype->descriptors[k]->stride * chunk->entities_count;
        buffer_append(buf, chunk->buffers[k], data_len);
      }
    }
  }
}

int network_create_server(const char *host, int port) {
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if (sockfd < 0) {
    perror("socket creation failed");
    return -1;
  }
  
  int opt = 1;
  if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
    perror("setsockopt failed");
    close(sockfd);
    return -1;
  }
  
  struct sockaddr_in addr;
  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_port = htons(port);
  
  if (inet_pton(AF_INET, host, &addr.sin_addr) <= 0) {
    perror("invalid address");
    close(sockfd);
    return -1;
  }
  
  if (bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
    perror("bind failed");
    close(sockfd);
    return -1;
  }
  
  if (listen(sockfd, 5) < 0) {
    perror("listen failed");
    close(sockfd);
    return -1;
  }
  
  return sockfd;
}

int network_accept_client(int server_fd) {
  struct sockaddr_in client_addr;
  socklen_t client_len = sizeof(client_addr);
  int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
  if (client_fd < 0) {
    perror("accept failed");
    return -1;
  }
  return client_fd;
}

int network_send_world(int client_fd, World *world, ComponentPathResolver path_resolver) {
  Buffer *buf = buffer_create(4096);
  world_serialize(world, buf, path_resolver);
  
  // Send size prefix
  uint32_t size = (uint32_t)buf->size;
  ssize_t sent = send(client_fd, &size, sizeof(uint32_t), 0);
  if (sent != sizeof(uint32_t)) {
    buffer_destroy(buf);
    return -1;
  }
  
  // Send data
  sent = send(client_fd, buf->data, buf->size, 0);
  int result = (sent == (ssize_t)buf->size) ? 0 : -1;
  
  buffer_destroy(buf);
  return result;
}

void network_close(int fd) {
  close(fd);
}

int network_connect_client(const char *host, int port) {
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);
  if (sockfd < 0) {
    perror("socket creation failed");
    return -1;
  }
  
  struct sockaddr_in addr;
  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_port = htons(port);
  
  if (inet_pton(AF_INET, host, &addr.sin_addr) <= 0) {
    perror("invalid address");
    close(sockfd);
    return -1;
  }
  
  if (connect(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
    perror("connection failed");
    close(sockfd);
    return -1;
  }
  
  return sockfd;
}

int network_receive_data(int sockfd, Buffer *buf) {
  uint32_t data_size;
  ssize_t received = recv(sockfd, &data_size, sizeof(uint32_t), 0);
  if (received != sizeof(uint32_t)) {
    return -1;
  }
  
  buffer_ensure_capacity(buf, data_size);
  
  size_t total_received = 0;
  while (total_received < data_size) {
    received = recv(sockfd, buf->data + buf->size + total_received, 
                    data_size - total_received, 0);
    if (received <= 0) {
      return -1;
    }
    total_received += received;
  }
  
  buf->size += data_size;
  return 0;
}

typedef struct {
  const uint8_t *data;
  size_t pos;
  size_t size;
} BufferReader;

void reader_init(BufferReader *reader, const uint8_t *data, size_t size) {
  reader->data = data;
  reader->pos = 0;
  reader->size = size;
}

uint32_t reader_read_u32(BufferReader *reader) {
  if (reader->pos + sizeof(uint32_t) > reader->size) {
    return 0;
  }
  uint32_t value;
  memcpy(&value, reader->data + reader->pos, sizeof(uint32_t));
  reader->pos += sizeof(uint32_t);
  return value;
}

void reader_read_bytes(BufferReader *reader, void *dest, size_t len) {
  if (reader->pos + len > reader->size) {
    return;
  }
  memcpy(dest, reader->data + reader->pos, len);
  reader->pos += len;
}

World* world_deserialize(Buffer *buf, ComponentPathLookup path_lookup) {
  World *world = world_create();
  BufferReader reader;
  reader_init(&reader, buf->data, buf->size);
  
  while (reader.pos < reader.size) {
    if (reader.pos + sizeof(uint32_t) > reader.size) break;
    
    uint32_t component_count = reader_read_u32(&reader);
    if (component_count == 0 || component_count > 100) break;
    
    ComponentDescriptor **descriptors = malloc(component_count * sizeof(ComponentDescriptor*));
    char **paths = malloc(component_count * sizeof(char*));
    
    for (uint32_t i = 0; i < component_count; i++) {
      uint32_t path_len = reader_read_u32(&reader);
      char *path = malloc(path_len + 1);
      reader_read_bytes(&reader, path, path_len);
      path[path_len] = '\0';
      paths[i] = path;
      
      descriptors[i] = path_lookup(path);
      if (!descriptors[i]) {
        for (uint32_t j = 0; j <= i; j++) {
          free(paths[j]);
        }
        free(paths);
        free(descriptors);
        world_destroy(world);
        return NULL;
      }
    }
    
    uint32_t total_entities = reader_read_u32(&reader);
    
    Archetype archetype = {.descriptors = descriptors, .length = component_count};
    
    for (uint32_t i = 0; i < total_entities; i++) {
      entity_create(world, archetype);
    }
    
    ChunkContainer *container = &world->containers[world->containers_count - 1];
    
    for (uint32_t comp_idx = 0; comp_idx < component_count; comp_idx++) {
      size_t stride = descriptors[comp_idx]->stride;
      
      for (size_t chunk_idx = 0; chunk_idx < container->chunks_count; chunk_idx++) {
        Chunk *chunk = &container->chunks[chunk_idx];
        size_t entities_in_chunk = chunk->entities_count;
        size_t data_len = stride * entities_in_chunk;
        reader_read_bytes(&reader, chunk->buffers[comp_idx], data_len);
      }
    }
    
    for (uint32_t i = 0; i < component_count; i++) {
      free(paths[i]);
    }
    free(paths);
  }
  
  return world;
}
