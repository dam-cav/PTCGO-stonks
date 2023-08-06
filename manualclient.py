import ssl
import json
import configparser
from math import floor
from base64 import b64decode
from random import randint
from socket import *
from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS, cross_origin
from threading import Thread
from pydub import AudioSegment
from pydub.playback import play

from utils.communication.login import *
from utils.db.goodtrades import *
from utils.db.readtrade import *

config = configparser.ConfigParser()
config.read('config.ini')

#connection config
global_count = 0
username = config['connection']['user']
pss = b64decode(config['connection']['credential']).decode()
HOST_NUMBER = randint(1, 9)
SERVER_VERSION_NUMBER = config['connection']['serverVersion']
GAME_VERSION = config['connection']['clientVersion']
SCANNING_DELAY = float(config['connection']['scanningDelay'])
SCANNING_TIMEOUT = floor(int(config['connection']['scanningTimeout']) / 3)

#packs_config
CURRENT_PACKS_ID = config['trades']['currentPacksId']

#db_config
DB_CONFIG = config['db']

#device_config
DEVICE_CONFIG = config['device']

#connection
cc = socket(AF_INET, SOCK_STREAM)
cc.connect(("cake-prod-connection-" + SERVER_VERSION_NUMBER + "-" + str(HOST_NUMBER) +".direwolfdigital.com", 8181))
proto = ssl.PROTOCOL_TLS
secureserversock = ssl.wrap_socket(cc, ssl_version=proto)

trade_uid_to_accept = None
trade_history = {}
barter_groups = {}
trade_iteration = 0

def tradeTableName(iteration):
	return 'TradesAlpha' if iteration % 2 == 0 else 'TradesBeta'

class ManualThread():
	def connectionMantainer(self):
		global GAME_VERSION
		global DB_CONFIG
		global CURRENT_PACKS_ID 
		global secureserversock
		global username
		global pss
		global global_count
		global trade_uid_to_accept
		global trade_history
		global barter_groups
		global trade_iteration

		found_sound = AudioSegment.from_mp3("sounds/found.mp3")
		nothing_sound = AudioSegment.from_mp3("sounds/nothing.mp3")

		login(DEVICE_CONFIG, secureserversock, GAME_VERSION, username, pss, global_count)

		while True:
			##############################################################
			# REQUEST NUMBER OF AVAILABLE TRADES

			message_tradecount = '{\"name\":\"ViewAllPublicTradesCount\",\"value\":null}'
			send_tradecount = toHeaderBlocks([len(message_tradecount) + 8]) + toByteHeader([0,0,0,'x',0,0,0,0]) + message_tradecount.encode('utf-8')
			print(getMessageName(send_tradecount))
			secureserversock.send(send_tradecount)

			##############################################################
			# GET NUMBER OF AVAILABLE TRADES

			dataFromClient = pingPongTillMessage(secureserversock, 'LotsRetrievedCount')

			if getMessageName(dataFromClient) == 'LotsRetrievedCount':
					trade_limit = re.search('\"count\":([0-9]*)}}', (dataFromClient[12:].decode())).group(1)
					trade_limit = int(int(trade_limit)/300)
			else:
				print('Something went wrong')
				exit()

			##############################################################

			bufferloader = bytes([])
			lastGroupMessageReceived = False
			expected_message_length = 0
			trade_message_number = toByteHeader([0,0,0,'x'])
			trade_message_number = int.from_bytes(trade_message_number, "big")

			trade_getted = True
			offset_multiply = 0
			server_message_name = 'Pong'

			truncateTrades(DB_CONFIG, tradeTableName(trade_iteration))

			while offset_multiply < trade_limit:
				# ------------------------------------------------------------
				# If there is a trade to be made and it is not already waiting for a response
				if trade_uid_to_accept and trade_history.get(trade_uid_to_accept) != 'queued':
					print('IN DICT: ' + str(trade_history.get(trade_uid_to_accept)))
					print(not (trade_history.get(trade_uid_to_accept, {}).get('error') == '$$$com.direwolfdigital.exchange.LotAlreadyLocked$$$'))
					
					# # if the trade is not already in the queue and has not already expired
					# if not (trade_history.get(trade_uid_to_accept, {}).get('error') == '$$$com.direwolfdigital.exchange.LotAlreadyLocked$$$'):
					accept_trade = '{\"name\":\"AcceptTrade\",\"value\":{\"lotID\":\"' + trade_uid_to_accept +'\"}}'
					send_trade = toHeaderBlocks([len(accept_trade) + 8, trade_message_number]) + toByteHeader([0,0,0,0]) + accept_trade.encode('utf-8')
					print(getMessageName(send_trade))
					secureserversock.send(send_trade)
					trade_history[trade_uid_to_accept] = 'queued'
					# # if it has not failed because it is already in the queue, but for another reason
					# else:
					#	  print('TRADE IS DEFINITELY ALREADY EXPIRED')
					#	  trade_uid_to_accept = None

				# ------------------------------------------------------------
				# If I got the trade page
				# AND I haven't scrolled through all trades yet
				# AND I am not using this cycle to wait for a trade result
				if trade_getted and offset_multiply < trade_limit and not trade_uid_to_accept:
					trade_message_number = trade_message_number + 1
					reading_status = int(float(offset_multiply) / float(trade_limit) * 100)
					# print('CLIENT >> (ViewAllPublicTradesWithPagination - ' + str(trade_message_number) + ' ' + str(reading_status) + '% )')
					print('[ READING TRADES - {percent}% ]'.format(percent=reading_status))
					clear_content = (('{\"name\":\"ViewAllPublicTradesWithPagination\",\"value\":{\"offset\":' + str(offset_multiply * 300) +',\"limit\":300}}'))
					getpage = (toHeaderBlocks([len(clear_content) + 8, trade_message_number]) + toByteHeader([0,0,0,0])) + clear_content.encode('utf-8')
					secureserversock.send(getpage)

					offset_multiply = offset_multiply + 1
					trade_getted = False # trades just requested therefore not yet obtained

				# ------------------------------------------------------------
				# GET RESPONSE FROM SERVER
				print('?', end= '') # this means "response from server is expected"
				dataFromServer = secureserversock.recv(8192)
				server_message_name = getMessageName(dataFromServer)

				global_count = global_count + 1

				# start of a new message
				if len(bufferloader) == 0:
					lastGroupMessageReceived = False
					expected_message_length = getExpectedMessageLength(dataFromServer)

				# load buffer on long messages
				bufferloader = bufferloader + dataFromServer

				# CLEAR OUTPUT FOR TRADE RESULTS (this is something you MUST clearly see, so spam '\n')
				if server_message_name == 'ItemsAddedToCollection' or server_message_name == 'ErrorPurchasingLot':
					print('\n\n\n\n\n\n\n' + server_message_name + '\n\n\n\n\n\n\n')
					trade_result = json.loads(dataFromServer[12:].decode())
					if trade_result.get('value', {}).get('error'):
						print('\n\n\n' + trade_result['value']['error' ]+ '\n\n\n\n')
					trade_history[trade_uid_to_accept] = trade_result['value']
					trade_uid_to_accept = None
					# in case of an error, you usually know why, example:
					# {\"name\":\"ErrorPurchasingLot\",\"value\":{\"error\":\"$$$com.direwolfdigital.exchange.LotAlreadyLocked$$$\"}}

				# end of a message
				if len(bufferloader) >= expected_message_length:
					lastGroupMessageReceived = True

					trade_content = deflateReadablePart(bufferloader).decode() if server_message_name == 'DEFLATE' else None
					if trade_content:
						possible_trade_message_name = getMessageBodyName(trade_content)

						if possible_trade_message_name == 'LotsRetrieved':
							# print('PLACING TRADES IN DB...')
							trade_thread = Thread(target=tradesToSql, args=(DB_CONFIG, trade_content, tradeTableName(trade_iteration), reading_status))
							trade_thread.start()
							trade_getted = True
							time.sleep(SCANNING_DELAY) # slow down a little, to avoid DDOSing the server and to give db time to load
						else:
							print('\n\n' + possible_trade_message_name)
					# else:
					# 	print('\n\n' + server_message_name)

					bufferloader = bytes([])

				print('@', end= '') # this means "the server responded"

			# let INSERT threads finish
			for x in range(0, SCANNING_TIMEOUT):
				sendPing(secureserversock)
				dataFromClient = secureserversock.recv(8192)
				time.sleep(3)

			barter_groups = {}

			good_trades = getGoodTrades(DB_CONFIG, tradeTableName(trade_iteration), CURRENT_PACKS_ID)

			for trade_pair in good_trades:
				if barter_groups.get(trade_pair['duid2'], None):
					barter_groups[trade_pair['duid2']].append({
						'uid1': trade_pair['uid1'],
						'duid1': trade_pair['duid1'],
						'gain': trade_pair['gain'],
						'risk': trade_pair['risk'],
						'bonus1': trade_pair['bonus1'] == 'yes',
						'bonus2': trade_pair['bonus2'] == 'yes',
					})
				else:
					barter_groups[trade_pair['duid2']] = [{
						'uid1': trade_pair['uid1'],
						'duid1': trade_pair['duid1'],
						'gain': trade_pair['gain'],
						'risk': trade_pair['risk'],
						'bonus1': trade_pair['bonus1'] == 'yes',
						'bonus2': trade_pair['bonus2'] == 'yes',
					}]

			if len(barter_groups) > 0:
				play(found_sound)
				print('FOUND PROFITABLE TRADES TO DO!')
			else:
				play(nothing_sound)
				print('NO PROFITABLE TRADES FOUND!')


			trade_iteration = trade_iteration +1

		##############################################################

	def api(self):
		global DB_CONFIG
		global CURRENT_PACKS_ID 
		global trade_uid_to_accept
		global trade_history
		global barter_groups
		app = Flask(__name__)
		CORS(app)
		# app.config['SECRET_KEY'] = 'super secret'
		# app.config['CORS_HEADERS'] = 'Content-Type'

		@app.route("/")
		def hello():
			return "Hello, World!"

		@app.route("/goodtrades")
		def requestGoodTrades():
			global barter_groups

			resp = jsonify(barter_groups)
			return resp

		# example: http://127.0.0.1:5000/tradefor?archetype_id=uuuuuuuu-iiii-dddd-vvvv-444444444444
		@app.route("/tradefor")
		def tradeFor():
			archetype_id = request.args.get('archetype_id')

			print(archetype_id)

			group = objectToPacks(DB_CONFIG, tradeTableName(trade_iteration + 1), archetype_id, CURRENT_PACKS_ID)
			resp = jsonify(group)

			return resp

		# example: http://127.0.0.1:5000/trade?uid=uuuuuuuu-iiii-dddd-vvvv-444444444444
		@app.route("/trade")
		def tradePair():
			duid = request.args.get('duid')

			tr = readTrade(DB_CONFIG, tradeTableName(trade_iteration + 1), duid)
			resp = jsonify(tr)

			return resp

		@app.route("/accepttrade", methods = ['POST', 'OPTION'])
		@cross_origin(headers=['Content-Type'])
		def acceptTrade():
			global trade_uid_to_accept
			global trade_history
			uid = request.args.get('uid')

			if request.method == 'POST':
				if trade_uid_to_accept == None:
					trade_uid_to_accept = uid
					resp = jsonify({'uid': uid, 'result':'queued'})
	
					return resp
				else:
					resp = jsonify({'uid': uid, 'result':'error'})
	
					return resp

		@app.route("/tradehistory")
		def tradeHistory():
			global trade_uid_to_accept
			global trade_history
			uid = request.args.get('uid')

			resp = jsonify(trade_history.get(uid))
			return resp

		app.run()


T1 = Thread(target=ManualThread().connectionMantainer, args=())
T2 = Thread(target=ManualThread().api, args=())
T1.start()
T2.start()
T1.join()
T2.join()
