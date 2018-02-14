'''
Use the ID_converter.py to get a list of biosampleIDs (as values in a json dict). 
Then this script will count the attributes in those samples from the master data 
file samples.csv.

'''

import json, sys, csv, itertools
from tqdm import tqdm
import pandas as pd
import networkx as nx

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def get_biosample_ids(json_id_map):

	with open(json_id_map, 'r') as f:
		data_=f.read()
		data_dict = dict(json.loads(data_))
		return list(data_dict.values())

def count_attributes(master_samples_data, total, total_attribute_counts):
	print('Counting attributes in samples...')
	profile_dict = {}

	with open(samples_subset, 'w') as fy:
		writer=csv.writer(fy, delimiter=',')
		with open(master_samples_data, 'r') as samples:
			reader = csv.reader(samples)
			for row in tqdm(reader, total=total):
				sampleID = row[0]
				if sampleID in BioSampleIDs:
					writer.writerow(row)
					attributes = row[1:]
					for attribute in attributes:
						if attribute not in profile_dict:
							profile_dict[attribute] = 1
						else:
							profile_dict[attribute] += 1						
		with open(total_attribute_counts, 'w') as fp:
				json.dump(profile_dict, fp)
		print('saved attribute counts')
		return profile_dict

def counts2df(total_attribute_counts, total_attribute_counts_csv):

	with open(total_attribute_counts, 'r') as f:
			data_=f.read()
			data_dict = dict(json.loads(data_))
			# print(data_dict)
			df = (pd.DataFrame
				.from_dict(data_dict, orient='index')
				.reset_index()
				.rename(columns = {'index':'attribute', 0:'frequency'})
				.sort_values(by=['frequency'], ascending = False)
				.reset_index()
				.drop(labels=['index'], axis=1))
			df.to_csv(total_attribute_counts_csv)
	return df

def cooccur_count(samples_subset):
	print('counting cooccurance of attributes')
	tcd = {}

	with open(samples_subset, 'r') as f:
		samples_type_list = csv.reader(f, delimiter=',')
		line_counter = 0
		total_lines = file_len(samples_subset)
		for type_list_ in tqdm(samples_type_list, unit='line', total=total_lines):
			type_list = type_list_[1:]
			types_permutations = itertools.combinations(type_list, 2)
			for perm in types_permutations:
				(A, B) = perm
				# first_letter = str(A[0]).lower()
				# if first_letter not in string.ascii_lowercase:
				#     first_letter = "#"
				if A not in tcd:
					tcd[A] = {}

				if B not in tcd[A]:
					tcd[A][B] = 0

				tcd[A][B] += 1
			line_counter += 1

	with open(samples_subset_coocurences, 'w') as fout:
		json.dump(tcd, fout)

def nestJSON2CSV(samples_subset_coocurences, samples_subset_coocurences_csv):
	d=[]
	with open(samples_subset_coocurences, 'r') as fin:
			matrix = json.load(fin)

			for attribute1 in matrix.keys():
				inner_dict = matrix.get(attribute1)
				for attribute2 in inner_dict:
					count = inner_dict.get(attribute2)

					sort_list = [attribute1, attribute2]
					attribute1_ = sorted(sort_list)[0]
					attribute2_ = sorted(sort_list)[1]



					d.append({'attribute1':attribute1_, 'attribute2':attribute2_, 'count':count})

	df = pd.DataFrame(d)
	df.to_csv(samples_subset_coocurences_csv)

def prob_calc(samples_subset_coocurences_csv, total_attribute_counts_csv, coexistencesProb, samples_subset):

	print('Calculating probability normalised weights...')

	# calculate expected probability and weights

	total_lines = file_len(samples_subset)

	# read in data
	coexist_df = pd.read_csv(samples_subset_coocurences_csv, index_col = 0, dtype={'attribute1': str, 'attribute2': str, 'count': int})
	attributes_df = pd.read_csv(total_attribute_counts_csv, index_col = 0, dtype={'attribute': str, 'frequency': int})

	#NB count is the observed frequency

	# probability calculations and mapping
	attributes_df['prob'] = attributes_df['frequency'] / total_lines
	merge1_df = pd.merge(left = coexist_df, right = attributes_df, left_on = 'attribute1', right_on = 'attribute')


	merge1_df.rename(columns={'prob':'Attribute1_prob'}, inplace=True)
	merge2_df = merge1_df[['attribute1', 'attribute2', 'count', 'Attribute1_prob']]
	merge3_df = pd.merge(left = merge2_df, right = attributes_df, left_on = 'attribute2', right_on = 'attribute')
	merge3_df.rename(columns={'prob':'Attribute2_prob'}, inplace=True)
	merge4_df = merge3_df[['attribute1', 'attribute2', 'count', 'Attribute1_prob', 'Attribute2_prob']]

	merge4_df['exp'] = ((merge4_df['Attribute1_prob'] * merge4_df['Attribute2_prob']) * total_lines) # looked into warning it throws can't see an issue

	merge4_df['diff'] = merge4_df['count'] - merge4_df['exp']
	merge4_df['weight'] = merge4_df['diff']/merge4_df['diff'].sum() # as per stats deffinition 'weights' must add up to 1

	# output
	merge5_df = merge4_df.sort_values(['diff'])
	print(merge5_df)
	coexistProb_df = merge5_df[['attribute1', 'attribute2', 'count', 'exp', 'diff', 'weight']]

	# during merge only rows with the corresponding columns are merged!
	no_missing = coexist_df.shape[0] - coexistProb_df.shape[0]
	if no_missing > 0:
		print('WARNING: '+str(no_missing)+' pairs missing due to input file discrepancy.')
	else:
		print('Full house. No pairs were thrown out.')
	coexistProb_df.to_csv(coexistencesProb, header = True, mode = 'w')

	return coexistProb_df

def build_netX(for_gephi, coexistProb_df):
	print('Building NetworkX...')
	G=nx.Graph()
	G = nx.from_pandas_dataframe(coexistProb_df,source='attribute1', target='attribute2', edge_attr='weight')

	# # for cytoscape save
	# nx.write_gml(G,'coexistences.gml')

	# for gephi save
	nx.write_gexf(G,for_gephi) # this file is used by coexistence.py


if __name__ == '__main__':

	# input file names
	json_id_map = 'fetched_BioSampleIDs.json' # created by ID_converter.py
	master_samples_data = 'samples.csv' # created by curami

	# output file names
	total_attribute_counts = 'profile_dict.json' # a dictionary of total attribute counts in the sample subset
	samples_subset = 'samples_subset.csv' # a slice of the master samples data sliced by the samples in the subset
	samples_subset_coocurences = 'samples_subset_coocurences.json' # json dump of cooccurance counts in subset
	samples_subset_coocurences_csv = 'samples_subset_coocurences.csv'
	total_attribute_counts_csv = 'metagenome_profile.csv'
	coexistencesProb = 'coexistencesProb.csv'
	for_gephi = 'coexistences.gexf'

	# input setup (get IDs and count total samples in DB)
	BioSampleIDs = get_biosample_ids(json_id_map)
	total = file_len(master_samples_data)
	counts2df(total_attribute_counts, total_attribute_counts_csv) # put counts in a csv file

	# churn through samples.csv (takes about 1h)
	# profile_dict = count_attributes(master_samples_data, total, total_attribute_counts)

	# coocurence analysis and sample profile
	profile_df = counts2df(total_attribute_counts, total_attribute_counts_csv)
	# cooccur_count(samples_subset)
	nestJSON2CSV(samples_subset_coocurences, samples_subset_coocurences_csv)
	coexistProb_df = prob_calc(samples_subset_coocurences_csv, total_attribute_counts_csv, coexistencesProb, samples_subset)
	build_netX(for_gephi, coexistProb_df)










	


	







































