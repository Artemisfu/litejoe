from server3 import *
import json

root = Router()


@url("/portfolio", "GET", root)
def portfolio(req, resp):
    # username = req.headers.get("username")
    username = "abc"
    data = {}
    with open("./db/" + username + "_portfolio.json", "r") as f:
        data = json.load(f)
    pages_path = "./pages/portfolio/"
    page = ""
    with open(pages_path + "table_element.html", 'r') as te, open(pages_path + "portfolio.html", 'r') as template:
        page = template.read()
        table_element = te.read()
        inset_html = ""
        for stock, line in data.keys():
            inset_html += table_element.format({"stock": stock, "quantity": line[0], "price": line[1], "gain": line[2]})
        page = page.format(inset_html)
    resp.html(page)


@url("/portfolio/update", "POST", root)
def portfolio_update(req, resp):
    pass


if __name__ == "__main__":
    portfolio(None, None)
