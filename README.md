#OpBot
This is an irc bot that gives people (that are on a whitelist) op when they join a channel.
It can also check the weather by using the yr.no service.  

##Setup
Change these values in `settings.conf` before usage:

```python
nick = BotNick
server = Irc.Server
port = IrcPort
channel = #IrcChannel
whitelist = ["nick1", "nick2"]
```

##Usage
- Run with python `python opbot.py`
- The bot needs op before it can give op to others
- The weather function can be called by typing `.weather [city]` in the channel
- City names and geonames are saved in a sqlite3 database. (`geoames.sql`)
- For more information on the weather service, please refer to https://github.com/KarlHerler/yr-py

