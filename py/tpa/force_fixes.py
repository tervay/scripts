from protos.tpa import Team


def fix_team(team: Team) -> Team:
    fns = [fix_team_city, fix_team_state_prov, fix_team_country]
    for f in fns:
        team = f(team)

    return team


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
    }

    # Use 0 as default
    if team.city in d:
        team.city = d[team.city].get(team.team_number, d[team.city].get(0, ""))

    return team


def fix_team_state_prov(team: Team) -> Team:
    d = {
        "LA": {0: "Louisiana"},
        "FL": {1390: "Florida"},
        "NY": {1713: "New York"},
        "PA": {0: "Pennsylvania"},
        "IL": {2112: "Illinois"},
        "OR": {2142: "Oregon"},
        "OK": {3144: "Oklahoma"},
        "CA": {4101: "California"},
        "TX": {4282: "Texas"},
        "MI": {4834: "Michigan"},
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
    }

    # Use 0 as default
    if team.state_prov in d:
        team.state_prov = d[team.state_prov].get(
            team.team_number, d[team.state_prov].get(0, "")
        )

    return team


def fix_team_country(team: Team) -> Team:
    d = {
        "Chinese Taipei": {0: "Taiwan"},
    }

    # Use 0 as default
    if team.country in d:
        team.country = d[team.country].get(team.team_number, d[team.country].get(0, ""))

    return team
