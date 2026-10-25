#pragma once
#include <stdint.h>
namespace MspeSav {
void InitFatFallback();
void Flush();
bool IsPersistentName(const char *name);
bool Exists(const char *name,uint32_t *out_len=nullptr);
int Load(const char *name,uint8_t **out_data,uint32_t *out_len);
int Store(const char *name,const uint8_t *data,uint32_t len);
int Remove(const char *name);
const char *BackendName();
}
