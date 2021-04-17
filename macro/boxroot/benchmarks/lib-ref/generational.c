#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/gc.h>

#include "abstract_out_of_heap.h"

typedef value ref;

ref generational_ref_create(value v) {
    struct block *b = alloc_abstract_block();
    *(Block_data(b)) = v;
    caml_register_generational_global_root(Block_data(b));
    return Val_block(b);
}

value generational_ref_get(ref r) {
    return Block_val(r)->v;
}

value generational_ref_modify(ref r, value v) {
    struct block *b = Block_val(r);
    caml_modify_generational_global_root(Block_data(b), v);
    return Val_unit;
}

value generational_ref_delete(ref r) {
    struct block *b = Block_val(r);
    caml_remove_generational_global_root(Block_data(b));
    free_abstract_block(b);
    return Val_unit;
}
