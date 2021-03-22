import glob
import datetime
import re
import os

import vcr
import tornado.ioloop
import tornado.httpserver
import tornado.web
from suds import Client
import requests

from baselayer.app.env import load_env
from baselayer.log import make_log


def get_cache_file():
    files = glob.glob("cache/test_server_recordings_*.yaml")
    today = datetime.date.today().isoformat()

    # If no cache files, just return a fresh one stamped for today
    if len(files) == 0:
        return f"cache/test_server_recordings_{today}.yaml"

    current_file = files[0]
    current_file_date = datetime.date.fromisoformat(
        re.findall(r"\d+-\d+-\d+", current_file)[0]
    )
    # Cache should be refreshed
    if (today - current_file_date).days > refresh_cache_days:
        # Delete old cache and return new file path
        os.remove(current_file)
        return f"cache/test_server_recordings_{today}.yaml"

    # Cache is still valid
    return current_file


class TestRouteHandler(tornado.web.RequestHandler):
    """
    This handler intercepts calls coming from SkyPortal API handlers which make
    requests to external web services (like the LT telescope) and wraps them in a
    vcr context so that requests are cached and played back. The handler will forward
    the request to the approriate "real" host, cache the results, and pass them back
    to the SkyPortal test API server.
    """

    def get(self):
        is_wsdl = self.get_query_argument('wsdl', None)
        cache = get_cache_file()
        with vcr.use_cassette(cache, record_mode="new_episodes") as cass:
            base_route = self.request.uri.split("?")[0]

            if (
                "test_server" in cfg
                and "redirects" in cfg["test_server"]
                and base_route in cfg["test_server.redirects"]
            ):
                real_host = cfg["test_server.redirects"][base_route]
                url = real_host + self.request.uri

                # Convert Tornado HTTPHeaders object to a regular dict
                headers = {}
                for k, v in self.request.headers.get_all():
                    if k in headers:
                        headers[k].append(v)
                    else:
                        headers[k] = [v]

                if is_wsdl is not None:
                    log(f"Forwarding WSDL call {url}")
                    Client(url=url, headers=headers, cache=None)
                else:
                    log(f"Forwarding GET call: {url}")
                    requests.get(url, headers=headers)

                # Get recorded document and pass it back
                response = cass.responses_of(
                    vcr.request.Request("GET", url, "", headers)
                )[0]
                self.set_status(
                    response["status"]["code"], response["status"]["message"]
                )
                for k, v in response["headers"].items():
                    # Content Length may change (for the SOAP call) as we overwrite the host
                    # in the response WSDL. Similarly, the response from this test server
                    # will not be chunked even if the real response was.
                    if k != "Content-Length" and not (
                        k == "Transfer-Encoding" and "chunked" in v
                    ):
                        self.set_header(k, v[0])

                if is_wsdl is not None:
                    # Override service location in the service definition
                    # so we can intercept the followup POST call
                    response_body = (
                        response["body"]["string"]
                        .decode("utf-8")
                        .replace(
                            real_host, f"http://localhost:{cfg['ports.test_server']}"
                        )
                    )
                else:
                    response_body = response["body"]["string"]

                self.write(response_body)

            else:
                self.set_status(500)
                self.write("Could not find test route redirect")

    def post(self):
        is_soap_action = "Soapaction" in self.request.headers
        cache = get_cache_file()
        with vcr.use_cassette(
            cache,
            record_mode="new_episodes",
            match_on=['uri', 'method', 'body'],
        ) as cass:
            if (
                "test_server" in cfg
                and "redirects" in cfg["test_server"]
                and self.request.uri in cfg["test_server.redirects"]
            ):
                real_host = cfg["test_server.redirects"][self.request.uri]
                url = real_host + self.request.uri

                if is_soap_action:
                    log(f"Forwarding SOAP method call {url}")

                # Convert Tornado HTTPHeaders object to a regular dict
                headers = {}
                for k, v in self.request.headers.get_all():
                    headers[k] = v

                requests.post(url, data=self.request.body, headers=headers)

                # Get recorded document and pass it back
                response = cass.responses_of(
                    vcr.request.Request("POST", url, self.request.body, headers)
                )[0]
                self.set_status(
                    response["status"]["code"], response["status"]["message"]
                )
                for k, v in response["headers"].items():
                    # The response from this test server will not be chunked even if
                    # the real response was
                    if not (k == "Transfer-Encoding" and "chunked" in v):
                        self.set_header(k, v[0])
                self.write(response["body"]["string"])

            else:
                self.set_status(500)
                self.write("Could not find test route redirect")


def make_app():
    return tornado.web.Application(
        [
            (".*", TestRouteHandler),
        ]
    )


if __name__ == "__main__":
    env, cfg = load_env()
    log = make_log("testserver")

    if "test_server" in cfg:
        app = make_app()
        server = tornado.httpserver.HTTPServer(app)
        port = cfg["test_server.port"]
        server.listen(port)

        refresh_cache_days = cfg["test_server.refresh_cache_days"]

        log(f"Listening for test HTTP requests on port {port}")
        tornado.ioloop.IOLoop.current().start()
