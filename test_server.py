import server3
from server3 import *

n_root = Router()

@url("/a", "GET")
def a(req, resp):
    print("Call a")
    resp.html("a")

@url("/a", "GET", n_root)
def aa(req, resp):
    print("Call new a")
    resp.html("new a")

@url("/b", "*")
def b(req, resp):
    print("Call b")
    resp.html("b")

@url("/b/:a", "GET")
def b_a(req, resp):
    print("call /b/:a, params: {}".format(req.url_params))
    resp.html("b")

@url("/c/*", "GET")
def c_all(req, resp):
    print("call c all, url", req.raw_url)
    resp.html("c")

@url("/b/:a/c/:b", "GET")
def b_a_c_b(req, resp):
    print("call /b/:a/c/:b, params: {}".format(req.url_params))
    resp.html("bacb")

@url("/", ["GET",  "POST"])
def index(req, resp):
    resp.json({"resp": "hello"})

def test():
    req = Request("GET /a HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /a/ HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("POST /b HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /b HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /b/ccc HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("POST /b/ddd HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /c/a HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /c/b HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    req = Request("GET /c/b/c HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

    
    req = Request("GET /b/ddd/c/aaasd HTTP/1.1\nHost: zmk.pw\nConnection: keep-alive")
    handle_request(req)

if __name__ == "__main__":
    s1 = init_server()
    s2 = init_server(8090, n_root)
    s1.join()
    s2.join()