# FatumBot.py

A Fatum Bot inspired Interface Class for the Randonautica API, to be used in chatbot implementations. Requires a valid Randonautica API token.

## Dependencies

The class requires the *Requests* module. Install by:

```
$ pip install requests
```

## Usage

```python
>>> from dotenv import load_dotenv
>>> from fatumbot import FatumBot

>>> # load the Randonautica API token
>>> load_dotenv()
>>> RNDO_TOKEN = os.getenv('RNDO_TOKEN')

>>> # instantiate the class and generate points
>>> r = FatumBot(RNDO_TOKEN)
>>> coords = stringToGeo("29.97913,31.13427")
>>> r.setLocation('user1', coords['lat'], coords['lon'])

['Location set with radius 2000.\nUse `/radius <radius>` if you want to change your search radius.']

>>> r.setRadius('user1', 1800)

['Your search radius has been set to 1800 meters!']

>>> r.fetchBlindspot('user1', 'quantum')

['Blindspot found:\nEntropy: `temporal`\nLatitude: `29.9812`\nLongitue: `31.1439`\nDistance: `958.53`m\nBearing: `76.22`°', 'geo:29.9812,31.1439']

>>> r.fetchAnomaly('user1', 'attractor')

['Attractor anomaly found:\nEntropy: `temporal`\nLatitude: `29.9812`\nLongitue: `31.1439`\nPower: `3.26`\nRadius: `67`m\nZ-score: `3.56`\nDistance: `958.53`m\nBearing: `76.22`°', 'geo:29.9812,31.1439']
```
