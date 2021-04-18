(* This file is part of the llir project. *)
(* Licensing information can be found in the LICENSE file. *)
(* (C) 2018 Nandor Licker. All rights reserved. *)

let rec fft_in_place v = function
  | 0 -> ()
  | 1 -> ()
  | n ->
    let h = n / 2 in

    let h0 = Complex.vec_init h (fun i -> Complex.vec_get v (i * 2 + 0)) in
    let h1 = Complex.vec_init h (fun i -> Complex.vec_get v (i * 2 + 1)) in
    fft_in_place h0 h;
    fft_in_place h1 h;

    for i = 0 to n / 2 - 1 do
      let e = Complex.vec_get h0 i in
      let o = Complex.vec_get h1 i in
      let r = (-2.) *. Float.pi *. float_of_int i /. float_of_int n in
      let w = Complex.exp (Complex.make 0. r) in

      Complex.(vec_set v (i)         (add e (mul w o)));
      Complex.(vec_set v (i + n / 2) (sub e (mul w o)));
    done


let rec fft v =
  let x = Complex.vec_dup v in
  let n = Complex.vec_length v in
  fft_in_place x n;
  x

let test n =
  let freqs = [2.; 5.; 11.; 17.; 29.] in
  let x = Complex.vec_init n (fun i ->
    let r = float_of_int i /. float_of_int n in
    Complex.make (List.fold_left (+.) 0.0 (List.map (fun freq ->
      sin (2. *. Float.pi *. freq *. r)
    ) freqs)) 0.0
  )
  in
  let v = fft x in
  for i = 0 to n - 1 do
    let xi = Complex.re (Complex.vec_get x i)in
    let vi = Complex.abs (Complex.vec_get v i) in
    Printf.eprintf "% 3d\t%+ 2.5f\t% 2.5f\n" i xi vi;
  done

let () =
  let n = (try int_of_string (Sys.argv.(1)) with _ -> 64) in
  test n
