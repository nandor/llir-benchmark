#include "caml/mlvalues.h"
#include "caml/memory.h"
#include "caml/alloc.h"
#include "caml/gc.h"

/* code reused or inspired from ocaml/testsuite/tests/gc-roots/globrootsprim.c */

#include "abstract_out_of_heap.h"

struct block *alloc_abstract_block() {
    struct block *b = malloc(sizeof(struct block));
    b->header = Make_header(1, Abstract_tag, Caml_black);
    return b;
}

void free_abstract_block(struct block *b) {
    free(b);
}
