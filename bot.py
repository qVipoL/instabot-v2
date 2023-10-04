from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    MediaNotFound,
    PleaseWaitFewMinutes,
    ClientLoginRequired,
    ClientNotFoundError,
)
import os
import logging
import datetime
import time
import random
from models import BotStartModel


DELAY_RANGE = [5, 10]


def setup_logger(filename: str):
    logger = logging.getLogger(filename)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    log_file = f"./{filename}/bot_log_{timestamp}.log"

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"
    )

    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


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
        session_path: str = None,
        logger=None,
    ):
        self.username = username
        self.password = password
        self.api = Client()
        self.api.delay_range = delay_range
        self.session_path = session_path
        self.logger = logger

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

            self.logger.info("Before proxy: %s" % before_ip)
            self.logger.info("After proxy: %s" % after_ip)

    def login(self):
        """
        Attempts to login to Instagram using either the provided session information
        or the provided username and password.
        """

        session = (
            self.api.load_settings(self.session_path)
            if os.path.exists(self.session_path)
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
                    self.logger.info(
                        "Session is invalid, need to login via username and password"
                    )

                    old_session = self.api.get_settings()

                    # use the same device uuids across logins
                    self.api.set_settings({})
                    self.api.set_uuids(old_session["uuids"])

                    self.api.login(self.username, self.password)

                login_via_session = True

            except Exception as e:
                self.logger.info(
                    "Couldn't login user using session information: %s" % e
                )

        if not login_via_session:
            try:
                self.logger.info(
                    "Attempting to login via username and password. username: %s"
                    % self.username
                )

                if self.api.login(self.username, self.password):
                    login_via_pw = True
                    self.api.dump_settings(self.session_path)

            except Exception as e:
                self.logger.info(
                    "Couldn't login user using username and password: %s" % e
                )

        if not login_via_pw and not login_via_session:
            raise Exception("Couldn't login user with either password or session")

        self.logger.info(
            "Logged in via session" if login_via_session else "Logged in via password"
        )

    def find_and_like_posts(self, hashtag: str, amount: int = 1):
        """
        Finds and likes {amount} posts by {hashtag}
        """
        try:
            if self.total_likes >= self.max_likes:
                self.logger.info("Reached max likes per day")
                return

            medias = self.api.hashtag_medias_recent_v1(hashtag, amount)

            self.logger.info("Found %s posts" % len(medias))

            for media in medias:
                if self.total_likes >= self.max_likes:
                    self.logger.info("Reached max likes per day")
                    return

                if media.has_liked:
                    continue

                self.api.media_like(media.pk)
                self.logger.info("Liked post: %s" % media.pk)
                self.total_likes += 1

            self.logger.info("Total liked %s posts" % self.total_likes)
            self.logger.info(
                f"Total requests {self.total_likes + self.total_subs + self.total_stories}"
            )
        except ClientNotFoundError:
            self.logger.info("Couldn't find posts for hashtag: %s" % hashtag)
            pass
        except MediaNotFound:
            self.logger.info("Couldn't find posts for hashtag: %s" % hashtag)
            pass
        except Exception as e:
            self.logger.info("Couldn't like post: %s" % e)
            raise e

    def find_and_follow_users(self, query: str, amount: int = 1):
        """
        Finds and follows {amount} users by {query}
        """
        try:
            if self.total_subs >= self.max_follows:
                self.logger.info("Reached max follows per day")
                return

            followed_users = self.api.user_following_v1(user_id=self.api.user_id)

            users = self.api.search_users_v1(query, amount)
            users = users[:amount]

            self.logger.info("Found %s users" % len(users))

            for user in users:
                if self.total_subs >= self.max_follows:
                    self.logger.info("Reached max follows per day")
                    return

                if user.is_private:
                    continue

                if user.pk in followed_users:
                    continue

                self.api.user_follow(user.pk)
                self.total_subs += 1
                self.logger.info("Followed user: %s" % user.username)

            self.logger.info("Total followed %s users" % self.total_subs)
            self.logger.info(
                f"Total requests {self.total_likes + self.total_subs + self.total_stories}"
            )
        except Exception as e:
            self.logger.info("Couldn't follow user: %s" % e)
            raise e

    def find_and_watch_stories(
        self, hashtag: str, users_amount: int = 1, amount: int = 1
    ):
        """
        Finds and watches {amount} of stories for {users_amount} of users by {hashtag}
        """
        try:
            if self.total_stories >= self.max_stories:
                self.logger.info("Reached max stories per day")
                return

            users = self.api.search_users_v1(hashtag, users_amount)
            users = users[:users_amount]

            self.logger.info("Found %s users to watch stories" % len(users))

            for user in users:
                if self.total_stories >= self.max_stories:
                    self.logger.info("Reached max stories per day")
                    return

                if user.is_private:
                    continue

                stories = self.api.user_stories_v1(user.pk, amount)

                if len(stories) == 0:
                    continue

                self.logger.info(
                    "Found %s stories for user: %s" % (len(stories), user.username)
                )

                story_pks = [story.pk for story in stories]
                self.api.story_seen(story_pks)
                self.total_stories += len(story_pks)

                self.logger.info(
                    "Watched %s stories for user: %s" % (len(story_pks), user.username)
                )

            self.logger.info("Total watched %s stories" % self.total_stories)
            self.logger.info(
                f"Total requests {self.total_likes + self.total_subs + self.total_stories}"
            )
        except MediaNotFound:
            self.logger.info("Couldn't find stories for user: %s" % user.username)
            pass
        except Exception as e:
            self.logger.info("Couldn't watch stories: %s" % e)
            raise e


def run_bot(config: BotStartModel):
    username = config.username
    password = config.password
    proxy = config.proxy
    max_likes_day = config.max_likes_day
    max_follows_day = config.max_follows_day
    max_stories_day = config.max_stories_day
    min_time_between_cycles_secs = config.min_time_between_cycles_secs
    max_time_between_cycles_secs = config.max_time_between_cycles_secs
    min_time_between_actions_secs = config.min_time_between_actions_secs
    max_time_between_actions_secs = config.max_time_between_actions_secs
    posts_hashtag_list = config.posts_hashtag_list
    follow_hashtag_list = config.follow_hashtag_list
    stories_hashtag_list = config.stories_hashtag_list

    os.makedirs(username, exist_ok=True)
    logger = setup_logger(username)
    session_path = f"./{username}/session.json"

    bot = InstaBot(
        username=username,
        password=password,
        delay_range=DELAY_RANGE,
        max_likes=max_likes_day,
        max_follows=max_follows_day,
        max_stories=max_stories_day,
        proxy=proxy,
        session_path=session_path,
        logger=logger,
    )

    # 5 minutes
    min_time_between_cycles_secs = 5 * 60
    # 1 hour
    max_time_between_cycles_secs = 60 * 60

    # 1 minute
    min_time_between_actions_secs = 60
    # 10 minutes
    max_time_between_actions_secs = 10 * 60

    bot.login()

    time.sleep(
        random.randint(min_time_between_cycles_secs, max_time_between_cycles_secs)
    )

    while True:
        if (
            bot.total_likes >= bot.max_likes
            and bot.total_subs >= bot.max_follows
            and bot.total_stories >= bot.max_stories
        ):
            # sleep from 15 to 20 hours when finished
            time.sleep(random.randint(15 * 60 * 60, 20 * 60 * 60))
            logger.info("Reached max likes, follows and stories per day")
            break

        try:
            bot.find_and_like_posts(random.choice(posts_hashtag_list), 1)
            time.sleep(
                random.randint(
                    min_time_between_actions_secs, max_time_between_actions_secs
                )
            )
            bot.find_and_follow_users(random.choice(follow_hashtag_list), 1)
            time.sleep(
                random.randint(
                    min_time_between_actions_secs, max_time_between_actions_secs
                )
            )
            bot.find_and_watch_stories(random.choice(stories_hashtag_list), 1, 5)
        except PleaseWaitFewMinutes:
            logger.info("Reached rate limit")
            # sleep for 1 hour
            time.sleep(60 * 60)
        except LoginRequired:
            logger.info("Login required")
            bot.login()
        except ClientLoginRequired:
            logger.info("Login required")
            bot.login()
        finally:
            time.sleep(
                random.randint(
                    min_time_between_cycles_secs, max_time_between_cycles_secs
                )
            )
