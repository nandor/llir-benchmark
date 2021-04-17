module Ref = Ref.Config.Ref

type 'a mlist = | Nil | Cons of { hd : 'a; mutable tl: 'a mlist }

type 'a t = {
  alive: bool ref;
  bag: 'a Ref.t mlist;
  (* note: bag is an *unordered* list of values *)
 }

let consume { alive; bag } =
  assert !alive;
  alive := false;
  bag

let fresh bag = { alive = ref true; bag }

let set_tl dst tl =
  match dst with
  | Nil -> invalid_arg "set_tl"
  | Cons cell -> cell.tl <- tl

let rec mlist_map f = function
  | Nil -> Nil
  | Cons { hd; tl } ->
    let dst = Cons { hd = Ref.create (f (Ref.consume hd)); tl = Nil } in
    mlist_map_dst dst f tl;
    dst
and mlist_map_dst dst f = function
  | Nil -> ()
  | Cons { hd; tl } ->
    let dst' = Cons { hd = Ref.create (f (Ref.consume hd)); tl = Nil } in
    set_tl dst dst';
    mlist_map_dst dst' f tl

let rec mlist_delete = function
  | Nil -> ()
  | Cons { hd; tl } -> Ref.delete hd; mlist_delete tl

let rec mlist_append_in_place la lb =
  match la with
  | Nil -> lb
  | Cons _ ->
    mlist_set_tail la lb;
    la
and mlist_set_tail li tail =
  match li with
  | Nil -> assert false
  | Cons ({ hd = _; tl } as cell) ->
    match tl with
    | Nil -> cell.tl <- tail
    | _ -> mlist_set_tail tl tail

let map f li =
  (* unordered map *)
  consume li
  |> mlist_map f
  |> fresh

let return x = fresh (Cons { hd = Ref.create x; tl = Nil })

let pair l1 l2 =
  let l1, l2 = consume l1, consume l2 in
  let rec pair1 acc xs1 l2 =
    match xs1 with
    | Nil -> acc
    | Cons { hd = x1; tl = xs1 } -> pair2 acc x1 xs1 l2 l2
  and pair2 acc x1 xs1 xs2 l2 =
    match xs2 with
    | Nil -> pair1 acc xs1 l2
    | Cons { hd = x2; tl = xs2 } ->
      let p = Ref.create (Ref.get x1, Ref.get x2) in
      pair2 (Cons { hd = p; tl = acc }) x1 xs1 xs2 l2
  in
  let l12 = pair1 Nil l1 l2 in
  mlist_delete l1;
  mlist_delete l2;
  fresh l12

let bind f li =
  let rec flatten_rev_map f acc = function
    | Nil -> acc
    | Cons { hd; tl } ->
      let li = consume (f (Ref.consume hd)) in
      flatten_rev_map f (mlist_append_in_place li acc) tl
  in
  consume li
  |> flatten_rev_map f Nil
  |> fresh

let fail () = fresh Nil
let choice l1 l2 = fresh (mlist_append_in_place (consume l1) (consume l2))

let run li f =
  let rec iter f = function
    | Nil -> ()
    | Cons { hd = x; tl = xs } -> f (Ref.consume x); iter f xs
  in iter f (consume li)
