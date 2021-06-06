from geopy.geocoders import Nominatim

from protos.tpa import Event, Team
from py.util import SHORT_TO_STATE


def fix_team(team: Team) -> Team:
    for f in [fix_team_city, fix_team_state_prov, fix_team_country, fix_team_geo]:
        team = f(team)

    return team


def fix_event(event: Event) -> Event:
    for f in [fix_event_city, fix_event_state_prov, fix_event_country, fix_event_geo]:
        event = f(event)

    return event


def fix_team_city(team: Team) -> Team:
    d = {
        "Falmouth/Gorham": {172: "Falmouth"},
        "Famindale": {361: "Farmingdale"},
        "Harrisonburburg": {1154: "Harrisonburg"},
        "currently meeting in Bedford": {1519: "Bedford"},
        "rishon le tzion": {6741: "Rishon LeZion"},
        "Kibutz E'in Shemer": {1657: "Ein Shemer"},
        "Gadera": {1942: "Gedera"},
        "Port Hueneme CBC Base": {0: "Oxnard"},
        "pttsburgh": {3108: "Pittsburgh"},
        "Okland": {4047: "Oakland"},
        "San Antoino": {4670: "San Antonio"},
        "Southbury / Middlebury": {2064: "Middlebury"},
        "Rosh Hayin": {1943: "Rosh HaAyin"},
        "APO": {3011: "Wiesbaden"},
        "bet-hasmonai": {4661: "Azarya"},
        "Petah Tiqua": {5928: "Petah Tikva"},
        "Kfar hanoar Neurim ": {7039: "Ne'urim"},
        "Cuautilán Izcalli": {4371: "Cuautitlán Izcalli"},
        "Santa Catarina / Tuxtla Gutierrez, Chiapas": {6017: "Santa Catarina"},
        "Wuri Dist.": {7130: "Wuri District"},
        "taybe": {7177: "Tayibe"},
        "Santiago": {2576: ""},
        "St. Cloud & Harmony": {1390: "St. Cloud"},
        "Detroi": {4834: "Detroit"},
        "Pghp": {1707: "Pittsburgh"},
        "Cape Vincent / Clayton": {1713: "Cape Vincent"},
        "Kefar Blum": {3034: "Kfar Blum"},
        "Dabburiya": {5715: "Daburiyya"},
        "Jaffa of Nazareth": {7554: "Yafa an-Naseriyye"},
        "arara negev": {6149: "Ar'arat an-Naqab"},
        "Jadeh Mahbas": {7329: ""},
        "Tamra GLIL": {1946: "Tamra"},
    }

    # Use 0 as default
    if team.city in d:
        team.city = d[team.city].get(team.team_number, d[team.city].get(0, team.city))

    return team


def fix_team_state_prov(team: Team) -> Team:
    d = {
        "TA": {0: "Tel Aviv District"},
        "Tel-Aviv": {6741: ""},
        "HaMerkaz": {0: "Center District"},
        "HaMerkaz (Central)": {1952: "Center District"},
        "HaDarom": {0: ""},
        "HaDarom (Southern)": {2216: ""},
        "HaZafon": {0: ""},
        "HaZafon (Northern)": {0: ""},
        "Kaohsiung Special Municipality": {0: ""},
        "Changhua": {0: ""},
        "Taipei Special Municipality": {0: ""},
        "Tainan Municipality": {0: ""},
        "Taichung Municipality": {0: ""},
        "Dolnoslaskie": {7570: ""},
        "Región Metropolitana de Santiago": {0: ""},
    }

    # Use 0 as default
    if team.state_prov in d:
        team.state_prov = d[team.state_prov].get(
            team.team_number, d[team.state_prov].get(0, team.state_prov)
        )

    if team.state_prov in SHORT_TO_STATE and team.country == "USA":
        team.state_prov = SHORT_TO_STATE[team.state_prov]

    return team


def fix_team_country(team: Team) -> Team:
    d = {
        "Chinese Taipei": {0: "Taiwan"},
    }

    # Use 0 as default
    if team.country in d:
        team.country = d[team.country].get(
            team.team_number, d[team.country].get(0, team.country)
        )

    return team


def fix_team_geo(team: Team) -> Team:
    nom = Nominatim(user_agent="frcscripts")
    try:
        loc = nom.geocode(f"{team.city}, {team.state_prov}, {team.country}")
    except:
        print(f"Could not locate {team}")
        return team

    if loc is None:
        print(f"Could not locate {team}")
        return team

    team.lat = loc.latitude
    team.lng = loc.longitude
    return team


def fix_event_city(event: Event) -> Event:
    d = {
        "": {
            "2006ca": "Los Angeles",
            "2007az": "Phoenix",
            "2007br": "Porto Alegre",
            "2007ca": "Los Angeles",
            "2007co": "Denver",
            "2007ct": "Hartford",
            "2007fl": "Orlando",
            "2013mm": "Montgomery Township",
            "2013mshsl": "Minneapolis",
            "2013rsr": "New Orleans",
            "2014bfbg": "Lexington",
        },
        "Seatwen": {0: ""},
        "Troy": {0: "City of Troy"},
    }

    # Use 0 as default
    if event.city in d:
        event.city = d[event.city].get(event.key, d[event.city].get(0, event.city))

    return event


def fix_event_state_prov(event: Event) -> Event:
    d = {
        "": {
            "2006ca": "California",
            "2007az": "Arizona",
            "2007br": "",
            "2007ca": "California",
            "2007co": "Colorado",
            "2007ct": "Connecticut",
            "2007fl": "Florida",
            "2013mm": "New Jersey",
            "2013mshsl": "Minnesota",
            "2013rsr": "Louisiana",
            "2014bfbg": "Kentucky",
        },
        "HaMerkaz": {0: "Center District"},
        "KY": {"2008ios": ""},
        "TXQ": {0: "Taichung City"},
    }

    # Use 0 as default
    if event.state_prov in d:
        event.state_prov = d[event.state_prov].get(
            event.key, d[event.state_prov].get(0, event.state_prov)
        )

    if event.state_prov in SHORT_TO_STATE and event.country == "USA":
        event.state_prov = SHORT_TO_STATE[event.state_prov]

    return event


def fix_event_country(event: Event) -> Event:
    d = {
        "": {"2007br": "Brazil", 0: "USA"},
        "Chinese Taipei": {0: "Taiwan"},
        "Austrialia": {"2017aurb": "Australia"},
        "Northern Israel": {"2008ios": "Israel"},
    }

    # Use 0 as default
    if event.country in d:
        event.country = d[event.country].get(
            event.key, d[event.country].get(0, event.country)
        )

    return event


def fix_event_geo(event: Event) -> Event:
    nom = Nominatim(user_agent="frcscripts")
    try:
        loc = nom.geocode(f"{event.city}, {event.state_prov}, {event.country}")
    except:
        print(f"Could not locate {event}")
        return event

    if loc is None:
        print(f"Could not locate {event}")
        event.lat = 0.0
        event.lng = 0.0
        return event

    event.lat = loc.latitude
    event.lng = loc.longitude
    return event
