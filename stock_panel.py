from server3 import *
import base64


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

    resp.html("Welcome to go to main page: {}".format(user), 200)


@url("/cookies", "GET")
def cookies(req, resp):
    print(req.headers["Cookie"])
    resp.json(req.cookies, 200)


if __name__ == "__main__":
    from function import *
    s = Server()
    s.add_middleware(UserMiddleWare())
    s.start()
    s.join()
