set(CMAKE_C_COMPILER cl.exe)
set(CMAKE_CXX_COMPILER cl.exe)

# UTF-8 encoded source files
add_compile_options("/utf-8")

# Visual Studio 17.10 included a new constexpr mutex constructor, which requires a new version of
# VC Runtime to work properly.
# As of writing this, Proton still uses an older version, meaning a build using this causes a crash
# on startup.
# Temporarily disable it, until we get Proton support.
add_compile_definitions(_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR)
