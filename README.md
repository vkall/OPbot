#OpBot
This is an irc bot with the following functionalities: 
- Gives people that are on a whitelist op when they join the channel.
- Checks the weather by using the yr.no service.  `.w [city]`
- Converts currencies using the http://www.google.com/finance/converter service. `.ex [amount] [fromCurrency] [toCurrency]`

##Setup
Change these values in `settings.conf` before usage:

```python
nick = BotNick
server = Irc.Server
port = IrcPort
channel = #IrcChannel
whitelist = nick1,nick2,nick3
```

##Usage
- Run with python `python opbot.py`
- The bot needs op before it can give op to others
- The weather function can be called by typing `.weather [city]` in the channel
- For more information on the weather service, please refer to https://github.com/KarlHerler/yr-py

##Database
- For the weather service we need correct geonames for all cities.
- City names and geonames are saved in a sqlite3 database. (`geonames.sql`)
- The database has one table called cities. It consists of two varchar fields: city and geoname.

Example data:

```
city              geoname                                
----------------  ---------------------------------------
sutton-coldfield  United_Kingdom/England/Sutton_Coldfield
gillingham        United_Kingdom/England/Gillingham~26486
worthing          United_Kingdom/England/Worthing~2633521
hastings          United_Kingdom/England/Hastings        
london            United_Kingdom/England/London          
birmingham        United_Kingdom/England/Birmingham
```

