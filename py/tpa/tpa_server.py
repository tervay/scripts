from typing import AsyncIterator, ForwardRef

from protos.tpa import *
from py.tba import tba
from py.tpa.force_fixes import (
    fix_event,
    fix_event_alliance,
    fix_match,
    fix_team,
    gen_missing_event_alliances,
)

SBs = {
    2015: (MatchScoreBreakdown2015, MatchScoreBreakdown2015Alliance),
    2016: (MatchScoreBreakdown2016, MatchScoreBreakdown2016Alliance),
    2017: (MatchScoreBreakdown2017, MatchScoreBreakdown2017Alliance),
    2018: (MatchScoreBreakdown2018, MatchScoreBreakdown2018Alliance),
    2019: (MatchScoreBreakdown2019, MatchScoreBreakdown2019Alliance),
    2020: (MatchScoreBreakdown2020, MatchScoreBreakdown2020Alliance),
}


def tba_match_to_tpa_match(m) -> Match:
    if "score_breakdown" not in m or m["score_breakdown"] is None:
        return fix_match(Match().from_dict(m))

    sb = m["score_breakdown"].copy()
    del m["score_breakdown"]

    m = Match().from_dict(m)
    if "2015" in m.event_key:
        m.score_breakdown_2015 = MatchScoreBreakdown2015().from_dict(sb)
    if "2016" in m.event_key:
        m.score_breakdown_2016 = MatchScoreBreakdown2016().from_dict(sb)
    if "2017" in m.event_key:
        m.score_breakdown_2017 = MatchScoreBreakdown2017().from_dict(sb)
    if "2018" in m.event_key:
        m.score_breakdown_2018 = MatchScoreBreakdown2018().from_dict(sb)
    if "2019" in m.event_key:
        m.score_breakdown_2019 = MatchScoreBreakdown2019().from_dict(sb)
    if "2020" in m.event_key:
        m.score_breakdown_2020 = MatchScoreBreakdown2020().from_dict(sb)

    return fix_match(m)


class TPAService(TpaBase):
    async def get_district_events(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_district_events")
        return None

    async def get_district_events_keys(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_district_events_keys")
        return None

    async def get_district_events_simple(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_district_events_simple")
        return None

    async def get_district_rankings(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("DistrictRanking")]:
        print("called get_district_rankings")
        return None

    async def get_district_teams(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("Team")]:
        print("called get_district_teams")
        return None

    async def get_district_teams_keys(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_district_teams_keys")
        return None

    async def get_district_teams_simple(
        self, district_key: str
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_district_teams_simple")
        return None

    async def get_districts_by_year(
        self, year: int
    ) -> AsyncIterator[ForwardRef("DistrictList")]:
        print("called get_districts_by_year")
        return None

    async def get_event(self, event_key: str) -> "Event":
        return fix_event(Event().from_dict(tba.event(event=event_key)))

    async def get_event_alliances(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("EliminationAlliance")]:
        try:
            for i, a in enumerate(tba.event_alliances(event=event_key), start=1):
                yield fix_event_alliance(EliminationAlliance().from_dict(a), i)
        except TypeError:
            if event_key == "2007sac":
                return

            for ea in gen_missing_event_alliances(
                [m async for m in self.get_event_matches(event_key=event_key)]
            ):
                yield ea

    async def get_event_awards(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Award")]:
        awards = tba.event_awards(event=event_key)
        for a in awards:
            yield Award().from_dict(a)

    async def get_event_district_points(self, event_key: str) -> "EventDistrictPoints":
        try:
            edp = tba.event_district_points(event=event_key)
        except TypeError:
            return EventDistrictPoints()

        for key, pts in edp["points"].items():
            for ptk, ptv in pts.items():
                pts[ptk] = int(ptv)

        return EventDistrictPoints().from_dict(edp)

    async def get_event_insights(self, event_key: str) -> "EventInsights":
        print("called get_event_insights")
        return None

    async def get_event_match_timeseries(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_match_timeseries")
        return None

    async def get_event_matches(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Match")]:
        for m in tba.event_matches(event=event_key):
            m_ = tba_match_to_tpa_match(m)
            yield m_

    async def get_event_matches_keys(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_matches_keys")
        return None

    async def get_event_matches_simple(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("MatchSimple")]:
        print("called get_event_matches_simple")
        return None

    async def get_event_op_rs(self, event_key: str) -> "EventOpRs":
        return EventOpRs().from_dict(tba.event_oprs(event=event_key))

    async def get_event_rankings(self, event_key: str) -> "EventRanking":
        return EventRanking().from_dict(tba.event_rankings(event=event_key))

    async def get_event_simple(self, event_key: str) -> "EventSimple":
        print("called get_event_simple")
        return None

    async def get_event_teams(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Team")]:
        teams = tba.event_teams(event=event_key)
        for t in teams:
            yield fix_team(Team().from_dict(t))

    async def get_event_teams_keys(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_teams_keys")
        return None

    async def get_event_teams_simple(
        self, event_key: str
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_event_teams_simple")
        return None

    async def get_events_by_year(self, year: int) -> AsyncIterator[ForwardRef("Event")]:
        events = tba.events(year=year)
        for e in events:
            yield fix_event(Event().from_dict(e))

    async def get_events_by_year_keys(
        self, year: int
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_events_by_year_keys")
        return None

    async def get_events_by_year_simple(
        self, year: int
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_events_by_year_simple")
        return None

    async def get_match(self, match_key: str) -> "Match":
        return tba_match_to_tpa_match(tba.match(key=match_key))

    async def get_match_simple(self, match_key: str) -> "MatchSimple":
        print("called get_match_simple")
        return None

    async def get_match_zebra(self, match_key: str) -> "Zebra":
        print("called get_match_zebra")
        return None

    async def get_team(self, team_key: str) -> "Team":
        return fix_team(Team().from_dict(tba.team(team=team_key)))

    async def get_team_awards(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("Award")]:
        print("called get_team_awards")
        return None

    async def get_team_awards_by_year(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Award")]:
        awards = tba.team_awards(team_key, year=year)
        for award in awards:
            yield Award().from_dict(award)

    async def get_team_districts(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("DistrictList")]:
        print("called get_team_districts")
        return None

    async def get_team_event_awards(
        self, team_key: str, event_key: str
    ) -> AsyncIterator[ForwardRef("Award")]:
        for a in tba.team_awards(team=team_key, event=event_key):
            yield Award().from_dict(a)

    async def get_team_event_matches(
        self, team_key: str, event_key: str
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_team_event_matches")
        return None

    async def get_team_event_matches_keys(
        self, team_key: str, event_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_event_matches_keys")
        return None

    async def get_team_event_matches_simple(
        self, team_key: str, event_key: str
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_team_event_matches_simple")
        return None

    async def get_team_event_status(
        self, team_key: str, event_key: str
    ) -> "TeamEventStatus":
        print("called get_team_event_status")
        return None

    async def get_team_events(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_team_events")
        return None

    async def get_team_events_by_year(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Event")]:
        for e in tba.team_events(team=team_key, year=year):
            yield fix_event(Event().from_dict(e))

    async def get_team_events_by_year_keys(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_events_by_year_keys")
        return None

    async def get_team_events_by_year_simple(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_team_events_by_year_simple")
        return None

    async def get_team_events_keys(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_events_keys")
        return None

    async def get_team_events_simple(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_team_events_simple")
        return None

    async def get_team_matches_by_year(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Match")]:
        for m in tba.team_matches(team=team_key, year=year):
            m_ = tba_match_to_tpa_match(m)
            yield m_

    async def get_team_matches_by_year_keys(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_matches_by_year_keys")
        return None

    async def get_team_matches_by_year_simple(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("MatchSimple")]:
        print("called get_team_matches_by_year_simple")
        return None

    async def get_team_media_by_tag(
        self, team_key: str, media_tag: str
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_tag")
        return None

    async def get_team_media_by_tag_year(
        self, team_key: str, media_tag: str, year: int
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_tag_year")
        return None

    async def get_team_media_by_year(
        self, team_key: str, year: int
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_year")
        return None

    async def get_team_robots(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("TeamRobot")]:
        print("called get_team_robots")
        return None

    async def get_team_simple(self, team_key: str) -> "TeamSimple":
        print("called get_team_simple")
        return None

    async def get_team_social_media(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_social_media")
        return None

    async def get_team_years_participated(
        self, team_key: str
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_years_participated")
        return None

    async def get_teams(self, page_num: int) -> AsyncIterator[ForwardRef("Team")]:
        for t in tba.teams(page=page_num):
            yield fix_team(Team().from_dict(t))

    async def get_teams_by_year(
        self, year: int, page_num: int
    ) -> AsyncIterator[ForwardRef("Team")]:
        for t in tba.teams(page=page_num, year=year):
            yield fix_team(Team().from_dict(t))

    async def get_teams_by_year_keys(
        self, year: int, page_num: int
    ) -> AsyncIterator[ForwardRef("Response")]:
        for t in tba.teams(year=year, page=page_num, keys=True):
            yield Response(string_value=t)

    async def get_teams_by_year_simple(
        self, year: int, page_num: int
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_teams_by_year_simple")
        return None

    async def get_teams_keys(
        self, page_num: int
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_teams_keys")
        return None

    async def get_teams_simple(
        self, page_num: int
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_teams_simple")
        return None
