from bs4 import BeautifulSoup
import requests


class DataCollection:
    BASEURL = 'https://my.gcc.edu'

    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__session = None
        self.response = None

    def http_get(self, url, **kwargs):
        if self.__session is None:
            self.create_session()
        self.response = self.__session.get(url, **kwargs)
        return self.response

    def http_post(self, url, **kwargs):
        if self.__session is None:
            self.create_session()
        self.response = self.__session.post(url, **kwargs)
        return self.response

    def ensure_screen(self, url):
        if self.response is None or self.response.url != url:
            self.http_get(url)

    def to_url(self, path):
        if path.startswith(self.BASEURL):
            return path
        path = '/' + path.lstrip('/')
        return self.BASEURL + path

    def make_soup(self, features='html.parser'):
        """Makes a BeautifulSoup object for the last GET or POST response.

        :param features: - Desirable features of the parser to be
         used. This may be the name of a specific parser ("lxml",
         "lxml-xml", "html.parser", or "html5lib") or it may be the
         type of markup to be used ("html", "html5", "xml"). It's
         recommended that you name a specific parser, so that
         Beautiful Soup gives you the same results across platforms
         and virtual environments. (defaults to html.parser)

        :return: the BeautifulSoup object or None if no response exists
        """
        if self.response is not None:
            return BeautifulSoup(self.response.text, features=features)
        return None

    def prepare_payload(self, payload=None, postback: str=None, search=''):
        """This formats a payload dictionary to include within POST and GET requests.

        https://my.gcc.edu/ uses the values of hidden html input tags to keep track
        of the context of actions. It requires the values of those tags to be attached
        to the payload, so this method automatically takes care of adding in those values.

        :param payload: - the dictionary to prepare (defaults to making a new dictionary)
        :param postback: - an optional postback string "javascript:__doPostBack('eventTargetValue','eventArgumentValue')"
        :param search: - the default search parameter (set to None to exclude search)
        :return: the newly prepared payload dictionary
        """

        # default to a new empty dictionary if none was provided
        if payload is None:
            payload = {}

        # mygcc uses the values of several hidden html tags to track the
        # current viewstate of the user in order to determine context.
        # This fetches and includes those tags within the payload.
        soup = self.make_soup()
        if soup is not None:
            for hidden_input in soup.find_all('input', {'type': 'hidden'}):
                input_name = hidden_input.get('name')
                input_value = hidden_input.get('value')
                if input_name is not None and input_value is not None:
                    payload[input_name] = input_value

        # If a formatted postback string was included, we need to parse it
        # this string tells mygcc what action the user is attempting to do.
        if postback is not None:
            # javascript:__doPostBack('eventTargetValue','eventArgumentValue')
            postback = postback.replace('javascript:__doPostBack(', '')
            postback = postback.replace(')', '')
            postback = postback.replace("'", '')
            postback_elements = postback.split(',', 1)
            if len(postback_elements) == 2:
                payload['__EVENTTARGET'] = postback_elements[0]
                payload['__EVENTARGUMENT'] = postback_elements[1]

        # This empty search tag is included in most requests, so we
        # automatically include it unless told otherwise.
        if search is not None:
            payload['siteNavBar$ctl00$tbSearch'] = search

        return payload

    def create_session(self):
        """Creates a new Session and performs login"""
        url = self.to_url('/ICS/')
        payload = {
            '_scriptManager_HiddenField': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR': '',
            '___BrowserRefresh': '',
            'siteNavBar$ctl00$tbSearch': '',
            'userName': self.__username,
            'password': self.__password,
            'siteNavBar$btnLogin': 'Login'}
        self.__session = requests.Session()
        self.response = self.__session.post(url, data=payload)
