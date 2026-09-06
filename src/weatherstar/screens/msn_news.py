"""MSN Top Stories screen with a vertical headline ticker.

Headlines are a module-level literal (as in the legacy display source).  The
``headlines`` component scrolls them with the classic color coding: category
prefixes in cyan, ``BREAKING`` in red and ``UPDATE`` in yellow.
"""

from __future__ import annotations

from weatherstar.components.base import ComponentSpec
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen

#: Literal headline set ported from ``displays.py::draw_msn_news``.
MSN_HEADLINES: list[tuple[str, str]] = [
    (
        "Breaking: Major Winter Storm System Moving Across United States "
        "Bringing Heavy Snow and Ice",
        "https://www.msn.com/weather",
    ),
    (
        "Technology: Apple Announces Revolutionary New Product Line at Annual Developer Conference",
        "https://www.msn.com/technology",
    ),
    (
        "Sports: Underdog Team Wins Championship in Dramatic Overtime Victory Against All Odds",
        "https://www.msn.com/sports",
    ),
    (
        "World News: Global Climate Summit Concludes with Historic Agreement Among Nations",
        "https://www.msn.com/world",
    ),
    (
        "Business: Stock Market Reaches All-Time High as Economic Recovery Continues to Accelerate",
        "https://www.msn.com/money",
    ),
    (
        "Entertainment: Surprise Winners at Annual Award Show Leave Audiences Stunned",
        "https://www.msn.com/entertainment",
    ),
    (
        "Health: Scientists Announce Major Medical Breakthrough in Cancer Research Treatment",
        "https://www.msn.com/health",
    ),
    (
        "Science: Space Mission Successfully Launches New Era of Deep Space Exploration",
        "https://www.msn.com/news/technology",
    ),
    (
        "Politics: Congress Passes Landmark Legislation with Bipartisan Support",
        "https://www.msn.com/politics",
    ),
    (
        "Local: Community Rallies Together to Support Families Affected by Recent Events",
        "https://www.msn.com/local",
    ),
    (
        "Weather: Hurricane Season Expected to Be More Active Than Normal This Year",
        "https://www.weather.com",
    ),
    (
        "Technology: Artificial Intelligence Breakthrough Could Transform Daily Life",
        "https://www.msn.com/technology",
    ),
]


@plugin
class MsnNewsScreen(Screen):
    name = "msn_news"
    media = ("backgrounds", "logos")
    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(
            component="header", config={"title_top": "MSN", "title_bottom": "Top Stories"}
        ),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="headlines",
            config={
                "numbered": True,
                "accent": "category",
                "red_terms": ("BREAKING",),
                "yellow_terms": ("UPDATE",),
                "empty_text": "No headlines available",
            },
        ),
    )

    def prepare(self, ctx) -> None:
        self.component("headlines").set_headlines(MSN_HEADLINES)
