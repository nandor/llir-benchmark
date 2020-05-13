Set Implicit Arguments.

Inductive tuple (A: Type) :=
  | cons
    (a0: A) (a1: A) (a2: A) (a3: A) (a4: A) (a5: A) (a6: A) (a7: A)
  .

Definition explode (B: Type) (b: B): tuple B := cons b b b b b b b b.

Inductive Unit := unit.


Definition explode8 (A: Type) (v: A) :=
 explode (explode (explode (explode (explode (explode v))))).

Compute explode (explode8 Unit).
