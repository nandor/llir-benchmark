type 'a t
external create : 'a -> 'a t         = "generational_ref_create"
external get : 'a t -> 'a            = "generational_ref_get"
external modify : 'a t -> 'a -> unit = "generational_ref_modify"
external delete : 'a t -> unit       = "generational_ref_delete"
