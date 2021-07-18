import sys
from http import HTTPStatus
from flask import Flask, render_template, request, redirect, url_for, abort
import json
from clients import Translator, NewsSiteHandler
from typing import NamedTuple

import exceptions

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("form.html", news_sites=news_sites)


@app.route("/init", methods=["POST", "GET"])
def init():
    if request.method == "POST":
        global news_handler
        news_handler = NewsSiteHandler.from_url(request.form["url"])
        return redirect(url_for("news"))
    if request.method == "GET":
        abort(HTTPStatus.NOT_FOUND)


@app.route("/news")
def news():
    try:
        page_data = next(news_handler)
    except NameError:
        abort(HTTPStatus.NOT_FOUND)
    except StopIteration:
        redirect(url_for("index"))
    return render_template(
        "news.html",
        page_data=page_data,
        translated_content=translator(page_data.html_content),
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise exceptions.WrongNumberOfArguments(3, len(sys.argv))
    news_sites = json.load(open("news_sites.json"))
    translator = Translator.from_auth_data_paths(sys.argv[1], sys.argv[2])
    app.run(host="localhost", port=5000, debug=True)
