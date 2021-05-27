from collections import defaultdict

from tqdm.asyncio import trange

from py.cli import expose, pprint
from py.tpa import tpa_cm


@expose
async def most_states():
    states = defaultdict(set)
    async with tpa_cm() as tpa:
        async for year in trange(1992, 2021):
            async for event in tpa.get_events_by_year(year=year):
                async for award in tpa.get_event_awards(event_key=event.key):
                    for recipient in award.recipient_list:
                        if len(event.state_prov) > 0:
                            states[recipient.team_key].add(event.state_prov)

    counts = {t: len(s) for t, s in states.items()}
    pprint(sorted(counts.items(), key=lambda t: -(t[1]))[:25])
