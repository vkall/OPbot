import socket
import time

class OpBot:

	def __init__(self):
		self.nick = "BotNick"
		self.server = "Server"
		self.port = 6667
		self.channel = "#channel"
		self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.pingtimeout = 5 * 60 # 5 min
		self.last_ping = 0.0
		self.whitelist = ["nick1", "nick2"]

	def execute(self):
		self.connect()
		# Main loop 
		while 1:
			try:
			  	ircmsg = self.ircsock.recv(2048) 
			  	ircmsg = ircmsg.strip('\n\r')
				self.log(ircmsg) 
				self.activities(ircmsg)
				if (time.time() - self.last_ping) > self.pingtimeout:
					raise socket.timeout
				time.sleep(1)
			except socket.timeout:
				self.log("ERROR: timeout!")
				self.connect()

	def connect(self):
		# Connect to irc server
		self.ircsock.connect((self.server, self.port))
		self.ircsock.send("USER " + self.nick + " 0 * : " + self.nick + "\r\n")
		self.ircsock.send("NICK " + self.nick + "\n")
		time.sleep(5)
		# Join the channel
		self.ircsock.send("JOIN "+ self.channel +"\r\n")
		self.sendmsg("Someone OP me plz!")
		self.last_ping = time.time()

	def log(self, msg):
		# Print a timestamp and message
		timestamp = time.strftime("%H:%M:%S")
		print("[" + timestamp + "] " + msg)

	def activities(self, msg):
		# Check what activites should be done 
		if msg.find("PING :") != -1: 
			# Ping recieved from server
			self.last_ping = time.time()	
			self.pong()
	  	if msg.find("JOIN :" + self.channel ) != -1:
	  		# Someone joined the channel
	  		n = self.get_nick(msg)
	  		for approved_nick in self.whitelist:
	  			if approved_nick in n:
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


if __name__ == "__main__":
	bot = OpBot()
	bot.execute()
