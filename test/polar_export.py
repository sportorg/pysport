#!/bin/python
#
# Polar Flow HTML to GPX parser/convertor - Thomas Martin Schmid, 2014. Public domain*
#
# * If public domain is not legally valid in your legal jurisdiction
#   the MIT licence applies. See the LICENCE file.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
from datetime import datetime, time
import urllib

PART_INDEX_LAT = 0
PART_INDEX_LON = 1
PART_INDEX_TIME = 2
PART_INDEX_DIST  = 3
PART_INDEX_HEART_RATE = 4
PART_INDEX_SPEED = 5

if len(sys.argv) < 2:
	print("Usage: python polar_export.py [path_to_file]")
	sys.exit(1)

url_type = sys.argv[1].split(':')[0]
if url_type != 'http' and url_type != 'https' and url_type != 'ftp' and url_type != 'sftp':
	fin = open(sys.argv[1], "r")
	fout_url = sys.argv[1].replace('htm', 'gpx')
else:
	fin = urllib.urlopen(sys.argv[1])
	fout_url = "out.gpx"
fin_str = fin.read()
fin_data_begin = fin_str.find('"samples":[') + 12
fin_data_end = fin_str.find('}, publicExercise') - 2
fin_data_str = fin_str[fin_data_begin:fin_data_end]
data = []
for part in fin_data_str.split('],['):
	parts = part.split(',')
	lon_str = parts[PART_INDEX_LON][6:]
	lon_str_strip = lon_str[:len(lon_str)-1]
	data.append( [	float(parts[PART_INDEX_LAT][7:]),
			float(lon_str_strip),
			long(parts[PART_INDEX_TIME]) ] )

NAME = 'Runner' # <-- This is where you insert your name!
TIME = data[0][PART_INDEX_TIME]

def printTimeStamp(ds):
	ts = datetime.fromtimestamp(ds/1000)
	return '%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % ( ts.year, ts.month, ts.day,
													 ts.hour, ts.minute, ts.second, ds % 1000 )

bounds = [[ 180.0, 180.0],
	  [-180.0,-180.0]]
for sample in data:
	bounds[0][0] = min(bounds[0][0],sample[PART_INDEX_LAT])
	bounds[0][1] = min(bounds[0][1],sample[PART_INDEX_LON])
	bounds[1][0] = max(bounds[1][0],sample[PART_INDEX_LAT])
	bounds[1][1] = max(bounds[1][1],sample[PART_INDEX_LON])

out = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
	<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" creator="thynnmas' polar extractor" version="1.1" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
		<metadata>
			<author>
				<name>%s</name>
			</author>
			<time>%s</time>
			<bounds maxlon="%3.14f" maxlat="%3.14f" minlon="%3.14f" minlat="%3.14f"/>
		</metadata>
	<trk>
		<trkseg>''' % ( NAME,
				printTimeStamp(TIME),
				bounds[1][1],
				bounds[1][0],
				bounds[0][1],
				bounds[0][0] )

for sample in data:
	out += '''
			<trkpt lon="%3.14f" lat="%3.14f">
				<time>%s</time>
			</trkpt>''' % ( sample[PART_INDEX_LON],
					sample[PART_INDEX_LAT],
					printTimeStamp(sample[PART_INDEX_TIME]) )

out += '''
		</trkseg>
	</trk>
</gpx>'''

fout = open(fout_url, "w")
fout.write(out)
fout.close()

print ("Done")

