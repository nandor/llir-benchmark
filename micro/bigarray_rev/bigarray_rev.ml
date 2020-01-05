open Bigarray

let create_int n =
  let a = Array1.create int c_layout n in
  for i = 0 to Array1.dim a - 1 do
    Array1.set a i i
  done;
  a

let create_int32 n =
  let a = Array1.create int32 c_layout n in
  for i = 0 to Array1.dim a - 1 do
    Array1.set a i (Int32.of_int i)
  done;
  a

let rev a =
  if Array1.dim a > 0
  then
    for i = 0 to (Array1.dim a - 1) / 2 do
      let t = Array1.get a i in
      Array1.set a i (Array1.get a (Array1.dim a - (1 + i)));
      Array1.set a (Array1.dim a - (1 + i)) t
    done;
  a

open Harness.Micro_bench_types

let check_int _ a =
  try
    for i = 0 to Array1.dim a - 1 do
      if Array1.get a i <> (Array1.dim a - (1 + i))
      then raise Exit
    done;
    Ok
  with Exit -> Error "incorrect rev"

let check_int32 _ a =
  try
    for i = 0 to Array1.dim a - 1 do
      if Int32.to_int (Array1.get a i) <> (Array1.dim a - (1 + i))
      then raise Exit
    done;
    Ok
  with Exit -> Error "incorrect rev"

let () = Harness.Micro_bench_run.run
  [ "reverse int bigarray",
    Int (rev,
         create_int,
         check_int,
         [Range (0,10000), Short;
          Range (10001, 1000000), Long;
          Range (1000001, 100000000), Longer]);
    "reverse int32 bigarray",
    Int (rev,
         create_int32,
         check_int32,
         [Range (0,10000), Short;
          Range (10001, 1000000), Long;
          Range (1000001, 100000000), Longer]) ]
