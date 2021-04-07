import time

from server3 import *
import json
import urllib3
import os.path


def read_user_profile(user):
    filename = "./db/" + user + "_portfolio.json"
    if not os.path.exists(filename):
        data = {}
    else:
        with open(filename, 'r') as f:
            data = json.load(f)
    return data


pool_manager = urllib3.PoolManager()
API_KEY = "pk_81e6e804ceee4b32a2e96892a1d7a79d"


@url("/portfolio", "GET")
def portfolio(req, resp):
    username = req.headers.get("user")
    data = read_user_profile(username)
    pages_path = "./pages/portfolio/"
    with open(pages_path + "table_element.html", 'r') as te, open(pages_path + "portfolio.html", 'r') as template:
        page = template.read()
        table_element = te.read()
        inset_html = ""
        for stock, line in data.items():
            inset_html += table_element.format(
                **{"stock": stock, "quantity": "%.2f" % line[0], "price": "$%.2f" % line[1],
                   "gain": "%.2f%%" % compu_gain_loss(stock, line[1])})
        page = page % inset_html
    resp.html(page)


@url("/portfolio/update", "POST")
def portfolio_update(req, resp):
    user = req.headers.get("user")
    stock = req.post_params.get("stock_symbol")
    quantity = int(req.post_params.get("quantity"))
    price = int(req.post_params.get("price"))
    data = read_user_profile(user)
    if valid_stock(stock):
        update_stock(data, stock, quantity, price)
    else:
        resp.error(400, "stock symbols not found.")
        return
    with open("./db/%s_portfolio.json" % user, "w") as f:
        json.dump(data, f)
    resp.redirect("/portfolio")


request_urls = {"SYMBOLS": {"filename": "./caches/symbols.json",
                            "url": "https://cloud.iexapis.com/stable/ref-data/symbols?token="},
                "QUOTES": {"filename": "./caches/QUOTES.json",
                           "url": "https://cloud.iexapis.com/stable/stock/{symbol}/quote?token="}}


def load_ref(tag, expire_time=24 * 60 * 60 * 1000):
    ref = request_urls[tag]
    if os.path.exists(ref["filename"]):
        with open(ref["filename"], 'r') as f:
            symbols = json.load(f)
    else:
        symbols = {}
    if time.time() - symbols.get("last_request_time", 0) > expire_time:
        res = pool_manager.request("GET", ref["url"] + API_KEY)
        if res.status == 200:
            valid_stocks = json.loads(res.data)
            new_cache = {}
            for line in valid_stocks:
                new_cache[line["symbol"]] = line
            symbols = {"data": new_cache, "last_request_time": time.time()}
            with open(tag["filename"], 'w') as f:
                json.dump(symbols, f)
        else:
            return False
    return symbols


def valid_stock(stock) -> bool:
    return stock in load_ref("SYMBOLS").get("data")


def update_stock(data, stock, quantity, price):
    if stock in data.keys():
        line = data[stock]
        new_quantity = quantity + line[0]
        line[1] = (line[1] * line[0] + quantity * price) / new_quantity
        line[0] = new_quantity
    else:
        data[stock] = [quantity, price]


def compu_gain_loss(stock, price):
    if not valid_stock(stock):
        return 0
    res = pool_manager.request("GET", request_urls["QUOTES"]["url"].format(symbol=stock) + API_KEY)
    if res.status == 200:
        quotes = json.loads(res.data)
    else:
        return 0
    latest_price = quotes.get("latestPrice")
    return (latest_price - price) / price * 100


if __name__ == "__main__":
    portfolio(None, None)
