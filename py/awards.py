from collections import defaultdict

from tqdm.asyncio import trange

from py.cli import expose, pprint
from py.tba import AwardType, EventType
from py.tpa import tpa_cm


@expose
async def most_states():
    states = defaultdict(set)
    async with tpa_cm() as tpa:
        async for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                async for award in tpa.get_event_awards(event_key=event.key):
                    for recipient in award.recipient_list:
                        if len(event.state_prov) > 0:
                            states[recipient.team_key].add(event.state_prov)

    counts = {t: len(s) for t, s in states.items()}
    pprint(sorted(counts.items(), key=lambda t: -(t[1]))[:25])


@expose
async def wffa_families():
    winners = defaultdict(list)

    async with tpa_cm() as tpa:
        async for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                if event.event_type in EventType.CMP_EVENT_TYPES:
                    continue

                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type == 3:
                        for recipient in award.recipient_list:
                            last_name = recipient.awardee.split(" ")[-1]
                            winners[(last_name)].append(
                                (event.key, recipient.awardee, recipient.team_key)
                            )

    for (last_name), event_awardee_list in winners.items():
        if len(event_awardee_list) > 1:
            print(f"* {last_name} family?: ", end="")
            s = [f"{a} ({t}) ({e})" for e, a, t in event_awardee_list]
            print(", ".join(s))


@expose
async def wffa_info():
    async with tpa_cm() as tpa:
        async for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                award_type = (
                    "WFA" if event.event_type in EventType.CMP_EVENT_TYPES else "WFFA"
                )
                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type == AwardType.WOODIE_FLOWERS:
                        for recipient in award.recipient_list:
                            tcity, tstate, tcountry = "", "", ""
                            if len(recipient.team_key) > 0:
                                team = await tpa.get_team(team_key=recipient.team_key)
                                tcity, tstate, tcountry = (
                                    team.city,
                                    team.state_prov,
                                    team.country,
                                )

                            print(
                                f"{award_type}\t{event.key}\t{recipient.awardee}\t{recipient.team_key}\t"
                                + f"{tcity}\t{tstate}\t{tcountry}\t"
                                + f"{event.city}\t{event.state_prov}\t{event.country}"
                            )
