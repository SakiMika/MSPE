#include "mspe_sav_backend.h"
#include <fat.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace MspeSav {
namespace {
bool g_fat=false;
constexpr uint32_t kMaxSaveBytes=512*1024;
uint32_t fnv1a(const char *s) {
    uint32_t h=2166136261u;
    for(;s && *s;++s) {h^=(unsigned char)*s; h*=16777619u;}
    return h;
}
bool save_path(const char *name,char *out,size_t cap) {
    if(!name || !*name || strlen(name)>120 || !out || cap<32) return false;
    // Hashed basename keeps each guest DB separate and prevents path traversal.
    // Prefix MSPE isolates these saves from existing Zenonia/Ragnarok files.
    int n=snprintf(out,cap,"fat:/MSPE_%08lX.sav",(unsigned long)fnv1a(name));
    return n>0 && (size_t)n<cap;
}
}
void InitFatFallback() { g_fat=fatInitDefault(); }
void Flush() { /* close writes synchronously */ }
bool IsPersistentName(const char *name) {
    // All non-packaged DB names may be writable in this game.
    // The WIPI caller resolves immutable nitro:/ resources first.
    return name && *name && strlen(name)<=120;
}
const char *BackendName() { return g_fat?"FAT:/MSPE_*.sav":"RAM-only (no FAT)"; }
bool Exists(const char *name,uint32_t *out_len) {
    if(out_len) *out_len=0;
    char path[64]; if(!g_fat || !save_path(name,path,sizeof(path))) return false;
    FILE *f=fopen(path,"rb"); if(!f) return false;
    bool ok=fseek(f,0,SEEK_END)==0;
    long n=ok?ftell(f):-1; fclose(f);
    if(n<0 || (unsigned long)n>kMaxSaveBytes) return false;
    if(out_len)*out_len=(uint32_t)n;
    return true;
}
int Load(const char *name,uint8_t **out_data,uint32_t *out_len) {
    if(out_data)*out_data=nullptr;
    if(out_len)*out_len=0;
    uint32_t len=0;
    if(!out_data || !out_len || !Exists(name,&len))return -12;
    char path[64]; if(!save_path(name,path,sizeof(path)))return -9;
    FILE *f=fopen(path,"rb"); if(!f)return -12;
    uint8_t *data=(uint8_t*)malloc(len?len:1);
    if(!data){fclose(f);return -3;}
    bool ok=!len || fread(data,1,len,f)==len;
    fclose(f);
    if(!ok){free(data);return -12;}
    *out_data=data;*out_len=len;
    return 0;
}
int Store(const char *name,const uint8_t *data,uint32_t len) {
    if(len>kMaxSaveBytes || (len && !data))return -18;
    char path[64]; if(!g_fat || !save_path(name,path,sizeof(path)))return -12;
    FILE *f=fopen(path,"wb"); if(!f)return -12;
    bool ok=(!len || fwrite(data,1,len,f)==len) && fflush(f)==0;
    if(fclose(f)!=0)ok=false;
    return ok?0:-12;
}
int Remove(const char *name) {
    char path[64]; if(!g_fat || !save_path(name,path,sizeof(path)))return -12;
    return remove(path)==0?0:-12;
}
}
