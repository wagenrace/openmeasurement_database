#%%
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import IPythonConsole
from rdkit.Chem import Draw

s_chem = Chem.MolFromSmiles("C[C@@H](CC1=CC=CC=C1)NC.Cl")
r_chem = Chem.MolFromSmiles("C[C@H](CC1=CC=CC=C1)NC.Cl")


rdkbis = {}
s_fp = Chem.RDKFingerprint(s_chem, maxPath=1, bitInfo=rdkbis)
rdkbir = {}
r_fp = Chem.RDKFingerprint(r_chem, maxPath=1, bitInfo=rdkbir)

s = list(s_fp.GetOnBits())
r = list(r_fp.GetOnBits())


#%% Draw fingerprints Chem S
max_num_2_draw = 24
tpls = [(s_chem, x, rdkbis) for x in rdkbis]
Draw.DrawRDKitBits(
    tpls[:max_num_2_draw],
    molsPerRow=4,
    legends=[str(x) for x in rdkbis][:max_num_2_draw],
)

#%% Draw fingerprints Chem R
tplr = [(r_chem, x, rdkbir) for x in rdkbir]
Draw.DrawRDKitBits(
    tplr[:max_num_2_draw],
    molsPerRow=4,
    legends=[str(x) for x in rdkbir][:max_num_2_draw],
)
