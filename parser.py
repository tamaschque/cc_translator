import itertools
import numpy as np

from helpers import *
from lexer import get_tokens

class Tensor:
    def __init__(self, name, idx):
        self.name = name
        self.idx = idx

    def __repr__(self):
        return f"{self.name}[{self.idx}]"


class Parser:
    def __init__(self, tokens):
        self.tokens = [(tok.type, tok.value) for tok in tokens]

        self.output = []    # Lines of output

    def pre_parse(self):
        """
        This function takes in the list of Tokens and processess them into the following objects:
            self.destination    ... The resulting tensor 
            self.operation      ... The type of operation that is peformed on this
                                    tensor (assignment or addition)
            self.factors        ... List of tensors involved in the contraction
            self.weights        ... Thermal occupancy/vacancy weights
            self.scale          ... A possible scalar factor
        """
        self.destination = None
        self.operation = None
        self.factors = []
        self.scale = 1.0

        for type, value in self.tokens:

            if type == 'TENSOR':
                idx = transform_indices(value[1])
                name = construct_tensor_name(value[0], idx)

                fac = Tensor(name, idx)
                self.factors.append(fac)

            elif type == 'NUMBER':
                self.scale *= value          

            elif type in ['ILSHIFT', 'IADD']:
                self.operation = type

        self.destination = self.factors.pop(0)

        # Add occupancy/vacancy factors

        self.weights = []
        # With outer indices we mean all destination indices
        for i in self.destination.idx:
            for tensor in self.factors:

                if i in tensor.idx and tensor.name.startswith('V'):

                    occ_tensor = Tensor(
                        f'n_{get_ph_indices(i)}',
                        i
                    )
                    self.weights.append(occ_tensor)

        self.order_contractions()

    def parse_tokens(self):
        self.pre_parse()

        print(f"{self.destination=}")
        print(f"{self.factors=}")
        print(f"{self.weights=}")

        dst = self.destination
        if len(self.factors) == 1:
            t = self.factors.pop(0)

            if self.operation == "ILSHIFT":
                line = f'{dst.name} = mea.copy({t.name})'
                
            elif self.operation == "IADD":
                line = f'mea.add_to({dst.name, t.name})'

            self.output.append(line)

        elif len(self.factors) == 2:
            tl = self.factors.pop(0)
            tr = self.factors.pop(0)

            contraction = f'mea.contract({tl.idx},{tr.idx}->{dst.idx}, {tl.name}, {tr.name})'

            if self.operation == "ILSHIFT":
                line = f'{dst.name} = {contraction}'
                
            elif self.operation == "IADD":
                line = f'mea.add_to({dst.name}, {contraction})'

            self.output.append(line)

        elif len(self.factors) >= 3:

            if self.operation == "IADD":
                dst_name = dst.name
                dst.name = "TEMP"

            # --- Do first contraction explicitly
            tl = self.factors.pop(0)
            tr = self.factors.pop(0)

            contr_idx = contract(tl.idx, tr.idx)

            self.output.append(
                f'{dst.name} = mea.contract("{tl.idx},{tr.idx}->{contr_idx}", {tl.name}, {tr.name})'
            )

            # --- All other intermediate contractions
            tl_idx = contr_idx
            for tr in self.factors[:-1]:

                contr_idx = contract(tl_idx, tr.idx)

                self.output.append(
                    f'{dst.name} = mea.contract("{tl_idx},{tr.idx}->{contr_idx}", {dst.name}, {tr.name})'
                )

                tl_idx = contr_idx

            # --- Do final contraction explicitly again
            t = self.factors[-1]
            self.output.append(
                f'{dst.name} = mea.contract("{contr_idx},{t.idx}->{dst.idx}", {dst.name}, {t.name})'
            )

        # --- Account for possible occupancy/vacany weights
        self.contract_weights(dst)

        # --- Rescaling
        if self.scale != 1.0:
            self.output.append(
                f'mea.mul_by({dst.name}, mea.from_numpy({self.scale}))'
            )

        if dst.name == "TEMP":
            self.output.append(f'')
            self.output.append(
                f'mea.add_to({dst_name}, {dst.name})'
            )

    def order_contractions(self):
        """
        Determine the best ordering of contractions, prefering more reducing ones. So avoid unnecessairy blowups like:
            ki <- ( ci * dl ) * klcd
        Instead try to reorder it to:
            ki <- ( klcd * ci ) * dl
        Or even better try to reduce it early to
            ki <- ( klcd * dl ) * ci

        Since we don't expect more than 4 factors in a given line we can just check all N! combintation of a contraction of N tensors

        We avoid expansions and incentivise early reductions by punishing non-reducing steps by the current index amount. This way reducing it early nets a lower score.        
        """

        # For 2 factors there is nothing to optimize
        if len(self.factors) == 2:
            return

        # Just try every permutation and see which one is the most reducing
        # Complexity is N! (But so far I've only seen products of at max 4 tensors so 4! = 24 is more than bareble)

        permutations = list(itertools.permutations(range(len(self.factors))))


        def get_storage_need(permutation):
            factors = permute(self.factors, permutation)

            x = 0
            tl = factors[0]

            # print(f"P: {permutation}: {factors=}")
            for i in range(1,len(factors)):
                
                tr = factors[i]

                contracted = contract(tl.idx, tr.idx)


                max_len = max(len(tl.idx), len(tr.idx))

                if len(contracted) > max_len:
                    # Expansion is Punished - At this point we can abandon this permutation
                    x = np.inf
                    return x
                elif len(contracted) == max_len:
                    # Punished by length
                    # So if we have the option to reduce it it should happen sooner rather than later
                    x += len(contracted)            
                elif len(contracted) <= max_len:
                    # Rewarded by gain
                    x += len(contracted) - max_len  

                # print(f"{i=}: {contracted} | {x=}")

                tl.idx = contracted

            return x

        scores = []
        for p in permutations:

            scores.append(get_storage_need(p))

        # print(scores)
        # print(permutations)

        i = np.argmin(scores)

        # print(f"Best Permutation: {permutations[i]}")

        self.factors = permute(self.factors, permutations[i])

        return

    def contract_weights(self, t):
        if len(self.weights) > 0:
            self.output.append(f'')
            self.output.append(f'# Adding thermal weights')

        for n in self.weights:
            self.output.append(
                f'{t.name} = mea.contract(\"{t.idx},{n.idx}->{t.idx}\", {t.name}, {n.name})'
            )

        self.output.append(f'')

if __name__ == "__main__":

    WRITE_TO_FILE = True

    with open("showcase.txt", "w") as file:

        if not WRITE_TO_FILE:
            file = None


        line = get_line(229)
        line = r"""(*Kac)["ac"] += ( 1.0) * (*Tph)["ak"] * (*Tph)["dl"] * (*Vhhpp)["kldc"]"""
        
        print(f"Read Line:\n\t{line.strip()}", file=file)

        tokens = get_tokens(line)

        parser = Parser(tokens)
        parser.parse_tokens()

        print("\n\nTranslated Code:", file=file)
        for line in parser.output:
            print("\t" + line, file=file)

        print("\n", file=file)