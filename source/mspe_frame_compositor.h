#pragma once

// MSPE dual-screen compositor: preserves only pixels actually written to the
// live phone display between WIPI Draw* calls and a later offscreen FlushLcd.
// No deferred WIPI image handles are retained: the guest may destroy them.
// No libnds dependency, so this component is host-testable.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

namespace MspeFrame {
class PendingPixels {
public:
    static constexpr int Width=240;
    static constexpr int Height=320;
    static constexpr size_t Count=(size_t)Width*Height;
    static constexpr size_t MaskBytes=(Count+7u)/8u;

    PendingPixels()=default;
    PendingPixels(const PendingPixels&)=delete;
    PendingPixels& operator=(const PendingPixels&)=delete;

    bool write(int x,int y,uint16_t color) {
        if((unsigned)x>=Width || (unsigned)y>=Height || !ensure()) return false;
        const size_t idx=(size_t)y*Width+(size_t)x;
        pixels_[idx]=color;
        mask_[idx>>3] |= (uint8_t)(1u<<(idx&7));
        has_pixels_=true;
        return true;
    }

    void writeRow(int x,int y,const uint16_t *colors,int width) {
        if(!colors || width<=0 || (unsigned)y>=Height) return;
        int start=x<0?-x:0;
        int end=width;
        if((int64_t)x+end>Width) end=Width-x;
        if(start>=end || !ensure()) return;
        size_t idx=(size_t)y*Width+(size_t)(x+start);
        for(int col=start;col<end;col++,idx++) {
            pixels_[idx]=colors[col];
            mask_[idx>>3] |= (uint8_t)(1u<<(idx&7));
        }
        has_pixels_=true;
    }

    // If the phone framebuffer is the source of FlushLcd, its data already
    // includes direct-to-screen Draw* operations. No replay is required.
    void discard() {
        if(has_pixels_ && mask_) memset(mask_,0,MaskBytes);
        has_pixels_=false;
    }

    // Reapply captured pixels AFTER a separate offscreen source was flushed.
    // Each pixel is restored only once, in the last color actually written.
    uint32_t restore(uint16_t *destination,int stride) {
        if(!destination || stride<Width || !has_pixels_ || !mask_) return 0;
        uint32_t n=0;
        for(size_t idx=0;idx<Count;idx++) {
            if(mask_[idx>>3] & (uint8_t)(1u<<(idx&7))) {
                destination[(idx/Width)*(size_t)stride+idx%Width]=pixels_[idx];
                ++n;
            }
        }
        discard();
        return n;
    }
    bool pending() const { return has_pixels_; }

private:
    bool ensure() {
        if(pixels_ && mask_) return true;
        if(!pixels_) pixels_=(uint16_t*)malloc(Count*sizeof(uint16_t));
        if(!mask_) mask_=(uint8_t*)calloc(MaskBytes,1);
        if(!pixels_ || !mask_) return false;
        return true;
    }
    uint16_t *pixels_=nullptr;
    uint8_t *mask_=nullptr;
    bool has_pixels_=false;
};
}
