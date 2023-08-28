from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import os
import logging
import datetime
import time
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"bot_log_{timestamp}.log"

fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s")

ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

USERNAME = "0546605274"
PASSWORD = "AmazingNight123!"
PROXY = "http://xdjtexfm:89sugm26m8a5@2.56.119.93:5074"
DELAY_RANGE = [5, 10]

MIN_SECS_BETWEEN_ACTIONS = 5 * 60
MAX_SECS_BETWEEN_ACTIONS = 7 * 60

MAX_STORIES_PER_DAY = 150
MAX_LIKES_PER_DAY = 150
MAX_FOLLOWS_PER_DAY = 15

SESSION_PATH = "session.json"


class InstaBot:
    def __init__(
        self,
        username: str,
        password: str,
        delay_range: tuple,
        max_likes: int = 1,
        max_follows: int = 1,
        max_stories: int = 1,
        proxy: str = None,
    ):
        self.username = username
        self.password = password
        self.api = Client()
        self.api.delay_range = delay_range

        self.max_likes = max_likes
        self.max_follows = max_follows
        self.max_stories = max_stories

        self.total_likes = 0
        self.total_subs = 0
        self.total_stories = 0

        if proxy:
            before_ip = self.api._send_public_request("https://ipv4.webshare.io/")
            self.api.set_proxy(proxy)
            after_ip = self.api._send_public_request("https://ipv4.webshare.io/")

            logger.info("Before proxy: %s" % before_ip)
            logger.info("After proxy: %s" % after_ip)

    def login(self):
        """
        Attempts to login to Instagram using either the provided session information
        or the provided username and password.
        """

        session = (
            self.api.load_settings(SESSION_PATH)
            if os.path.exists(SESSION_PATH)
            else None
        )

        login_via_session = False
        login_via_pw = False

        if session:
            try:
                self.api.set_settings(session)
                self.api.login(self.username, self.password)

                # check if session is valid
                try:
                    self.api.get_timeline_feed()
                except LoginRequired:
                    logger.info(
                        "Session is invalid, need to login via username and password"
                    )

                    old_session = self.api.get_settings()

                    # use the same device uuids across logins
                    self.api.set_settings({})
                    self.api.set_uuids(old_session["uuids"])

                    self.api.login(self.username, self.password)

                login_via_session = True

            except Exception as e:
                logger.info("Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                logger.info(
                    "Attempting to login via username and password. username: %s"
                    % self.username
                )

                if self.api.login(self.username, self.password):
                    login_via_pw = True
                    self.api.dump_settings(SESSION_PATH)

            except Exception as e:
                logger.info("Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception("Couldn't login user with either password or session")

        logger.info(
            "Logged in via session" if login_via_session else "Logged in via password"
        )

    def find_and_like_posts(self, hashtag: str, amount: int = 1):
        """
        Finds and likes {amount} posts by {hashtag}
        """
        if self.total_likes >= self.max_likes:
            logger.info("Reached max likes per day")
            return

        medias = self.api.hashtag_medias_recent_v1(hashtag, amount)

        logger.info("Found %s posts" % len(medias))

        for media in medias:
            if self.total_likes >= self.max_likes:
                logger.info("Reached max likes per day")
                return

            if media.has_liked:
                continue

            self.api.media_like(media.pk)
            logger.info("Liked post: %s" % media.pk)
            self.total_likes += 1

        logger.info("Total liked %s posts" % self.total_likes)

    def find_and_follow_users(self, query: str, amount: int = 1):
        """
        Finds and follows {amount} users by {query}
        """
        if self.total_subs >= self.max_follows:
            logger.info("Reached max follows per day")
            return

        users = self.api.search_users_v1(query, amount)
        users = users[:amount]

        logger.info("Found %s users" % len(users))

        for user in users:
            if self.total_subs >= self.max_follows:
                logger.info("Reached max follows per day")
                return

            if user.is_private:
                continue

            self.api.user_follow(user.pk)
            self.total_subs += 1
            logger.info("Followed user: %s" % user.username)

        logger.info("Total followed %s users" % self.total_subs)

    def find_and_watch_stories(
        self, hashtag: str, users_amount: int = 1, amount: int = 1
    ):
        """
        Finds and watches {amount} of stories for {users_amount} of users by {hashtag}
        """
        if self.total_stories >= self.max_stories:
            logger.info("Reached max stories per day")
            return

        users = self.api.search_users_v1(hashtag, users_amount)

        for user in users:
            if self.total_stories >= self.max_stories:
                logger.info("Reached max stories per day")
                return

            if user.is_private:
                continue

            stories = self.api.user_stories_v1(user.pk, amount)

            if len(stories) == 0:
                continue

            logger.info("Found %s stories for user: %s" % (len(stories), user.username))

            story_pks = [story.pk for story in stories]
            self.api.story_seen(story_pks)
            self.total_stories += len(story_pks)

            logger.info(
                "Watched %s stories for user: %s" % (len(story_pks), user.username)
            )

        logger.info("Total watched %s stories" % self.total_stories)


def get_random_hashtag():
    hashtags = ["cats", "dogs", "food", "nature", "travel", "cars", "music", "art"]
    return random.choice(hashtags)


def get_random_username():
    usernames = [
        "skilled-bridge",
        "avital",
        "david",
        "daniel",
        "yoni",
        "yael",
        "shir",
        "shira",
    ]
    return random.choice(usernames)


def run_bot():
    bot = InstaBot(
        username=USERNAME,
        password=PASSWORD,
        delay_range=DELAY_RANGE,
        max_likes=MAX_LIKES_PER_DAY,
        max_follows=MAX_FOLLOWS_PER_DAY,
        max_stories=MAX_STORIES_PER_DAY,
        proxy=PROXY,
    )

    bot.login()

    while True:
        bot.find_and_like_posts(get_random_hashtag(), 1)
        bot.find_and_follow_users(get_random_username(), 1)
        bot.find_and_watch_stories(get_random_username(), 1, 5)

        time.sleep(random.randint(MIN_SECS_BETWEEN_ACTIONS, MAX_SECS_BETWEEN_ACTIONS))


def main():
    run_bot()


if __name__ == "__main__":
    main()
