import json, sys, csv
from tqdm import tqdm

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


if __name__ == '__main__':

	total = file_len('samples.csv')

	profile_dict = {}

	with open('fetched_BioSampleIDs.json', 'r') as f:
		data_=f.read()
		data_dict = dict(json.loads(data_))
		BioSampleIDs = list(data_dict.values())

	with open('samples.csv', 'r') as samples:
		
		reader = csv.reader(samples)
		for row in tqdm(reader, total=total):
			sampleID = row[0]
			if sampleID in BioSampleIDs:
				attributes = row[1:]
				for attribute in attributes:
					if attribute not in profile_dict:
						profile_dict[attribute] = 1
					else:
						profile_dict[attribute] += 1


	with open('profile_dict.json', 'w') as fp:
			json.dump(profile_dict, fp)