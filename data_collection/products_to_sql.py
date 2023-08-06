import re

filename = "objects"
with open("{}.log".format(filename), "r") as f:
	content = f.read()
	cards = content.split('[Info   :   Console] Card')
	broken = 0
	lines = {}

	for card in cards:
		infos = card.split('[Info   :   Console] ')
		if(len(infos) > 1):
			uid = infos[1]
			names = re.findall(r"(?:=|:) (.*)\n", infos[3])
			numbers = re.findall(r"(?:=|:) ([^\s]*)\n", infos[4])
			uuid = uid.replace('\n', '')

			line = '(' + ', '.join([
				'"' + uuid + '"',     # uuid
				'"' + names[0] + '"', # name
				'NULL',               # set_tag
				'NULL',               # set_number
				'NULL',               # card_number
				'NULL',               # mask
				'NULL',               # foilness
				'NULL',               # full_art
				'NULL',               # foil
				'"object"']) + '),'

			lines[uuid] = line

	for key in lines:
		with open("{}.sql".format(filename), "a") as f:
			f.write(lines[key] + '\n')

	print('ALL: ', str(len(cards)))
	print('BROKEN: ', str(broken))
	print('CLEAN: ', str(len(cards) - broken))
