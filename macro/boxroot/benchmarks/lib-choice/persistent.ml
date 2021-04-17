module Ref = Ref.Config.Ref

(* We want to implement a *linear* choice monad, in the sense that the
   monadic combinators "consume" ownership of their inputs (in the
   monad type). This restricts the sort of programs one can write
   (we could provide "dup" combinators), but it makes it easy to write
   versions that contain roots that must be explicitly deleted, and
   also to use data-structures that allocate less by reusing input lists.

   In this reference implementation, we dynamically enforce this
   ownership discipline with an "alive" reference on each value, which
   is set to false when it is consumed. *)

type 'a t = {
  alive: bool ref;
  bag: 'a Ref.t list;
  (* note: bag is an *unordered* list of values *)
 }

let consume { alive; bag } =
  assert !alive;
  alive := false;
  bag

let fresh bag = { alive = ref true; bag }

let map : type a b . (a -> b) -> a t -> b t = fun f li ->
  (* unordered map *)
  consume li
  |> List.rev_map (fun x -> Ref.create (f (Ref.consume x)))
  |> fresh

let return : type a . a -> a t = fun x ->
  fresh [Ref.create x]

let pair : type a b . a t -> b t -> (a * b) t = fun l1 l2 ->
  let l1, l2 = List.map Ref.consume (consume l1), List.map Ref.consume (consume l2) in
  List.fold_left (fun acc x1 ->
    List.fold_left (fun acc x2 ->
      Ref.create (x1, x2) :: acc
    ) acc l2
  ) [] l1
  |> fresh

let bind : type a b . (a -> b t) -> a t -> b t = fun f li ->
  consume li
  |> List.fold_left (fun acc x -> List.rev_append (consume (f (Ref.consume x))) acc) []
  |> fresh

let fail : type a . unit -> a t = fun () -> fresh []
let choice : type a . a t -> a t -> a t = fun l1 l2 ->
  fresh (List.rev_append (consume l1) (consume l2))

let run : type a . a t -> (a -> unit) -> unit = fun li f ->
  List.iter (fun x -> f (Ref.consume x)) (consume li)
