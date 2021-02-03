# Description of the brenparse library
Much of the data in the BRENDA database (https://www.brenda-enzymes.org/) is available through their SOAP client, but not all. The aim of this package is address this issue by parsing BRENDA html files to obtain the data therein. One needs to first download the html pages that one wishes to parse and this library can then be used to extract data.


## Installation
Download repository and unzip (alternatively fork or clone).

__If using an anaconda environment__ you may have to first locate the anaconda pip using whereis.
```bash
>>> whereis pip
```

Locate the appropriate file path (the one that has anaconda and the correct environment in the filepath) and run the modified command. For example:

```bash
>>> /home/username/anaconda3/envs/py37/bin/pip install -e .
```

__If _not_ using an anaconda environment__ simply install using pip:

```bash
>>> pip install -e .
```

The dependency beautifulsoup4 will be installed automatically (scripts were tested using beautifulsoup4 version 4.9.3). The library should now be available for loading in all your python scripts.


## Requirements
* Unix system
* python3
* beautifulsoup4


# How to use the brenparse library
The BRENDA database is parsed one html page at a time, with each page holding information for a single EC class (for example https://www.brenda-enzymes.org/enzyme.php?ecno=1.1.3.15). This page needs to be downloaded and stored locally. The path to this file represents the input to brenparse.

```python3
>>> from brenparse import parser
>>> filepath = parser.EXAMPLE_PAGE
>>> soup_obj = parser.open_ec(filepath)
```

 The generated soup object is subsequently passed to functions that parse the individual tables.

## Parsing BRENDA tables
The various tables in BRENDA contain a differing number of columns and the output obtained after parsing is therefore different. See each entry below for details.

### The organism table
The organism table represents a special case as there are no data values. The data is returned as as a dictionary with organism names as keys holding a list of UniProt identifiers as values. By default only records with UniProt identifiers are returned (i.e. leaving out records without identifiers).

```python3
>>> parser.Organism(soup_obj).get_data() # Parsing the ORGANISM table in BRENDA
{'Mus musculus': ['Q9NYQ2', 'Q9WU19'], 'Pachysandra terminalis': ['Q19U05'], 'Phaeodactylum tricornutum': ['B7FUG8'], 'Rattus norvegicus': ['Q07523'], 'Homo sapiens': ['Q9NYQ3', 'Q9UJM8'], 'Lactococcus lactis': ['Q9CG58'], 'Streptococcus iniae': ['A9QH69'], 'Arabidopsis thaliana': ['Q24JJ8', 'Q56ZN0', 'Q9LJH5', 'Q9LRR9'], 'Oryza sativa': ['Q10CE4']}
```

If the uid_orgs_only variable in get_data() is set to False then all records are returned.

```python3
>>> parser.Organism(soup_obj).get_data(uid_orgs_only=False) # Parsing the ORGANISM table in BRENDA
{'Amaranthus retroflexus': [], 'Brassica rapa': [], 'Cucumis sativus': [], 'Geotrichum candidum': [], 'Homo sapiens': ['Q9NYQ3', 'Q9UJM8'], 'Lactococcus lactis': ['Q9CG58'], 'Mammalia': [], 'Mus musculus': ['Q9NYQ2', 'Q9WU19'], 'Mycolicibacterium smegmatis': [], 'Oceanimonas doudoroffii': [], 'Pachysandra terminalis': ['Q19U05'], 'Phaeodactylum tricornutum': ['B7FUG8'], 'Pseudomonas stutzeri': [], 'Rattus norvegicus': ['Q07523'], 'Rattus sp': [], 'Spinacia oleracea': [], 'Streptococcus iniae': ['A9QH69'], 'Streptococcus pneumoniae': [], 'Sus scrofa': [], 'Triticum aestivum': [], 'Zea mays': [], 'Aerococcus viridans': [], 'Arabidopsis thaliana': ['Q24JJ8', 'Q56ZN0', 'Q9LJH5', 'Q9LRR9'], 'Carica papaya': [], 'Gallus gallus': [], 'Glycine max': [], 'Lathyrus sativus': [], 'Mesostigma viride': [], 'Nicotiana tabacum': [], 'Oryza sativa': ['Q10CE4'], 'Pediococcus sp': [], 'Plant': [], 'Rana pipiens': [], 'Roseobacter sp': [], 'Streptococcus cristatus': [], 'Streptococcus pyogenes': [], 'Tetrahymena pyriformis': [], 'Vigna unguiculata': []}
```


### Three-level tables
The three-level tables have the structure: value, organism, uniprot_id. The value can be numeric or text, depending on the table. The data is returned as a dictionary of organism names as keys, holding dictionaries as values wherein each UniProt identifier holds a list of values. By default only records with UniProt identifiers are returned (i.e. leaving out records without identifiers)

```python3
>>> parser.TemperatureOptimum(soup_obj).get_data() # Parsing the TEMPERATURE OPTIMUM table in BRENDA
{'Arabidopsis thaliana': {'Q24JJ8': [25.0], 'Q9LJH5': [25.0], 'Q9LRR9': [25.0]}}
```

If the uid_orgs_only variable in get_data() is set to False then all records are returned. For each organism, records without identifiers are collected under the "unknown" key.

```python3
>>> parser.TemperatureOptimum(soup_obj).get_data(uid_orgs_only=False) # Parsing the TEMPERATURE OPTIMUM table in BRENDA
{'Homo sapiens': {'unknown': [30.0, 37.0]}, '4 entries': {'unknown': [25.0]}, 'Aerococcus viridans': {'unknown': [25.0]}, 'Arabidopsis thaliana': {'Q24JJ8': [25.0], 'Q9LJH5': [25.0], 'Q9LRR9': [25.0]}, 'Pediococcus sp': {'unknown': [25.0]}, 'Rattus norvegicus': {'unknown': [25.0]}}
```


A full list of the three-level tables:
```python3
>>> TemperatureOptimum(soub_obj).get_data() # Parsing the TEMPERATURE OPTIMUM table in BRENDA
>>> Cofactor(soub_obj).get_data() # Parsing the COFACTOR table in BRENDA
>>> MetalsAndIons(soub_obj).get_data() # Parsing the METALS and IONS table in BRENDA
>>> Inhibitors(soub_obj).get_data() # the INHIBITORS table in BRENDA
>>> ActivatingCompound(soub_obj).get_data() # Parsing the ACTIVATING COMPOUND table in BRENDA
>>> SpecificActivity(soub_obj).get_data() # Parsing the SPECIFIC ACTIVITY table in BRENDA
>>> PhOptimum(soub_obj).get_data() # Parsing the pH OPTIMUM table in BRENDA
>>> PhRange(soub_obj).get_data() # Parsing the pH RANGE table in BRENDA
>>> TemperatureRange(soub_obj).get_data() # Parsing the TEMPERATURE RANGE table in BRENDA
>>> PhStability(soub_obj).get_data() # Parsing the pH STABILITY table in BRENDA
>>> TemperatureStability(soub_obj).get_data() # Parsing the TEMPERATURE STABILITY table in BRENDA
```

### Four-level tables
The four-level tables have the structure: value, comment, organism, uniprot_id. The value is always numeric. The data is returned as a dictionary of organism names as keys, holding nested dictionaries as values. The structure is dictionary[organism][uniprot_id][substrate] where the last level holds lists containing the values. By default only records with UniProt identifiers are returned (i.e. leaving out records without identifiers)

```python3
>>> parser.Km(soup_obj).get_data() # Parsing the KM VALUE [mM] table in BRENDA
{'Arabidopsis thaliana': {'Q24JJ8': [25.0], 'Q9LJH5': [25.0], 'Q9LRR9': [25.0]}}
```

If the uid_orgs_only variable in get_data() is set to False then all records are returned. For each organism, records without identifiers are collected under the "unknown" key.

```python3
>>> parser.Km(soup_obj).get_data(uid_orgs_only=False) # Parsing the KM VALUE [mM] table in BRENDA
{'Homo sapiens': {'unknown': {'2,6-dichlorophenolindophenol': [0.033], '2-Hydroxyoctanoate': [0.045], '2-oxo-octanoate': [0.04], 'glycolate': [0.0056, 0.12, 0.141, 0.2, 0.23, 0.32, 2.0], 'L-Mandelate': [1.5], 'glyoxylate': [2.2, 3.4], 'L-lactate': [16.5], 'O2': [0.44, 0.59, 0.64]}}, 'Rattus sp': {'unknown': {'2-mercaptoethanol-glyoxylate adduct': [0.75], 'Bromopyruvate': [4.4], 'DL-2-hydroxy-3-heptynoate': [0.38], 'DL-2-hydroxy-3-octynoate': [0.14], 'DL-methionine': [4.0], 'DL-vinylglycolate': [10.0], 'N-acetylcysteamine-glyoxylate adduct': [0.4], 'pantetheine-glyoxylate adduct': [0.7], 'coenzyme A-glyoxylate adduct': [2.2], 'DL-2-hydroxy-3-butynoate': [4.0], 'DL-2-hydroxy-3-hexynoate': [7.0], 'DL-2-hydroxy-3-pentynoate': [9.0], 'DL-2-hydroxyisocaproate': [0.6], 'DL-alpha-phenyllactate': [71.0], 'DL-lactate': [27.0], 'DL-phenyllactate': [0.1], 'L-alpha-hydroxyphenyllactate': [1.9], 'L-lysine': [90.0], 'L-methionine': [53.0], 'propane-1,3-dithiol-glyoxylate adduct': [0.03], 'DL-2-hydroxy-4-methylthiobutanoic acid': [0.7, 1.1], 'DL-2-hydroxycaproate': [0.15, 0.25, 1, 1.34, 3.2], 'DL-2-hydroxyisovalerate': [0.6, 8.0], 'DL-3-chlorolactate': [0.7, 0.8, 28.0], 'glycolate': [0.22, 0.24, 0.5, 2.1], 'L-2-Hydroxyisocaproate': [0.3, 0.32, 0.7, 0.9, 1.24, 1.26, 1.65], 'L-leucine': [5.3, 6.0, 6.4, 15.0], 'L-Mandelate': [0.16, 0.23, 0.4, 0.8], 'L-Phenyllactate': [0.09, 0.13], 'DL-2-hydroxybutyrate': [0.6, 0.6, 1.0, 1.2, 2.04, 3, 2.5, 12.7, 14.0], 'DL-2-hydroxyvalerate': [0.25, 0.35, 0.6, 13.0], 'glyoxylate': [1.41, 1.78], 'L-lactate': [1.8, 3.4, 4.68, 4.7, 6, 6.1, 8.5], 'L-tryptophan': [35.0, 40.0], 'O2': [0.3, 0.46]}}, 'Sus scrofa': {'unknown': {'dichlorophenolindophenol': [0.28], 'L-beta-Phenyllactate': [2.2], 'L-2-hydroxy-beta-methylvalerate': [2.4], 'glycolate': [0.31, 0.42], 'L-2-Hydroxyisocaproate': [0.68, 2.5], 'L-lactate': [16.0]}}, 'Dl-2-hydroxy-4-methylthiobutanoic acid': {'unknown': {'': [1]}}, 'Dl-2-hydroxycaproate': {'unknown': {'': [2]}}, 'Dl-2-hydroxyisovalerate': {'unknown': {'': [4]}}, 'Dl-3-chlorolactate': {'unknown': {'': [14]}}, 'Dl-alpha-hydroxy-n-valerate': {'unknown': {'': [8]}}, 'Dl-glycerate': {'unknown': {'': [29]}}, 'Glycolate': {'unknown': {'': [1]}}, 'Rattus norvegicus': {'unknown': {'L-2-hydroxy octanoate': [0.046], 'L-2-hydroxy palmitate': [1.36], '(S)-lactate': [0.0052]}}, 'Gallus gallus': {'unknown': {'L-2-hydroxy-4-methylthiobutanoic acid': [1.82], 'glycolate': [0.1]}}, 'L-2-hydroxyisocaproate': {'unknown': {'': [1]}}, 'Aerococcus viridans': {'unknown': {'L-alpha-hydroxy-isovalerate': [125.0], 'L-alpha-hydroxy-beta-methylvalerate': [140.0], 'DL-alpha-hydroxy-n-valerate': [5.5, 10.0], 'DL-glycerate': [5.0, 53.0], 'L-Mandelate': [0.3, 20.0], '(S)-lactate': [0.157, 0.175, 0.529, 0.863, 0.87, 0.94, 6.75, 7.5, 24.3, 25.5, 47.6, 50.7, 103.0], 'DL-alpha-hydroxy-n-butyrate': [18.0, 27.0], 'L-lactate': [0.34, 0.94], 'O2': [0.022, 0.029, 0.03, 0.16, 0.16]}}, 'L-leucine': {'unknown': {'': [10]}}, 'L-mandelate': {'unknown': {'': [10]}}, 'L-phenyllactate': {'unknown': {'': [0]}}, '(s)-lactate': {'unknown': {'': [52]}}, 'Dl-2-hydroxybutyrate': {'unknown': {'': [7]}}, 'Dl-2-hydroxyvalerate': {'unknown': {'': [7]}}, 'Dl-alpha-hydroxy-n-butyrate': {'unknown': {'': [22]}}, 'Spinacia oleracea': {'unknown': {'glycerate': [7.14]}}, 'Glyoxylate': {'unknown': {'': [2]}}, 'L-lactate': {'unknown': {'': [8]}}, 'L-tryptophan': {'unknown': {'': [38]}}, 'O2': {'unknown': {'': [0]}}, 'Amaranthus retroflexus': {'unknown': {'glycolate': [0.02, 0.058]}}, 'Zea mays': {'unknown': {'glycolate': [0.02, 0.056]}}, 'Glycine max': {'unknown': {'glycolate': [0.06]}}, 'Mesostigma viride': {'unknown': {'glycolate': [0.3], 'L-lactate': [9.3]}}, 'Geotrichum candidum': {'unknown': {'(S)-lactate': [3.6]}}}
```

A full list of the four-level tables:
```python3
>>> Km(soub_obj) # Parsing the KM VALUE [mM] table in BRENDA
>>> Kcat(soub_obj) # Parsing the TURNOVER NUMBER [1/s] table in BRENDA
>>> KcatDivKm(soub_obj) # Parsing the TURNOVER NUMBER [1/s] table in BRENDA
```


### Five-level tables
The five-level tables have the structure: value1, value2, reaction_diagram, organism, uniprot_id. The value is always text. The data is returned as a dictionary of organism names as keys, holding nested dictionaries as values. The structure is dictionary[organism][uniprot_id]["sub"/"prod"] where the last level stands for "substrate" or "product" and holds lists containing the text strings. By default only records with UniProt identifiers are returned (i.e. leaving out records without identifiers)

```python3
>>> parser.NaturalSubstrate(soup_obj).get_data() # Parsing the NATURAL SUBSTRATE table in BRENDA
{'Arabidopsis thaliana': {'Q24JJ8': [{'sub': ['2-hydroxycaprylate', 'O2'], 'prod': ['2-oxocaprylate', 'H2O2']}, {'sub': ['2-hydroxycaproate', 'O2'], 'prod': ['2-oxocaproate', 'H2O2']}, {'sub': ['2-hydroxypalmitate', 'O2'], 'prod': ['2-oxopalmitate', 'H2O2']}, {'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['L-lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}], 'Q9LJH5': [{'sub': ['2-hydroxycaprylate', 'O2'], 'prod': ['2-oxocaprylate', 'H2O2']}, {'sub': ['2-hydroxycaproate', 'O2'], 'prod': ['2-oxocaproate', 'H2O2']}, {'sub': ['2-hydroxypalmitate', 'O2'], 'prod': ['2-oxopalmitate', 'H2O2']}, {'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['L-lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}], 'Q9LRR9': [{'sub': ['2-hydroxycaprylate', 'O2'], 'prod': ['2-oxocaprylate', 'H2O2']}, {'sub': ['2-hydroxycaproate', 'O2'], 'prod': ['2-oxocaproate', 'H2O2']}, {'sub': ['2-hydroxypalmitate', 'O2'], 'prod': ['2-oxopalmitate', 'H2O2']}, {'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['L-lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}], 'Q56ZN0': [{'sub': ['glycolate', 'O2'], 'prod': ['glyoxylate', 'H2O2']}]}, 'Phaeodactylum tricornutum': {'B7FUG8': [{'sub': ['glycolate', 'acceptor'], 'prod': ['glyoxylate', 'reduced acceptor']}]}, 'Lactococcus lactis': {'Q9CG58': [{'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}, {'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}]}, 'Streptococcus iniae': {'A9QH69': [{'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}], 'A9QH71': [{'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}, {'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}]}, 'Homo sapiens': {'Q9NYQ3': [{'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}]}, 'Mus musculus': {'Q9NYQ2': [{'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}], 'Q9WU19': [{'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['glycolate', 'O2'], 'prod': ['glyoxylate', 'H2O2']}, {'sub': ['glycolate', 'O2'], 'prod': ['glyoxylate', 'H2O2']}]}, 'Rattus norvegicus': {'Q07523': [{'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}]}, 'Oryza sativa': {'Q10CE4': [{'sub': ['glycolate', 'O2'], 'prod': ['glyoxylate', 'H2O2']}]}}
```

If the uid_orgs_only variable in get_data() is set to False then all records are returned. For each organism, records without identifiers are collected under the "unknown" key.

```python3
>>> parser.NaturalSubstrate(soup_obj).get_data(uid_orgs_only=False) # Parsing the SUBSTRATE table in BRENDA
{'5 entries': {'unknown': [{'sub': ['(S)-lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}, {'sub': ['lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}, {'sub': ['DL-2-hydroxyisovalerate', 'O2'], 'prod': ['2-oxoisovalerate', 'H2O2']}]}, 'Arabidopsis thaliana': {'Q24JJ8': [{'sub': ['2-hydroxycaprylate', 'O2'], 'prod': ['2-oxocaprylate', 'H2O2']}, {'sub': ['2-hydroxycaproate', 'O2'], 'prod': ['2-oxocaproate', 'H2O2']}, {'sub': ['2-hydroxypalmitate', 'O2'], 'prod': ['2-oxopalmitate', 'H2O2']}, {'sub': ['an (S)-2-hydroxy carboxylate', 'O2'], 'prod': ['a 2-oxo carboxylate', 'H2O2']}, {'sub': ['L-lactate', 'O2'], 'prod': ['pyruvate', 'H2O2']}], ...
```

A full list of the five-level tables:
```python3
>>> Substrate(soub_obj) # Parsing the SUBSTRATE table in BRENDA
>>> NaturalSubstrate(soub_obj) # Parsing the NATURAL SUBSTRATE table in BRENDA
```
