# Questions
 *  WDYM with "outer indices" (with regard to the thermal weights?)

    Just the leftmost and rightmost indices of the destiniation indices? Or all of them?


 *  How to handle `[Tensor] += [Contractions]` ? Just do: `[Tensor] += mea.contract(...)` ? Do we just do?
    ```
    mea.add_to( Tensor, mea.contract(...) )
    ```
    Because especially if we have 3 or more contractions I guess we're gonna need some temporary variables to store the intermediates? So for this case I currently do:
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
    TEMP = mea.contract("klij,ak->alij, R_phph, T_ph)
    TEMP = mea.contract("alij,bl->abij, R_phph, T_ph)
    
    mea.add_to(R_phph, TEMP)
    ```

    Or do we need to create temporary tensors for all of these? So something more like:

    ```
    TEMP1 = mea.contract("klcd,cdij->klij, V_oioi, T_phph)
    TEMP2 = mea.contract("klij,ak->alij, TEMP1, T_ph)
    R_phph = mea.contract("alij,bl->abij, TEMP2, T_ph)
    ```
