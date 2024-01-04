set(CMAKE_SYSTEM_NAME Windows)

set(CMAKE_C_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-gcc)
set(CMAKE_CXX_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-g++)
set(CMAKE_RC_COMPILER ${MINGW_TOOLCHAIN_PREFIX}-windres)

# Use GDB-style debug info
add_compile_options("$<$<CONFIG:DEBUG>:-ggdb3>")
add_link_options("$<$<CONFIG:DEBUG>:-ggdb3>")

if(${LLVM_MINGW})
    # Link `libc++.dll` and `libunwind.dll` statically
    add_link_options("-static-libstdc++" "-Wl,-Bstatic" "-lunwind")

    # LLVM MinGW uses an old libc++, which still has things like std::format or std::ranges
    # marked as experimental
    add_compile_definitions(_LIBCPP_ENABLE_EXPERIMENTAL)
else()
    # Link `llibgcc_s_seh-1.dll`, `libwinpthread-1.dll`, and `libstdc++-6.dll` statically
    add_link_options("-static-libgcc" "-Wl,-Bstatic" "-lstdc++")
endif()
