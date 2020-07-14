This repo syncs calendars from The Events Calendar wordpress plugin to
Google Calendar.

## How it works ##

The `tec-sync.py` script grabs events from The Events Calendar in ical format in one month batches, by 
visiting a series of urls like:
 
* `https://hls.harvard.edu/calendar/2020-02/?ical=1&tribe_display=month`
* `https://hls.harvard.edu/calendar/2020-03/?ical=1&tribe_display=month`
* etc.

It starts with the current month and by default grabs six months in all, based on the `CRAWL_MONTHS`
setting.

The script then grabs all events from the destination Google Calendar and syncs with the source events,
looking at only events:

* New events are added.
* Updated events are modified.
* Deleted events falling within the six month range are deleted.

It is up to the user to call `python tec-sync.py` as often as desired.

## Requirements ##

Python 3.

## Installation ##

* `git clone` this repository.
* Set configuration parameters (see Configuration section).
* Save Google credentials file to `google_auth.json` (see Credentials section).
* Install python requirements, e.g.:
  * `python3 -mvenv .venv && ./.venv/bin/pip install requirements`
* Run `./.venv/bin/python tec-sync.py` in a cron job, no more often than the
  `CACHE_MINUTES` setting. 

## Configuration ##

Environment variables can either be provided in a file, by copying `.env.sample` to `.env` and
editing `.env`, or simply as environment variables, as in `SOURCE_URL=foo python tec-sync.py`.

Two environment variables must be set:

* `SOURCE_URL`: the URL of a The Events Calendar calendar, such as 
[https://hls.harvard.edu/calendar/](https://hls.harvard.edu/calendar/)
* `CALENDAR_ID`: the ID of the destination Google Calendar copied from the
calendar's settings page, such as `98d7g87df6gdf87g58d7@group.calendar.google.com`

The other variables listed in .env.sample are optional, and used to change the default
behavior of the script:

* `GOOGLE_CREDENTIALS_FILE=google_auth.json`: path to Google credentials file.
* `CRAWL_DELAY_SECONDS=5`: time to sleep between requests to source Wordpress calendar.
* `CACHE_MINUTES=1440`: how long to cache responses locally before hitting Wordpress site again.
   Set to 0 to avoid creating a shelf.db. 
* `CRAWL_MONTHS=6`: how many months of the source calendar to crawl.
* `EXTENDED_PROPERTY=tecId`: key used to store The Event Calendar's event IDs in the 
   Google events' extendedProperty field.

## Credentials ##

The script requires a Google credentials file that authorizes access to the calendar.
By default the credentials file should be saved as `google_auth.json`.

To set up credentials:

* Log into https://console.developers.google.com/
* Add a new Service Account. The account does not need any roles (you might need to grant
  it a role and then revoke it under Roles).
* Save the provided credentials fil to `google_auth.json`.
* Copy the email address from `client_email` in the credentials file, and share edit access
  for the target Google Calendar with that email address. 

## For developers ##

* [Google Calendar API reference](https://developers.google.com/calendar/v3/reference/events/list)

