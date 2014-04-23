import socket
import time
import logging
import logging.config
import ConfigParser
import sqlite3
from yr import yr

class OpBot:

	def __init__(self):
		# Irc settings
		self.conf = ConfigParser.RawConfigParser()
		self.conf.read("settings.conf")
		self.nick = self.conf.get("settings", "nick")
		self.server = self.conf.get("settings", "server")
		self.port = self.conf.getint("settings", "port")
		self.channel = self.conf.get("settings", "channel")
		self.whitelist = self.conf.get("settings", "whitelist")
		self.init_socket()
		# Setup logging
		logging.config.fileConfig(self.conf.get("settings", "logconfig"))
		self.logger = logging.getLogger(__name__)
	
	def init_socket(self):
		self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ircsock.settimeout(4*60) # 4 min

	def execute(self):
		self.connect()
		# Main loop 
		while 1:
			try:
			  	ircmsg = self.ircsock.recv(2048) 
			  	ircmsg = ircmsg.strip('\n\r')
			  	if ircmsg != "":
					self.logger.info(ircmsg) 
					self.activities(ircmsg)
			except socket.timeout:
				self.logger.warning("Timeout error")
				self.connect()

	def connect(self):
		self.ircsock.close()
		self.init_socket()
		try:
			# Connect to irc server
			self.logger.info("Connecting to server " + self.server)
			self.ircsock.connect((self.server, self.port))
			self.ircsock.send("USER " + self.nick + " 0 * : " + self.nick + "\r\n")
			self.ircsock.send("NICK " + self.nick + "\n")
			time.sleep(5)
			# Join the channel
			self.ircsock.send("JOIN "+ self.channel +"\r\n")
			self.sendmsg("Someone OP me plz!")
		except socket.gaierror:
			self.logger.warning("Connection error, trying again in 1 minute")
			time.sleep(60)
			self.connect()

	def activities(self, msg):
		# Check what activites should be done
		if msg.find("ERROR :Closing Link:")  != -1:
			raise socket.timeout
		if msg.find("PING :") != -1: 
			# Ping recieved from server	
			self.pong()
	  	if msg.find("JOIN :" + self.channel ) != -1:
	  		# Someone joined the channel
	  		n = self.get_nick(msg)
	  		for approved_nick in self.whitelist:
	  			if approved_nick.lower() in n.lower():
					self.op(n)
					break
		if msg.find(".weather ") != -1:
			city = msg.split(".weather ")[1]
			city = city.split(" ")[0] 
			city = city.decode("utf-8").lower()
			if city != "":
				self.weather(city)


	def pong(self):
		# Pong the server 
		self.ircsock.send("PONG :Pong\r\n") 

	def sendmsg(self, msg):
		# Send a message to the channel 
		self.ircsock.send("PRIVMSG "+ self.channel +" :"+ msg +"\r\n") 

	def op(self, to_op):
		# Op someone
		self.ircsock.send("MODE " + self.channel + " +o " + to_op + "\r\n")	

	def get_nick(self, data):
		# Retrieve the nick from a message							
		nick = data.split('!')[0]
		nick = nick.replace(':', ' ')
		nick = nick.replace(' ', '')
		nick = nick.strip(' \t\n\r')
		return nick

	def weather(self, city):
		conn = sqlite3.Connection("geonames.sql")
		cur = conn.cursor()
		cur.execute('SELECT * FROM cities WHERE city LIKE ?', (city,))
		row = cur.fetchone()
		if row != None:
			geoname = row[1].encode("utf-8")
			print "Weather for " + geoname
			try:
				y = yr(geoname)
				w = y.weather[0]
				self.sendmsg("Weather in " + city.capitalize().encode("utf-8") + ": " + w["weather"]["name"])
				self.sendmsg("Temperature: " + w["temperature"]["value"] + " C")
				self.sendmsg("Rain: " + w["precipitation"]["value"] + " mm")
				self.sendmsg("Wind: " + w["wind"]["speed"]["mps"] + " m/s " + w["wind"]["direction"]["name"])
			except Exception:
				self.sendmsg("Problem requesting weather for " + geoname)
		else:
			self.sendmsg("Could not find city " + city.encode("utf-8"))
		conn.close()

if __name__ == "__main__":
	bot = OpBot()
	bot.execute()
