type 'a t = { mutable contents: 'a }

(* Creating the record on the OCaml side could be incorrect with
   a floating-point argument if the compiler inlined the call and
   performaed some float-related optimization. (Our `delete` would
   become unsound). Instead of trying to play with [@@inline false],
   we call the C implementation, which uses a compatible
   representation. *)
external create : 'a -> 'a t = "gc_ref_create"

let get r = r.contents

let modify r v = r.contents <- v

let delete r = r.contents <- Obj.magic ()
