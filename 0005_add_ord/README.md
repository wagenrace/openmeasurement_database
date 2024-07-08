# Open Reaction Database

You might get an error with this submodule of [open reaction database](https://github.com/open-reaction-database/ord-data).
In that case run `git -C 0005_add_ord/ord-data lfs pull`

# Only InChI

This only using InChI part of the compounds. You can run it without the PubChem part.

Smallest dataset

```cmd
cd 0005_add_ord
python 01_load_data.py
```

Bigger dataset

```cmd
cd 0001_populate_chemicals
python 02_get_compounds.py
python 05_add_InChI.py
cd ../0005_add_ord
python 01_load_data.py
```