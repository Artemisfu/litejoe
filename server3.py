#This is a simple HTTP server which listens on port 8080, accepts connection request, and processes the client request 
#in sepearte threads. It implements basic service functions (methods) which generate HTTP response to service the HTTP requests. 
#Currently there are 3 service functions; default, welcome and getFile. The process function maps the requet URL pattern to the service function.
#When the requested resource in the URL is empty, the default function is called which currently invokes the welcome function.
#The welcome service function responds with a simple HTTP response: "Welcome to my homepage".
#The getFile service function fetches the requested html or img file and generates an HTTP response containing the file contents and appropriate headers.

#To extend this server's functionality, define your service function(s), and map it to suitable URL pattern in the process function.

#This web server runs on python v3
#Usage: execute this program, open your browser (preferably chrome) and type http://servername:8080
#e.g. if server.py and broswer are running on the same machine, then use http://localhost:8080



from socket import *
import threading
from urllib import parse
import json
import traceback
import datetime

def datetime_to_http_data(date: datetime.datetime):
    def pad_num(num):
        if num < 10:
            return '0' + str(num)
        return str(num)
    utc_date = date.astimezone(datetime.timezone.utc)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" ]
    months_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return "{}, {} {} {} {}:{}:{} GMT".format(day_names[utc_date.weekday()], pad_num(utc_date.day), months_names[utc_date.month], utc_date.year, pad_num(utc_date.hour), pad_num(utc_date.minute), pad_num(utc_date.second))

class CookieItem:
    # same_site could be Strict and Lax
    def __init__(self, key, value, expire=None, max_age=None, domain=None, path=None, secure=False, http_only=False, same_site="Strict"):
        self.key = key
        self.value = value
        self.expire = expire
        self.max_age = max_age
        self.domain = domain
        self.path = path
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

    def __str__(self):
        c = "{}:{}".format(self.key, self.value)
        if self.expire is not None:
            pass


class Response:
    STATUS = {'100': 'Continue',
            '101': 'Switching Protocol',
            '102': 'Processing',
            '103': 'Early Hints',
            '200': 'OK',
            '201': 'Created',
            '202': 'Accepted',
            '203': 'Non-Authoritative Information',
            '204': 'No Content',
            '205': 'Reset Content',
            '206': 'Partial Content',
            '207': 'Multi-Status',
            '208': 'Already Reported',
            '226': 'IM Used',
            '300': 'Multiple Choice',
            '301': 'Moved Permanently',
            '302': 'Found',
            '303': 'See Other',
            '304': 'Not Modified',
            '307': 'Temporary Redirect',
            '308': 'Permanent Redirect',
            '400': 'Bad Request',
            '401': 'Unauthorized',
            '403': 'Forbidden',
            '404': 'Not Found',
            '405': 'Method Not Allowed',
            '406': 'Not Acceptable',
            '407': 'Proxy Authentication Required',
            '408': 'Request Timeout',
            '409': 'Conflict',
            '410': 'Gone',
            '411': 'Length Required',
            '412': 'Precondition Failed',
            '413': 'Payload Too Large',
            '414': 'URI Too Long',
            '415': 'Unsupported Media Type',
            '416': 'Range Not Satisfiable',
            '417': 'Expectation Failed',
            '418': "I'm a teapot",
            '421': 'Misdirected Request',
            '422': 'Unprocessable Entity',
            '423': 'Locked',
            '424': 'Failed Dependency',
            '425': 'Too Early',
            '426': 'Upgrade Required',
            '428': 'Precondition Required',
            '429': 'Too Many Requests',
            '431': 'Request Header Fields Too Large',
            '451': 'Unavailable For Legal Reasons',
            '500': 'Internal Server Error',
            '501': 'Not Implemented',
            '502': 'Bad Gateway',
            '503': 'Service Unavailable',
            '504': 'Gateway Timeout',
            '505': 'HTTP Version Not Supported',
            '506': 'Variant Also Negotiates',
            '507': 'Insufficient Storage',
            '508': 'Loop Detected',
            '510': 'Not Extended',
            '511': 'Network Authentication Required'}

    
    def __init__(self, request):
        self.request = request
        self.status = -1
        self.headers = {}
        self.body = ""
        self.http_version = "HTTP/1.1"
        self.add_defult_headers()
        self.cookies = {}

    def add_defult_headers(self):
        self.headers["content-language"] = "en"

    def json(self, d, status = 200):
        self.body = json.dumps(d)
        self.headers["Content-Type"] = "application/json;charset=UTF-8"
        self.status = status

    def html(self, t, status = 200):
        self.body = t
        self.status = status
        self.headers["Content-Type"] = "text/html;charset=UTF-8"
        
    def error(self, status):
        status_info = self.STATUS.get(str(status), "NOT DEFINE")
        self.html("<h1>{} {}</h1>".format(status, status_info), status)

    def basic_auth(self, title):
        self.headers["WWW-Authenticate"] = "Basic realm=\"{}\"".format(title)
        self.status=401

    def redirect(self, url):
        self.status=302
        self.headers["Location"] = url

    def add_cookies(self, key, values):
        self.cookies[key] = values

    def encode(self):
        status = self.status
        if status == -1:
            status = 202
        status_info = self.STATUS.get(str(status), "NOT DEFINE")
        bodylen = len(self.body)
        self.headers["Content-Length"] = bodylen
        header_str = "{} {} {}".format(self.http_version, status, status_info) + '\r\n' + "\r\n".join(["{}:{}".format(i, self.headers[i]) for i in self.headers])
        for k in self.cookies:
            header_str += "\r\nSet-Cookie:{}={}".format(k, self.cookies[k])
        return (header_str + "\r\n\r\n" + self.body + "\r\n").encode()
        

class Request:
    def __init__(self, message):
        print(message)
        m = message.split("\r\n\r\n", 1)
        header, body = "", ""
        if len(m) == 1:
            m = m.split("\n\n", 1)                
            header = m[0]
            if len(m) > 1:
                body = m[1]
        elif len(m) >= 2:
            header = m[0]
            body = m[1]
        body = body.strip()
        lines = header.split("\n")
        headers = {i[0] :i[1] for i in map(lambda x: [i.strip() for i in x.split(":", 1)], lines[1:])}
        method, url, http_version = lines[0].split()
        self.http_version = http_version
        self.headers = headers
        self.method = method.upper()
        self.raw_url = url
        self.url = parse.urlparse(url)
        self.path = self.url.path
        self.params = {i[0]: i[1] for i in parse.parse_qsl(self.url.query)}
        self.body = body
        self.url_params={}
        cookies = self.headers["Cookie"]
        self.cookies = {i[0]: i[1] for i in map(lambda x: list(map(lambda y: y.strip(), x.split("=", 1))), cookies.split(";"))}


def not_found(req, resp):
    resp.html("<html><h1>404 Not Found</h1><h2>Sorry, The page request is Not Found.</h2></html>", 404)



class Router:
    GROUP = 1
    FUNC = 2
    NAMED_LIST = 3
    NAMED_GROUP = 4
    HTTP_METHODS = set(["GET", "POST", "HEAD", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"])
    def __init__(self, type=GROUP, param_name = "", top = False):
        self.routes = {}
        self.type = type
        self.functions = {}
        self.named_list = []
        self.param_name = param_name
        self.has_not_found = False

    
    def bind_not_found(self, func=not_found):
        if not self.has_not_found or func != not_found:
            self.add_url("*", not_found, ['*'])
            self.has_not_found = True

    def bind_func(self, methods, func):
        for m in methods:
            m = m.upper()
            if m in self.functions:
                    raise IndexError("{} already declare".format(m))
            if m in self.HTTP_METHODS or m == "*":
                self.functions[m] = func

    def match_func(self, method):
        m = method.upper()
        if m in self.functions:
            return self.functions[m]
        if "*" in self.functions:
            return self.functions['*']

    @staticmethod
    def split_path(path):
        if len(path) == 0:
            return "", ""
        start_index = 1 if path[0] == '/' else 0
        slash_index = path.find('/', start_index)
        if slash_index == -1:
            slash_index = len(path)
        f = path[start_index:slash_index]
        s = path[slash_index:]
        return f, s

    def add_url(self, url, func, methods):
        if len(url) == 0 or url == "/":
            self.routes[""] = Router(self.FUNC)
            self.routes[""].bind_func(methods, func)
            return
        f, s = self.split_path(url)

        if not f.startswith(":"):    
            if f not in self.routes:
                self.routes[f] = Router(self.GROUP)

            self.routes[f].add_url(s, func, methods)
            return
        
        if ":" not in self.routes:
            self.routes[":"] = Router(self.NAMED_LIST)
        r = Router(self.NAMED_GROUP, param_name=f[1:])
        self.routes[":"].named_list.append(r)
        r.add_url(s, func, methods)


    def match_url(self, request):
        path = request.path
        func, params = self.__match_url(path, request.method)
        request.url_params = params
        return func
        
    def __match_url(self, path, method):
        if self.type == self.FUNC:
            return self.match_func(method), {}
        if self.type == self.NAMED_LIST:
            for i in self.named_list:
                func, params = i.__match_url(path, method)
                if func != None:
                    return func, params
            return None, {}
        f, s = self.split_path(path)
        func, params = None, {}

        if self.type == self.NAMED_GROUP:
            nf, ns = self.split_path(s)
            if nf in self.routes:
                func, params = self.routes[nf].__match_url(ns, method)
            

        if func is None and f in self.routes:
            func, params = self.routes[f].__match_url(s, method)

        
        if func is None and ":" in self.routes:
            func, params = self.routes[":"].__match_url(path, method)

        if func is None and "*" in self.routes:
            func, params = self.routes["*"].__match_url(s, method)
        
        if func is not None and self.type == self.NAMED_GROUP:
            params[self.param_name] = f
        
        return func, params


root = Router()

def url(url, methods, root=root):
    if type(methods) is str:
        methods = [methods]
    def decorator(func):
        root.add_url(url, func, methods)
        return func
    return decorator

def handle_request(request, root=root):
    func = root.match_url(request)
    resp =  Response(request)
    if func is None:
        print("Func not implament")
    else:
        try:
            func(request, resp)
        except Exception as e:
            print("Handle request Error, request: {}, {}".format(request, e))
            traceback.print_exc()
            resp.error(500)
    print("Request [{}], Method: {}, resp status: {}".format(request.raw_url, request.method, resp.status))
    return resp


class ProcessHandler(threading.Thread):
    def __init__(self, connectionSocket, root):
        threading.Thread.__init__(self)
        self.connectionSocket = connectionSocket
        self.root = root

    def run(self):
        self.process()

    #We process client request here. The requested resource in the URL is mapped to a service function which generates the HTTP reponse 
    #that is eventually returned to the client. 
    def process(self) :    
        print("Start process request!")
        # Receives the request message from the client
        message = self.connectionSocket.recv(1024 * 1024).decode()


        if len(message) > 1:


            # Extract the path of the requested object from the message
            # Because the extracted path of the HTTP request includes
            # a character '/', we read the path from the second character


            request = Request(message)

            response = handle_request(request, self.root)


            self.connectionSocket.send(response.encode())
        # Close the client connection socket
        self.connectionSocket.close()





class ServerRunner(threading.Thread):
    def __init__(self, port=8080, root=root):
        threading.Thread.__init__(self)
        self.root = root
        self.port = port

    def run(self):
        self.init_server()

    def init_server(self):
        self.root.bind_not_found()
        serverSocket = socket(AF_INET, SOCK_STREAM)

        serverPort = self.port
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(("", serverPort))

        serverSocket.listen(5)
        print('The server is running')    

        #Main web server loop. It simply accepts TCP connections, and get the request processed in seperate threads.
        while True:
            
            # Set up a new connection from the client
            connectionSocket, addr = serverSocket.accept()
            #Clients timeout after 60 seconds of inactivity and must reconnect.
            connectionSocket.settimeout(60)
            # start new thread to handle incoming request
            h = ProcessHandler(connectionSocket, self.root)
            h.start()

def init_server(port=8080, root=root):
    runner = ServerRunner(port, root)
    runner.start()
    return runner

if __name__ == "__main__":
    # main()
    init_server()



