import requests
from typing import NamedTuple
from bs4 import BeautifulSoup
from http import HTTPStatus
from xml.etree import ElementTree

import exceptions


def get(url: str) -> requests.models.Response:
    """requests.get() with necessary headers and custom exceptions."""
    try:
        response = requests.get(url, headers={"User-Agent": "Chrome/50.0.2661.102"})
    except requests.exceptions.BaseHTTPError:
        raise exceptions.RequestError(url)
    if response.status_code != HTTPStatus.OK:
        raise exceptions.RequestError(url)
    return response


def post(url: str, data: str, headers: dict = None) -> requests.models.Response:
    """requests.post() with utf-8 data encoding and custom exceptions."""
    try:
        response = requests.post(url, data=data.encode("utf-8"), headers=headers)
    except requests.exceptions.BaseHTTPError:
        raise exceptions.RequestError(url)
    if response.status_code != HTTPStatus.OK:
        raise exceptions.RequestError(url)
    return response


class FeedItem(NamedTuple):
    title: str
    link: str


class RssReader:
    """Class for parsing RSS feed."""

    def __init__(self, feed: str):
        try:
            tree = ElementTree.fromstring(feed)
            self.news_items = []
            for item in tree.findall("channel/item"):
                self.news_items.append(
                    FeedItem(item.find("title").text, item.find("link").text)
                )
        except ElementTree.ParseError as e:
            raise exceptions.ParseError("RSS parser", e.msg)

    def __getitem__(self, index: int) -> FeedItem:
        """Returns feed item by index."""
        return self.news_items[index]


class NewsPage(NamedTuple):
    title: str
    html_content: str


class NewsSiteHandler:
    """
    Generate the latest news from news site using RSS feed.

    Page 'website/rss' must be available.
    """

    def __init__(self, rss_reader):
        self.rss_reader = rss_reader
        self.feed_index = 0

    @staticmethod
    def from_url(url: str):
        if url.endswith("/"):
            url = url[:-1]
        if not url.startswith("http"):
            url = "https://" + url
        return NewsSiteHandler(RssReader(get(f"{url}/rss").content.decode()))

    def __iter__(self):
        return self

    def __next__(self) -> NewsPage:
        try:
            next_item = self.rss_reader[self.feed_index]
            self.feed_index += 1
        except IndexError:
            raise StopIteration
        response = get(next_item.link)
        soup = BeautifulSoup(response.content, "html.parser")
        return NewsPage(
            next_item.title, "\n".join(map(BeautifulSoup.prettify, soup("p")))
        )


class Translator:
    """Translates text into Russian using Yandex.Translate REST API."""

    def __init__(self, iam_token: str, folder_id: str):
        """
        More about using Translate API: https://cloud.yandex.com/en-ru/docs/translate/quickstart

        Args:

        iam_token: a unique sequence of characters issued to a user after authentication.

        folder_id: the ID of any folder that your account is granted the editor role or higher for.
        """
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {iam_token}",
        }
        self.data_template = f"""
            {{
            "targetLanguageCode": "ru",
               "format" : "HTML",
               "texts": [
                 "%s"
               ],
               "folderId": "{folder_id}"
            }}
           """

    @staticmethod
    def from_auth_data_paths(oauth_token_filepath: str, folder_id_filepath: str):
        """
        More about using Translate API: https://cloud.yandex.com/en-ru/docs/translate/quickstart

        Args:

        oauth_token_filepath: path to OAuth token from Yandex.OAuth.

        folder_id_filepath: path to the ID of any folder that your account is granted the editor role or higher for.
        """
        with open(oauth_token_filepath) as f:
            oauth_token = f.read()
        with open(folder_id_filepath) as f:
            folder_id = f.read()
        data = f'{{"yandexPassportOauthToken":"{oauth_token}"}}'
        response = post("https://iam.api.cloud.yandex.net/iam/v1/tokens", data=data)
        return Translator(response.json()["iamToken"], folder_id)

    def __call__(self, text: str) -> str:
        """Returns the translation of the text into Russian"""
        response = post(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            data=self.data_template % text.replace('"', ""),
            headers=self.headers,
        )
        return response.json()["translations"][0]["text"]
