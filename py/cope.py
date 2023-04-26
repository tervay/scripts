from py.cli import expose
from py.util import CURRENT_YEAR_RANGE
import statbotics
from pprint import pprint
from tqdm import tqdm

sb = statbotics.Statbotics()


@expose
async def saik():
    rows = []
    for num in tqdm(range(1, 9500)):
        try:
            team_years = sb.get_team_years(team=num)
        except:
            continue

        team_years.sort(key=lambda d: d["year"])
        for i in range(len(team_years) - 1):
            a = team_years[i]
            b = team_years[i + 1]

            if b["year"] == 2023:
                x = b["unitless_epa_end"]
            else:
                x = b["norm_epa_end"]

            if x is None or a["norm_epa_end"] is None:
                continue

            rows.append(
                [
                    num,
                    a["year"],
                    b["year"],
                    a["norm_epa_end"],
                    x,
                    round(x - a["norm_epa_end"], 5),
                ]
            )

    rows.sort(key=lambda r: -r[-1])

    for r in rows:
        print(",".join([str(s) for s in r]))
