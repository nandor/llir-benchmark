#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>

typedef value ref;

ref gc_ref_create(value v) {
    CAMLparam1(v);
    CAMLlocal1(r);
    r = caml_alloc_small(1, 0);
    Field(r, 0) = v;
    CAMLreturn(r);
}

value gc_ref_get(ref r) {
    return Field(r, 0);
}

value gc_ref_delete(ref r) {
    caml_modify(&Field(r, 0), Val_unit);
    return Val_unit;
}

value gc_ref_modify(ref r, value v) {
    caml_modify(&Field(r, 0), v);
    return Val_unit;
}
