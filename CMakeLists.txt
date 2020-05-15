cmake_minimum_required(VERSION 3.15)
project(pglogical)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD 11)

get_property(POSTGRES_SRC_DIR GLOBAL PROPERTY POSTGRES_SRC_DIR)
get_property(POSTGRES_BIN_DIR GLOBAL PROPERTY POSTGRES_BIN_DIR)
get_property(POSTGRES_DISTRIB_LIB_DIR GLOBAL PROPERTY POSTGRES_DISTRIB_LIB_DIR)
include_directories(${POSTGRES_SRC_DIR}/src/include)
include_directories(${POSTGRES_SRC_DIR}/src/interfaces/libpq)

if(${CMAKE_HOST_SYSTEM_VERSION} MATCHES "^([^\\.]+\\.)+el7\\.x86_64$")
    get_property(LLVM_LIBRARY_DIRS GLOBAL PROPERTY LLVM_LIBRARY_DIRS)
    link_directories(${LLVM_LIBRARY_DIRS})
endif()

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/compat12)

set(pglogical_src
    pglogical_apply.c
    pglogical_conflict.c
    pglogical_manager.c
    pglogical.c
    pglogical_node.c
    pglogical_relcache.c
    pglogical_repset.c
    pglogical_rpc.c
    pglogical_functions.c
    pglogical_queue.c
    pglogical_fe.c
    pglogical_worker.c
    pglogical_sync.c
    pglogical_sequences.c
    pglogical_executor.c
    pglogical_dependency.c
    pglogical_apply_heap.c
    pglogical_apply_spi.c
    pglogical_output_config.c
    pglogical_output_plugin.c
    pglogical_output_proto.c
    pglogical_proto_json.c
    pglogical_proto_native.c
    pglogical_monitoring.c
    compat12/pglogical_compat.c
)

set(pglogical_create_subscriber_src
    pglogical_create_subscriber.c
    pglogical_fe.c
)

set(pglogical_output_src
    pglogical_output.c
)

add_executable(pglogical_create_subscriber
    ${pglogical_create_subscriber_src}
)

target_link_libraries(pglogical_create_subscriber pq pgcommon pgport)
add_dependencies(pglogical_create_subscriber postgres)

add_library(pglogical_output SHARED ${pglogical_output_src})
set_target_properties(pglogical_output PROPERTIES PREFIX "")
add_dependencies(pglogical_output postgres)

add_library(pglogical SHARED ${pglogical_src})
set_target_properties(pglogical PROPERTIES PREFIX "")
add_dependencies(pglogical postgres pglogical_create_subscriber pglogical_output)

add_custom_command(TARGET pglogical
    PRE_BUILD
    COMMAND awk '/\#define PGLOGICAL_VERSION[ \t]+\".*\"/ { print substr\($$3,2,length\($$3\)-2\) }' ${CMAKE_CURRENT_SOURCE_DIR}/pglogical.h > pglogical_version
    COMMAND sh -c \"sed 's/__PGLOGICAL_VERSION__/$$\(cat pglogical_version\)/\;s/__REQUIRES__//' ${CMAKE_CURRENT_SOURCE_DIR}/pglogical.control.in > ${CMAKE_CURRENT_SOURCE_DIR}/pglogical.control\"
)

target_link_libraries(pglogical pq)

install(TARGETS	pglogical pglogical_output
    DESTINATION ${POSTGRES_DISTRIB_LIB_DIR}
    LIBRARY DESTINATION ${LIBDIR}
)

install(TARGETS pglogical_create_subscriber
    RUNTIME DESTINATION ${PGBINDIR}
    LIBRARY DESTINATION ${LIBDIR}
)

file(GLOB SQL_FILES ${CMAKE_CURRENT_SOURCE_DIR}/pglogical_origin--*.sql ${CMAKE_CURRENT_SOURCE_DIR}/pglogical--*.sql)

set(PGSHAREDIR "share/postgresql")
install(FILES pglogical.control pglogical_origin.control ${SQL_FILES}
    DESTINATION ${PGSHAREDIR}/extension
)
