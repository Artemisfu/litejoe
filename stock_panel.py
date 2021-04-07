from server3 import *
import base64
from matplotlib import pyplot as plt
import pandas as pd
import matplotlib.dates as mdate
import matplotlib as mpl
import requests
import numpy as np


def isLogin(request):
    token = request.cookies.get("token")
    if not token:
        return None
    token = base64.b64decode(token).decode()
    user, password = token.split(":")
    if user != password:
        return None
    return user


class UserMiddleWare(MiddleWare):
    def pre_request(self, req: Request, resp: Response):
        user = isLogin(req)
        if user is not None:
            req.headers["user"] = user
        return True


@url("/login", "GET")
def login(req, resp):
    auth = req.headers.get("Authorization")
    if not auth:
        resp.basic_auth("Please Login")
        return
    auth_type, token = auth.split()
    if auth_type.lower() != 'basic':
        resp.error(406)
        return
    decode_token = base64.b64decode(token).decode()
    user, password = decode_token.split(":")
    if user != password:
        resp.basic_auth("Error username or password")
        return
    resp.add_cookie(CookieItem("token", token))
    resp.redirect("/")


@url("/logout", "GET")
def logout(req, resp):
    resp.remove_cookie("token")
    resp.redirect("/")


@url("/", "GET")
def index(req, resp):
    user = req.headers.get("user")
    if user is None:
        resp.redirect("/login")
        return

    resp.html("Welcome to go to main page: {}".format(user), 200)


@url("/cookies", "GET")
def cookies(req, resp):
    print(req.headers["Cookie"])
    resp.json(req.cookies, 200)


def draw_img(stock_name, content):
    data = json.loads(content)
    dates = [i['date'] for i in data]
    values = [i['close'] for i in data]
    time = pd.to_datetime(dates)
    fig = plt.figure(figsize=(12, 9))
    ax = plt.subplot(211)
    ax.xaxis.set_major_formatter(mdate.DateFormatter('%m %b'))
    plt.xticks(pd.date_range(time[0], time[-1], freq='20D')[1:])
    ax.plot(time, values, color='r')

    _, yv = np.meshgrid(np.linspace(0, 1, 210), np.linspace(0, 1, 90))
    xlims = mdate.date2num([time[0], time[-1]])
    extent = [xlims[0], xlims[1], min(values), max(values)]
    ax.imshow(yv, cmap=mpl.cm.Reds, origin='lower', alpha=0.5, aspect='auto',
              extent=extent)
    ax.fill_between(time, values, max(values), color='white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.savefig("imgs/{}.png".format(stock_name))


@url("/stock", ["GET", "POST"])
def stock(req, resp):
    app_token = "pk_81e6e804ceee4b32a2e96892a1d7a79d"

    symbol = req.params.get("symbol")
    if not symbol:
        symbol = req.post_params.get("symbol")

    with open("pages/stock/stock.html", 'r') as f:
        page = f.read()

    if symbol is not None:
        r = requests.get(
            "https://cloud.iexapis.com/stable/stock/{}/chart/ytd?chartCloseOnly=true&token={}".format(symbol,
                                                                                                      app_token))
        body = r.content
        if r.status_code != 200:
            page = page.format(input_value=symbol, error_display="block", error_info=body.decode(), img_url="",
                               img_display="none")
            resp.html(page, r.status_code)
            return
        draw_img(symbol, body)
        page = page.format(input_value=symbol, error_display="none", error_info="",
                           img_url="/imgs/{}.png".format(symbol),
                           img_display="block")
        resp.html(page)
        return
    page = page.format(input_value="", error_display="block", error_info="Input Stock Symbol and press <enter>",
                       img_url="", img_display="none")
    resp.html(page)


@url("/imgs/:img_name", "GET")
def imgs(req, resp):
    img_name = req.url_params["img_name"]
    try:
        with open("imgs/{}".format(img_name), "rb") as f:
            data = f.read()

        file_type = img_name.split(".")[-1]
        if file_type == "jpg":
            file_type = "jpeg"
        resp.headers["content - type"] = "image/{}".format(file_type)
        resp.body = data
        resp.status = 200
    except FileExistsError:
        resp.error(404)
        return


if __name__ == "__main__":
    s = Server()
    s.add_middleware(UserMiddleWare())
    s.start()
    s.join()
