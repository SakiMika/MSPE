.SUFFIXES:
ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITPRO=/opt/devkitpro; export DEVKITARM=$(DEVKITPRO)/devkitARM")
endif

include $(DEVKITARM)/ds_rules

GAME_TITLE      := MapleStory Pirate Edition
GAME_SUBTITLE1  := Nexon Mobile
GAME_SUBTITLE2  := WIPI to NDS

TARGET      := MSPE
BUILD       := build
SOURCES     := source
INCLUDES    := source
DATA        :=
GRAPHICS    :=
AUDIO       :=
ICON        := icon.bmp
NITRO       := nitrofs
PYTHON      ?= python

ARCH        := -march=armv5te -mtune=arm946e-s -mthumb-interwork
CALLBACK_CACHE ?= 0
CFLAGS      := -g -Wall -Wextra -O2 -ffunction-sections -fdata-sections $(ARCH) $(INCLUDE) -DARM9 -DZEN_CONSERVATIVE_CALLBACK_CACHE=$(CALLBACK_CACHE)
CXXFLAGS    := $(CFLAGS) -fno-rtti -fno-exceptions -fno-strict-aliasing -std=gnu++17
ASFLAGS     := -g $(ARCH)
LDFLAGS     := -specs=ds_arm9.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS        := -lnds9

# NitroFS needs the filesystem/FAT compatibility libraries. Keep the same
# ordering used by the current devkitPro NDS template.
ifneq ($(strip $(NITRO)),)
LIBS        := -lfilesystem -lfat $(LIBS)
endif

LIBDIRS     := $(LIBNDS) $(PORTLIBS)

ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(CURDIR) $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))

ifneq ($(strip $(ICON)),)
export GAME_ICON := $(CURDIR)/$(ICON)
endif
export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

ifneq ($(strip $(NITRO)),)
export NITRO_FILES := $(CURDIR)/$(NITRO)
endif

export LD := $(CXX)
export OFILES_BIN := $(addsuffix .o,$(BINFILES))
export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES := $(OFILES_BIN) $(OFILES_SOURCES)
export INCLUDE := $(foreach dir,$(INCLUDES),-iquote $(CURDIR)/$(dir)) \
                  $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                  -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

.PHONY: $(BUILD) clean all
all: $(BUILD)

$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).elf $(TARGET).nds $(TARGET).map

else
# Keep ARM9 at 0x8000; user-requested game code is MSPE.
# DLDI/autopatching with a non-#### game ID must be verified in emulator.
$(OUTPUT).nds: $(OUTPUT).elf $(NITRO_FILES) $(GAME_ICON)
	@echo "creating MapleStory Pirate Edition first-pass: ARM9@0x8000..."
	@ndstool -c $@ -9 $< $(_ARM7_ELF) -b $(GAME_ICON) "$(GAME_TITLE)" -h 0x8000 -g "MSPE" 01 "MapleStory" 01 $(_ADDFILES)
	@$(PYTHON) "$(dir $(OUTPUT))tools/patch_nds_header.py" "$@"

$(OUTPUT).elf: $(OFILES)
$(OFILES_SOURCES):

# Banner icon: ndstool reads the indexed 32x32 BMP directly.

-include $(DEPSDIR)/*.d
endif
