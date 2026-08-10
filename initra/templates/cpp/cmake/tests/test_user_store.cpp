// ponytail: plain <cassert> checks run by ctest -- no gtest/catch2 dependency.
// Swap in a framework if you outgrow assert-and-abort.
#include <cassert>
#include <iostream>

#include "user_store.h"

int main() {
  app::UserStore store;
  assert(store.List().empty());

  const app::User created = store.Create("Ada Lovelace", "Ada@Example.com");
  assert(created.id == 1);
  assert(created.email == "ada@example.com");  // emails are normalized
  assert(store.List().size() == 1);

  assert(store.Get(1).has_value());
  assert(!store.Get(99).has_value());

  const auto updated = store.Update(1, "Grace Hopper", "GRACE@example.com");
  assert(updated.has_value());
  assert(updated->name == "Grace Hopper");
  assert(updated->email == "grace@example.com");
  assert(!store.Update(99, "Nobody", "nobody@example.com").has_value());

  const app::User second = store.Create("Alan Turing", "alan@example.com");
  assert(second.id == 2);  // ids are not reused

  assert(store.Delete(1));
  assert(!store.Delete(1));
  assert(store.List().size() == 1);

  std::cout << "user_store tests passed" << std::endl;
  return 0;
}
