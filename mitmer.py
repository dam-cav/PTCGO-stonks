import os
import ssl
import time
import re
import configparser
from socket import *
from random import randint
from threading import Thread

from utils.pokeutils import *

#connection config
config = configparser.ConfigParser()
config.read('config.ini')
HOST_NUMBER = randint(1, 9)
SERVER_VERSION_NUMBER = config['connection']['serverVersion']

proto = ssl.PROTOCOL_TLSv1_2

print('setup connection with server')
serversock = socket(AF_INET, SOCK_STREAM)
serversock.connect(("cake-prod-connection-"+ SERVER_VERSION_NUMBER +"-" + str(HOST_NUMBER) +".direwolfdigital.com", 8181))
secureserversock = ssl.wrap_socket(serversock, ssl_version=proto)

print('setup connection with client')
clientsock = socket(AF_INET, SOCK_STREAM);
clientsock.bind(("127.0.0.1",8181));
clientsock.listen();

(clientConnected, clientAddress) = clientsock.accept();

secureclientsock = ssl.wrap_socket(clientConnected,
							server_side=True,
							certfile="certs/server.pem",
							keyfile="certs/server.key",
							ssl_version=proto)

global_count = 0
client_killed = False
server_listen_stopped = False
trade_limit = 0

print('both ready')

def doThingFromServer(bufferloader, on_trade_section):
	global secureclientsock
	global secureserversock

	global global_count
	global client_killed
	global server_listen_stopped
	global trade_limit

	trade_getted = False

	print('listening to server...')
	dataFromServer = secureserversock.recv(8192)
	moment = time.time()
	global_count = global_count + 1
	if not client_killed:
		secureclientsock.send(dataFromServer)

	server_message_name = getMessageName(dataFromServer)

	if server_message_name == 'LotsRetrievedCount':
		print(dataFromServer[12:].decode())
		# {"name":"LotsRetrievedCount","value":{"count":40000}}
		trade_limit = re.search('\"count\":([0-9]*)}}', (dataFromServer[12:].decode())).group(1)
		print()
		trade_limit = int(trade_limit)/300
		on_trade_section = True

	# load buffer on long messages
	if server_message_name == 'DEFLATE':
		bufferloader = bufferloader + dataFromServer

		# if the last buffer is not full, message is ended
		if len(dataFromServer) < 8192:

			if on_trade_section:
				trade_content = deflateReadablePart(bufferloader).decode()
				if trade_content:
					possible_trade_message_name = getMessageBodyName(trade_content)
					if possible_trade_message_name == 'LotsRetrieved':
						print('PUTTING TRADES IN DB...')
						trade_thread = Thread(target=tradesToSql, args=(DB_CONFIG, trade_content))
						trade_thread.start()
						trade_getted = True
				# saveDeflatedMessageInfosToFile(bufferloader, global_count, moment)
			bufferloader = bytes([])
	else:
		saveMessageInfosToFile(dataFromServer, global_count, 'server', server_message_name, moment)

	print('SERVER >> CLIENT (' + server_message_name + ' - ' + str(global_count) + ')')
	return bufferloader, on_trade_section, trade_getted

class MitmerThread():
	def clientlistener(self):
		global secureclientsock
		global secureserversock

		global global_count
		global client_killed
		global server_listen_stopped
		global trade_limit

		message_number = None

		while not client_killed:
			print('listening to client...')
			dataFromClient = secureclientsock.recv(8192)
			moment = time.time()
			global_count = global_count + 1

			message_number = dataFromClient[6:8]
			client_message_name = getMessageName(dataFromClient)

			# # stops automatically when reaching trades
			# if client_message_name == 'ViewAllPublicTradesCount':
			# 	client_killed = True
			# 	secureclientsock.close()

			secureserversock.send(dataFromClient)

			print('CLIENT >> SERVER (' + client_message_name + ' - ' + str(global_count) + ')')
			saveMessageInfosToFile(dataFromClient, global_count, 'client', client_message_name, moment)

		offset_multiply = 0
		on_trade_section = True
		bufferloader = bytes([])
		trade_getted = True

		message_number = int.from_bytes(message_number, "big")

		# from here clientlistener become serverlistener
		# and fake client
		while True:
			if server_listen_stopped:
				message_number = message_number + 1
				if trade_getted and offset_multiply < trade_limit:
					print('CLIENT >> SERVER (ViewAllPublicTradesWithPagination - ' + str(message_number) + ')')
					clear_content = (('{\"name\":\"ViewAllPublicTradesWithPagination\",\"value\":{\"offset\":' + str(offset_multiply * 300) +',\"limit\":300}}'))
					getpage = (toHeaderBlocks([len(clear_content) + 8, message_number]) + toByteHeader([0,0,0,0])) + clear_content.encode('utf-8')
					secureserversock.send(getpage)
					offset_multiply = offset_multiply + 1
					bufferloader, on_trade_section, trade_getted = doThingFromServer(bufferloader, on_trade_section)
			else:
				time.sleep(1)
				print('check pages: ' + str(offset_multiply))

	def serverlistener(self):
		global secureclientsock
		global secureserversock

		global global_count
		global client_killed
		global server_listen_stopped
		global trade_limit

		on_trade_section = False
		bufferloader = bytes([])

		# listen to server, send messages that to client
		while not client_killed:
			bufferloader, on_trade_section; _ = doThingFromServer(bufferloader, on_trade_section)
		server_listen_stopped = True


T1 = Thread(target=MitmerThread().clientlistener, args=())
T2 = Thread(target=MitmerThread().serverlistener, args=())
T1.start()
T2.start()
T1.join()
T2.join()