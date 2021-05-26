from typing import AsyncIterator, ForwardRef

from protos import *
from py.tba import tba


class TPAService(TpaBase):
    async def get_district_events(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_district_events")
        return None

    async def get_district_events_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_district_events_keys")
        return None

    async def get_district_events_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_district_events_simple")
        return None

    async def get_district_rankings(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("DistrictRanking")]:
        print("called get_district_rankings")
        return None

    async def get_district_teams(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Team")]:
        print("called get_district_teams")
        return None

    async def get_district_teams_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_district_teams_keys")
        return None

    async def get_district_teams_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_district_teams_simple")
        return None

    async def get_districts_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("DistrictList")]:
        print("called get_districts_by_year")
        return None

    async def get_event(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "Event":
        print("called get_event")
        return None

    async def get_event_alliances(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("EliminationAlliance")]:
        print("called get_event_alliances")
        return None

    async def get_event_awards(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Award")]:
        print("called get_event_awards")
        return None

    async def get_event_district_points(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "EventDistrictPoints":
        print("called get_event_district_points")
        return None

    async def get_event_insights(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "EventInsights":
        print("called get_event_insights")
        return None

    async def get_event_match_timeseries(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_match_timeseries")
        return None

    async def get_event_matches(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_event_matches")
        return None

    async def get_event_matches_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_matches_keys")
        return None

    async def get_event_matches_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("MatchSimple")]:
        print("called get_event_matches_simple")
        return None

    async def get_event_op_rs(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "EventOpRs":
        print("called get_event_op_rs")
        return None

    async def get_event_rankings(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "EventRanking":
        print("called get_event_rankings")
        return None

    async def get_event_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "EventSimple":
        print("called get_event_simple")
        return None

    async def get_event_teams(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Team")]:
        print("called get_event_teams")
        return None

    async def get_event_teams_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_event_teams_keys")
        return None

    async def get_event_teams_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_event_teams_simple")
        return None

    async def get_events_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_events_by_year")
        return None

    async def get_events_by_year_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_events_by_year_keys")
        return None

    async def get_events_by_year_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_events_by_year_simple")
        return None

    async def get_match(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "Match":
        print("called get_match")
        return None

    async def get_match_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "MatchSimple":
        print("called get_match_simple")
        return None

    async def get_match_zebra(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "Zebra":
        print("called get_match_zebra")
        return None

    async def get_status(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "ApiStatus":
        print("called get_status")
        return None

    async def get_team(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "Team":
        return Team().from_dict(tba.team(team=team_key))

    async def get_team_awards(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Award")]:
        print("called get_team_awards")
        return None

    async def get_team_awards_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Award")]:
        print("called get_team_awards_by_year")
        return None

    async def get_team_districts(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("DistrictList")]:
        print("called get_team_districts")
        return None

    async def get_team_event_awards(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Award")]:
        print("called get_team_event_awards")
        return None

    async def get_team_event_matches(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_team_event_matches")
        return None

    async def get_team_event_matches_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_event_matches_keys")
        return None

    async def get_team_event_matches_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_team_event_matches_simple")
        return None

    async def get_team_event_status(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "TeamEventStatus":
        print("called get_team_event_status")
        return None

    async def get_team_events(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_team_events")
        return None

    async def get_team_events_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Event")]:
        print("called get_team_events_by_year")
        return None

    async def get_team_events_by_year_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_events_by_year_keys")
        return None

    async def get_team_events_by_year_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_team_events_by_year_simple")
        return None

    async def get_team_events_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_events_keys")
        return None

    async def get_team_events_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("EventSimple")]:
        print("called get_team_events_simple")
        return None

    async def get_team_matches_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Match")]:
        print("called get_team_matches_by_year")
        return None

    async def get_team_matches_by_year_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_matches_by_year_keys")
        return None

    async def get_team_matches_by_year_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("MatchSimple")]:
        print("called get_team_matches_by_year_simple")
        return None

    async def get_team_media_by_tag(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_tag")
        return None

    async def get_team_media_by_tag_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_tag_year")
        return None

    async def get_team_media_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_media_by_year")
        return None

    async def get_team_robots(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("TeamRobot")]:
        print("called get_team_robots")
        return None

    async def get_team_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> "TeamSimple":
        print("called get_team_simple")
        return None

    async def get_team_social_media(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Media")]:
        print("called get_team_social_media")
        return None

    async def get_team_years_participated(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_team_years_participated")
        return None

    async def get_teams(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Team")]:
        print("called get_teams")
        return None

    async def get_teams_by_year(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Team")]:
        print("called get_teams_by_year")
        return None

    async def get_teams_by_year_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_teams_by_year_keys")
        return None

    async def get_teams_by_year_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_teams_by_year_simple")
        return None

    async def get_teams_keys(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("Response")]:
        print("called get_teams_keys")
        return None

    async def get_teams_simple(
        self,
        year: int,
        media_tag: str,
        if_modified_since: str,
        page_num: int,
        match_key: str,
        district_key: str,
        team_key: str,
        event_key: str,
    ) -> AsyncIterator[ForwardRef("TeamSimple")]:
        print("called get_teams_simple")
        return None
