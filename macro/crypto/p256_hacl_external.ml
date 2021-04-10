(* The MIT License (MIT)
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
 *   SOFTWARE. *)

open Util
open Util_p256
open Hacl_star

external p256_verify :
  Bigstring.t -> Bigstring.t -> Bigstring.t -> Bigstring.t -> bool =
  "ml_Hacl_P256_ecdsa_verif_without_hash" [@@noalloc]

(* Runs the same underlying C function from hacl-star-raw, but bypasses
   the Ctypes bindings, using the same style as ocaml-uecc *)
let () =
  let (p256_pk, p256_signature) = gen_key_sig () in
  let r, s = Bytes.sub p256_signature 0 32, Bytes.sub p256_signature 32 32 in
  let b_r = Bigstring.of_bytes r in
  let b_s = Bigstring.of_bytes s in
  let b_p256_pk = Bigstring.of_bytes p256_pk in
  for _ = 0 to int_of_string Sys.argv.(1) do
    assert (p256_verify b_p256_pk msg b_r b_s);
  done
