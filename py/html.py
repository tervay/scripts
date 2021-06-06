from protos.tpa import FakeEvent
from py.cli import expose
from py.util import file_cm, get_savepath
from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader("templates"))


@expose
def fake_page(fake_event_path):
    with file_cm(fake_event_path, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    template = env.get_template("fake_event.html")

    with file_cm(
        get_savepath(f"fake_events/{fake_event.event_key}_page.html"), "w+"
    ) as f:
        print(
            template.render(
                event=fake_event,
                year=fake_event.event_key[:4],
                quals=list(
                    filter(lambda m: m.comp_level == "qm", fake_event.schedule.matches)
                ),
                qf=list(
                    filter(lambda m: m.comp_level == "qf", fake_event.schedule.matches)
                ),
                sf=list(
                    filter(lambda m: m.comp_level == "sf", fake_event.schedule.matches)
                ),
                f=list(
                    filter(lambda m: m.comp_level == "f", fake_event.schedule.matches)
                ),
            ),
            file=f,
        )
