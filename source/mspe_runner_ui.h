#pragma once
#include <stdint.h>

// MSPE diagnostic overlay icon.  This intentionally has NO dependency on
// Zenonia's old world-map artwork (zen_map_art.h was never part of MSPE).
// The destination is a 256x192 RGB555 Nintendo DS bitmap background.
namespace MspeRunnerUI {
constexpr int IconX = 236;
constexpr int IconY = 4;
constexpr int IconSize = 16;
static_assert(IconX >= 0 && IconX + IconSize <= 256, "LOG icon must fit display width");
static_assert(IconY >= 0 && IconY + IconSize <= 192, "LOG icon must fit display height");

inline uint16_t color(int red, int green, int blue) {
    return (uint16_t)(0x8000u | (uint16_t(red >> 3)) |
                     (uint16_t(green >> 3) << 5) |
                     (uint16_t(blue >> 3) << 10));
}

inline void gear(uint16_t *framebuffer) {
    if (!framebuffer) return;
    static const uint16_t rows[IconSize] = {
        0x0180, 0x03c0, 0x33cc, 0x7ffe,
        0x3ffc, 0x1e78, 0x3c3c, 0xfc3f,
        0xfc3f, 0x3c3c, 0x1e78, 0x3ffc,
        0x7ffe, 0x33cc, 0x03c0, 0x0180
    };
    const uint16_t background = color(25, 13, 40);
    const uint16_t foreground = color(214, 187, 247);
    for (int y = 0; y < IconSize; ++y) {
        uint16_t *line = framebuffer + (IconY + y) * 256 + IconX;
        for (int x = 0; x < IconSize; ++x)
            line[x] = (rows[y] & (uint16_t(1u) << (15 - x))) ? foreground : background;
    }
}
} // namespace MspeRunnerUI
