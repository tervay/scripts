from tqdm import tqdm

from py.cli import expose, pprint
from py.tba import helpers, tba
from py.tpa import tpa_cm


@expose
def about(num):
    pprint(tba.team(num, simple=True))


@expose
def dlf_wffa():
    events = helpers.flatten_lists([tba.events(year=y) for y in range(2008, 2022)])
    events = helpers.filter_completed_events(events)

    dlf = {}
    wffa = {}

    for event in tqdm(events):
        awards = tba.event_awards(event=event["key"])
        for award in awards:
            if award["award_type"] == 4:
                for recipient in award["recipient_list"]:
                    dlf[recipient["awardee"]] = (event["key"], recipient["team_key"])

            if award["award_type"] == 3:
                for recipient in award["recipient_list"]:
                    wffa[recipient["awardee"]] = (event["key"], recipient["team_key"])

    pprint(set(dlf.keys()) & set(wffa.keys()))


@expose
async def test(n):
    async with tpa_cm() as tpa:
        res = await tpa.get_team(team_key=f"frc{n}")
        print(res)
