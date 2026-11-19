# Questions
 *  WDYM with "outer indices" (with regard to the thermal weights?)

    Just the leftmost and rightmost indices of the destiniation indices? As is implemented currently


 *  How to handle `[Tensor] += [Contractions]` ? Just do: `[Tensor] += mea.contract(...)` ? Currently I do:
    ```
    mea.add_to( Tensor, mea.contract(...) )
    ```
    Or for 3 or more contractions I guess we're gonna need some temporary variables to store the intermediates? So for this case I currently do:
    ```
    TEMP = mea.contract(...)
    TEMP = mea.contract(...)

    mea.add_to(Tensor, TEMP)
    ```


 *  How do handle products of 3 or more tensors? Eg.

    ```
    (*Rpphh)["abij"] += (*Vhhpp)["klcd"] * (*Tpphh)["cdij"] * (*Tph)["ak"] * (*Tph)["bl"]
    ```

    Can we be "sloppy" with the indices? So just stupidly do:

    ```
    TEMP = mea.contract("klcd,cdij->klij, V_oioi, T_phph)
    TEMP = mea.contract("klij,ak->alij, TEMP, T_ph)
    TEMP = mea.contract("alij,bl->abij, TEMP, T_ph)
    
    mea.add_to(R_phph, TEMP)
    ```
   Or directly write into `R_phph` for `<<=`