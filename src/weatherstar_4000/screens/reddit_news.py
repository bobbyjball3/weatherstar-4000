"""Reddit Headlines screen with a vertical headline ticker.

Headlines are a module-level literal (as in the legacy display source).  The
``headlines`` component scrolls them token by token so ``r/...`` subreddit
mentions render in cyan and bracketed tags (``[OC]``) in yellow.
"""

from __future__ import annotations

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

#: Literal headline set ported from ``displays.py::draw_reddit_news``.
REDDIT_HEADLINES: list[tuple[str, str]] = [
    (
        "r/news: Major Storm System Approaching East Coast with Potential for "
        "Historic Snowfall Amounts",
        "https://reddit.com/r/news",
    ),
    (
        "r/worldnews: International Summit Concludes with Unexpected Alliance "
        "Between Former Rivals",
        "https://reddit.com/r/worldnews",
    ),
    (
        "r/technology: New AI Breakthrough Could Revolutionize How We Interact with Computers",
        "https://reddit.com/r/technology",
    ),
    (
        "r/science: Scientists Discover New Species in Previously Unexplored Deep Ocean Trench",
        "https://reddit.com/r/science",
    ),
    (
        "r/gaming: Popular Game Franchise Gets Surprise Major Update After Years of Silence",
        "https://reddit.com/r/gaming",
    ),
    (
        "r/movies: Independent Film Breaks Box Office Records in Limited Release",
        "https://reddit.com/r/movies",
    ),
    (
        "r/sports: Underdog Team's Cinderella Story Continues with Another Upset Victory",
        "https://reddit.com/r/sports",
    ),
    (
        "r/space: New Images from James Webb Space Telescope Reveal Stunning Cosmic Phenomena",
        "https://reddit.com/r/space",
    ),
    (
        "r/AskReddit: What's the most interesting historical fact you know that sounds fake?",
        "https://reddit.com/r/AskReddit",
    ),
    (
        "r/todayilearned: TIL that honey never spoils and archaeologists have "
        "found 3000 year old honey",
        "https://reddit.com/r/todayilearned",
    ),
    (
        "r/EarthPorn: Sunrise over the Grand Canyon after fresh snowfall [OC] [4032x3024]",
        "https://reddit.com/r/EarthPorn",
    ),
    (
        "r/dataisbeautiful: [OC] Visualization of global temperature changes over the last century",
        "https://reddit.com/r/dataisbeautiful",
    ),
]


@plugin
class RedditNewsScreen(Screen):
    name = "reddit_news"
    media = ("backgrounds", "logos")
    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Reddit", "title_bottom": "Headlines"},
        ),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="headlines",
            config={
                "numbered": False,
                "accent": "token",
                "empty_text": "No headlines available",
            },
        ),
    )

    def prepare(self, ctx) -> None:
        self.component("headlines").set_headlines(REDDIT_HEADLINES)
