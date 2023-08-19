# Enable Edit and Continue - replace /Zi with /ZI
string(REPLACE "/Zi" "" CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")
string(REPLACE "/Zi" "" CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}")
add_compile_options("$<$<CONFIG:DEBUG>:/ZI>")

add_link_options("/INCREMENTAL")

# Only enable /GL (which conflicts with /ZI) in release mode
string(REPLACE "/GL" "" CMAKE_C_COMPILE_OPTIONS_IPO "${CMAKE_C_COMPILE_OPTIONS_IPO}")
string(REPLACE "/GL" "" CMAKE_CXX_COMPILE_OPTIONS_IPO "${CMAKE_CXX_COMPILE_OPTIONS_IPO}")
add_compile_options("$<$<CONFIG:RELEASE>:/GL>")

# UTF-8 encoded source files
add_compile_options("/utf-8")
