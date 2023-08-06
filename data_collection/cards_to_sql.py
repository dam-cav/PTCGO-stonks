import re

filename = "cards"
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
			if(len(numbers) < 2):
				possible_promocustom = re.findall(r"([0-9]{3})(.*)", numbers[0])[0]
				if(len(possible_promocustom) < 2):
					print('NOT SAVABLE: {name}'.format(name=names))
					broken = broken + 1
					continue
				numbers = [
					'custom_{set}'.format(set=possible_promocustom[1]),
					'-1',
					possible_promocustom[0],
					'#{num}'.format(num=possible_promocustom[0])
				]

			aspect = re.findall(r"(?:=|:) ([^\s]*)\n", infos[5])

			if (len(aspect) == 6):
				aspect[1] = aspect[1] + ' ' + aspect[2]

			uuid = uid.replace('\n', '')

			line = '(' + ', '.join([
				'"' + uuid + '"',
				'"' + names[0] + '"',                           # name
				'"' + numbers[0] + '"',                         # set_tag
				numbers[1],                                     # set_number
				numbers[2],                                     # card_number
				'"' + aspect[0] + '"',                          # mask
				('"' + aspect[1] + '"') if aspect[1] else None, # foilness
				'True' if aspect[-2] else 'False',              # full_art
				'True' if aspect[-1] else 'False',              # foil
				'"card"']) + '),'

			lines[uuid] = line

	for key in lines:
		with open("{}.sql".format(filename), "a") as f:
			f.write(lines[key] + '\n')

	print('ALL: ', str(len(cards)))
	print('BROKEN: ', str(broken))
	print('CLEAN: ', str(len(cards) - broken))
