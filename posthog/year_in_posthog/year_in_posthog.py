import os
from typing import Dict, List, Union

import structlog
from django.http import HttpResponse
from django.template.loader import get_template
from sentry_sdk import capture_exception

from posthog import settings
from posthog.year_in_posthog.calculate_2022 import calculate_year_in_posthog_2022
from posthog.year_in_posthog.crypto import user_id_decrypt

logger = structlog.get_logger(__name__)

badge_preference = ["astronaut", "deep_diver", "curator", "flag_raiser", "popcorn_muncher", "scientist", "champion"]

human_badge = {
    "astronaut": "Astronaut",
    "deep_diver": "Deep Diver",
    "curator": "Curator",
    "flag_raiser": "Flag Raiser",
    "popcorn_muncher": "Popcorn muncher",
    "scientist": "Scientist",
    "champion": "Champion",
}

highlight_color = {
    "astronaut": "#E2E8FE",
    "deep_diver": "#41CBC4",
    "curator": "#FFF",
    "flag_raiser": "#FF906E",
    "popcorn_muncher": "#C5A1FF",
    "scientist": "#FFD371",
    "champion": "#FE729D",
}

explanation = {
    "astronaut": "When it comes to data, there are no small steps - only giant leaps. And we think you're out of this world.",
    "deep_diver": "You've dived into your data far deeper than the average Joe (no offence, Joe). What's at the bottom of the data lake? You're going to find out.",
    "curator": "Product analytics is an art, as well as a science. And you're an artist. Your dashboards belong in a museum.",
    "flag_raiser": "You've raised so many feature flags we've started to suspect that semaphore is your first language. Keep it up!",
    "popcorn_muncher": "You're addicted to reality TV. And, by reality TV, we mean session recordings. You care about the UX and we want to celebrate that!",
    "scientist": "You’ve earned this badge from your never ending curiosity and need for knowledge. One result we know for sure, you are doing amazing things. ",
    "champion": "Unmatched. Unstoppable. You're like the Usain Bolt of hedgehogs! We're grateful to have you as a PostHog power user.",
}


def count_from(data: Dict, badge: str) -> List[Dict[str, Union[int, str]]]:
    stats = data["stats"]
    # noinspection PyBroadException
    try:
        if badge == "astronaut" or badge == "deep_diver":
            return [{"count": stats["insight_created_count"], "description": "Insights created"}]
        elif badge == "curator":
            return [{"count": stats["dashboard_created_count"], "description": "Dashboards created"}]
        elif badge == "flag_raiser":
            return [{"count": stats["flag_created_count"], "description": "Feature flags created"}]
        elif badge == "popcorn_muncher":
            return [{"count": stats["viewed_recording_count"], "description": "Session recordings viewed"}]
        elif badge == "scientist":
            return [{"count": stats["experiments_created_count"], "description": "Experiments created"}]
        elif badge == "curator":
            return [
                {"count": stats["insight_created_count"], "description": "Insights created"},
                {"count": stats["viewed_recording_count"], "description": "Session recordings viewed"},
                {"count": stats["flag_created_count"], "description": "Feature flags created"},
            ]
        else:
            raise Exception("A user has to have one badge!")
    except Exception as e:
        logger.error("Error getting stats", exc_info=True, exc=e, data=data or "no data", badge=badge)
        return []


def sort_list_based_on_preference(badges: List[str]) -> str:
    """sort a list based on its order in badge_preferences and then choose the last one"""
    badges_by_preference = [x for _, x in sorted(zip(badge_preference, badges))]
    return badges_by_preference[-1]


def render_2022(request, user_token: str) -> HttpResponse:
    data = None
    try:
        user_id = user_id_decrypt(user_token)

        data = calculate_year_in_posthog_2022(user_id)

        badge = sort_list_based_on_preference(data["badges"])

        context = {
            "debug": settings.DEBUG,
            "api_token": os.environ.get("DEBUG_API_TOKEN", "unknown") if settings.DEBUG else "sTMFPsFhdP1Ssg",
            "badge": badge,
            "human_badge": human_badge.get(badge),
            "highlight_color": highlight_color.get(badge),
            "image": f"badges/2022_{badge}.png",
            "opengraph_image": f"open-graph/2022_{badge}.png",
            "explanation": explanation.get(badge),
            "stats": count_from(data, badge),
        }

        template = get_template("2022.html")
        html = template.render(context, request=request)
        return HttpResponse(html)
    except Exception as e:
        capture_exception(e)
        logger.error("Error rendering 2022 page", exc_info=True, exc=e, data=data or "no data")
        return HttpResponse("Error rendering 2022 page", status=500)
