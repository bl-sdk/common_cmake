set(CMAKE_SYSTEM_NAME Windows)

set(CMAKE_C_COMPILER clang)
set(CMAKE_C_COMPILER_TARGET ${CLANG_TRIPLE})
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET ${CLANG_TRIPLE})
set(CMAKE_RC_COMPILER llvm-rc)

# Problem: CMake runs toolchain files multiple times, but can't read cache variables on some runs.
# Workaround: On first run (in which cache variables are always accessible), set an intermediary environment variable.
# https://stackoverflow.com/a/29997033
# This also means we can pre-set them to when running inside a container
if(MSVC_WINE_ENV_SCRIPT OR XWIN_DIR)
    set(ENV{MSVC_WINE_ENV_SCRIPT} "${MSVC_WINE_ENV_SCRIPT}")
    set(ENV{XWIN_DIR} "${XWIN_DIR}")
else()
    set(MSVC_WINE_ENV_SCRIPT "$ENV{MSVC_WINE_ENV_SCRIPT}")
    set(XWIN_DIR "$ENV{XWIN_DIR}")
endif()

if(EXISTS ${MSVC_WINE_ENV_SCRIPT})
    # @brief Extract paths from the env script and pass them to another function
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

    _extract_from_env("INCLUDE" "-isystem" _msvc_wine_system_includes)
    add_compile_options(${_msvc_wine_system_includes})

    string(REPLACE ";" " " _msvc_wine_system_include_string "${_msvc_wine_system_includes}")
    set(CMAKE_RC_FLAGS "${CMAKE_RC_FLAGS} ${_msvc_wine_system_include_string}")

    _extract_from_env("LIB" "-L" _msvc_wine_link_options)
    add_link_options(${_msvc_wine_link_options})
elseif(EXISTS ${XWIN_DIR})
    set(_xwin_system_includes
        "-isystem${XWIN_DIR}/sdk/include/um"
        "-isystem${XWIN_DIR}/sdk/include/ucrt"
        "-isystem${XWIN_DIR}/sdk/include/shared"
        "-isystem${XWIN_DIR}/crt/include"
    )
    add_compile_options(${_xwin_system_includes})

    string(REPLACE ";" " " _xwin_system_include_string "${_xwin_system_includes}")
    set(CMAKE_RC_FLAGS "${CMAKE_RC_FLAGS} ${_xwin_system_include_string}")

    if(NOT DEFINED XWIN_ARCH)
        if(${CLANG_TRIPLE} MATCHES 64)
            set(XWIN_ARCH x86_64)
        else()
            set(XWIN_ARCH x86)
        endif()
    endif()

    add_link_options(
        "-L${XWIN_DIR}/sdk/lib/um/${XWIN_ARCH}"
        "-L${XWIN_DIR}/crt/lib/${XWIN_ARCH}"
        "-L${XWIN_DIR}/sdk/lib/ucrt/${XWIN_ARCH}"
    )
else()
    message(FATAL_ERROR "One of 'MSVC_WINE_ENV_SCRIPT' or 'XWIN_DIR' must be defined, could not find windows headers/libs!")
endif()

add_compile_options(-ffreestanding)

add_compile_options("$<$<CONFIG:DEBUG>:-gdwarf>")
add_link_options("$<$<CONFIG:DEBUG>:-gdwarf>" "$<$<CONFIG:DEBUG>:-Wl,/ignore:longsections>")

# Visual Studio 17.10 included a new constexpr mutex constructor, which requires a new version of
# VC Runtime to work properly. The cross compile build downloads the same headers.
# As of writing this, Proton still uses an older version, meaning a build using this causes a crash
# on startup.
# Temporarily disable it, until we get Proton support.
add_compile_definitions(_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR)

# See llvm-project#59689 - use the builtin so that offsetof becomes constexpr
add_compile_definitions(_CRT_USE_BUILTIN_OFFSETOF)
