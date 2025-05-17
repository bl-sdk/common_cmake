# Problem: CMake runs toolchain files multiple times, but can't read cache variables on some runs.
# Workaround: On first run (in which cache variables are always accessible), set an intermediary environment variable.
# https://stackoverflow.com/a/29997033
if(MSVC_WINE_ENV_SCRIPT)
    set(ENV{_MSVC_WINE_ENV_SCRIPT} "${MSVC_WINE_ENV_SCRIPT}")
else()
    set(MSVC_WINE_ENV_SCRIPT "$ENV{_MSVC_WINE_ENV_SCRIPT}")
endif()

# This toolchain is based on https://github.com/mstorsjo/msvc-wine
# Follow the instructions in that repo to download a copy of the windows sdk headers/libs
# Then when including this toolchain, define 'MSVC_WINE_ENV_SCRIPT' as the path to 'msvcenv.sh'
if(NOT EXISTS ${MSVC_WINE_ENV_SCRIPT})
    message(FATAL_ERROR "Could not find windows headers/libs, you must define 'MSVC_WINE_ENV_SCRIPT'!")
endif()

set(CMAKE_SYSTEM_NAME Windows)

set(CMAKE_C_COMPILER clang)
set(CMAKE_C_COMPILER_TARGET ${CLANG_TRIPLE})
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET ${CLANG_TRIPLE})
set(CMAKE_RC_COMPILER llvm-rc)

# @brief Extract paths from the env script into a list
#
# @param env_var The environment variable to extract
# @param prefix A prefix to add to the start of each path (e.g. `-I`)
# @param output_var The output var to set to the list of extracted paths
function(_extract_from_env env_var prefix output_var)
    execute_process(
        COMMAND bash -c ". ${MSVC_WINE_ENV_SCRIPT} && echo \"\$${env_var}\""
        OUTPUT_VARIABLE env_output
        COMMAND_ERROR_IS_FATAL ANY
    )
    string(REPLACE "z:\\" "${prefix}/" env_output "${env_output}")
    string(REPLACE "\\" "/" env_output "${env_output}")
    string(REGEX MATCHALL "[^;\r\n]+" env_output_list "${env_output}")

    set(${output_var} ${env_output_list} PARENT_SCOPE)
endfunction()

# Must use -idirafter to make sure this is loaded after the standard clang includes.
# This mirrors what clang does when reading from the env var, if you sourced the script.
# If we use -isystem, they come first, which causes issues when trying to use intrinsics.
_extract_from_env("INCLUDE" "-idirafter" _msvc_wine_system_includes)
add_compile_options(${_msvc_wine_system_includes})

string(REPLACE ";" " " _msvc_wine_system_include_string "${_msvc_wine_system_includes}")
set(CMAKE_RC_FLAGS "${CMAKE_RC_FLAGS} ${_msvc_wine_system_include_string}")

_extract_from_env("LIB" "-L" _msvc_wine_link_options)
add_link_options(${_msvc_wine_link_options})

add_compile_options("-ffreestanding")

add_compile_options("$<$<CONFIG:DEBUG>:-gdwarf>")
add_link_options("$<$<CONFIG:DEBUG>:-gdwarf>" "$<$<CONFIG:DEBUG>:-Wl,/ignore:longsections>")
