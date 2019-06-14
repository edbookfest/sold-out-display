#!/usr/bin/python2.7
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from log import log


class DateHelper:
    @staticmethod
    def day_ord(n):
        return str(n) + ("th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

    @staticmethod
    def showtime(date):
        hours = date.strftime("%-I")
        mins = date.strftime("%M")
        suffix = date.strftime("%p")
        output = str(hours)
        if mins != "00":
            output += ":" + str(mins)
        output += suffix.lower()
        return output


class Event(object):
    def __init__(self, data):
        self.id = int(data["id"])
        self.title = data["title"].encode("utf-8")
        self.start = datetime.strptime(data["start"], "%Y-%m-%d %H:%M:%S")
        self.is_sold_out = bool(data["soldout"])


class Collection(object):
    def __init__(self, title):
        self.title = title
        self.all_events = []
        self.sold_out_events = []
        self.dates = {}

    def add(self, event):
        self.all_events.append(event)
        self.dates.setdefault(event.start.day, []).append(event.start.strftime("%H:%M"))
        if event.is_sold_out:
            self.sold_out_events.append(event)

    def has_multiple_events(self):
        return bool(len(self.all_events) > 1)

    def has_sold_out_events(self):
        return bool(len(self.sold_out_events) >= 1)


class JsonParser:
    def __init__(self):
        self.sold_out_events = []

    def fancy_join(self, separator, last_separator, items):
        return last_separator.join([separator.join(items[:-1]), items[-1]] if len(items) > 2 else items)

    def datesorter(self, collection):
        d = defaultdict(list)
        for dt in map(lambda x: x.start, collection.sold_out_events):
            d[dt.day].append(DateHelper.showtime(dt))

        output = []
        for date, times in d.iteritems():
            line = DateHelper.day_ord(date)
            if len(collection.dates[date]) > 1:
                times.sort()
                formatted_times = ', '.join(times)
                line += " " + formatted_times
            output.append(line)
        output.sort()

        return self.fancy_join(', ', ' & ', output)

    def __display_for_multiple_days(self, titles):
        # log(str(len(events)) + " sold out events")

        sold_out_list = []
        for title, collection in titles.iteritems():
            if collection.has_sold_out_events():
                line = title
                if collection.has_multiple_events():
                    line += " (" + self.datesorter(collection) + ")"
                sold_out_list.append(line)
        sold_out_list.sort()

        return sold_out_list

    def __display_for_single_day(self, all_events, date, hide_past=False, cutoff=0):
        events = filter(lambda event: event.start.date() == date, all_events)
        log(str(len(events)) + " events sold out on " + date.strftime("%Y-%m-%d"))

        if hide_past:
            events = self.__filter_events_after_start(events, cutoff)

        sold_out_list = []
        for event in events:
            sold_out_list.append(event.start.strftime("%H:%M") + '  ' + event.title)
        sold_out_list.sort()

        return sold_out_list

    def __filter_events_after_start(self, events, cutoff):
        filtered = []

        for event in events:
            cutoff_after_event = event.start + timedelta(minutes=cutoff)
            if cutoff_after_event.time() >= datetime.now().time():
                filtered.append(event)

        log(str(len(filtered)) + " events sold out after event start cutoff")

        return filtered

    def parse(self, filename, today_only):
        # type: (str, bool) -> list

        with open(filename, 'r') as f:
            data = json.load(f)
            f.close()

        all_events = []
        for item in data:
            try:
                event = Event(item)
                all_events.append(event)
            except ValueError as e:
                log('%s - %s (%s): %s' % ("Failed to parse event", item["title"], item["id"], e.message))

        log(str(len(data)) + " events in feed")
        log(str(len(all_events)) + " events parsed successfully")

        if today_only:
            sold_out_events = filter(lambda event: event.is_sold_out, all_events)
            today = date.today()
            return self.__display_for_single_day(sold_out_events, today)
        else:
            titles = {}
            for event in all_events:
                titles.setdefault(event.title, Collection(event.title)).add(event)
            log(str(len(titles)) + " unique titles found")
            return self.__display_for_multiple_days(titles)
