#OpBot
This is a irc bot that gives people (that are on a whitelist) op when they join a channel. 

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
Run with python
`python opbot.py`