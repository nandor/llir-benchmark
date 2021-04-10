/* The MIT License
 *
 *   Copyright (c) 2021 Nomadic Labs <contact@nomadic-labs.com>
 *
 *   Permission is hereby granted, free of charge, to any person obtaining a copy
 *   of this software and associated documentation files (the "Software"), to deal
 *   in the Software without restriction, including without limitation the rights
 *   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *   copies of the Software, and to permit persons to whom the Software is
 *   furnished to do so, subject to the following conditions:
 *
 *   The above copyright notice and this permission notice shall be included in all
 *   copies or substantial portions of the Software.
 *
 *   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 *   SOFTWARE.
 */


#include <caml/mlvalues.h>
#include <caml/bigarray.h>


CAMLprim value ml_Hacl_Ed25519_verify(value pk, value m, value sig) {
    return Val_bool(Hacl_Ed25519_verify(Caml_ba_data_val(pk),
                                        Caml_ba_array_val(m)->dim[0],
                                        Caml_ba_data_val(m),
                                        Caml_ba_data_val(sig)));
}

CAMLprim value ml_Hacl_P256_ecdsa_verif_without_hash(value pk, value m, value r, value s) {
    return Val_bool(Hacl_P256_ecdsa_verif_without_hash(Caml_ba_array_val(m)->dim[0],
                                                       Caml_ba_data_val(m),
                                                       Caml_ba_data_val(pk),
                                                       Caml_ba_data_val(r),
                                                       Caml_ba_data_val(s)));
}
