# Build the toolchain 
make -j1 V=sc toolchain/compile

# Build everything else
make -j $(($(nproc)+1)) V=sc world
