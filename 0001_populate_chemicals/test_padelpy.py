from padelpy import from_smiles

# calculate molecular descriptors for propane
descriptors = from_smiles("CCC")

# calculate molecular descriptors for propane and butane
descriptors = from_smiles(["CCC", "CCCC"])

# in addition to descriptors, calculate PubChem fingerprints
desc_fp = from_smiles("CCC", fingerprints=True)

# only calculate fingerprints
fingerprints = from_smiles("CCC", fingerprints=True, descriptors=False)
