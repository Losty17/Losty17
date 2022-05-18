from os import getenv

import tweepy
import re
import pathlib

from dotenv import load_dotenv
from tweepy import API, OAuth2AppHandler

load_dotenv()


class User:
    def __init__(self, client: API) -> None:
        OWNER_ID = getenv("OWNER_ID")
        _user = client.get_user(user_id=OWNER_ID)

        self.id = _user.id
        self.name = _user.name


class Tweet:
    def __init__(self, text: str, images: list[str], user: User) -> None:
        self.text = text
        self.images = images
        self.user = user

    def __str__(self) -> str:
        img_str = ''

        for img in self.images:
            if img_str == '':
                img_str += ' - '
            img_str += f'[Link]({img}) '

        return f"{self.text}{img_str}"


class Bot:
    def __init__(self) -> None:
        API_KEY = getenv("API_KEY")
        API_SECRET = getenv("API_SECRET")
        auth = OAuth2AppHandler(API_KEY, API_SECRET)

        self.client = API(auth=auth)
        self.user = self.get_user()

    def get_user(self) -> User:
        return User(self.client)

    def get_last_tweet(self) -> Tweet:
        tweets = self.client.user_timeline(
            user_id=self.user.id, include_rts=True)

        return self.create_tweet(tweets[0])

    def get_tweets(self) -> list[Tweet]:
        src = self.client.user_timeline(
            user_id=self.user.id, include_rts=True, count='5'
        )

        tweets = []
        for tweet in src:
            tweets.append(self.create_tweet(tweet))

        return tweets

    def create_tweet(self, tweet: tweepy.Tweet) -> Tweet:
        text = re.sub(
            r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''',
            "",
            tweet.text
        )
        text = text.strip()

        try:
            imgs = [n['expanded_url'] for n in tweet.entities['media']]
        except KeyError as e:
            imgs = []

        return Tweet(text, imgs, self.user)


class ReadmeUpdater:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    def print_last_tweets(self) -> str:
        tweets = self.bot.get_tweets()
        for tweet in tweets:
            print(tweet)

    def replace_chunk(self, content, marker, chunk, inline=False):
        r = re.compile(
            r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(
                marker, marker),
            re.DOTALL,
        )
        if not inline:
            chunk = f"\n{chunk}\n"
        chunk = f"<!-- {marker} starts -->{chunk}<!-- {marker} ends -->"
        return r.sub(chunk, content)

    def update_readme(self):
        root = pathlib.Path(__file__).parent.resolve()
        readme = root / "README.md"
        readme_contents = readme.open().read()

        data = self.bot.get_tweets()
        res = ''
        for i in data:
            res += f'* {i.__str__()}\n'

        rewritten = self.replace_chunk(
            readme_contents, "last_tweet", res)

        readme.open("w", encoding='utf-8').write(rewritten)


if __name__ == "__main__":
    readme_updater = ReadmeUpdater(Bot())

    readme_updater.update_readme()
