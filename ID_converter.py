'''
This script exmpands ENA study IDS to extract the related sample IDS then attempts to convert these into BioSamples IDs

Input file is a list of ENA study/sample IDs

Output is a dictionary of the mapped IDs and a list of IDs that failed to find a BioSamples ID.

'''

import requests, sys, csv, re, json, time, logging
from lxml import html
from tqdm import tqdm
import xml.etree.ElementTree as ET
from xml.dom import minidom
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def ENAtoBioSID(ENA_ids):

	BioSampleIDs = {}
	missing_BioSampleIDs = []

	# for an_id in tqdm(ENA_ids, unit='IDs'):
	for an_id in ENA_ids:
		# print(type(an_id))

		# for ENA_accession_ in tqdm(reader, total=no_studies, unit='IDs'):
		# 	ENA_accession = ENA_accession_[0]
		sample_url = 'https://www.ebi.ac.uk/ena/data/view/' + an_id + '&display=xml'

		
		try:
			s = requests.get(sample_url)
		except:
			time.sleep(65)
			try:
				s = requests.get(sample_url, verify=False)
			except:
				logger.warn('Connection timeout for ENA ID to BioSampleID ' + str(an_id), exc_info=True)
				continue

		soup2 = BeautifulSoup(s.content, "lxml")

		'''
		test module
		catch experiments and runs (they dont have a BioSamples ID)
		these should not be passed on from beautiful soup.

		'''
		# if soup2.experiment:
		# 	print('experiment slipped through!')
		# 	sys.exit()
		# 	if soup2.experiment and soup2.sample:
		# 		print('missing samples!!')
		# 		sys.exit()
		# 	else:
		# 		continue
		# elif soup2.run:
		# 	print('run slipped through!')
		# 	sys.exit()
		# 	if soup2.run and soup2.sample:
		# 		print('missing samples!!')
		# 		sys.exit()
		# 	else:
		# 		continue


		if soup2.sample:
			try:
				BioSampleID = soup2.find('external_id', { 'namespace' : 'BioSample' }).text.strip()
				BioSampleIDs[an_id] = BioSampleID
			except AttributeError:
				missing_BioSampleIDs.append(an_id)
				logger.warn('Missing sample ID in a sample XML type' + str(sample_url))
				print('Missing sample ID in a sample ' + sample_url)
		else:
			# print(sample_url)
			# print('This is not a sample, run or experiment')
			logger.warn('Missing information in a non sample XML type' + str(sample_url))
			# logger.warn(str(soup2.root))
			missing_BioSampleIDs.append(an_id)


	return (BioSampleIDs, missing_BioSampleIDs)

def expand_IDs(input_study_file, no_studies):

	with open(input_study_file) as f:
		
		ENA_ids = set([])

		reader = csv.reader(f)
		for ENA_accession_ in tqdm(reader, total=no_studies, unit='IDs'):
			ENA_accession = ENA_accession_[0]

			try:
				url = 'http://www.ebi.ac.uk/ena/data/view/' + ENA_accession + '&display=xml'
				r = requests.get(url)
			except ConnectionError:
				time.sleep(65)
				try:
					r = requests.get(url, verify=False)
				except ConnectionError:
					logger.warn('Connection timeout for ' + str(url), exc_info=True)
					continue
			soup = BeautifulSoup(r.content, "lxml")

			if soup.study:

				sample_ids = []

				# only find is that belong to a sample (not experiments or )
				for link in soup.find_all("xref_link"):
					if link.find('db').contents[0] == 'ENA-SAMPLE':
						sample_id = link.find('id').contents[0]

					if sample_id:
						sample_ids.append(sample_id)

				for sample_id_ in tqdm(sample_ids):

					# separate by comma if neccesary and convert sample_id_to a list
					if ',' in sample_id_:
						sample_id_list = sample_id_.split(",")
					else:
						sample_id_list = [sample_id_]

					# unpacking the dashed ranges that ENA returns if neccesary
					for individualOrRange in sample_id_list:
						if '-' in individualOrRange:
							id_split = re.split(r'-', individualOrRange)
							id1 = int(re.match('.*?([0-9]+)$', id_split[0]).group(1))
							id2 = int(re.match('.*?([0-9]+)$', id_split[1]).group(1))
							prefix1 = re.match('^([a-zA-Z]+)', id_split[0]).group(1)
							prefix2 = re.match('^([a-zA-Z]+)', id_split[1]).group(1)
							if prefix1 != prefix2:
								logger.warn("ENA prefix doesn't match")
								raise ValueError("ENA prefix doesn't match")
								sys.exit()
							else:
								# list_ENA_ids.append(id_split[0])
								ENA_ids.update(set([id_split[0]]))
								count = 0
								while id1 != id2:
									# print('id1: ' + str(id1))
									# print('id2: ' + str(id2))
									id1 += 1
									count += 1
									unpacked_id = prefix1 + str(id1)

									# list_ENA_ids.append(unpacked_id)
									ENA_ids.update(set([unpacked_id]))
									if id1 > id2:
										# print('id1: ' + str(id1))
										# print('id2: ' + str(id2))
										logger.warn('MISSED THIS ENA ID (id1>id2): ' + str(individualOrRange))
										continue

									# elif count % 1000000 == 0:
										# print('Number of ids: ' + str(len(ENA_ids)))
										# print('id1: ' + str(id1))
										# print('id2: ' + str(id2))

						else:
							ENA_ids.update(set([individualOrRange]))
							# list_ENA_ids.append(sample_id_)
			else:
				print(url)
				print('This is not a study but should be?')
				sys.exit()

		return list(ENA_ids)
		# return list_ENA_ids

if __name__ == '__main__':

	# initialise
	logging.basicConfig(filename='test.log', level=logging.INFO)
	logger = logging.getLogger(__name__)
	input_study_file = 'input.txt'
	no_studies = file_len(input_study_file)


	# expand studies
	print('fetching samples associated with the studies')
	ENA_ids = expand_IDs(input_study_file, no_studies)
	with open('expanded_ENAIDs.json', 'w') as fs:
		json.dump(ENA_ids, fs)
	print(str(len(ENA_ids)) + ' samples extracted from ' + str(no_studies) + ' studies')

	# map to BioSamples IDs
	print('Converting ENA IDs to BioSample IDs')

	# untested multithreading

	# pool = ThreadPool(4) 
	# results = pool.map(ENAtoBioSID, ENA_ids)
	# pool.close() 
	# pool.join() 

	results = ENAtoBioSID(ENA_ids)
	BioSampleIDs = results[0]
	missing_BioSampleIDs = results[1]


	# output
	with open('fetched_BioSampleIDs.json', 'w') as fp:
		json.dump(BioSampleIDs, fp)
	with open('missing_BioSampleIDs.json', 'w') as fd:
		json.dump(missing_BioSampleIDs, fd)



				


















