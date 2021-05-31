from key import key

from .main import *

tba = TBA(key)


class EventType:
    REGIONAL = 0
    DISTRICT = 1
    DISTRICT_CMP = 2
    CMP_DIVISION = 3
    CMP_FINALS = 4
    DISTRICT_CMP_DIVISION = 5
    FOC = 6
    REMOTE = 7

    OFFSEASON = 99
    PRESEASON = 100
    UNLABLED = -1

    DISTRICT_EVENT_TYPES = {
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
    }

    NON_CMP_EVENT_TYPES = {
        REGIONAL,
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
        REMOTE,
    }

    CMP_EVENT_TYPES = {
        CMP_DIVISION,
        CMP_FINALS,
    }

    SEASON_EVENT_TYPES = {
        REGIONAL,
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
        CMP_DIVISION,
        CMP_FINALS,
        FOC,
        REMOTE,
    }


class AwardType:
    CHAIRMANS = 0
    WINNER = 1
    FINALIST = 2

    WOODIE_FLOWERS = 3
    DEANS_LIST = 4
    VOLUNTEER = 5
    FOUNDERS = 6
    BART_KAMEN_MEMORIAL = 7
    MAKE_IT_LOUD = 8

    ENGINEERING_INSPIRATION = 9
    ROOKIE_ALL_STAR = 10
    GRACIOUS_PROFESSIONALISM = 11
    COOPERTITION = 12
    JUDGES = 13
    HIGHEST_ROOKIE_SEED = 14
    ROOKIE_INSPIRATION = 15
    INDUSTRIAL_DESIGN = 16
    QUALITY = 17
    SAFETY = 18
    SPORTSMANSHIP = 19
    CREATIVITY = 20
    ENGINEERING_EXCELLENCE = 21
    ENTREPRENEURSHIP = 22
    EXCELLENCE_IN_DESIGN = 23
    EXCELLENCE_IN_DESIGN_CAD = 24
    EXCELLENCE_IN_DESIGN_ANIMATION = 25
    DRIVING_TOMORROWS_TECHNOLOGY = 26
    IMAGERY = 27
    MEDIA_AND_TECHNOLOGY = 28
    INNOVATION_IN_CONTROL = 29
    SPIRIT = 30
    WEBSITE = 31
    VISUALIZATION = 32
    AUTODESK_INVENTOR = 33
    FUTURE_INNOVATOR = 34
    RECOGNITION_OF_EXTRAORDINARY_SERVICE = 35
    OUTSTANDING_CART = 36
    WSU_AIM_HIGHER = 37
    LEADERSHIP_IN_CONTROL = 38
    NUM_1_SEED = 39
    INCREDIBLE_PLAY = 40
    PEOPLES_CHOICE_ANIMATION = 41
    VISUALIZATION_RISING_STAR = 42
    BEST_OFFENSIVE_ROUND = 43
    BEST_PLAY_OF_THE_DAY = 44
    FEATHERWEIGHT_IN_THE_FINALS = 45
    MOST_PHOTOGENIC = 46
    OUTSTANDING_DEFENSE = 47
    POWER_TO_SIMPLIFY = 48
    AGAINST_ALL_ODDS = 49
    RISING_STAR = 50
    CHAIRMANS_HONORABLE_MENTION = 51
    CONTENT_COMMUNICATION_HONORABLE_MENTION = 52
    TECHNICAL_EXECUTION_HONORABLE_MENTION = 53
    REALIZATION = 54
    REALIZATION_HONORABLE_MENTION = 55
    DESIGN_YOUR_FUTURE = 56
    DESIGN_YOUR_FUTURE_HONORABLE_MENTION = 57
    SPECIAL_RECOGNITION_CHARACTER_ANIMATION = 58
    HIGH_SCORE = 59
    TEACHER_PIONEER = 60
    BEST_CRAFTSMANSHIP = 61
    BEST_DEFENSIVE_MATCH = 62
    PLAY_OF_THE_DAY = 63
    PROGRAMMING = 64
    PROFESSIONALISM = 65
    GOLDEN_CORNDOG = 66
    MOST_IMPROVED_TEAM = 67
    WILDCARD = 68
    CHAIRMANS_FINALIST = 69
    OTHER = 70
    AUTONOMOUS = 71
    INNOVATION_CHALLENGE_SEMI_FINALIST = 72
    ROOKIE_GAME_CHANGER = 73
    SKILLS_COMPETITION_WINNER = 74
    SKILLS_COMPETITION_FINALIST = 75
    ROOKIE_DESIGN = 76
    ENGINEERING_DESIGN = 77
    DESIGNERS = 78
    CONCEPT = 79

    BLUE_BANNER_AWARDS = {
        CHAIRMANS,
        CHAIRMANS_FINALIST,
        WINNER,
        WOODIE_FLOWERS,
        SKILLS_COMPETITION_WINNER,
    }
    INDIVIDUAL_AWARDS = {
        WOODIE_FLOWERS,
        DEANS_LIST,
        VOLUNTEER,
        FOUNDERS,
        BART_KAMEN_MEMORIAL,
        MAKE_IT_LOUD,
    }
    NON_JUDGED_NON_TEAM_AWARDS = {  # awards not used in the district point model
        HIGHEST_ROOKIE_SEED,
        WOODIE_FLOWERS,
        DEANS_LIST,
        VOLUNTEER,
        WINNER,
        FINALIST,
        WILDCARD,
    }
    CMP_QUALIFYING_AWARDS = {WINNER, CHAIRMANS, WILDCARD, ENGINEERING_INSPIRATION}
