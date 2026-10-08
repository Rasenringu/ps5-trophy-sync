include $(PS5_PAYLOAD_SDK)/toolchain/prospero.mk
.PHONY: all
all:
	bash ../scripts/container-build.sh
# Disable the SDK privilege patch hook in a project-local CRT copy.
build/crt-readonly.o: $(PS5_PAYLOAD_SDK)/target/lib/crt1.o
	mkdir -p build
	$(OBJCOPY) --weaken-symbol=__patch_init $< $@
