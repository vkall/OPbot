import ConfigParser
import logging
import logging.config
import random
import re
import socket
import sqlite3
import threading
import time
import urllib
import urllib2

from bs4 import BeautifulSoup
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
		self.whitelist = self.conf.get("settings", "whitelist").split(",")
		self.urlReg = re.compile(r"(http://[^ ]+|https://[^ ]+)")
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
			  		if ircmsg.startswith("PING :") == False:
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
		except (socket.gaierror, socket.timeout, socket.error):
			self.logger.warning("Connection error, trying again in 1 minute")
			time.sleep(60)
			self.connect()

	def activities(self, msg):
		split_msg = msg.split(self.channel + " :")

		if len(split_msg) > 0 and split_msg[0].endswith("PRIVMSG "):
			# commands called from chat
			if split_msg[1].startswith(".weather "):
				city = split_msg[1].split(".weather ")[1]
				city = city.split(" ")[0] 
				city = city.decode("utf-8").lower()
				if city != "":
					self.weather(city)

			elif split_msg[1].startswith(".w "):
				city = split_msg[1].split(".w ")[1]
				city = city.split(" ")[0] 
				city = city.decode("utf-8").lower()
				if city != "":
					self.weather(city)

			elif split_msg[1].startswith(".ex "):
				ex_input = split_msg[1].split(".ex ")[1]
				ex_input = ex_input.split(" ")
				if len(ex_input) >= 3:
					self.currency_exchange(ex_input[1], ex_input[2], ex_input[0])
				else:
					self.sendmsg("Exchange input must be '.ex amount fromCurrency toCurrency'")
			
			elif split_msg[1].startswith(".8ball "):
				self.eightball()

			elif split_msg[1].startswith(".op"):
				n = self.get_nick(msg)
				opped = False
			  	for approved_nick in self.whitelist:
		  			if approved_nick.lower() in n.lower():
						self.op(n)
						opped = True
						break
				if opped == False:
					self.sendmsg("The nick " + n + " is not in the whitelist")

			url = self.urlReg.findall(split_msg[1])
			if url:
				for u in url:
					try:
						print "Found url " + u
						t = threading.Thread(target=self.getUrlTitle, args=(u.rstrip(),))
						t.daemon = True
						t.start()
					except:
						print "Couldn't parse url " + u

		else:
			# Other server events
			if msg.startswith("ERROR :Closing Link:"):
				raise socket.timeout

			elif msg.startswith("PING :"): 
				self.pong()

			elif msg.endswith("JOIN :" + self.channel ):
		  		n = self.get_nick(msg)
				for approved_nick in self.whitelist:
		 			if approved_nick.lower() in n.lower():
						self.op(n)
						break


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
			city = row[0].encode("utf-8")
			print "Weather for " + geoname
			try:
				y = yr(geoname)
				w = y.weather[0]
				self.sendmsg("Weather in " + city.capitalize() + ": " + w["weather"]["name"])
				self.sendmsg("Temperature: " + w["temperature"]["value"] + " C")
				self.sendmsg("Rain: " + w["precipitation"]["value"] + " mm")
				self.sendmsg("Wind: " + w["wind"]["speed"]["mps"] + " m/s " + w["wind"]["direction"]["name"])
			except Exception:
				self.sendmsg("Problem requesting weather for " + geoname)
		else:
			self.sendmsg("Could not find city " + city.encode("utf-8"))
		conn.close()

	def currency_exchange(self, fromCur, toCur, amount):
		amount = amount.replace(",",".")
		url = "http://www.google.com/finance/converter?a=" + urllib.quote(amount) +"&from=" + urllib.quote(fromCur) +"&to=" + urllib.quote(toCur)
		print "Exchange: " + url
		response = urllib2.urlopen(url)
		soup = BeautifulSoup(response.read())
		resultdiv = soup.find("div", {"id":"currency_converter_result"})
		if resultdiv.span is not None:
			self.sendmsg(resultdiv.contents[0] + resultdiv.span.contents[0])
		else:
			self.sendmsg("Could not convert " + amount + " " + fromCur + " to " + toCur)
					
	def eightball(self):
		theMatrix = [
					"It is certain",
					"It is decidedly so",
					"Without a doubt",
					"Yes definitely",
					"You may rely on it",
					"As I see it, yes",
					"Most likely",
					"Outlook good",
					"Yes",
					"Signs point to yes",
					"Reply hazy try again",
					"Ask again later",
					"Better not tell you now",
					"Only in Glorious Pampas",
					"Cannot predict now",
					"Concentrate and ask again",
					"Don't count on it",
					"My reply is no",
					"My sources say no",
					"Outlook not so good",
					"Very doubtful"
				]
		theChosenOne = random.randint(0, len(theMatrix)-1)
		self.sendmsg(theMatrix[theChosenOne])
				
	def getUrlTitle(self, url):
		try:
			#Fetches title even when direct image link is posted
			imgurPicOnlyReg = re.compile(r"(http://|https://)i\.imgur\.com/[^ ]+(\.jpg|\.png|\.gif|\.gifv)")
			imgurPicOnly = imgurPicOnlyReg.findall(url)
			if imgurPicOnly:
				url=url[:-4]

			html = urllib2.urlopen(url).read()
			soup = BeautifulSoup(html)
			title = soup.title.string
			if isinstance(title, unicode):
				title = title.splitlines()
			else:
				title = title.rstrip(["\n","\r"])
			t = ""
			for i in title:
				t = t + i
			t = t.encode("utf-8").strip()
			if t != "":
				self.sendmsg(str(t))
				self.logger.info("url title: " + str(t))
		except urllib2.HTTPError, e:
			print "Error parsing url: " + str(e.code) + " " + e.msg
			self.logger.info("Error parsing url: " + str(e.code) + " " + e.msg)
   
			
if __name__ == "__main__":
	bot = OpBot()
	bot.execute()
