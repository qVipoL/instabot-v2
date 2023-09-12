import pydantic
from typing import Optional


class BotStartModel(pydantic.BaseModel):
    username: str
    password: str
    proxy: Optional[str]
    max_likes_day: int
    max_follows_day: int
    max_stories_day: int
    min_time_between_cycles_secs: int
    max_time_between_cycles_secs: int
    min_time_between_actions_secs: int
    max_time_between_actions_secs: int
    posts_hashtag_list: list[str]
    follow_hashtag_list: list[str]
    stories_hashtag_list: list[str]


class BotResponseModel(pydantic.BaseModel):
    message: str
    total_bots: int
