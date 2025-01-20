# fcb_matches_to_Calendar
This project retrieves data about upcoming matches from FC Barcelona official website (https://www.fcbarcelona.es/es/futbol/primer-equipo/calendario) and adds them to your google calendar.

You might need to install the following python packages:

```bash
pip install beautifulsoup4
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

You will also need to follow the steps 1-4 from this webpage to create your google calendar API:

https://medium.com/@ayushbhatnagarmit/supercharge-your-scheduling-automating-google-calendar-with-python-87f752010375


Once executed the script, it will create a new calendar named 'Football' if not found one and create there an event for every football game  with confirmed date.
