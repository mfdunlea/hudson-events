import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_months_to_scrape():
    today = datetime.today()
    months = []
    for i in range(2):
        d = today.replace(day=1) + timedelta(days=32 * i)
        months.append(d.strftime("%Y-%B").lower())
    return months

def parse_date(day_str):
    # "Thursday, April 2" -> "2026-04-02"
    try:
        day_str = day_str.strip()
        # Remove day of week
        day_str = day_str.split(", ", 1)[1]  # "April 2"
        dt = datetime.strptime(day_str + " 2026", "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return ""

def parse_time(time_str):
    # "10:30—11:00 AM" -> "10:30 AM"
    try:
        time_str = time_str.strip()
        # Grab just the start time and the AM/PM
        match = re.match(r'(\d+:\d+)[—-][\d:]+\s*(AM|PM)', time_str)
        if match:
            return match.group(1) + " " + match.group(2)
        return time_str
    except:
        return ""

def scrape_month(year_month):
    url = f"https://townofhudson.assabetinteractive.com/calendar/{year_month}/"
    print(f"Fetching {url}")

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    for h2 in soup.find_all("h2"):
        link = h2.find("a")
        if not link:
            continue

        # Extract each field using its class
        day_tag      = link.find("span", class_="event-day")
        time_tag     = link.find("span", class_="event-time")
        location_tag = link.find("span", class_="event-location-location")

        if not day_tag:
            continue

        date_str     = parse_date(day_tag.get_text())
        time_str     = parse_time(time_tag.get_text()) if time_tag else ""
        location_str = location_tag.get_text(strip=True) if location_tag else ""
        event_url    = link.get("href", "")

        # Get title and description from the event's own page would be ideal
        # but for now derive title from the URL slug
        next_h3 = h2.find_next_sibling("h3")
        title = next_h3.get_text(strip=True) if next_h3 else slug.replace("-", " ").title()

        # Check for registration link nearby
        next_a = h2.find_next_sibling("a")
        registration = bool(next_a and "register" in next_a.get_text(strip=True).lower())

        # Get description from next paragraph
        next_p = h2.find_next_sibling("p")
        desc = next_p.get_text(strip=True) if next_p else ""

        events.append({
            "title":        title,
            "date":         date_str,
            "time":         time_str,
            "location":     location_str,
            "description":  desc,
            "registration": registration,
            "url":          event_url,
            "source":       "Hudson Public Library"
        })

    return events

def main():
    all_events = []

    for month in get_months_to_scrape():
        events = scrape_month(month)
        all_events.extend(events)
        print(f"  Found {len(events)} events")

    with open("events.json", "w") as f:
        json.dump(all_events, f, indent=2)

    print(f"\nDone. {len(all_events)} total events written to events.json")

main()