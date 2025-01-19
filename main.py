from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def start_calendar_service():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_calendar(service):
    # Search if the calendar already exists
    print("Searching for \'Football\' calendar...")

    football_calendar = None
    calendar_list = service.calendarList().list().execute().get('items', [])
    for calendar in calendar_list:
        if calendar['summary'] == 'Football':
            football_calendar = calendar
            print(f"\nFound! Using this calendar")
        
    if football_calendar:
        return football_calendar
    else:
        # Create a new calendar
        print('\nNot found! Creating new calendar...')
        
        new_calendar = {
            'summary': 'Football',
            'timeZone': 'Europe/Madrid'
        }
        created_calendar = service.calendars().insert(body=new_calendar).execute()

        print(f"Created calendar: {created_calendar['id']}")
        return created_calendar


def add_to_calendar(calendar, service, match):
    
    print(f'\nCreating event for:\n {match}')
    event = {
        'summary': f'{match["home_team"]} vs {match["away_team"]} - {match["competition"]}',
        'start': {
            'dateTime': (match['date']).isoformat(),
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': (match['date'] + timedelta(hours=2)).isoformat(),
            'timeZone': 'Europe/Madrid',
        },
    }
    service.events().insert(calendarId=calendar['id'], body=event).execute()
    

def get_dates(html_text):

    dates = html_text.find_all('div', {"class" : "fixture-info__time"})
    known_dates = []
    for date in dates:
        try:
            timestamp = int(date['data-kickoff']) / 1000 #Originally is in miliseconds
            if datetime.fromtimestamp(timestamp) not in known_dates:
                known_dates.append(datetime.fromtimestamp(timestamp))

        except: # This means that the match exact date isn't confirmed yet -> ignore
            pass
    
    return known_dates

def get_matches(html_text):
    home_teams = list(map(lambda x: x.string.strip(), html_text.find_all('div', {"class" : "fixture-info__name fixture-info__name--home"})))
    away_teams = list(map(lambda x: x.string.strip(), html_text.find_all('div', {"class" : "fixture-info__name fixture-info__name--away"})))
    competitions = list(map(lambda x: x.string.strip(),  html_text.find_all('span', {"class" : "fixture-result-list__name visually-hidden"})))
    dates = get_dates(html_text) 

    #dates length will be shorter as not all matches have a confirmed date
    matches = zip(home_teams[:len(dates)], away_teams[:len(dates)], competitions[:len(dates)], dates) 
    all_matches = []
    for match in matches: # Structure the information for more readable access
        match_dictionari = {
            'home_team' : match[0],
            'away_team' : match[1],
            'competition' : match[2],
            'date' : match[3],
        }
        all_matches.append(match_dictionari)
    
    return all_matches

def list_calendar_events(calendar, service):
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    events_result = service.events().list(calendarId=calendar['id'], timeMin=now,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    return events

def is_in_calendar(calendar_events, match):
    for event in calendar_events:
        if event['summary'] == f'{match["home_team"]} vs {match["away_team"]} - {match["competition"]}':
            return True
        
    return False

def main():
    request = requests.get("https://www.fcbarcelona.es/es/futbol/primer-equipo/calendario")
    html_text = BeautifulSoup(request.text, 'lxml')

    all_matches = get_matches(html_text)

    service = start_calendar_service()
    calendar = get_calendar(service)
    calendar_events = list_calendar_events(calendar, service)
    
    for match in all_matches:
        if not is_in_calendar(calendar_events, match):
            add_to_calendar(calendar, service, match)

    print("\nALL KNOWN BARÇA MATCHES ADDED TO YOUR CALENDAR\n")
            
    

if __name__ == '__main__':
    main()