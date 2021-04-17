#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>

#include "abstract_out_of_heap.h"

typedef value ref;

ref global_ref_create(value v) {
    struct block *b = alloc_abstract_block();
    *(Block_data(b)) = v;
    caml_register_global_root(Block_data(b));
    return Val_block(b);
}

value global_ref_get(ref r) {
    return *(Block_data(Block_val(r)));
}

value global_ref_modify(ref r, value v) {
    struct block *b = Block_val(r);
    *Block_data(b) = v;
    return Val_unit;
}

value global_ref_delete(ref r) {
    struct block *b = Block_val(r);
    caml_remove_global_root(Block_data(b));
    free_abstract_block(b);
    return Val_unit;
}
