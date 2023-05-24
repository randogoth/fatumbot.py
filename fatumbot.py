import json
import os
import time
import re
import requests
from requests.structures import CaseInsensitiveDict

class FatumBot:
    """
    Fatum Bot API Class
    ~~~~~~~~~~~~~~~~~~~

    Fatum Bot inspired Interface for the Randonautica API, to be used in chatbot implementations.

    >>> from fatumbot import FatumBot
    >>> r = FatumBot()
    >>> coords = stringToGeo("29.97913,31.13427")
    >>> r.setLocation(<userid>, coords['lat'], coords['lon'])
    >>> r.setRadius(<userid>, <radius>)
    >>> r.fetchBlindspot(<userid>, <type>)
    >>> r.fetchAnomaly(<userid>, <type>)

    :copyright: (c) 2022 by randogoth
    :license: MIT, see LICENSE for more details.
    """

    DB = {}

    RNDO_TOKEN = ''
    QRNG_URL = 'https://api.randonautica.com/v1'
    DEFAULT_PARAMS = 'latitude={}&longitude={}&radius={}&source={}'
    DEFAULT_RADIUS = 2000
    DEFAULT_RADIUS_MIN = 1000
    DEFAULT_RADIUS_MAX = 10000
    DEFAULT_SOURCE = 'temporal'
    SOURCES = ['temporal', 'pseudo']
    POINT_TYPE = ['Blindspot', 'Attractor', 'Void']
    REQUEST_LIMIT = 10
    COORDS_PATTERN = r'([-+]?\d*\.?\d+)[,| ] ?([-+]?\d*\.?\d+)'
    DB_FILENAME = 'database.json'

    # Set Strings

    MSG_NO_TOKEN = 'No Randonautica API Token provided. Aborting.'
    MSG_SET_LOCATION = 'Please set your location first.\nOn the Telegram mobile-app use the in-built function📎 > `Send location`.\nYou can also provide a `<Google Maps URL>`.\nLatitude and Longitude can also be provided in this format: `28.3809,-16.5379`'
    MSG_DEFAULT_RADIUS = 'Location set with radius 2000.\nUse `/radius <radius>` if you want to change your search radius.'
    MSG_SET_RADIUS_LIMITS = f'Please provide a radius in meters.\nMin. {DEFAULT_RADIUS_MIN} and max. {DEFAULT_RADIUS_MAX}.'
    MSG_RADIUS_SET = 'Your search radius has been set to {} meters!'
    MSG_SOURCE_SET = 'Your entropy source has been set to "{}"!'
    MSG_SOURCE_INVALID = 'An entropy source with the name "{}" does not exist! Using "{}"'
    MSG_SOURCE_AVAILABLE = 'The following sources are available: {}'
    MSG_RATE_LIMIT_REACHED = 'Sorry, you are requesting too many points in a too short time period.\nPlease try again in {} seconds.'
    MSG_ANOMALY_FOUND = '{} anomaly found:\nEntropy: `{}`\nLatitude: `{}`\nLongitue: `{}`\nPower: `{:.2f}`\nRadius: `{:.2f}`m\nZ-score: `{:.2f}`\nDistance: `{:.2f}`m\nBearing: `{:.2f}`°'
    MSG_BLINDSPOT_FOUND = 'Blindspot found:\nEntropy: `{}`\nLatitude: `{}`\nLongitue: `{}`\nDistance: `{:.2f}`m\nBearing: `{:.2f}`°'
    MSG_NO_ANOMALY_FOUND = 'Sorry, no anomaly could be found. Please increase your search radius or try again.'

    def __init__(self, token):
        if not token:
            print(self.MSG_NO_TOKEN)
        else:
            self.RNDO_TOKEN = token
            with open('help.txt', 'r') as f:
                self.MSG_HELPTEXT = f.read()
            if os.path.isfile(self.DB_FILENAME):
                with open(self.DB_FILENAME, 'r') as f:
                    self.DB = json.load(f)

    # Private Methods

    def __fromAPI(self, endpoint, params):
        """fetches data from Randonautica API as GET request using the API token for authorization and returns JSON"""
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {self.RNDO_TOKEN}"
        response = requests.get(f'{self.QRNG_URL}{endpoint}?{params}', headers=headers)
        if response.ok:
            return json.loads(response.text)
        else:
            return json.loads(json.dumps({ 'status' : response.status_code, 'error' : response.text }))

    def __setDefaultParams(self, user):
        """returns the default parameter string needed for every API call populated with user dataset"""
        return self.DEFAULT_PARAMS.format(
            user['loc']['lat'], 
            user['loc']['lon'], 
            user['rad'], 
            user['src']
        )

    def __rateLimit(self, id):
        """sets and returns the timeout from the last user interaction in seconds"""
        user = self.__fromDB(id)
        timestamp = int(time.time())
        if 'ts' in self.DB[id]:
            timeout = timestamp - user['ts']
            if timeout < self.REQUEST_LIMIT:
                return timeout
        self.__toDB(id, 'ts', timestamp)
        return self.REQUEST_LIMIT

    def __fromDB(self, id):
        """fetches dataset for a given user ID"""
        if id in self.DB:
            return self.DB[id]
        else:
            return False

    def __toDB(self, id, field, value):
        """changes dataset field for a given user ID"""
        if id in self.DB:
            self.DB[id][field] = value
            with open(self.DB_FILENAME, 'w+') as f: 
                f.write(json.dumps(self.DB, indent=4))
            return True
        else:
            return False

    def __initUserLocation(self, id, loc, rad, src):
        """initializes default fields for a user ID dataset or updates location"""
        if id not in self.DB:
            self.DB.update({ 
                id: {
                    'loc' : loc,
                    'rad' : rad, 
                    'src' : src 
                }
            })
        else:
            self.DB[id]['loc'] = loc

    # Fatum User Session Setup

    def setLocation(self, id, lat, lon):
        """
        sets user location in dataset to a given set of coordinates
        
        :param any id: Unique user identifier
        :param float lat: Decimal center latitude of search location
        :param float lon: Decimal center longitude of search location

        returns a list of reply strings
        
        """
        location = { 'lat' : lat, 'lon' : lon }
        if not self.__toDB(id, 'loc', location ):
            self.__initUserLocation(id, location, self.DEFAULT_RADIUS, self.DEFAULT_SOURCE)
        return [ self.MSG_DEFAULT_RADIUS ]

    def setRadius(self, id, radius):
        """
        sets user radius in dataset to a given value in meters
        
        :param any id: Unique user identifier
        :param int radius: Search radius in meters

        returns a list of reply strings
        
        """
        if int(radius) < self.DEFAULT_RADIUS_MIN or int(radius) > self.DEFAULT_RADIUS_MAX:
            return [ self.MSG_SET_RADIUS_LIMITS ]
        if self.__toDB(id, 'rad', radius ):
                return [ self.MSG_RADIUS_SET.format(radius) ]
        else:
            return [ self.MSG_SET_LOCATION ]

    def setSource(self, id, source):
        """
        sets entropy source in dataset to user selected one that is available
        
        :param any id: Unique user identifier
        :param str source: Either 'pseudo' or 'temporal' as entropy source for the point generation

        returns a list of reply strings

        """
        if source in self.SOURCES:
            if self.__toDB(id, 'src', source ):
                return [ self.MSG_SOURCE_SET.format(source) ]
            else:
                return [ self.MSG_SET_LOCATION ]
        else:
            user = self.__fromDB(id)
            if user:
                return [ self.MSG_SOURCE_INVALID.format(source, user['src']), self.MSG_SOURCE_AVAILABLE.format(self.SOURCES) ]
            else:
                return [ self.MSG_SET_LOCATION ]

    def fetchAnomaly(self, id, type):
        """
        fetches an Anomaly type point from the Randonautica API and returns message list

        :param any id: Unique user identifier
        :param str type: Type of anomaly 'attractor', 'void', 'power', or 'pair'

        returns a list of reply strings
        
        """
        user = self.__fromDB(id)
        if user:
            req = self.__rateLimit(id)
            if req < self.REQUEST_LIMIT:
                return [ self.MSG_RATE_LIMIT_REACHED.format(self.REQUEST_LIMIT - req) ]
            params = self.__setDefaultParams(user)
            json = self.__fromAPI('/gen/anomaly', params + f'&type={type}')
            if 'result' in json:
                point = json['result']['points'][0]
                return [
                    self.MSG_ANOMALY_FOUND.format(
                    self.POINT_TYPE[int(point['type'])],
                    user['src'],
                    point['location']['latitude'], 
                    point['location']['longitude'],
                    point['power'],
                    point['radius'],
                    point['z_score'],
                    point['distance'],
                    point['bearing']
                    ),
                    f"@@{point['location']['latitude']},{point['location']['longitude']}"
                ]
            else:
                if 'error' in json:
                    if json['status'] == 418:
                        return [ self.MSG_NO_ANOMALY_FOUND ]
                    else:
                        return [ json['error'] ] 
        else:
            return [ self.MSG_SET_LOCATION ]

    def fetchBlindspot(self, id, type):
        """
        fetches a Blindspot type point from the Randonautica API and returns message list
        
        :param any id: Unique user identifier
        :param str type: Type of blindspot 'quantum', 'pseudo'

        returns a list of reply strings
        
        """
        user = self.__fromDB(id)
        if user:
            req = self.__rateLimit(id)
            if req < self.REQUEST_LIMIT:
                return [ self.MSG_RATE_LIMIT_REACHED.format(self.REQUEST_LIMIT - req) ]
            source = user['src']
            esrc = user['src']
            if type == 'pseudo':
                esrc = 'pseudo'
                self.__toDB(id, 'src', 'pseudo')
            user = self.__fromDB(id)
            params = self.__setDefaultParams(user)
            json = self.__fromAPI('/gen/blindspot', params )
            self.__toDB(id, 'src', source)
            if 'result' in json:
                point = json['result']['points'][0]
                return [ 
                    self.MSG_BLINDSPOT_FOUND.format(
                        esrc,
                        point['location']['latitude'],
                        point['location']['longitude'],
                        point['distance'],
                        point['bearing']
                    ),
                    f"geo:{point['location']['latitude']},{point['location']['longitude']}"
                ]
            else:
                if 'error' in json:
                    return [ json['error'] ] 
        else:
            return [ self.MSG_SET_LOCATION ]

    def stringToGeo(self, string):
            """
            gets decimal latitude and longitude values from any string containing 
            'xx.xxxxx,yy.yyyyy' formatted coordinates
            
            :param str string: String containing a decimal lat, lon coordinate
            
            """
            coords_re = re.compile(self.COORDS_PATTERN)
            if coords_re.search(string):
                return { 
                    'lat' : coords_re.search(string).group(1), 
                    'lon' : coords_re.search(string).group(2) 
                }
            else:
                return False
