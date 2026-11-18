
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
    idx = idx1 + idx2
    idx_out = ""
    for i in idx:
        if idx.count(i) == 1:
            idx_out += i
    return idx_out

def get_line(line, filename="CcsdReference.cxx"):
    with open(filename, "r") as file:
        lines = file.readlines()

        return lines[line-1]

if __name__ == "__main__":
    print(contract("abij","klij"))
