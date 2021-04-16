
let _ =
  let n = (int_of_string Sys.argv.(1)) in
  let a = Vec.create n in
  for i = 0 to n do
    Vec.push a i
  done;
  let b = Vec.create n in
  for i = 0 to n do
    Vec.push b i
  done;

  let s = ref 0 in
  for i = 0 to n do
    match Vec.get a i, Vec.get b i with
    | Some a', Some b' -> s := !s + a' * b'
    | _, _ -> assert false
  done;

  print_endline (string_of_int !s)
