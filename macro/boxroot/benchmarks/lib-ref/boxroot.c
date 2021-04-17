#define CAML_NAME_SPACE
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include <assert.h>
#include <locale.h>

#include "../../boxroot/boxroot.h"

typedef value ref;

#define Boxroot_val(r) (boxroot*)&(Field(r,0))

ref boxroot_ref_create(value v) {
    boxroot b = boxroot_create(v);
    value r = caml_alloc_small(1, Abstract_tag);
    *Boxroot_val(r) = b;
    return r;
}

value boxroot_ref_get(ref r) {
    return boxroot_get(*Boxroot_val(r));
}

value boxroot_ref_delete(ref r) {
    boxroot_delete(*Boxroot_val(r));
    return Val_unit;
}

value boxroot_ref_modify(ref r, value v) {
    boxroot_modify(Boxroot_val(r), v);
    return Val_unit;
}

value boxroot_ref_setup(value unit)
{
  if (!boxroot_setup()) caml_failwith("boxroot_scan_hook_setup");
  return unit;
}

value boxroot_stats(value unit)
{
  char *old_locale = setlocale(LC_NUMERIC, NULL);
  setlocale(LC_NUMERIC, "en_US.UTF-8");
  boxroot_print_stats();
  setlocale(LC_NUMERIC, old_locale);
  return unit;
}

value boxroot_ref_teardown(value unit)
{
  boxroot_teardown();
  return unit;
}
