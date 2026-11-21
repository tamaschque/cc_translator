import math
import copy

def transform_indices(idx):
    if len(idx) == 4:
        # LO-RO-LI-RI -> LO-LI-RO-RI
        idx = idx[0] + idx[2] + idx[1] + idx[3]
    
    return idx

def get_ph_indices(idx):
    """Talapus uses the convention for p and h for particle/hole indices instead of actually writing out the characters. So eg. Kac -> K_pp"""
    particle = "abcdefgh"
    hole     = "ijklmno"

    output = ""
    for i in idx:
        if i in particle:
            output += "p"
        elif i in hole:
            output += "h"
        else:
            raise ValueError(f"Illegal index \"{i}\" encountered.")

    return output

def construct_tensor_name(full_name: str, idx):
    if full_name.startswith("V"):
        new_idx = "oi"
        name = "V_" + len(idx)//2 * new_idx

    else:
        name = full_name[:-len(idx)]
        name += "_" + get_ph_indices(idx)
    return name

def contract(idx1, idx2):
    """Return the contraction of the two sets of indices."""

    idx = idx1 + idx2
    idx_out = ""
    for i in idx:
        if idx.count(i) == 1:
            idx_out += i
    return idx_out


def nice_contract(idx1, idx2):

    # For a contraction with a tensor with only 2 indices we can just replace the common idx with the other one
    if len(idx1) == 2 or len(idx2) == 2:

        # Order indices by length
        idx = list(sorted([idx1,idx2], key=lambda x: len(x)))
        idx1 = idx[0]
        idx2 = idx[1]

        i_old = (set(idx1) & set(idx2)).pop()
        i_new = idx1.replace(i_old, '')

        return idx2.replace(i_old, i_new)

    # For other cases we can look it the contraction is nice in some way
    else:

        def get_idx_type(i, idx1, idx2):
            if (idx1+idx2).count(i) >= 2:
                return 'C'
            else:
                return 'D'

        types_1 = ''.join(get_idx_type(i, idx1, idx2) for i in idx1)
        types_2 = ''.join(get_idx_type(i, idx1, idx2) for i in idx2)

        match (types_1, types_2):

            # TODO: Generalize this to arbitrary contraction with maybe regex? D+?C+?, C+?D+?

            case ('DDCC', 'CCDD'):
                return idx1[:2] + idx2[2:]
            case ('CCDD', 'DDCC'):
                return idx2[:2] + idx1[2:]

            case _:
                return contract(idx1, idx2)


def get_line(line, filename="CcsdReference.cxx"):
    with open(filename, "r") as file:
        lines = file.readlines()

        return lines[line-1]

def permute(arr, permutation = None):
    if permutation is None:
        permutation = list(range(len(arr)))

    result = []
    for i in permutation:
        result.append(copy.deepcopy(arr[i]))

    return result



if __name__ == "__main__":

    x = permute(["a","b","c","d"], [3,1,2,0])
