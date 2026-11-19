
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
        # FIXME: Outer Indices != All indices in destination?

        self.weights = []
        outer_idx = [self.destination.idx[0], self.destination.idx[-1]]
        for i in outer_idx:
            for tensor in self.factors:

                if i in tensor.idx and tensor.name.startswith('V'):

                    occ_tensor = Tensor(
                        f'n_{get_ph_indices(i)}',
                        i
                    )
                    self.weights.append(occ_tensor)

        self.order_contractions()   # TODO

    def parse_tokens(self):
        self.pre_parse()

        # print(f"{self.factors=}")
        # print(f"{self.weights=}")


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
        Determine the best ordering of contractions, prefering more reducing ones.
        
        In general a contractions of a N indices requires:
            

        """
        # TODO
        

        return

    def contract_weights(self, t):
        if len(self.weights) > 0:
            self.output.append(f'')
            self.output.append(f'# Adding thermal weights')

        for n in self.weights:
            self.output.append(
                f'{t.name} = mea.contract({t.idx},{n.idx}->{t.idx}, {t.name}, {n.name})'
            )

        self.output.append(f'')

if __name__ == "__main__":

    with open("showcase.txt", "w") as file:

        for n in range(86,91):

            line = get_line(n)

            file.write(f"Read Line:\n\t{line.strip()}")

            tokens = get_tokens(line)

            parser = Parser(tokens)
            parser.parse_tokens()

            file.write("\n\nTranslated Code:\n")
            for line in parser.output:
                file.write("\t" + line + "\n")

            file.write("\n")