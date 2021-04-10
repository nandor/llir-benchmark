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

(* let (p256_pk, p256_signature) = *)
let gen_key_sig () =
  let open Hacl_star in
  let sk_size = 32 in
  let rec get_valid_sk () =
    let sk = gen sk_size in
    if Hacl.P256.valid_sk sk then sk else get_valid_sk ()
  in
  (* let get_valid_sk () =
   *   let seed = gen sk_size in
   *   let sk = Bytes.create sk_size in
   *   Hacl.P256.reduction seed sk;
   *   sk
   * in *)
  let hacl_p256_keypair () =
    let pk_size_raw = 64 in
    let pk = Bytes.create pk_size_raw in
    let sk = get_valid_sk () in
    let pk_of_sk sk pk = Hacl.P256.dh_initiator pk sk in
    if pk_of_sk sk pk then (sk, pk) else failwith "P256.keypair: failure"
  in
  let (sk, pk) = hacl_p256_keypair () in
  let sig_size = 64 in
  let msg = Bigstring.to_bytes msg in
  let signature = Bytes.create sig_size in
  let k = get_valid_sk () in
  assert (Hacl.P256.sign sk msg k signature) ;
  (pk, signature)
