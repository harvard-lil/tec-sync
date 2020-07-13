This repo syncs events calendar from The Events Calendar wordpress plugin to
Google Calendar.

## Credentials ##

The script requires a Google credentials file that authorizes a "service account" with domain-wide
delegation to manage the relevant calendar.

The service account can be created, and credentials file downloaded, in the
[Google Developer Console](https://console.developers.google.com/iam-admin/serviceaccounts).
The service account does not require any roles; you just need the credentials file and the
account's client ID for the next step.

The service account then needs domain-wide delegation enabled at https://admin.google.com/
under <hamburger menu> -> Security -> API Controls. Using the client ID from the last step,
grant the scope "https://www.googleapis.com/auth/calendar".

By default the credentials file should be saved as `google_auth.json` in this directory.

## Config ##

Set the environment variables listed in .env.sample, either in a file named .env or
in the environment.

## Useful docs ##

* [Google Calendar API reference](https://developers.google.com/calendar/v3/reference/events/list)

