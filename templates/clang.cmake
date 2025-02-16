set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_RC_COMPILER llvm-rc)

add_compile_options(${CLANG_ARCH})
add_link_options(${CLANG_ARCH})

# Visual Studio 17.10 included a new constexpr mutex constructor, which requires a new version of
# VC Runtime to work properly. Clang uses these same headers.
# As of writing this, Proton still uses an older version, meaning a build using this causes a crash
# on startup.
# Temporarily disable it, until we get Proton support.
add_compile_definitions(_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR)

# See llvm-project#59689 - use the builtin so that offsetof becomes constexpr
add_compile_definitions(_CRT_USE_BUILTIN_OFFSETOF)
