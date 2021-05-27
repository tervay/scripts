from tqdm import tqdm as tqdm_sync
from tqdm.asyncio import tqdm

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

    for event in tqdm_sync(events):
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
async def async_dlf_wffa():
    dlf, wffa = {}, {}
    async with tpa_cm() as tpa:
        async for event in tqdm(
            await helpers.flatten_lists_async(
                [tpa.get_events_by_year(year=y) for y in range(2008, 2022)]
            )
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                m = {4: dlf, 3: wffa}
                if award.award_type in m:
                    for recipient in award.recipient_list:
                        m[award.award_type][recipient.awardee] = (
                            event.key,
                            recipient.team_key,
                        )

    pprint(set(dlf.keys()) & set(wffa.keys()))


@expose
async def test(n):
    async with tpa_cm() as tpa:
        async for t in tpa.get_teams(page_num=n):
            print(t)
