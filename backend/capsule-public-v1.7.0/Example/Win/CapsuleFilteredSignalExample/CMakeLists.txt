cmake_minimum_required(VERSION 3.13)

project(CapsuleFilteredSignalExample LANGUAGES CXX)

add_executable(CapsuleFilteredSignalExample main.cpp)

set(CAPSULE_WIN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../capsuleAPI/Win")

target_include_directories(CapsuleFilteredSignalExample
    PRIVATE
        "${CAPSULE_WIN_DIR}/Include"
        "${CAPSULE_WIN_DIR}/Source"
)

target_link_libraries(CapsuleFilteredSignalExample
    PRIVATE
        "${CAPSULE_WIN_DIR}/Lib/CapsuleClient.lib"
        ws2_32
)

set_target_properties(CapsuleFilteredSignalExample PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)

# Keep runtime dependency near the built executable for local runs.
add_custom_command(TARGET CapsuleFilteredSignalExample POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CAPSULE_WIN_DIR}/Lib/CapsuleClient.dll"
            "$<TARGET_FILE_DIR:CapsuleFilteredSignalExample>/CapsuleClient.dll"
)
