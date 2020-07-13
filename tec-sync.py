import shelve
from copy import deepcopy
from datetime import date, datetime
from time import time, sleep

from dateutil.parser import isoparse
from tqdm import tqdm
from googleapiclient.discovery import build
from ics import Calendar
import requests
from dateutil.relativedelta import relativedelta
from google.oauth2 import service_account
import environ


# read config
env = environ.Env()
environ.Env.read_env()  # read from .env file if any
SOURCE_URL = env('SOURCE_URL')
CALENDAR_OWNER = env('CALENDAR_OWNER')
CALENDAR_ID = env('CALENDAR_ID')
GOOGLE_CREDENTIALS_FILE = env('GOOGLE_CREDENTIALS_FILE', default='google_auth.json')
CRAWL_DELAY_SECONDS = env.int('CRAWL_DELAY_SECONDS', default=5)
CACHE_MINUTES = env.int('CACHE_MINUTES', default=24*60)
CRAWL_MONTHS = env.int('CRAWL_MONTHS', default=6)


def get_gcal_service():
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar'],
        subject=CALENDAR_OWNER)
    return build('calendar', 'v3', credentials=credentials)


def get_gcal_events(service):
    page_token = None
    while True:
        events = service.events().list(calendarId=CALENDAR_ID, pageToken=page_token, maxResults=2500).execute()
        yield from events.get('items', [])
        page_token = events.get('nextPageToken')
        if not page_token:
            break


def fetch_cached_get(url):
    with shelve.open('shelf') as db:
        if url not in db or db[url]['timestamp'] < time() - 60*CACHE_MINUTES:
            print("Fetching %s from web" % url)
            response = requests.get(url)
            response.raise_for_status()
            sleep(CRAWL_DELAY_SECONDS)
            db[url] = {
                'timestamp': time(),
                'text': response.text,
            }
        else:
            print("Returning cached %s" % url)
        return db[url]['text']


print("Fetching gcal events ...")
service = get_gcal_service()
gcal_events = []
gcal_events_by_hls_id = {}
for e in get_gcal_events(service):
    gcal_events.append(e)
    hlsId = e.get('extendedProperties', {}).get('private', {}).get('hlsId')
    if hlsId:
        gcal_events_by_hls_id[hlsId] = e

gcal_events_found = set()
events_added = 0
events_updated = 0
events_deleted = 0
events_same = 0
first_month = None
last_month = None
source_tz = None
for month_offset in range(CRAWL_MONTHS):
    month = datetime.utcnow().date() + relativedelta(months=month_offset)
    if not first_month:
        first_month = [month.year, month.month]
    last_month = [month.year, month.month]
    month = month.strftime('%Y-%m')
    print("Syncing %s" % month)
    url = "%s%s/?ical=1&tribe_display=month" % (SOURCE_URL, month)
    calendar = Calendar(fetch_cached_get(url))
    for event in tqdm(calendar.events):
        if source_tz is None:
            source_tz = event.begin.tzinfo
        if event.uid in gcal_events_by_hls_id:
            gcal_events_found.add(gcal_events_by_hls_id[event.uid]['id'])
            old_event = gcal_events_by_hls_id[event.uid]
            new_event = deepcopy(old_event)
            new_event['summary'] = event.name
            if event.location:
                new_event['location'] = event.location
            new_event['description'] = event.description
            new_event['start'] = {'dateTime': event.begin.isoformat()}
            new_event['end'] = {'dateTime': event.end.isoformat()}
            new_event['source']['url'] = event.url
            if old_event != new_event:
                response = service.events().update(calendarId=CALENDAR_ID, eventId=new_event['id'], body=new_event).execute()
                events_updated += 1
            else:
                events_same += 1
        else:
            data = {
                'summary': event.name,
                'location': event.location,
                'description': event.description,
                'start': {'dateTime': event.begin.isoformat()},
                'end': {'dateTime': event.end.isoformat()},
                'source': {
                    'title': 'HLS Events Page',
                    'url': event.url,
                },
                "extendedProperties": {
                    "private": {
                        "hlsId": event.uid,
                    }
                }
            }
            response = service.events().insert(calendarId=CALENDAR_ID, body=data).execute()
            events_added += 1

if source_tz:
    start_of_range = datetime(year=first_month[0], month=first_month[1], day=1, tzinfo=source_tz)
    end_of_range = datetime(year=last_month[0], month=last_month[1], day=1, tzinfo=source_tz) + relativedelta(months=1)
    print("Deleting unmatched events between %s and %s ..." % (start_of_range, end_of_range))
    for event in tqdm(gcal_events):
        if event['id'] not in gcal_events_found:
            event_date = isoparse(event['start']['dateTime'])
            if event_date > start_of_range and event_date < end_of_range:
                service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
                events_deleted += 1

print("Summary: %s events added, %s events updated, %s events deleted, %s events preserved" % (events_added, events_updated, events_deleted, events_same))