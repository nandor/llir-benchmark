(* this *linear* function consumes the ownership of its argument *)
type ('a, 'b) linfun = 'a -> 'b
module type LinChoice = sig
  (* a choice/non-determinism monad whose combinators are linear (own their arguments);
     this is pointed out explicitly so that C implementation can free their input structures
     without having to track liveness. *)
    type 'a t

    val map : ('a -> 'b) -> ('a t, 'b t) linfun

    val return : 'a -> 'a t
    val pair : ('a t, ('b t, ('a * 'b) t) linfun) linfun

    val bind : ('a -> 'b t) -> ('a t, 'b t) linfun

    val fail : unit -> 'a t
    val choice : ('a t, ('a t, 'a t) linfun) linfun

    val run : ('a t, ('a -> unit) -> unit) linfun
end

let implementations : (string * (module LinChoice)) list = [
  "persistent", (module Persistent);
  "ephemeral", (module Ephemeral);
]

let implem_name, implem_module =
  Ref.Config.choose_implem "CHOICE" implementations

module Choice = struct
  include (val implem_module : LinChoice)
  module Syntax = struct
    let ( let+ ) a f = map f a
    let ( and+ ) a1 a2 = pair a1 a2
    let ( let* ) m f = bind f m
  end
end
