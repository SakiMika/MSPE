#pragma once
#include <stdint.h>
// MapleStory Pirate Edition has no standalone or embedded PNG asset stream.
// The retained generic CreateImage compatibility code is not used by this ELF.
struct RvPngCacheEntry {
    uint32_t crc32,fnv1a,idat_len,offset,pixels;
    uint16_t width,height;
    uint8_t bit_depth,interlace;
    uint16_t reserved;
};
static const uint32_t kRvPngCacheEntryCount=0u;
static const RvPngCacheEntry kRvPngCacheEntries[]={{0,0,0,0,0,0,0,0,0,0}};
