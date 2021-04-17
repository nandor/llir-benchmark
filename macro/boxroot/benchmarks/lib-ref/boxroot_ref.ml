type 'a t
external create : 'a -> 'a t         = "boxroot_ref_create"
external get : 'a t -> 'a            = "boxroot_ref_get" [@@noalloc]
external modify : 'a t -> 'a -> unit = "boxroot_ref_modify" [@@noalloc]
external delete : 'a t -> unit       = "boxroot_ref_delete" [@@noalloc]

external setup : unit -> unit = "boxroot_ref_setup"
external teardown : unit -> unit = "boxroot_ref_teardown"

external stats : unit -> unit = "boxroot_stats"

let show_stats = ref false

let () =
  setup ();
  at_exit (fun () ->
    if !show_stats then stats ();
    teardown ())
