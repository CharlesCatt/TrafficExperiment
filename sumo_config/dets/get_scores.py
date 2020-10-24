#!/usr/local/bin/python3

# read xml files, getting interval data to penalise the traffic intersections


import os
import sys
import optparse

from xml.dom import minidom


# parse an xml file by name
mydoc = minidom.parse('/Users/charlie/a1726075/2020/s2/AML/sumoStuff/corridor/dets/CC_e1Detector_CE_0_10.xml')

intervals = mydoc.getElementsByTagName('interval')

# one specific item attribute
print('Interval #1 attribute:')
print(intervals[0].attributes['speed'].value)

# notes before finishing this: I don't think the detecter plates
# pick up good enough stats for measuring congestion
