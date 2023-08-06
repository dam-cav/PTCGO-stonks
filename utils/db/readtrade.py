import json
import mysql.connector
import time
from .connection import *

def truncateTrades(config, current_table):
	mydb = getMyDb(config)

	sql = 'TRUNCATE TABLE ' + current_table + ';'

	mycursor = mydb.cursor()
	mycursor.execute(sql)

def tradesToSql(config, content, current_table, percent):
	# DEBUG USING JSON FILE
	# with open("LOTSRETRIVED.json", "r") as f:
		# content = f.read()
		# print(content)

	now_timestamp = round(time.time() * 1000)

	mydb = getMyDb(config)

	sql = "INSERT INTO " + current_table +" \
	( \
		duid, \
		uid, \
		given_archetypeid, \
		given_quantity, \
		extra_objects, \
		requested_archetypeid, \
		requested_quantity, \
		expiration_timestamp, \
		creation_timestamp, \
		owner_name, \
		inspected_at \
	) \
	VALUES ( \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s, \
		%s \
	)"

	trade_dict = json.loads(content)

	trade_for_db = []

	for trade in trade_dict['value']['lots']:

		# You can search for trades of a specific owner!
		# if trade['ownerName'] == 'SEARCHED_OWNER':
		# 	print(trade)

		# number of different products requested
		if len(trade['cardPrice']) != 1:
			# I only want trades that only require new packs 
			continue

		tradedict = {} # dict with separate and summed archetypes
		for item in trade['items']:
			if tradedict.get(item['archetypeID'], None):
				tradedict[item['archetypeID']] = tradedict[item['archetypeID']] + 1
			else:
				tradedict[item['archetypeID']] = 1

		different_archetype_ids_count = len(tradedict.keys())

		for archetype_id in tradedict:
			# print(trade['id'] + archetype_id) # duid
			# print(trade['id']) # uid
			# print(archetype_id) # given_archetypeid
			# print(tradedict[archetype_id]) # given_quantity

			pricekey = list(trade['cardPrice'].keys())[0]
			# print(pricekey) # requested_archetypeid
			trade['cardPrice'][pricekey] # requested_quantity

			# print(trade['expirationDate']) # expiration_timestamp

			creationdate = trade['items'][0]['created'] # creation_timestamp

			val = (
				trade['id'] + '_' + archetype_id,
				trade['id'],
				archetype_id,
				tradedict[archetype_id],
				True if different_archetype_ids_count > 1 else False,
				pricekey,
				trade['cardPrice'][pricekey],
				trade['expirationDate'],
				creationdate,
				trade['ownerName'],
				now_timestamp
			)

			trade_for_db.append(val)

	# (this was used to control the db insert bottleneck)
	# start_cicle = time.time()

	for val in trade_for_db:
		try:
			mycursor = mydb.cursor()

			mycursor.execute(sql, val)
		except mysql.connector.errors.IntegrityError:
			print('!', end='') # this means "the change was already there"
			# (since while we download the message pages, users are accepting and creating new ones,
			# it is normal to find trades already downloaded due to misalignment with the pages)
			continue

	# print('INS ' + str(time.time() - start_cicle))
	print('\n{{ TRADES INSERTED IN DB - {percent}% }}'.format(percent=percent))