external local_fixpoint : (float -> float) -> float -> float = "local_fixpoint"
external boxroot_fixpoint : (float -> float) -> float -> float = "boxroot_fixpoint"
external generational_fixpoint : (float -> float) -> float -> float = "generational_fixpoint"

external boxroot_setup : unit -> unit = "caml_boxroot_setup"
external boxroot_teardown : unit -> unit = "caml_boxroot_teardown"

external boxroot_stats : unit -> unit = "caml_boxroot_stats"

let implementations = [
  "local", local_fixpoint;
  "boxroot", boxroot_fixpoint;
  "generational", generational_fixpoint;
]

let fixpoint =
  try List.assoc (Sys.getenv "ROOT") implementations with
  | _ ->
    Printf.eprintf "We expect an environment variable ROOT with value one of [ %s ].\n%!"
      (String.concat " | " (List.map fst implementations));
    exit 2

let n =
  try int_of_string (Sys.getenv "N") with
  | _ ->
    Printf.eprintf "We expect an environment variable N, whose value is an integer";
    exit 2

let show_stats =
  match Sys.getenv "STATS" with
  | "true" | "1" | "yes" -> true
  | "false" | "0" | "no" -> false
  | _ | exception _ -> false

let () =
  boxroot_setup ();
  for _i = 1 to (100_000_000 / (max 1 n)) do
    ignore (fixpoint (fun x -> if truncate x >= n then x else x +. 1.) 1.)
  done;
  if show_stats then boxroot_stats ();
  boxroot_teardown ();
  Printf.printf "local_roots(ROOT=%-*s, N=%s): %.2fs\n%!"
    (List.fold_left max 0 (List.map String.length (List.map fst implementations)))
    (Sys.getenv "ROOT") (Sys.getenv "N") (Sys.time ())
