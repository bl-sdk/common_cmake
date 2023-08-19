set(CMAKE_SYSTEM_NAME Windows)

set(CMAKE_C_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-gcc)
set(CMAKE_CXX_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-g++)
set(CMAKE_RC_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-windres)

# Use GDB-style debug info
add_compile_options("$<$<CONFIG:DEBUG>:-ggdb3>")
add_link_options("$<$<CONFIG:DEBUG>:-ggdb3>")

# Link `libc++.dll` and `libunwind.dll` statically
add_link_options("-static-libstdc++" "-Wl,-Bstatic" "-lunwind")

# Workaround until llvm-project 692518d04b makes it into a release (i.e. 17)
add_compile_definitions(_LIBCXXABI_DISABLE_VISIBILITY_ANNOTATIONS)
