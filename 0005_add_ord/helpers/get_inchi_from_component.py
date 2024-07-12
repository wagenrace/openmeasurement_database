from ord_schema.proto.reaction_pb2 import CompoundIdentifier, Compound

from rdkit import Chem


def get_inchi(component: Compound) -> str:
    inchi = ""
    smiles = ""
    for identifier in component.identifiers:
        if identifier.type == CompoundIdentifier.INCHI:
            inchi = identifier.value
        if identifier.type == CompoundIdentifier.SMILES:
            smiles = identifier.value

    if not inchi and smiles:
        chem = Chem.MolFromSmiles(smiles)
        inchi = Chem.MolToInchi(chem)

    inchi = str(inchi)
    return inchi
