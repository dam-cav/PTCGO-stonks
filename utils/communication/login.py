import requests
from socket import *
from ..pokeutils import * 

def login(device_config, serverSock, game_version, username, pss, global_count):
	##############################################################
	# SESSION REQUEST

	global_count = global_count +1

	message_one = '{\"name\":\"RequestSession\",\"value\":{\"connectionInfo\":{\"hostName\":\"foo\",\"countryCode\":\"en_US\",\"clientParameters\":{\"clientVersion\":\"' \
	+ game_version \
	+ '\",\"clientPlatform\":\"WindowsPlayer\",\"Locale\":\"en_US\",\"DeviceName\":\"' \
	+ device_config['deviceName'] \
	+ '\",\"DeviceModel\":\"System Product Name (System manufacturer)\",\"DeviceType\":\"Desktop\",\"GraphicsDeviceName\":\"' \
	+ device_config['fakeGraphicsDevice'] \
	+ '\",\"GraphicsMemorySize\":\"' \
	+ device_config['fakeGraphicsMemorySize'] \
	+ '\",\"OperatingSystem\":\"Windows 10  (10.0.0) 64bit\",\"ProcessorType\":\"' \
	+ device_config['fakeProcessor'] \
	+ '\",\"SystemMemorySize\":\"' \
	+ device_config['fakeSystemMemorySize'] \
	+ '\",\"DeviceID\":\"' \
	+ device_config['deviceId'] \
	+ '\"}}}}'
	
	send_one = toHeaderBlocks([len(message_one) + 8, global_count]) + toByteHeader([0,0,0,0]) + message_one.encode('utf-8')
	print('CLIENT >> ' + getMessageName(send_one))
	serverSock.send(send_one)

	dataFromClient = serverSock.recv(8192) # GrantedSession
	print('SERVER >> ' + getMessageName(dataFromClient))

	##############################################################
	# REQUEST LOGIN TYPES

	global_count = global_count +1
	message_two = '{\"name\":\"RequestLogin\",\"value\":null}'
	send_two = toHeaderBlocks([len(message_two) + 8, global_count]) + toByteHeader([0,0,0,0]) + message_two.encode('utf-8')
	print('CLIENT >> ' + getMessageName(send_two))
	serverSock.send(send_two)

	dataFromClient = serverSock.recv(8192) # RequestedAuthType
	print('SERVER >> ' + getMessageName(dataFromClient))

	##############################################################
	# LOGIN ON HTTPS SITE, GET SERVICE_TICKET

	first_get = requests.get('https://sso.pokemon.com/sso/login?service=https://www.pokemontcg.com/cas/game_client_signin&locale=en', \
		headers={
			"Content-Type":	"application/x-www-form-urlencoded",
			"User-Agent": "Ye Olde User Agent",
			"Accept-Encoding": "*;q=1;gzip=0",
			"Connection": "keep-alive",
			"Host":	"sso.pokemon.com"
		})

	first_get_response_body = first_get.text
	lt_value = re.search('<input type="hidden" name="lt" value="(.*)" />', first_get_response_body).group(1)
	print('---\nLT:', lt_value)

	set_cookie = first_get.headers.get("Set-Cookie")
	cookie = re.search('JSESSIONID=(.*); Path', set_cookie).group(1)
	print('JSESSIONID:', cookie)

	payload='lt='+lt_value+'&execution=e1s1&_eventId=submit&username=' + username + '&password=' + pss
	headers = {
	  'Content-Type': 'application/x-www-form-urlencoded',
	  'User-Agent': 'Ye Olde User Agent',
	  'Accept-Encoding': '*;q=1;gzip=0',
	  'Content-Length': str(len(payload)),
	  'Host': 'sso.pokemon.com',
	  'Cookie': 'JSESSIONID='+cookie+'; com.pokemon.cas.web.servlet.i18n.CustomLocaleResolver.LOCALE=en'
	}

	first_post = requests.request("POST", 'https://sso.pokemon.com/sso/login?service=https://www.pokemontcg.com/cas/game_client_signin&locale=en', headers=headers, data=payload, allow_redirects=False)

	service_location = first_post.headers.get("Location")
	service_ticket = re.search('ticket=(.*)', service_location).group(1)
	print('TICKET:', service_ticket, '\n---')

	##############################################################
	# SEND SERVICE TICKET

	global_count = global_count +1
	message_three = '{\"name\":\"AuthenticateCASTicket\",\"value\":{\"accountName\":\"' + username + '\",\"serviceTicket\":\"'+service_ticket+'\",\"serviceName\":\"https://www.pokemontcg.com/cas/game_client_signin\"}}'
	message_three = toHeaderBlocks([len(message_three) + 8, global_count]) + toByteHeader([0,0,0,0]) + message_three.encode('utf-8')
	print('CLIENT >> ' + getMessageName(message_three))
	serverSock.send(message_three)

	dataFromClient = serverSock.recv(8192)
	print('SERVER >> ' + getMessageName(dataFromClient))

	##############################################################
	# THE SERVER SENDS VARIOUS INFO (NOT DEFLATED)
	# I am simply waiting to have received the latest
	# note that orders and times may vary

	# EulaSuccessful
	# CohortsForAccount
	# AuthenticationSuccessful
	# PlayerNotInGame
	# NetworkStatusIndicatorConfiguration
	# DefaultTrainerChallengeDeckMessage
	# CurrentVersusSeason
	# CurrentDailyRewardTrack
	# QuestConfigurationUpdated
	# DailyLogin
	# AccountPropertiesUpdated

	sendPing(serverSock)
	print('##############################################################')

	pingPongTillMessage(serverSock, 'AccountPropertiesUpdated')

	##############################################################

	global_count = global_count +1
	message_four_all_checksum = "e832bcbc73c28f4e276e0e28ff242df1"
	message_four = '{\"name\":\"GetSetData\",\"value\":{\"optionalChecksums\":{\"all\":\"' + message_four_all_checksum + '\"}}}'
	send_four = toHeaderBlocks([len(message_four) + 8, global_count]) + toByteHeader([0,0,0,0]) + message_four.encode('utf-8')
	print('CLIENT >> ' + getMessageName(send_four))
	serverSock.send(send_four)

	global_count = global_count +1
	# !!! NOTE: CHANGE BETWEEN VERSIONS
	message_five = "{\"name\":\"GetAllLocalizationReleases\",\"value\":{\"locale\":\"en_US\",\"keyedChecksums\":{\"CR40\":\"6fce65b6cdb8e4274561ebc212f3ee4f\",\"CR88\":\"0ea62e6a0cf108bcf8760adcc966fb76\",\"CRR49\":\"7cf8c9ce11ce90a026d6910529f8e888\",\"CR109\":\"a1487ca47b8587c5fee23c79557b233e\",\"CRSM5\":\"c80ba6f6c7c7da734a9710c4e3efcbce\",\"CR99\":\"4d5b5dc3d48624e7309bf47ea10f3507\",\"CR69\":\"3208f53444e38b13c116fc05d701400f\",\"CR51\":\"c580c9cd56d5531c245bddb15a9e2cbe\",\"CRR85\":\"0a4d7afb30682525e9613c5908b25fd5\",\"CRR74\":\"a75dcb093882acdb83a35589b7931926\",\"CR96\":\"69cf2d3cca1bf4de56d335260dacfd11\",\"CRR90\":\"7ab73e4aab163496e9cff26397a46245\",\"CRR53\":\"10eb1d2fdcaa06749a6fb2f5a5fb287b\",\"CR66\":\"59962ae5aff2afc5d83b05b2d0b276b1\",\"CRR64\":\"c8e64283905a4965576dd9345500f224\",\"CRSM9\":\"44a2afc0626b45665041ca980a7be74a\",\"CRR70\":\"981672734a9e63c6f772f09ac1b67b72\",\"CR100\":\"8d759b2fe8da1796efc2b273e92b4c81\",\"CRR59\":\"333de50594e3541cf13e062566beca45\",\"CRR75\":\"a14e5035cb3531562f3b0c018d25d8c9\",\"CR131\":\"cc7a24845132ba3a6a9eb09422a8b3b7\",\"CR122\":\"fa65f989e4480a8b91bc1e6a45dd6ac0\",\"CR117\":\"97709d5b983278e11d71fba52e9d1ca9\",\"CR106\":\"b2949b822b5528b0c07d8558dc495caf\",\"CRR81\":\"0306a3cdb7b40674d57cce9228b118ed\",\"CRR65p1\":\"fe938e360c515025effa7051bf4eace9\",\"CR36\":\"aff05da292c1840302bf93762c1c42ef\",\"CR133\":\"9df8e1cdb7e987c91ecac358a258e537\",\"CRR88\":\"e26db992fc3084e619bac46e55226237\",\"CRR63\":\"d3ae5dc9e2d5565c36135fc4683b153b\",\"CR58\":\"16204188ce09b9f210057874f9a9c161\",\"CR111\":\"eacec505379dd2f20d57221a321b5abf\",\"CR47\":\"a91c7a75ce3e88af44d25693bcec2205\",\"CR128\":\"d63afa0c78865dbafd733026826c896c\",\"CRSM11\":\"a51500ef00f193d2052d8d1d637a488a\",\"CR26\":\"8529f5260d14bc79f853e72cd574fc61\",\"CRR67\":\"3ce33cc530e22bd09a1671e6425a322f\",\"CRR48\":\"e60f440203adef1b555242301d9ec924\",\"CR55\":\"480807b5767d885dfcb7183c124de0bf\",\"CRR52\":\"0e2bb754489618bc18f1d8b2c68bf520\",\"CRR65\":\"70f11510d70f7b9e5958ead7195af0ba\",\"CR30\":\"ef9ad173fdd72154c40057fc6615da37\",\"CR78\":\"a6144aa7c8593d4659f3a4b39c70a077\",\"CR125\":\"3501460bef4982ff4a901e038079055b\",\"CR67\":\"8a0cf76f48b8cd3571a5cb1d8b0182a2\",\"CR57\":\"9ab9ef90382fc2601496605c0ffda22b\",\"CR114\":\"632d31b5d0ab706587dc47896957ed37\",\"CRR84\":\"bbcd7afe8bec0fb734193d90f4024b12\",\"CR103\":\"eb3388731c60992f1a6d495ed0e2e9fd\",\"CR46\":\"6d3669b0d269d658581e1d1fcd0b2b58\",\"CRR73\":\"78aae3fdd99465dec74e75c36d43bc18\",\"CR127\":\"c6d1dd26dee02083e921709ca09a8413\",\"CRR51\":\"8770a08da6b0983982efc459c310376a\",\"CR52\":\"e42f965a0c5d89171a60b5a4d2f64e02\",\"CRR62\":\"beaf11a2cbb0619f379f633739005de1\",\"CRR57\":\"0c5b207f36f02a879c9eab5a166b8f5c\",\"CR45\":\"f8102821af03d8b877331c348c6fd981\",\"CRR54\":\"1e7f55e0ec5b90db9397b536231400f6\",\"CRWorlds17\":\"ee67560e20677caa47e0aef814e6b2af\",\"CRR68\":\"6931087833d2f0943c856445bd8403f0\",\"CRR80\":\"c1b118212de78842e74bc8fefc6f9fb8\",\"CR120\":\"b8f726cd3be2dc2ff415ee1b66f52d23\",\"CR60\":\"818e91f4e8a237da1fbc0ffcce85fc39\",\"CRR55CR1\":\"3e6b9f894867e34feb6429e76fc723ac\",\"CR105\":\"7bbcd6073f5ed2f0e15ba8378efd8a90\",\"CR71\":\"24757e6fbf048f24d9b8c573abf8ffc6\",\"CR89\":\"baf1f17ba5da498415264337b35131f4\",\"CRR80cr1\":\"afaec5461443d7f7059d8c1f304a9e81\",\"CR39\":\"de0aeb258dc926e4ffe6ed25a6ef60cb\",\"CR116\":\"985b6efdb639256284ad7d42a1a631ac\",\"CRR76\":\"335ac38ec042048d029d517a6f22d05f\",\"CRSM12\":\"eb3fed34216c57c8c72820fe6bfb2a85\",\"CR25\":\"f0c2931f4242df6e85e7c66c8fe316bb\",\"CR97\":\"24383c51188ea5c9cd47191c4aaae86f\",\"CR70\":\"b5fcef9b32cdc184ed8f3d2ee427712f\",\"CR92\":\"315c2eb55b5fa7a7b4e8804b95bfaee3\",\"CR85\":\"8f36b3e8520b500ad9047cc81b4bf680\",\"CR35\":\"0140249cad3e4c8c055519e39a80ae0c\",\"CR12\":\"c45f9910815c1dcc19349863a51b5499\",\"CR86\":\"aa11d8041b97d57ace5d42e297c8b2ff\",\"CRSM6\":\"97bc4e885853dcef841c35c7c7f51695\",\"CR68\":\"623d9c361791e3433b1147f55a89be79\",\"SM3\":\"0d3462a6d92f3f8bc62eff6887b8d46a\",\"CR74\":\"4ef18f2aa6f51d2d15c4ae9e24e14fe6\",\"CR20\":\"45b6d65add8ca2ad58256d2fe1228854\",\"CR63\":\"a30d036e3c19919774d46790783439ec\",\"CR110\":\"4a4c307634fc0f75d48a9e7a735d204c\",\"CRR79\":\"de3cc67ca74ab2e8bdf59bcf51cccc22\",\"CR56\":\"802040fd558ae7400f82c661f2451324\",\"CR79\":\"6d147d8f2da44ef125c16ca0b67aff08\",\"CR81\":\"6c415932216de36c871a0c3dafc734e4\",\"CRR89\":\"ed47af6d0420fbfeb0086731d4f6e74f\",\"CR94\":\"d41f0dd82192cf63d149d328177dcb51\",\"CRR54CR1\":\"d77c356e3bccda9552733d73b9936e7c\",\"CR115\":\"8a85e530745310eb2dc5f24156ba888a\",\"CR83\":\"3eba9b4cb89631edd30b38a1e4ec2bed\",\"CRR66\":\"980b7317e41924ebc9d8f89741515df2\",\"CR75\":\"f5abe3c029127ccf792a4a6bc6d05342\",\"CRR65cr1\":\"7928adda497d503c88b89a08601dce5f\",\"CRApril\":\"0ed2853d3df266723607012d02425f8c\",\"CRR55\":\"538839806bd8b25aa4e096a7cb7fa45b\",\"CR121\":\"cde8c342196cc9b40d97144eb6a5c4c4\",\"CR118\":\"8750bb0d5716869bdd5ea11b14dcc4f3\",\"CRR50\":\"bfe815659a66f411dc1c490cafb509bf\",\"CRR61\":\"b653f24b244f923448d0a661b78e31fd\",\"CRSM10\":\"c40b1cc7a83820dd67298f0f2c4fe11f\",\"CR132\":\"be54a8cc05af6ea32b1414c1f81c1ceb\",\"CRR83\":\"ed335e632455918e648f8baf3585f1c0\",\"CR72\":\"edc9319631f73664c527766f0d143763\",\"CR126\":\"76d07ed1e2e906b276f9fb8a1f9751e1\",\"CR16\":\"4a52fb511e99dc714e75837bb107f3e6\",\"CR107\":\"03980c7a4fdcb439237393b55020395f\",\"CRSM4\":\"5db70a8134a7e47bd5e3028a9f8f7ed4\",\"CR124\":\"0e4583f393dab896d85db8e5a12b91e9\",\"CRSM7\":\"822fd178398c319dc3fe0d4071fe8f98\",\"CR80\":\"627e9bffc15415f3a56b38b3539d5db5\",\"CR38\":\"1ac526b5a67b171ca957702607ee059d\",\"CRR86\":\"ae23f3be20d8cff95ce6d0559677c629\",\"CR91\":\"14f4b0a4e4e6f68e14a047554e7f129b\",\"CRR72\":\"6a3d80c76fb98aed9752b1ee88dd1993\",\"CR104\":\"1d9b3cac9f1600fb2fb6385a31b4658c\",\"CR53\":\"9c270cee7f92300896816dc47dec87ca\",\"CR129\":\"2314528fbd48497c19da64d0cca58229\",\"CR21\":\"f1ae1b0c189003301e2f75da49a579a2\",\"CR31\":\"b0a88eafe77c889a94bd3c0946964a32\",\"CR113\":\"6506007ff6d3eccba00046615a0aa239\",\"CR42\":\"de621ac3751a252416b5138e3629b94f\",\"CR102\":\"9d98a0d81ed53e24f5cc090319f646d5\",\"CRR77\":\"a12b0a0a26cfb820571badb5c5fdb212\",\"CR73\":\"2b320aaf451029916668f1aab6a48446\",\"CR108\":\"0225fc5c5ab0c7ad8d22948f3a94cfd1\",\"CR62\":\"38e9526cde4ca5de18d8e8cc6bd97d0b\",\"CR76\":\"4bdf5d324526446997d02c8f092992e5\",\"CRApril2\":\"96e26337aa9abd79df8cfde6af4bbf7c\",\"CR98\":\"6cc9de914273283cbbebfe847467188d\",\"CR119\":\"44035fb08b44095f32ec7c28f6c63e98\",\"CRR71\":\"ddad4db8b099c96bd3c50e50013a9d51\",\"CR87\":\"df01531bdf2ce4882b9a4997ba60c7a6\",\"CR50\":\"a7e2d56dc8483faf44abe76f92e0b76e\",\"CRGUM\":\"33e3a309e38e3e6ba2783e164ec818a4\",\"CR84\":\"26424c9623e38bec0117fe76c818462a\",\"CR95\":\"7d3befb9795f4c5b514dd2175f6edee3\",\"R46\":\"444941f419191503f9392fcd7bdf5992\",\"CR65\":\"e6b78faf7692d1b8db75fc0267d8a27c\",\"CRR82\":\"c09af41cc8dac46272c7809100db05e7\",\"CR54\":\"e4b32a5907d2d2f61b07193fc98e3211\",\"CR101\":\"7235ee0595346ad794e3f95bef02e253\",\"CR130\":\"d8689131ae6354516f1058946cf2fc1a\",\"CRR87\":\"df1d485de7af76859e1edb283e0c651f\",\"CRR60\":\"dd339f48f67dd21112db218ff9846ef7\",\"CR43\":\"34a9dcee087e1dfbd716f8a1e29d25d9\",\"CR22\":\"18d04e1c79afa25f786925cab46d3a16\",\"CR27\":\"3cb4161476421e82505b5b0b049eb796\",\"CR59\":\"0b365a61ef90afa3a60f071a60605bde\",\"CR61\":\"52730883b55bde504746afa44cb5a32b\",\"CRDM\":\"2bb15a9c9904e836f988bd11460de2bf\",\"CR112\":\"5af412ffd4707cf5a1e305999b9644a4\",\"CRR47\":\"ddee9012c9061713596d5e0909fa16dd\",\"CR90\":\"b99592a448bce556d4e71ec9fdc5b2db\",\"CR37\":\"64d80bea66d0d28e6851147b8cfea8e2\",\"CR134\":\"972986e8d4e5e2e65c0a0b5768aee436\",\"CRR69\":\"6a60f06416554411f48c18f15bf14352\",\"CR10\":\"434118c7038cf2492d7ac88c89e64826\",\"CRSL\":\"02de7a6327b0e6286db3255e318e3ca3\",\"CRR58\":\"ba57c5462d83707468f6668c9b77caac\",\"CR32\":\"68df5a071807d46c9d2fa313e1d97b9b\",\"CR123\":\"73e0acfa073e7e9c924750b19da9c444\",\"CRSM8\":\"634599ff76b5c518216136ab50ec6c3e\",\"CRR91\":\"595649ecc9cc502ef65d20d98f7d94ec\",\"CRR91CR1\":\"26fe307f4332b2d4f1d9627b3a9470f2\",\"CRR92\":\"e45be02ab4353315ce901d232199b836\",\"CRR78\":\"a5916711029f36fd1244e71037e52498\",\"CRR93\":\"add1ec47bb6ad9354c3baab156bb08e9\",\"CRR94\":\"b1fcec832bc0169e5a43f3a7026b93d1\",\"CR0\":\"2b1a30aa3bfe181247625cad07631f0c\",\"CRR95\":\"0a24e43b7172875e3c661165d4c49105\"}}}"
	send_five = toHeaderBlocks([len(message_five) + 8, global_count]) + toByteHeader([0,0,0,0]) + message_five.encode('utf-8')
	print('CLIENT >> ' + getMessageName(send_five))
	serverSock.send(send_five)

	##############################################################
	# THE SERVER SENDS VARIOUS INFO (NOT DEFLATED)
	# I am simply waiting to have received the latest
	# note that orders and times may vary

	# ChecksumMatch
	# AllLocalizationReleases

	pingPongTillMessage(serverSock, 'AllLocalizationReleases')

	##############################################################

	first_sequence = [
		{ 	#'\x00\x00\x00 )\x00\x00\x00G\x00\x00\x00\x00'
		'header': toByteHeader([0,0,0,'G',0,0,0,0]),
		'body': '{\"name\":\"GetWallet\",\"value\":null}'
		},

		{ 	#'\x00\x00\x00+\x00\x00\x00H\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'H',0,0,0,0]),
		'body': '{\"name\":\"GetDeckList\",\"value\":null}'
		},

		{ 	#'\x00\x00\x001\x00\x00\x00I\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'I',0,0,0,0]),
		'body': '{\"name\":\"GetAvatarDeckList\",\"value\":null}'
		},

		{ 	#'\x00\x00\x004\x00\x00\x00J\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'J',0,0,0,0]),
		'body': '{\"name\":\"GetProtobufScenarios\",\"value\":null}'
		},

		{ 	#'\x00\x00\x00.\x00\x00\x00K\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'K',0,0,0,0]),
		'body': '{\"name\":\"GetNotifications\",\"value\":{}}'
		},

		{ 	#'\x00\x00\x004\x00\x00\x00L\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'L',0,0,0,0]),
		'body': '{\"name\":\"GetActiveTournaments\",\"value\":null}'
		},

		{ 	#'\x00\x00\x004\x00\x00\x00M\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'M',0,0,0,0]),
		'body': '{\"name\":\"GetArchetypeListKeys\",\"value\":null}'
		},

		{ 	#'\x00\x00\x007\x00\x00\x00N\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'N',0,0,0,0]),
		'body': '{\"name\":\"GetArchetypeIDsByFamily\",\"value\":null}'
		},

		{ 	#'\x00\x00\x00>\x00\x00\x00O\x00\x00\x00\x00
		'header': toByteHeader([0,0,0,'O',0,0,0,0]),
		'body': '{\"name\":\"GetFormatLegalityForArchetypes\",\"value\":null}'
		}
	]

	for message in first_sequence:
		send_message = toHeaderBlocks([len(message.get('body')) + 8]) + message.get('header') + message.get('body').encode('utf-8')
		print('CLIENT >> ' + getMessageName(send_message))
		serverSock.send(send_message)

	##############################################################
	# THE SERVER SENDS VARIOUS INFO (NOT DEFLATED)
	# I am simply waiting to have received the latest
	# note that orders and times may vary

	pingPongTillMessage(serverSock, 'ArchetypeKeys')

	# SERVER << ArchetypeKeys
	# {"name":"ArchetypeKeys","value":{"keys":["SM10","TK7A","XY6","Promo_HGSS","XY2","TK5B","DM","SM6","BW10","BW4","BW7","SWSH3","SWSH_Energy","TK8A","SM11","TK9B","SM7","TATM","XY9","AvatarItems","CP","BW6","TwentiethAnn","SWSH6","XY0","HGSS_Energy","BW5","SL","BW8","SWSH2","HGSS1","SM_Energy","SM8","BW1","SM3","TK10B","XY5","HGSS2","XY8","TK5A","COL","TK6B","Promo_BW","NoSet","XY12","Free_Energy","XY_Energy","BW2","RSP","SM12","SM4","TK9A","SWSH5","RewardItems","HGSS3","BW9","XY1","XY4","Promo_SWSH","TK10A","SM2","TK7B","XY7","XY11","Promo_SM","DV","SF","TK6A","Promo_XY","HGSS4","SWSH1","BW11","XY3","SM9","HF","GUM","SWSH4","TK8B","XY10","SM5","BW_Energy","BW3","SM1"]}}

	##############################################################

	# do not repeat those by copy-paste!
	counter = 0
	singlecounter = 0


	lastGroupMessageReceived = False
	expected_message_length = 0
	bufferloader = bytes([])
	while counter < 4 or not lastGroupMessageReceived: # SERVER >> OnlineDecksFound
		dataFromClient = serverSock.recv(8192)
		print('>', end="")

		try:
			# TODO: it would seem that it can replace it with a check between message type 1 and 0
			# instead of exploiting the triggered error

			stringFromServer = dataFromClient[12:].decode()

			if "Pong" in stringFromServer:
				print(getMessageName(dataFromClient))
				time.sleep(3)
				sendPing(serverSock)
				continue
			
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")			

			# end of message
			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				print('SERVER >> ' + getMessageName(bufferloader))
				bufferloader = bytes([])
			continue

			# DEPRECATED WAY OF SKIPPING MESSAGES
			# if dataFromClient[12:].decode()[-2:] == '}}':
			#	  lastGroupMessage = getMessageName(bufferloader)
			#	  print(lastGroupMessage)
		except UnicodeDecodeError as err:
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")

			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				counter = counter + 1
				print(counter)
				print('SERVER >> ' + getMessageBodyName(deflateReadablePart(bufferloader)))
				bufferloader = bytes([])
			continue

	##############################################################

	message_six = '{\"name\":\"GetProtobufAllAvatarArchetypesList\",\"value\":{\"checksum\":\"\"}}'
	send_six = toHeaderBlocks([len(message_six) + 8]) + toByteHeader([0,0,0,'q',0,0,0,0]) + message_six.encode('utf-8')
	print(getMessageName(send_six))
	serverSock.send(send_six)

	##############################################################

	archetype_keys = [
	{'header': toByteHeader([0,0,0,'r',0,0,0,0]),'archetypeKey': 'SM10'},
	{'header': toByteHeader([0,0,0,'s',0,0,0,0]),'archetypeKey': 'TK7A'},
	{'header': toByteHeader([0,0,0,'t',0,0,0,0]),'archetypeKey': 'XY6'},
	{'header': toByteHeader([0,0,0,'u',0,0,0,0]),'archetypeKey': 'Promo_HGSS'},
	{'header': toByteHeader([0,0,0,'v',0,0,0,0]),'archetypeKey': 'XY2'},
	{'header': toByteHeader([0,0,0,'w',0,0,0,0]),'archetypeKey': 'TK5B'},
	{'header': toByteHeader([0,0,0,'x',0,0,0,0]),'archetypeKey': 'DM'},
	{'header': toByteHeader([0,0,0,'y',0,0,0,0]),'archetypeKey': 'SM6'},
	{'header': toByteHeader([0,0,0,'z',0,0,0,0]),'archetypeKey': 'BW10'},
	{'header': toByteHeader([0,0,0,'{',0,0,0,0]),'archetypeKey': 'BW4'},
	{'header': toByteHeader([0,0,0,'|',0,0,0,0]),'archetypeKey': 'BW7'},
	{'header': toByteHeader([0,0,0,'}',0,0,0,0]),'archetypeKey': 'SWSH3'},
	{'header': toByteHeader([0,0,0,'~',0,0,0,0]),'archetypeKey': 'SWSH_Energy'},
	{'header': toByteHeader([0,0,0,127,0,0,0,0]),'archetypeKey': 'TK8A'},
	{'header': toByteHeader([0,0,0,128,0,0,0,0]),'archetypeKey': 'SM11'},
	{'header': toByteHeader([0,0,0,129,0,0,0,0]),'archetypeKey': 'TK9B'},
	{'header': toByteHeader([0,0,0,130,0,0,0,0]),'archetypeKey': 'SM7'},
	{'header': toByteHeader([0,0,0,131,0,0,0,0]),'archetypeKey': 'TATM'},
	{'header': toByteHeader([0,0,0,132,0,0,0,0]),'archetypeKey': 'XY9'},
	{'header': toByteHeader([0,0,0,133,0,0,0,0]),'archetypeKey': 'AvatarItems'},
	{'header': toByteHeader([0,0,0,134,0,0,0,0]),'archetypeKey': 'CP'},
	{'header': toByteHeader([0,0,0,135,0,0,0,0]),'archetypeKey': 'BW6'},
	{'header': toByteHeader([0,0,0,136,0,0,0,0]),'archetypeKey': 'TwentiethAnn'},
	{'header': toByteHeader([0,0,0,137,0,0,0,0]),'archetypeKey': 'SWSH6'},
	{'header': toByteHeader([0,0,0,138,0,0,0,0]),'archetypeKey': 'XY0'},
	{'header': toByteHeader([0,0,0,139,0,0,0,0]),'archetypeKey': 'HGSS_Energy'},
	{'header': toByteHeader([0,0,0,140,0,0,0,0]),'archetypeKey': 'BW5'},
	{'header': toByteHeader([0,0,0,141,0,0,0,0]),'archetypeKey': 'SL'},
	{'header': toByteHeader([0,0,0,142,0,0,0,0]),'archetypeKey': 'BW8'},
	{'header': toByteHeader([0,0,0,143,0,0,0,0]),'archetypeKey': 'SWSH2'},
	{'header': toByteHeader([0,0,0,144,0,0,0,0]),'archetypeKey': 'HGSS1'},
	{'header': toByteHeader([0,0,0,145,0,0,0,0]),'archetypeKey': 'SM_Energy'},
	{'header': toByteHeader([0,0,0,146,0,0,0,0]),'archetypeKey': 'SM8'},
	{'header': toByteHeader([0,0,0,147,0,0,0,0]),'archetypeKey': 'BW1'},
	{'header': toByteHeader([0,0,0,148,0,0,0,0]),'archetypeKey': 'SM3'},
	{'header': toByteHeader([0,0,0,149,0,0,0,0]),'archetypeKey': 'TK10B'},
	{'header': toByteHeader([0,0,0,150,0,0,0,0]),'archetypeKey': 'XY5'},
	{'header': toByteHeader([0,0,0,151,0,0,0,0]),'archetypeKey': 'HGSS2'},
	{'header': toByteHeader([0,0,0,152,0,0,0,0]),'archetypeKey': 'XY8'},
	{'header': toByteHeader([0,0,0,153,0,0,0,0]),'archetypeKey': 'TK5A'},
	{'header': toByteHeader([0,0,0,154,0,0,0,0]),'archetypeKey': 'COL'},
	{'header': toByteHeader([0,0,0,155,0,0,0,0]),'archetypeKey': 'TK6B'},
	{'header': toByteHeader([0,0,0,156,0,0,0,0]),'archetypeKey': 'Promo_BW'},
	{'header': toByteHeader([0,0,0,157,0,0,0,0]),'archetypeKey': 'NoSet'},
	{'header': toByteHeader([0,0,0,158,0,0,0,0]),'archetypeKey': 'XY12'},
	{'header': toByteHeader([0,0,0,159,0,0,0,0]),'archetypeKey': 'Free_Energy'},
	{'header': toByteHeader([0,0,0,160,0,0,0,0]),'archetypeKey': 'XY_Energy'},
	{'header': toByteHeader([0,0,0,161,0,0,0,0]),'archetypeKey': 'BW2'},
	{'header': toByteHeader([0,0,0,162,0,0,0,0]),'archetypeKey': 'RSP'},
	{'header': toByteHeader([0,0,0,163,0,0,0,0]),'archetypeKey': 'SM12'},
	{'header': toByteHeader([0,0,0,164,0,0,0,0]),'archetypeKey': 'SM4'},
	{'header': toByteHeader([0,0,0,165,0,0,0,0]),'archetypeKey': 'TK9A'},
	{'header': toByteHeader([0,0,0,166,0,0,0,0]),'archetypeKey': 'SWSH5'},
	{'header': toByteHeader([0,0,0,167,0,0,0,0]),'archetypeKey': 'RewardItems'},
	{'header': toByteHeader([0,0,0,168,0,0,0,0]),'archetypeKey': 'HGSS3'},
	{'header': toByteHeader([0,0,0,169,0,0,0,0]),'archetypeKey': 'BW9'},
	{'header': toByteHeader([0,0,0,170,0,0,0,0]),'archetypeKey': 'XY1'},
	{'header': toByteHeader([0,0,0,171,0,0,0,0]),'archetypeKey': 'XY4'},
	{'header': toByteHeader([0,0,0,172,0,0,0,0]),'archetypeKey': 'Promo_SWSH'},
	{'header': toByteHeader([0,0,0,173,0,0,0,0]),'archetypeKey': 'TK10A'},
	{'header': toByteHeader([0,0,0,174,0,0,0,0]),'archetypeKey': 'SM2'},
	{'header': toByteHeader([0,0,0,175,0,0,0,0]),'archetypeKey': 'TK7B'},
	{'header': toByteHeader([0,0,0,176,0,0,0,0]),'archetypeKey': 'XY7'},
	{'header': toByteHeader([0,0,0,177,0,0,0,0]),'archetypeKey': 'XY11'},
	{'header': toByteHeader([0,0,0,178,0,0,0,0]),'archetypeKey': 'Promo_SM'},
	{'header': toByteHeader([0,0,0,179,0,0,0,0]),'archetypeKey': 'DV'},
	{'header': toByteHeader([0,0,0,180,0,0,0,0]),'archetypeKey': 'SF'},
	{'header': toByteHeader([0,0,0,181,0,0,0,0]),'archetypeKey': 'TK6A'},
	{'header': toByteHeader([0,0,0,182,0,0,0,0]),'archetypeKey': 'Promo_XY'},
	{'header': toByteHeader([0,0,0,183,0,0,0,0]),'archetypeKey': 'HGSS4'},
	{'header': toByteHeader([0,0,0,184,0,0,0,0]),'archetypeKey': 'SWSH1'},
	{'header': toByteHeader([0,0,0,185,0,0,0,0]),'archetypeKey': 'BW11'},
	{'header': toByteHeader([0,0,0,186,0,0,0,0]),'archetypeKey': 'XY3'},
	{'header': toByteHeader([0,0,0,187,0,0,0,0]),'archetypeKey': 'SM9'},
	{'header': toByteHeader([0,0,0,188,0,0,0,0]),'archetypeKey': 'HF'},
	{'header': toByteHeader([0,0,0,189,0,0,0,0]),'archetypeKey': 'GUM'},
	{'header': toByteHeader([0,0,0,190,0,0,0,0]),'archetypeKey': 'SWSH4'},
	{'header': toByteHeader([0,0,0,191,0,0,0,0]),'archetypeKey': 'TK8B'},
	{'header': toByteHeader([0,0,0,192,0,0,0,0]),'archetypeKey': 'XY10'},
	{'header': toByteHeader([0,0,0,193,0,0,0,0]),'archetypeKey': 'SM5'},
	{'header': toByteHeader([0,0,0,194,0,0,0,0]),'archetypeKey': 'BW_Energy'},
	{'header': toByteHeader([0,0,0,195,0,0,0,0]),'archetypeKey': 'BW3'},
	{'header': toByteHeader([0,0,0,196,0,0,0,0]),'archetypeKey': 'SM1'}]
	# ... it seems it is not mandatory to keep up to date with all expansions

	print('CLIENT >> GetProtobufArchetypesList')
	for headerkey in archetype_keys:
		arche_message_content = '{\"name\":\"GetProtobufArchetypesList\",\"value\":{\"key\":\"' + headerkey.get('archetypeKey') + '\",\"checksum\":\"\"}}'
		send_message = toHeaderBlocks([len(arche_message_content) + 8]) + headerkey.get('header') + arche_message_content.encode('utf-8')
		print('.', end='')
		serverSock.send(send_message)
	print('')

	##############################################################

	sendPing(serverSock)

	# This is the old bad way of skipping
	# but for this part seems that JUST WERKS, so use it!

	bufferloader = bytes([])
	while counter < 88:
		dataFromClient = serverSock.recv(8192)
		try:
			stringFromServer = dataFromClient[12:].decode()
			if "Pong" in stringFromServer:
				print(getMessageName(dataFromClient))
				time.sleep(3)
				sendPing(serverSock)
				continue
			bufferloader = bufferloader + dataFromClient

		except UnicodeDecodeError as err:
			bufferloader = bufferloader + dataFromClient
			singlecounter = singlecounter +1


			if len(dataFromClient) < 8192:
				counter = counter + 1
				print('PB2-'+ str(counter))

				try:
					inflated = zlib.decompress(bufferloader[12:])
					print(getMessageName(toByteHeader([0,0,0,0,0,0,0,0,0,0,0,0]) + inflated))
				except zlib.error as err:
					print('inflation of the message failed, ignoring it and moving on...')

				bufferloader = bytes([])
			continue

	##############################################################

	second_sequence = [
		{	  #00 00 00 32 00 00 00 63 00 00 00 00
		'header': toByteHeader([0,0,0,'c',0,0,0,0]), # 0,0,0,'R',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
		{ 	#00 00 00 35 00 00 00 64 00 00 00 00
		'header': toByteHeader([0,0,0,'d',0,0,0,0]), # 0,0,0,'5',
		'body': '{\"name\":\"GetFeatureStatuses_v2\",\"value\":null}'
		},
		{ 	#00 00 00 32 00 00 00 65 00 00 00 00
		'header': toByteHeader([0,0,0,'e',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
		{ 	#00 00 00 32 00 00 00 66 00 00 00 00
		'header': toByteHeader([0,0,0,'f',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
		{ 	#00 00 00 31 00 00 00 67 00 00 00 00
		'header': toByteHeader([0,0,0,'g',0,0,0,0]), # 0,0,0,'1',
		'body': '{\"name\":\"GetArchetypeFlags\",\"value\":null}'
		},
		{ 	#00 00 00 38 00 00 00 68 00 00 00 00
		'header': toByteHeader([0,0,0,'h',0,0,0,0]), # 0,0,0,'8',
		'body': '{\"name\":\"IsUserInActiveTournament\",\"value\":null}'
		},
		{ 	#00 00 00 2f 00 00 00 69 00 00 00 00
		'header': toByteHeader([0,0,0,'i',0,0,0,0]), # 0,0,0,'/',
		'body': '{\"name\":\"GetDynamicPages\",\"value\":null}'
		},
		{ 	#00 00 00 32 00 00 00 6a 00 00 00 00
		'header': toByteHeader([0,0,0,'j',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetDynamicVersions\",\"value\":null}'
		},
		{ 	#00 00 00 32 00 00 00 6b 00 00 00 00
		'header': toByteHeader([0,0,0,'k',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
	]

	for message in second_sequence:
		send_message = toHeaderBlocks([len(message.get('body')) + 8]) + message.get('header') + message.get('body').encode('utf-8')
		print('CLIENT >> ' + getMessageName(send_message))
		serverSock.send(send_message)

	sendPing(serverSock)
	time.sleep(0.5)

	##############################################################

	lastGroupMessageReceived = False
	expected_message_length = 0
	bufferloader = bytes([])
	while counter < 89 or not lastGroupMessageReceived: # SERVER >> CollectionCountFound repeats itself
		print(counter)
		dataFromClient = serverSock.recv(8192)
		print('>', end="")

		try:
			# TODO: it would seem that it can replace it with a check between message type 1 and 0
			# instead of exploiting the triggered error

			stringFromServer = dataFromClient[12:].decode()

			if "Pong" in stringFromServer:
				print(getMessageName(dataFromClient))
				time.sleep(3)
				sendPing(serverSock)
				continue
			
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")			

			# end of message
			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				print('SERVER >> ' + getMessageName(bufferloader))
				bufferloader = bytes([])
			continue

			# DEPRECATED WAY OF SKIPPING MESSAGES
			# if dataFromClient[12:].decode()[-2:] == '}}':
			#	  lastGroupMessage = getMessageName(bufferloader)
			#	  print(lastGroupMessage)
		except UnicodeDecodeError as err:
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")

			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				counter = counter + 1
				print(counter)
				print('SERVER >> ' + getMessageBodyName(deflateReadablePart(bufferloader)))
				bufferloader = bytes([])
			continue

	sendPing(serverSock)
	time.sleep(0.5)

	##############################################################

	third_sequence = [
		#00 00 00 3a 00 00 00 6c 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'l',0,0,0,0]), # 0,0,0,':',
		'body': '{\"name\":\"GetAllBannedCardsByFormats\",\"value\":null}'
		},
		#00 00 00 32 00 00 00 6d 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'m',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
		#00 00 00 2a 00 00 00 6e 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'n',0,0,0,0]), # 0,0,0,'*',
		'body': '{\"name\":\"ViewMyLots\",\"value\":null}'
		},
		#00 00 00 32 00 00 00 6f 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'o',0,0,0,0]), # 0,0,0,'2',
		'body': '{\"name\":\"GetCollectionCount\",\"value\":null}'
		},
	]

	for message in third_sequence:
		send_message = toHeaderBlocks([len(message.get('body')) + 8]) + message.get('header') + message.get('body').encode('utf-8')
		print(getMessageName(send_message))
		serverSock.send(send_message)

	##############################################################

	lastGroupMessageReceived = False
	expected_message_length = 0
	bufferloader = bytes([])
	while counter < 94 or not lastGroupMessageReceived: # SERVER >> CollectionCountFound repeats itself
		print(counter)
		dataFromClient = serverSock.recv(8192)
		print('>', end="")

		try:
			# TODO: it would seem that it can replace it with a check between message type 1 and 0
			# instead of exploiting the triggered error

			stringFromServer = dataFromClient[12:].decode()

			if "Pong" in stringFromServer:
				print(getMessageName(dataFromClient))
				time.sleep(3)
				sendPing(serverSock)
				continue
			
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")			

			# end of message
			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				print('SERVER >> ' + getMessageName(bufferloader))
				bufferloader = bytes([])
			continue

			# DEPRECATED WAY OF SKIPPING MESSAGES
			# if dataFromClient[12:].decode()[-2:] == '}}':
			#	  lastGroupMessage = getMessageName(bufferloader)
			#	  print(lastGroupMessage)
		except UnicodeDecodeError as err:
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")

			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				counter = counter + 1
				print(counter)
				print('SERVER >> ' + getMessageBodyName(deflateReadablePart(bufferloader)))
				bufferloader = bytes([])
			continue

	##############################################################

	fourth_sequence = [
		#00 00 00 27 00 00 00 70 00 00 00 00 
		{
		'header': toByteHeader([0,0,0,'p',0,0,0,0]), # 0,0,0,'\'',
		'body': '{\"name\":\"GetMotd\",\"value\":null}'
		},
		#00 00 00 29 00 00 00 71 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'q',0,0,0,0]), # 0,0,0,')',
		'body': '{\"name\":\"PublicRooms\",\"value\":{}}'
		},
		#00 00 00 2d 00 00 00 72 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'r',0,0,0,0]), # 0,0,0,'-',
		'body': '{\"name\":\"GetFriendRoster\",\"value\":{}}'
		},
		#00 00 00 33 00 00 00 73 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'s',0,0,0,0]), # 0,0,0,'3',
		'body': '{\"name\":\"GetPokemonFamilyMap\",\"value\":null}'
		},
		#00 00 00 4b 00 00 00 74 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'t',0,0,0,0]), # 0,0,0,'K',
		'body': '{\"name\":\"GetQuests\",\"value\":\"f05bbbb0-6619-11e9-890c-22000ae91443\"}'
		},
		#00 00 00 2f 00 00 00 75 00 00 00 00 
		{
		'header': toByteHeader([0,0,0,'u',0,0,0,0]), # 0,0,0,'/',
		'body': '{\"name\":\"GetGuidOverride\",\"value\":null}'
		},
		#00 00 00 3a 00 00 00 76 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'v',0,0,0,0]), # 0,0,0,':',
		'body': '{\"name\":\"GetAllBannedCardsByFormats\",\"value\":null}'
		},
		#00 00 00 2a 00 00 00 77 00 00 00 00
		{
		'header': toByteHeader([0,0,0,'w',0,0,0,0]), # 0,0,0,'*',
		'body': '{\"name\":\"ViewMyLots\",\"value\":null}'
		},
	]

	for message in third_sequence:
		send_message = toHeaderBlocks([len(message.get('body')) + 8]) + message.get('header') + message.get('body').encode('utf-8')
		print(getMessageName(send_message))
		serverSock.send(send_message)

	##############################################################

	lastGroupMessageReceived = False
	expected_message_length = 0
	bufferloader = bytes([])
	while counter < 96 or not lastGroupMessageReceived: # SERVER >> CollectionCountFound repeats itself
		print(counter)
		dataFromClient = serverSock.recv(8192)
		print('>', end="")

		try:
			# TODO: it would seem that it can replace it with a check between message type 1 and 0
			# instead of exploiting the triggered error

			stringFromServer = dataFromClient[12:].decode()

			if "Pong" in stringFromServer:
				print(getMessageName(dataFromClient))
				time.sleep(3)
				sendPing(serverSock)
				continue
			
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				#printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")			

			# end of message
			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				print('SERVER >> ' + getMessageName(bufferloader))
				bufferloader = bytes([])
			continue

			# DEPRECATED WAY OF SKIPPING MESSAGES
			# if dataFromClient[12:].decode()[-2:] == '}}':
			#	  lastGroupMessage = getMessageName(bufferloader)
			#	  print(lastGroupMessage)
		except UnicodeDecodeError as err:
			# start new message
			if len(bufferloader) == 0:
				lastGroupMessageReceived = False
				# printMessageHeaderInfos(dataFromClient)
				expected_message_length = getExpectedMessageLength(dataFromClient)

			bufferloader = bufferloader + dataFromClient
			print('>', end="")

			if len(bufferloader) >= expected_message_length:
				lastGroupMessageReceived = True
				counter = counter + 1
				print(counter)
				print('SERVER >> ' + getMessageBodyName(deflateReadablePart(bufferloader)))
				bufferloader = bytes([])
			continue

	print('LOGIN COMPLETED! ############################################')

	##############################################################