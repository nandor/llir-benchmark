type 'a t
external create : 'a -> 'a t         = "gc_ref_create"
external get : 'a t -> 'a            = "gc_ref_get" [@@noalloc]
external modify : 'a t -> 'a -> unit = "gc_ref_modify" [@@noalloc]
external delete : 'a t -> unit       = "gc_ref_delete" [@@noalloc]
