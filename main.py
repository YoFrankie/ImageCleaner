import glob
import os
import hashlib
import json
import argparse
import re
from geopy.geocoders import Nominatim
from get_lat_lon_exif_pil import *

def sha256ofFile(filepath):
	import hashlib
	with open(filepath, 'rb') as f:
		sha = hashlib.sha256()
		filecont = f.read()
		sha.update(filecont)
		shaval = sha.hexdigest()
		return shaval

def moveToSubfolders(path):
	p = re.compile('.*_(\d{8})_.*')
	filesForDate = {}
	for subdir, dirs, files in os.walk(path):
		for file in files:
			filepath = subdir + os.sep + file
			m = p.match(filepath)
			if not m is None:
				date = m.group(1)
				if not date in filesForDate:
					filesForDate[date] = []
				filesForDate[date].append(filepath)

	geolocator = Nominatim()
	for date, files in filesForDate.iteritems():
		if len(files) > 5:
			movedir = os.path.join(os.path.dirname(files[0]), date)
			location = None
			if not os.path.exists(movedir):
				os.makedirs(movedir)
			for f in files:
				exif_data = get_exif_data(f)
				if not exif_data is None:
					lat, lon = get_lat_lon(exif_data)
					if not lat is None and not lon is None:
						location = geolocator.reverse("{},{}".format(lat, lon))
			if not location is None:
				print(location.address)




def walkPath(path, deleteCache=True, cacheDir=''):
	cachefile = cacheDir + hashlib.sha256(path).hexdigest()

	if os.path.exists(cachefile):
		if deleteCache:
			os.remove(cachefile)
		else:
			with open(cachefile, 'r') as f:
				return json.load(f)

	shas = {}
	count = 0
	for subdir, dirs, files in os.walk(path):
		for file in files:
			count += 1
			if count % 100 == 0:
				print 'found {} files'.format(count)
			#print os.path.join(subdir, file)
			filepath = subdir + os.sep + file
			realpath = os.path.realpath(filepath)
			if 'SHA256' in realpath:
				hashstart = realpath.rfind('--')
				shaval = realpath[hashstart+2:]
				if '.' in shaval:
					shaval = shaval[:shaval.find('.')]
			else:
				shaval = sha256ofFile(filepath)

			assert len(shaval) == 64
			shas[shaval] = (file, filepath)

	with open(cachefile, 'w') as f:
		json.dump(shas, f)
	return shas

def compare(sourceDir='', destDir='', args=None):
	shasSource = walkPath(sourceDir, deleteCache=args.deleteSourceCache, cacheDir=args.cacheDir)
	shasDest = walkPath(destDir, deleteCache=args.deleteDestCache, cacheDir=args.cacheDir)

	sorteddict = {}
	for sha in shasSource:
		if sha in shasDest:
			sorteddict[shasSource[sha][0]] = 'found {} in {}'.format(shasSource[sha][0], shasDest[sha][1])
			if args.deleteIfFound:
				if not args.deleteAskFirst or raw_input('delete {} found in {}: '.format(shasSource[sha][1], shasDest[sha][1])) == 'y':
					os.remove(shasSource[sha][1])
		else:
			sorteddict[shasSource[sha][0]] = 'not found ' + shasSource[sha][0]

	for i, text in sorted(sorteddict.items()):
		print text

sourceDirIn = '/home/markus/Desktop/20160410_GalaxyS2'
# destDir = '/home/markus/Desktop/20150225_GalaxyS2'
destDirIn = '/home/markus/GitAnnex'

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--deleteIfFound', dest='deleteIfFound', default=True, help='Delete if file is found in dest')
parser.add_argument('--deleteAskFirst', dest='deleteAskFirst', default=False, help='Ask before deletion')
parser.add_argument('--deleteSourceCache', dest='deleteSourceCache', default=False, help='Delete source cache')
parser.add_argument('--deleteDestCache', dest='deleteDestCache', default=False, help='Delete dest cache')
parser.add_argument('--cacheDir', dest='cacheDir', default='/home/markus/.ImageCleaner/', help='Cache dir')
args = parser.parse_args()

# compare(sourceDir=sourceDirIn, destDir=destDirIn, args=args)
moveToSubfolders(sourceDirIn)



