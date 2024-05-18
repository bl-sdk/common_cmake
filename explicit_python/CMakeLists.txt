add_library(explicit_python INTERFACE)

if(DEFINED ENV{EXPLICIT_PYTHON_DIR})
    set(_py_include_folder     "$ENV{EXPLICIT_PYTHON_DIR}/include")
    set(_py_lib_folder         "$ENV{EXPLICIT_PYTHON_DIR}/libs")
    set(_py_precompiled_folder "$ENV{EXPLICIT_PYTHON_DIR}")
elseif(DEFINED EXPLICIT_PYTHON_DIR)
    set(_py_include_folder     "${EXPLICIT_PYTHON_DIR}/include")
    set(_py_lib_folder         "${EXPLICIT_PYTHON_DIR}/libs")
    set(_py_precompiled_folder "${EXPLICIT_PYTHON_DIR}")
elseif(DEFINED EXPLICIT_PYTHON_VERSION AND DEFINED EXPLICIT_PYTHON_ARCH)
    include(FetchContent)
    FetchContent_Declare(
        _explicit_python_fetch
        # For some reason, actually putting our download command under DOWNLOAD_COMMAND causes cmake to
        # fail to touch some files in the stamp dir
        # Putting it under UPDATE_COMMAND instead works fine - and even means the cwd we download into
        # is the source dir, not the subbuild dir, which seems more appropriate
        DOWNLOAD_COMMAND ""
        UPDATE_COMMAND python "${CMAKE_CURRENT_SOURCE_DIR}/download.py" --cache --dir . ${EXPLICIT_PYTHON_VERSION} ${EXPLICIT_PYTHON_ARCH}
    )
    FetchContent_MakeAvailable(_explicit_python_fetch)

    set(_py_include_folder     "${_explicit_python_fetch_SOURCE_DIR}/include")
    set(_py_lib_folder         "${_explicit_python_fetch_SOURCE_DIR}/libs")
    set(_py_precompiled_folder "${_explicit_python_fetch_SOURCE_DIR}")

else()
    message(FATAL_ERROR "Cannot find Python version to link against!")
endif()

target_include_directories(explicit_python INTERFACE "${_py_include_folder}")

# Python debug files are all formatted `[name]_d.[extension]`
# While we can easily glob for them, it makes it annoying to find the release versions
# Instead, we glob for everything, then do a regex match to filter down
# We'll repeat this pattern a few more times

file(GLOB explicit_python_libs "${_py_lib_folder}/*.lib")
foreach(_file ${explicit_python_libs})
    if ("${_file}" MATCHES "_d\.[A-Za-z]+$")
        target_link_libraries(explicit_python INTERFACE "$<$<CONFIG:DEBUG>:${_file}>")
    else()
        target_link_libraries(explicit_python INTERFACE "$<$<NOT:$<CONFIG:DEBUG>>:${_file}>")
    endif()
endforeach()

# We need to install some files into the root dir, and some into /DLLs
# Can't seem to easily make install(FILES ...) preserve dir, so function it is

function(_install_python_files source_folder install_folder)
    file(GLOB dlls "${source_folder}/*.dll")
    file(GLOB pyds "${source_folder}/*.pyd")
    file(GLOB zips "${source_folder}/*.zip")
    foreach(_file ${dlls} ${pyds} ${zips})
        if ("${_file}" MATCHES "_d\.[A-Za-z]+$")
            install(
                FILES ${_file}
                CONFIGURATIONS Debug
                DESTINATION ${install_folder}
            )
        else()
            install(
                FILES ${_file}
                CONFIGURATIONS Release
                DESTINATION ${install_folder}
            )
        endif()
    endforeach()

    # PDBs are always debug
    file(GLOB pdbs "${source_folder}/*.pdb")
    install(
        FILES ${pdbs}
        CONFIGURATIONS Debug
        DESTINATION ${install_folder}
    )
endfunction()

_install_python_files("${_py_precompiled_folder}" ".")
_install_python_files("${_py_precompiled_folder}/DLLs" "DLLs")
