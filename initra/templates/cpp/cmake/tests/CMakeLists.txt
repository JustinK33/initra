add_executable(test_user_store test_user_store.cpp)
target_link_libraries(test_user_store PRIVATE {{project_name}}_lib)
add_test(NAME user_store COMMAND test_user_store)

add_executable(test_server test_server.cpp)
target_link_libraries(test_server PRIVATE {{project_name}}_lib)
add_test(NAME server COMMAND test_server)
