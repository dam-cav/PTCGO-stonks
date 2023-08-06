import re
import zlib
import time

# make the header array into bytes
def toByteHeader(array):
	messageheader = bytes([])
	for val in array:
		if type(val) is int:
			messageheader = messageheader + bytes([val])
		if type(val) is str:
			messageheader = messageheader + val.encode('utf-8')
	return messageheader

def toHeaderBlocks(array):
	messageheader = bytes([])
	for val in array:
		messageheader = messageheader + (val).to_bytes(4, 'big')
	return messageheader

# gets the "name" value from json
def getMessageBodyName(request):
	try:
		request_content = request if isinstance(request, str) else request.decode()

		# search only on first 80 chars
		groups = re.search('\"name\":\"(.*)\",\"value\"', request_content[:min(80, len(request_content))])
	except UnicodeDecodeError as err:
		# print(err)
		return 'DEFLATE'

	if not groups:
		print(request)
		return 'REGEX_ERROR'
	return groups.group(1).split('\"')[0]

# strips the header for getMessageBodyName
def getMessageName(request):
	return getMessageBodyName(request[12:])

# inflate body of message to become readable
def deflateReadablePart(readablebuffer):
	doubleheader = 12 + 2
	stream = readablebuffer[doubleheader:]
	try:
		decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
		inflated = decompressor.decompress(stream)
		return inflated
	except zlib.error as err:
		#print(err)
		return ''

def getExpectedMessageLength(message):
	# 4 is the length of the first part wher it's written the length of the rest
	return int.from_bytes(message[:4], "big") + 4

def printMessageHeaderInfos(message):
	lenght = int.from_bytes(message[:4], "big") + 4
	sequence_number = int.from_bytes(message[:8][4:], "big")
	message_type = int.from_bytes(message[:12][8:], "big")
	print('Length: {lenght}'.format(lenght=lenght))
	print('Sequence: {sequence_number}'.format(sequence_number=sequence_number))
	print('Type: {message_type}'.format(message_type=message_type))

### CLIENT FUNCTIONS

def sendPing(scc):
	message_ping = '{\"name\":\"Ping\",\"value\":null}'
	send_ping = toByteHeader([0,0,0,'$',0,0,0,0,0,0,0,4]) + message_ping.encode('utf-8')
	print(getMessageName(send_ping))
	scc.send(send_ping)

# Note: this is still not using the new way of determining message end!
# maybe update it one day!
def pingPongTillMessage(socket, expected_message_name):
	bufferloader = bytes([])
	lastGroupMessageReceived = False
	lastGroupMessage = None
	expected_message_length = 0

	while not lastGroupMessageReceived:
		dataFromClient = socket.recv(8192)

		stringFromServer = getMessageName(dataFromClient)
		if stringFromServer == "Pong":
			print('SERVER >> ' + getMessageName(dataFromClient))
			time.sleep(3)
			sendPing(socket)
			continue
		else:
			bufferloader = bufferloader + dataFromClient

			if len(dataFromClient) < 8192:
				
				lastGroupMessage = getMessageName(bufferloader)
				print('SERVER >> ' + lastGroupMessage)
				if lastGroupMessage == expected_message_name:
					lastGroupMessageReceived = bufferloader
				bufferloader = bytes([])

	return lastGroupMessageReceived

### SERVER FUNCTIONS

def getNextUsefulMessage(connstream):
	dataFromClient = connstream.recv(1024) # RequestSession
	stringFromClient = dataFromClient[12:].decode()
	if "Ping" not in stringFromClient:
		return dataFromClient

	message_pong = '{\"name\":\"Pong\",\"value\":{\"timestamp\":null}}'
	send_pong = toByteHeader([0,0,0,'2',0,0,0,0,0,0,0,6]) + message_pong.encode('utf-8')
	print('SERVER <<')
	print(send_pong)
	connstream.send(send_pong)
	print('\n')

	return getNextUsefulMessage(connstream)

### FILE LOG FUNCTIONS

def saveMessageInfosToFile(content, count, side, name, seconds):
	header = content[:12]
	try:
		out = content[12:].decode()
		try:
			with open('-'.join(["exchange/out",format(count, '05d'),side,str(format(seconds,'.1f')),'N',name]) +".json", "w") as f:
				f.write(out)
		except UnicodeEncodeError:
			return
	except UnicodeDecodeError as err:
		with open('-'.join(["exchange/out",format(count, '05d'),side,str(format(seconds,'.1f')),"B",name]) + ".json", "wb") as f:
			f.write(content)

	with open('-'.join(["exchange/HEAD",format(count, '05d'),side,str(format(seconds,'.1f')),'H',name]) +".json", "wb") as f:
		f.write(header)

def saveDeflatedMessageInfosToFile(buffer, count, seconds):
	doubleheader = 12 + 2
	header = buffer[:doubleheader]
	stream = buffer[doubleheader:]

	try:
		decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
		inflated = decompressor.decompress(stream)

		name = getMessageBodyName(inflated)

		with open('-'.join(["exchange/out",format(count, '05d'),'server',str(format(seconds,'.1f')),"D",name]) +".json", "wb") as f:
			f.write(inflated)
	except zlib.error:
		with open('-'.join(["exchange/out",format(count, '05d'),'server',str(format(seconds,'.1f')),"F",'CANTGET']) + ".json", "wb") as f:
			f.write(buffer)

	with open('-'.join(["exchange/HEAD",format(count, '05d'),'server',str(format(seconds,'.1f')),'H','hisname']) +".json", "wb") as f:
		f.write(header)