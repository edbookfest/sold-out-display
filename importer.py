import sys
import traceback
import urllib
import urllib2

import dateutil.parser
import xml.etree.ElementTree as ET

from urllib2 import URLError


def get_soldout(url, today_only):

    def ord(n):
        return str(n) + ("th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

    def get_event_day(datestring):
        date = dateutil.parser.parse(datestring)
        return str('(' + ord(date.day) + ')')

    def get_all_events(xml_root):
        events = []
        for child in xml_root:
            if child.get('Hide') != '1':
                if child.get('Status') == "SoldOut":
                    events.append(str(child.get('EventName')))
        return events

    def process_events(xml):
        root = ET.fromstring(xml)
        events = get_all_events(root)
        processed_events = []
        for child in root:
            if child.get('Hide') != '1':
                if child.get('Status') == "SoldOut":
                    if events.count(str(child.get('EventName'))) > 1:
                        processed_events.append(str(child.get('EventName')) + ' ' + get_event_day(str(child.get('EventDateTime'))))
                    else:
                        processed_events.append(str(child.get('EventName')))
        processed_events.sort()
        return processed_events

    try:
        data = urllib.urlencode(
            {'TodayOnly': today_only, 'ChangesSince': 1428321600})
        resp = urllib2.urlopen(urllib2.Request(url + '?' + data))
        xml = resp.read()
        events = process_events(xml)
        return events
    except URLError as e:
        print >>sys.stderr, "Could not connect to feed at " + url
    except Exception, err:
        print >>sys.stderr, Exception
        traceback.print_exc()

    return None

