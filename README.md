# Metagenomics Profiling

Given a subset of ENA project identifiers related to metagenomics can we explore the sample attributes, profile different types and curate? All code is written in python 3. Note that you also require samples.csv. This is a large file that exceeds the 100MB limit on git. This file can be generated using the BioSamples API with `make_input.py` (see https://github.com/EBIBioSamples/curami for more details). Otherwise please get in touch and I can send you the latest dump (hewgreen@ebi.ac.uk).

## Getting Started

1. Have a look at the attribute counts in `metagenome_profile.csv`. This is for the whole subset of 38120 samples.
1. Look at the coocurence raw data in `samples_subset_coocurences.csv` or weighted `coexistencesProb.csv`
1. Download gephi and look at `session_file.gephi` or `coexistences.gexf`

## Data Processing (`ID_converter.py`)
`input.txt` contains a list of ENA project identifiers. `ID_converter.py` expands these project IDs into individual sample IDS using the ENA API and XML parsing. Then we convert these into BiopSamples IDs again from the ENA API with XML parsing. The script makes three files, `expanded_ENAIDs.json`, `missing_BioSampleIDs.json` and `fetched_BioSampleIDs.json`. The latter is required for the next script.

## Attribute Analysis

`profiler.py` requires `fetched_BioSampleIDs.json` and `samples.csv`. It returns the following:

`profile_dict.json` - counts of attributes in the samples
`metagenome_profile.csv` - counts of attributes in the samples
`samples_subset.csv` - each sample and the attributes associated with them (extracted from samples.csv)
`samples_subset_coocurences.json` - nested dictionary of coocurences counted
`samples_subset_coocurences.csv` - coocurences counted in a 4 column csv (index, attribute 1, attribute 2 and count respectively)
`coexistencesProb.csv` - weighted coocurences taking popularity into account when considering coocurrence. This is used as the edge weight in gephi.
`coexistences.gexf` - a file readable by gephi to explore the coocurences (a free graph layout too https://gephi.org). There is also a session file in the repo that has been colored and laid out.


## Future
- Dimension reduction of the samples and clustering to define different subsets
- Building slicing capability into curation app curami so these attributes can be refined
