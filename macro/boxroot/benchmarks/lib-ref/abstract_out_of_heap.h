#ifndef ABSTRACT_OUT_OF_HEAP_H

#include "caml/mlvalues.h"

/* code reused or inspired from ocaml/testsuite/tests/gc-roots/globrootsprim.c */

struct block { value header; value v; };

#define Block_val(r) ((struct block*) &((value*) r)[-1])
#define Val_block(b) ((value) &((b)->v))

struct block *alloc_abstract_block(void);
void free_abstract_block (struct block *);

#define Block_data(b) &((b)->v)

#endif // ABSTRACT_OUT_OF_HEAP_H
