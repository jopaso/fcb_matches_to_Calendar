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
    

def get_date(match):

    date = match.find('div', {"class" : "fixture-info__time"})
    try:
        timestamp = int(date['data-kickoff']) / 1000 #Originally is in miliseconds
        return datetime.fromtimestamp(timestamp)

    except: # This means that the match exact date isn't confirmed yet -> ignore
        return None

def get_matches(html_text):
    matches_list = html_text.find_all('div', {"class" : "fixture-result-list__fixture"})
    all_matches = []
    contador = 0
    for match in matches_list:
        
        #print(f'{match}\n\n\n')
        home_team = match.find('div', {"class" : "fixture-info__name fixture-info__name--home"}).string.strip()
        away_team = match.find('div', {"class" : "fixture-info__name fixture-info__name--away"}).string.strip()
        competition = match.find('div', {"class" : "fixture-result-list__fixture-competition"}).string
       

        date = get_date(match)

        if date is None or competition is None:
            #print(f"Fecha no confirmada para {home_team} vs {away_team} - {competition}")
            continue
        else:
            #print(f"Añadiendo {home_team} vs {away_team} - {competition}")
            match_dictionari = {
            'home_team' : home_team,
            'away_team' : away_team,
            'competition' : competition.strip(),
            'date' : date,
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
        print(f'\nCreating event for:\n {match}')
        if not is_in_calendar(calendar_events, match):
            add_to_calendar(calendar, service, match)

    print("\nALL KNOWN BARÇA MATCHES ADDED TO YOUR CALENDAR\n")
            
    

if __name__ == '__main__':
    main()