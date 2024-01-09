import requests
import pyautogui
import copy
import json
import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from fake_useragent import UserAgent
from playsound import playsound
from colorama import Back, Fore, Style, init
from dotenv import dotenv_values

init(autoreset=True)


class Tracker:
	def __init__(self):
		self.config = dotenv_values('.env')

		try:
			self.API_KEY = self.config['API_KEY']
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}API key not found!{Back.RESET}')

			os.abort()

		self.BASE_URL = 'https://api.wolvesville.com/'

		self.ROLES = []
		self.ADVANCED_ROLES = []
		self.ROLE_ICONS = {}
		self.ROTATION = []
		self.PLAYERS = []
		self.CARDS = {}
		self.ICONS = {}


		for _ in range(16):
			self.PLAYERS.append({
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set()
			})

		self.HEADERS = {
			'Authorization': f'Bot {self.API_KEY}',
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		}

	def load_cards(self):
		try:
			with open('cards.json', 'r') as cards_file:
				self.CARDS = json.load(cards_file)
		except:
			self.CARDS = {}

	def write_cards(self, player, cards):
		if player not in self.CARDS:
			self.CARDS[player] = cards

		else:
			self.CARDS[player].update(cards)

		with open('cards.json', 'w') as cards_file:
			json.dump(self.CARDS, cards_file)

	def load_icons(self):
		try:
			with open('icons.json', 'r') as icons_file:
				self.ICONS = json.load(icons_file)
		except:
			self.ICONS = {}

	def write_icons(self, player, icons):
		if player not in self.ICONS:
			self.ICONS[player] = icons

		else:
			self.ICONS[player].update(icons)

		with open('icons.json', 'w') as icons_file:
			json.dump(self.ICONS, icons_file)

	def get_roles(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting roles...')

		ENDPOINT = 'roles'

		data = requests.get(f'{self.BASE_URL}{ENDPOINT}', headers=self.HEADERS).json()

		roles = {}

		for role in data['roles']:
			role['id'] = role['id'].replace('random-village', 'random-villager')

			if role['id'] == 'random-other':
				role['name'] = 'RO'

			if role['name'] == 'Random regular villager':
				role['name'] = 'RRV'

			elif role['name'] == 'Random strong villager':
				role['name'] = 'RSV'

			elif role['name'] == 'Random werewolf':
				role['name'] = 'RW'

			elif role['name'] == 'Random killer':
				role['name'] = 'RK'

			elif role['name'] == 'Random voting':
				role['name'] = 'RV'

			elif role['name'] == 'Random other':
				role['name'] = 'RO'

			if role['team'] == 'RANDOM_VILLAGER':
				role['team'] = 'VILLAGER'

			elif role['team'] == 'RANDOM_WEREWOLF':
				role['team'] = 'WEREWOLF'

			role['team'] = role['team'].replace('_', ' ')

			roles[role['id']] = {
				'team': role['team'],
				'aura': role['aura'],
				'name': role['name']
			}

			role.pop('id')

		roles['cursed'] = roles.pop('cursed-human')

		roles['red-lady'] = roles.pop('harlot')

		roles['random-other'] = roles.pop('random-others')

		roles['random-werewolf-weak'] = {
			'team': 'WEREWOLF',
			'aura': 'EVIL',
			'name': 'RWW'
		}

		roles['random-werewolf-strong'] = {
			'team': 'WEREWOLF',
			'aura': 'EVIL',
			'name': 'RSW'
		}

		advanced_roles = data['advancedRolesMapping']

		advanced_roles['cursed'] = advanced_roles.pop('cursed-human')

		advanced_roles['red-lady'] = advanced_roles.pop('harlot')

		return roles, advanced_roles

	def get_rotations(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting role rotations...')

		ENDPOINT = 'roleRotations'

		data = requests.get(f'{self.BASE_URL}{ENDPOINT}', headers=self.HEADERS).json()

		rotations = {}

		for gamemode_data in data:
			if gamemode_data['gameMode'] in ['quick', 'sandbox']:
				rotations[gamemode_data['gameMode'].title()] = [d['roleRotation']['roles'] for d in gamemode_data['roleRotations']]

		for gamemode in rotations:
			for i in range(len(rotations[gamemode])):
				rotations[gamemode][i] = [r for r in rotations[gamemode][i]]

				for j in range(len(rotations[gamemode][i])):
					for l in range(len(rotations[gamemode][i][j])):
						if 'role' in rotations[gamemode][i][j][l]:
							rotations[gamemode][i][j][l] = rotations[gamemode][i][j][l]['role']
							rotations[gamemode][i][j][l] = rotations[gamemode][i][j][l].replace('random-village', 'random-villager')

							if rotations[gamemode][i][j][l] == 'cursed-human':
								rotations[gamemode][i][j][l] = 'cursed'

							elif rotations[gamemode][i][j][l] == 'harlot':
								rotations[gamemode][i][j][l] = 'red-lady'

							elif rotations[gamemode][i][j][l] == 'random-villager-other':
								rotations[gamemode][i][j][l] = 'random-other'

						else:
							rotations[gamemode][i][j][l] = rotations[gamemode][i][j][l]['roles']

							for k in range(len(rotations[gamemode][i][j][l])):
								rotations[gamemode][i][j][l][k] = rotations[gamemode][i][j][l][k].replace('random-village', 'random-villager')

								if rotations[gamemode][i][j][l][k] == 'cursed-human':
									rotations[gamemode][i][j][l][k] = 'cursed'

								elif rotations[gamemode][i][j][l][k] == 'harlot':
									rotations[gamemode][i][j][l][k] = 'red-lady'

								elif rotations[gamemode][i][j][l][k] == 'random-villager-other':
									rotations[gamemode][i][j][l][k] = 'random-other'

		return rotations

	def get_cards(self, username):
		ENDPOINT = f'players/search?username={username}'

		data = requests.get(f'{self.BASE_URL}{ENDPOINT}', headers=self.HEADERS)

		if not data.ok:
			return

		data = data.json()

		cards = {c['roleId1']: c['roleId2'] for c in data['roleCards'] if 'roleId2' in c}

		if 'fool' in cards:
			cards.pop('fool')

		if 'headhunter' in cards:
			cards.pop('headhunter')

		if 'harlot' in cards:
			cards['red-lady'] = cards.pop('harlot')

		if 'cursed-human' in cards:
			cards['cursed'] = cards.pop('cursed-human')

		for achievement in data['gameStats']['achievements']:
			if achievement['roleId'] in ['fool', 'headhunter']:
				continue

			for role in self.ROLES:
				if achievement['roleId'] in self.ADVANCED_ROLES.get(role, []):
					cards[role] = achievement['roleId']

					break

		return cards

	def choose_rotation(self, rotations):
		gamemodes = list(rotations)

		print()

		for i, gamemode in enumerate(gamemodes):
			print(f'{Style.BRIGHT}{Fore.GREEN}{i + 1}. {Fore.RESET}{Back.GREEN}{gamemode}')

		while True:
			choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Gamemode:{Fore.RESET} ')

			if choice.isdigit() and 1 <= int(choice) <= i + 1:
				rotations = rotations[gamemodes[int(choice) - 1]]

				break

		diff_roles = []

		for i in range(len(rotations)):
			left_roles = []

			for j in range(len(rotations)):
				if j == i:
					continue

				left_roles += rotations[j]

			for role in rotations[i]:
				if role not in left_roles and len(role) == 1:
					diff_roles.append(self.ROLES[role[0]])

					break

		print()

		for i, role in enumerate(diff_roles):
			print(f'{Style.BRIGHT}{Fore.GREEN}{i + 1}. {Fore.RESET}{Back.GREEN}{role["name"]}')

		while True:
			choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Which of these roles is in the game:{Fore.RESET} ')

			if choice.isdigit() and 1 <= int(choice) <= i + 1:
				rotation = rotations[int(choice) - 1]

				break

			print(f'\n{Style.BRIGHT}{Back.RED}Incorrect choice!{Back.RESET}')

		for i in range(len(rotation)):
			if len(rotation[i]) > 1:
				print()

				for j, roles in enumerate(rotation[i]):
					if len(roles) == 1:
						role = self.ROLES[role]['name']

						print(f'{Style.BRIGHT}{Fore.GREEN}{j + 1}. {Fore.RESET}{Back.GREEN}{role}')

					else:
						roles = ' + '.join([self.ROLES[role]['name'] for role in roles])

						print(f'{Style.BRIGHT}{Fore.GREEN}{j + 1}. {Fore.RESET}{Back.GREEN}{roles}')

				while True:
					choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Which of these roles is in the game:{Fore.RESET} ')

					if choice.isdigit() and 1 <= int(choice) <= j + 1:
						rotation[i] = rotation[i][int(choice) - 1]

						break

					print(f'\n{Style.BRIGHT}{Back.RED}Incorrect choice!{Back.RESET}')

			else:
				role = rotation[i][0]

				rotation[i] = self.ROLES[role]

				rotation[i]['id'] = role

		while True:
			for i in range(len(rotation)):
				if isinstance(rotation[i], list):
					for j in range(len(rotation[i])):
						print(rotation[i][j])
						role = self.ROLES[rotation[i][j]]
						role['id'] = rotation[i][j]

						rotation.insert(i + 1, role)

					rotation.pop(i)

					break

			else:
				break

		return rotation

	def clear_player_info(self, player, info):
		if info == 'all':
			self.PLAYERS[player] = {
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set()
			}

		elif info == 'name':
			self.PLAYERS[player]['name'] = None

		elif info == 'team':
			self.PLAYERS[player]['team'] = None
			self.PLAYERS[player]['teams_exclude'] = set()

		elif info == 'aura':
			self.PLAYERS[player]['aura'] = None

		elif info == 'equal':
			self.PLAYERS[player]['equal'] = set()
			self.PLAYERS[player]['not_equal'] = set()

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Invalid info!{Back.RESET}')

			return

	def set_name(self, player, name):
		cards = self.get_cards(name)

		if cards is None:
			input(f'\n{Style.BRIGHT}{Back.RED}Invalid name!{Back.RESET}')

			return

		else:
			self.PLAYERS[player]['name'] = name

			self.write_cards(name, cards)

			role = self.PLAYERS[player]['role']

			if role and role not in self.ADVANCED_ROLES:
				for src_role in self.ADVANCED_ROLES:
					if role in self.ADVANCED_ROLES[src_role]:
						break

				self.write_cards(name, {src_role: role})

	def set_role(self, player, role):
		for r in self.ROTATION:
			if role.lower() == r['name'].lower():
				name = self.PLAYERS[player]['name']

				self.PLAYERS[player]['role'] = r['id']
				self.PLAYERS[player]['team'] = r['team']
				self.PLAYERS[player]['aura'] = r['aura']

				for equal_player in self.PLAYERS[player]['equal']:
					self.PLAYERS[equal_player]['team'] = self.PLAYERS[player]['team']

				for not_equal_player in self.PLAYERS[player]['not_equal']:
					self.PLAYERS[not_equal_player]['teams_exclude'].add(self.PLAYERS[player]['team'])

				if name and r['id'] not in self.ADVANCED_ROLES:
					for src_role in self.ADVANCED_ROLES:
						if r['id'] in self.ADVANCED_ROLES[src_role]:
							break

					self.write_cards(name, {src_role: r['id']})

				break

		else:
			return 1

	def set_advanced_role(self, query):
		src_role = None
		dst_role = None

		for role in self.ROLES:
			if self.ROLES[role]['name'].lower() == query:
				dst_role = role

				break

		if not dst_role:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role!{Back.RESET}')

			return

		if dst_role in self.ADVANCED_ROLES:
			src_role = self.ADVANCED_ROLES[dst_role]

		else:
			for role in self.ADVANCED_ROLES:
				found = False

				for advanced_role in self.ADVANCED_ROLES[role]:
					if advanced_role == dst_role:
						src_role = role
						found = True

						break

				if found:
					break

		if not src_role:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role!{Back.RESET}')

			return

		if isinstance(src_role, list):
			for role in self.ROTATION:
				if role['id'] not in src_role:
					continue

				found = False

				for advanced_role in self.ADVANCED_ROLES[dst_role]:
					if advanced_role == role['id']:
						src_role = role['id']
						found = True

						break

				if found:
					break

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role!{Back.RESET}')

				return

		for r, role in enumerate(self.ROTATION):
			if role['id'] == src_role:
				self.ROTATION[r] = self.ROLES[dst_role]
				self.ROTATION[r]['id'] = dst_role

				break

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role!{Back.RESET}')

			return

		for p, player in enumerate(self.PLAYERS):
			if self.PLAYERS[p]['role'] == src_role:
				self.PLAYERS[p]['role'] = dst_role
				self.PLAYERS[p]['team'] = self.ROLES[src_role]['team']
				self.PLAYERS[p]['aura'] = self.ROLES[src_role]['aura']

				for equal_player in self.PLAYERS[p]['equal']:
					self.PLAYERS[equal_player]['team'] = self.PLAYERS[p]['team']

				for not_equal_player in self.PLAYERS[p]['not_equal']:
					self.PLAYERS[not_equal_player]['teams_exclude'].add(self.PLAYERS[p]['team'])

				if player['name'] and src_role in self.ADVANCED_ROLES:
					self.write_cards(player['name'], {
						src_role: dst_role
					})

				break

	def set_cursed(self):
		for r, role in enumerate(self.ROTATION):
			if role['id'] == 'cursed':
				self.ROTATION[r] = self.ROLES['werewolf']
				self.ROTATION[r]['id'] = role['id']

				break

		for r, player in enumerate(self.PLAYERS):
			if player['role'] == 'cursed':
				self.PLAYERS[r]['role'] = 'werewolf'
				self.PLAYERS[r]['team'] = 'WEREWOLF'
				self.PLAYERS[r]['aura'] = 'EVIL'

				for equal_player in self.PLAYERS[r]['equal']:
					self.PLAYERS[equal_player]['equal'].remove(r)

				for not_equal_player in self.PLAYERS[r]['not_equal']:
					self.PLAYERS[not_equal_player]['not_equal'].remove(r)

				self.PLAYERS[r]['equal'] = set() 
				self.PLAYERS[r]['not_equal'] = set() 

				break

	def set_equal(self, players, equal):
		if equal:
			self.PLAYERS[players[1]]['equal'].add(players[0])
			self.PLAYERS[players[0]]['equal'].add(players[1])

			if self.PLAYERS[players[0]]['team']:
				self.PLAYERS[players[1]]['team'] = self.PLAYERS[players[0]]['team']

			elif self.PLAYERS[players[1]]['team']:
				self.PLAYERS[players[0]]['team'] = self.PLAYERS[players[1]]['team']
				self.PLAYERS[players[0]]['teams_exclude'] = self.PLAYERS[players[1]]['team']

			if self.PLAYERS[players[0]]['teams_exclude']:
				self.PLAYERS[players[1]]['teams_exclude'] = self.PLAYERS[players[1]]['teams_exclude']

			elif self.PLAYERS[players[1]]['teams_exclude']:
				self.PLAYERS[players[0]]['teams_exclude'] = self.PLAYERS[players[1]]['teams_exclude']

		else:
			self.PLAYERS[players[1]]['not_equal'].add(players[0])
			self.PLAYERS[players[0]]['not_equal'].add(players[1])

			if self.PLAYERS[players[0]]['team']:
				self.PLAYERS[players[1]]['teams_exclude'].add(self.PLAYERS[players[0]]['team'])

			elif self.PLAYERS[players[1]]['team']:
				self.PLAYERS[players[0]]['teams_exclude'].add(self.PLAYERS[players[1]]['team'])

	def set_player_info(self, player, info):
		if player.isdigit() and 1 <= int(player) <= 16:
			player = int(player) - 1

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect number!{Back.RESET}')

			return

		if info.lower() == 'dead':
			self.PLAYERS[player]['dead'] = True

		elif info.lower() == 'alive':
			self.PLAYERS[player]['dead'] = False

		elif info.lower() in ['good', 'evil', 'unknown']:
			self.PLAYERS[player]['aura'] = info.upper()

		else:
			if self.set_role(player, info):
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role or aura!{Back.RESET}')

	def monitor(self):
		banner(self.__class__.__name__)

		players_info = ''

		remaining = {
			'GOOD': [],
			'EVIL': [],
			'UNKNOWN': []
		}

		distinct_rotation = []

		for role in self.ROTATION:
			if role not in distinct_rotation:
				distinct_rotation.append(role)

		for role in distinct_rotation:
			total = self.ROTATION.count(role)
			found = 0

			for player in self.PLAYERS:
				if player['role'] == role['id']:
					found += 1

					if found == total:
						break

			for _ in range(total - found):
				remaining[role['aura']].append(role['name'])

		remaining_good = ', '.join(remaining['GOOD'])
		remaining_evil = ', '.join(remaining['EVIL'])
		remaining_unknown = ', '.join(remaining['UNKNOWN'])

		remaining_info = f'\n{Style.BRIGHT}{Back.RED}REMAINING{Back.RESET}' + \
					f'\n{Fore.GREEN}GOOD:{Fore.RESET} {remaining_good}' + \
					f'\n{Fore.RED}EVIL:{Fore.RESET} {remaining_evil}' + \
					f'\n{Fore.CYAN}UNKNOWN:{Fore.RESET} {remaining_unknown}'

		for i, player in enumerate(self.PLAYERS):
			name = player['name']
			team = player['team']
			teams_exclude = player['teams_exclude']
			aura = player['aura']

			cards = list(self.CARDS.get(name, {}).values())

			possible_advanced_roles = []

			if not player['role']:
				for role in self.ROTATION:
					if role['id'] in cards and \
						role['team'] not in teams_exclude and \
						(not team or team == role['team']) and \
						(not aura or aura == role['aura']) \
						and self.ROLES[role['id']]['name'] in remaining[role['aura']]:
						possible_advanced_roles.append(self.ROLES[role['id']]['name'])

			info = f'{i + 1}'

			if name:
				info += f' ({name})'

			if player['role']:
				role = self.ROLES[player['role']]['name']
				info += f' - {role}'

			elif team:
				info += f' [{team}]'

			elif teams_exclude:
				teams_exclude = ', '.join(teams_exclude)

				info += f' [NOT {teams_exclude}]'

			if possible_advanced_roles:
				possible_advanced_roles = ', '.join(possible_advanced_roles)

				info += f' + POSSIBLE {possible_advanced_roles}'

			info += '\n'

			if player['aura'] == 'GOOD':
				info = f'{Back.GREEN}{info}{Back.RESET}'

			elif player['aura'] == 'EVIL':
				info = f'{Back.RED}{info}{Back.RESET}'

			elif player['aura'] == 'UNKNOWN':
				info = f'{Back.CYAN}{info}{Back.RESET}'

			if player['dead']:
				info = f'\t{Style.DIM}{info}'

			else:
				info = f'{Style.BRIGHT}{info}'

			players_info += info

		print(f'{Style.BRIGHT}{players_info}{remaining_info}')

	def process(self):
		cmd = input(f'\n{Style.BRIGHT}{Fore.RED}>{Fore.RESET} ')

		if not cmd:
			return

		elif cmd.lower() == 'end':
			return 1

		elif cmd.lower().startswith('clear '):
			info = cmd.lower().split('clear ')[1].split(' ')

			if len(info) >= 1 and info[0].isdigit() and 1 <= int(info[0]) <= 16:
				if len(info) == 1:
					info.append('all')

				player = int(info[0]) - 1
				info = info[1]

				self.clear_player_info(player, info)

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Invalid info!{Back.RESET}')

		elif cmd.lower().startswith('name of '):
			cmd = cmd.split(' ')

			if len(cmd) == 5 and cmd[3].lower() == 'is' and cmd[2].isdigit() and 1 <= int(cmd[2]) <= 16:
				player = int(cmd[2]) - 1
				name = cmd[4]

				self.set_name(player, name)

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect number!{Back.RESET}')

		elif cmd.lower().startswith('there is '):
			query = cmd.lower().split('there is ')[1]

			self.set_advanced_role(query)

		elif cmd.lower() == 'cursed turned':
			self.set_cursed()

		elif '=' in cmd:
			if not(cmd.count('!=') == 1 or cmd.count('=') == 1):
				input(f'\n{Style.BRIGHT}{Back.RED}Invalid syntax!{Back.RESET}')

				return

			equal = '!=' if '!=' in cmd else '='

			players = cmd.split(f' {equal} ')

			if len(players) == 2 and players[0].isdigit() and players[1].isdigit():
				players = list(map(int, players))

				if not (1 <= players[0] <= 16 and 1 <= players[1] <= 16):
					input(f'\n{Style.BRIGHT}{Back.RED}Invalid number(s)!{Back.RESET}')

					return

				players[0] -= 1
				players[1] -= 1

				self.set_equal(players, equal == '=')

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Invalid syntax!{Back.RESET}')

		else:
			try:
				player, info = cmd.lower().split(' is ')
			except ValueError:
				print(f'\n{Style.BRIGHT}{Fore.RED}Usage:')
				print(f'{Style.BRIGHT}{Fore.RED}[number] is [role / aura / dead / alive]')
				print(f'{Style.BRIGHT}{Fore.RED}[number] [= / !=] [number]')
				print(f'{Style.BRIGHT}{Fore.RED}Name of [number] is [name]')
				print(f'{Style.BRIGHT}{Fore.RED}There is [advanced role]')
				print(f'{Style.BRIGHT}{Fore.RED}Cursed turned')
				print(f'{Style.BRIGHT}{Fore.RED}Clear [number] [all / name / team / aura / equal]')
				print(f'{Style.BRIGHT}{Fore.RED}end - stop tracker')
				input()

				return

			self.set_player_info(player, info)

	def run(self):
		banner(self.__class__.__name__)

		self.load_cards()

		self.ROLES, self.ADVANCED_ROLES = self.get_roles()

		rotations = self.get_rotations()

		self.ROTATION = self.choose_rotation(rotations)

		try:
			while True:
				self.monitor()

				if self.process():
					return
		except KeyboardInterrupt:
			return


class TrackerV2(Tracker):
	def __init__(self):
		super().__init__()
		
		self.USER_DATA_DIR = os.getenv('LOCALAPPDATA') + r'\\Google\\Chrome\\User Data\\WolvesGod'
		self.user_agent = UserAgent(verify_ssl=False)
		self.page = None
		self.day_chat = None
		self.dead_chat = None
		self.last_message_number = 1

	def choose_rotation(self, rotations, roles):
		flatten_rotations = []

		for gamemode in rotations:
			for t, top_rotations in enumerate(rotations[gamemode]):
				permutated_top_rotations = [top_rotations.copy()]

				for permutated_top_rotation in permutated_top_rotations:
					permutations = []

					for i in range(len(permutated_top_rotation)):
						if len(permutated_top_rotation[i]) > 1:
							for j in range(len(permutated_top_rotation[i])):
								permutations.append(permutated_top_rotation[i][j])

							permutated_top_rotation.pop(i)

							break

					for permutation in permutations:
						if isinstance(permutation, list):
							permutated_top_rotations.append(permutated_top_rotation + [[p] for p in permutation])

						else:
							permutated_top_rotations.append(permutated_top_rotation + [[permutation]])

				for permutated_top_rotation in permutated_top_rotations:
					if len(permutated_top_rotation) == len(roles):
						flatten_rotations.append(permutated_top_rotation)

		for t in range(len(flatten_rotations)):
			for r in range(len(roles)):
				flatten_rotations[t][r] = flatten_rotations[t][r][0]

		rotations = copy.deepcopy(flatten_rotations)

		matches = [0 for _ in range(len(rotations))]

		for role in roles:
			for t, top_rotations in enumerate(flatten_rotations):
				for r, rotation_role in enumerate(top_rotations):
					if role in [rotation_role] + self.ADVANCED_ROLES.get(rotation_role, []):
						flatten_rotations[t].pop(r)

						matches[t] += 1

						break

		max_matches = max(matches)

		if max_matches < 7:
			return

		for m in range(len(rotations)):
			if matches[m] == max_matches:
				rotation = rotations[m]

				break

		for r in range(len(rotation)):
			if rotation[r] not in roles:
				for advanced_role in self.ADVANCED_ROLES.get(rotation[r], []):
					if advanced_role in roles:
						rotation[r] = advanced_role

						break

			role = rotation[r]

			rotation[r] = self.ROLES[role]

			rotation[r]['id'] = role

		return rotation

	def update_players(self): 
		service_messages = []

		for chat in (self.day_chat, self.dead_chat):
			try:
				if chat.is_hidden(timeout=1000):
					break

				result = chat.evaluate('''
					(chat, last_message_number) => {
						let service_messages = [];

						let messages = chat.querySelectorAll("div [dir=auto]");

						if (messages.length < last_message_number) return null;

						for (let m = last_message_number; m < messages.length; ++m) {
							blocks = messages[m].querySelectorAll("div > span");

							if (blocks.length >= 3) service_messages.push(messages[m].textContent);
						}

						last_message_number = messages.length;

						return [service_messages, last_message_number];
					}
				''', self.last_message_number)

				if result is not None:
					service_messages, self.last_message_number = result

					break
			except:
				continue

		for service_message in service_messages:
			print(service_message)

			player = None
			number = None
			name = None
			role = None
			dead = True

			if 'убил' in service_message:
				service_message = service_message.replace('.', '').replace('!', '')

				if 'дождь' in service_message:
					player = service_message.split(' дождь на ')[1].split(' и убил его.')[0]

				elif 'воду' in service_message:
					if 'себя' in service_message:
						...

					else:
						players = service_message.split(' кинул святую воду и убил ')

						for p in range(2):
							number = int(players[p].split(' ')[0]) - 1
							name = players[p].split(' ')[1]	

							if '/' in service_message:
								role = players[p].split(' / ')[1].split(')')[0]

							self.set_name(number, name)
							self.PLAYERS[number]['dead'] = not p

							if role:
								self.set_role(number, role)

					continue	

				else:
					if 'убили' in service_message:
						sep = ' убили '

					elif 'убила' in service_message:
						sep = ' убила '

					else:
						sep = ' убил '

					player = service_message.split(sep)[1]

			elif 'зарезал' in service_message:
				player = service_message.split(' зарезал ')[1]

			elif 'взрывом' in service_message:
				player = service_message.split(' был убит взрывом!')[0]

			elif 'застрелил' in service_message:
				if 'Надзиратель' in service_message:
					player = service_message.split(' застрелил ')[1]

				else:
					players = service_message.split(' застрелил ')

					for p in range(2):
						number = int(players[p].split(' ')[0]) - 1
						name = players[p].split(' ')[1]	

						if '/' in service_message:
							role = players[p].split(' / ')[1].split(')')[0]

						self.set_name(number, name)
						self.PLAYERS[number]['dead'] = p

						if role:
							self.set_role(number, role)

					continue

			elif 'камень' in service_message:
				players = service_message.split(' и убил его')[0].split(' бросил камень в ')

				for p in range(2):
					number = int(players[p].split(' ')[0]) - 1
					name = players[p].split(' ')[1]	

					if '/' in service_message:
						role = players[p].split(' / ')[1].split(')')[0]

					self.set_name(number, name)
					self.PLAYERS[number]['dead'] = p

					if role:
						self.set_role(number, role)

				continue

			elif 'казнил' in service_message:
				player = service_message.split(' ночью. ')[1].split(' умер.')[0]

			elif 'Меч' in service_message:
				player = service_message.split(' чтобы убить ')[1]

			elif 'Куртизанка' in service_message:
				player = service_message.split(' посетил ')[0]
				role = 'Red lady'

			elif 'Силач' in service_message:
				...

			elif 'раскрыть роль' in service_message:
				player = service_message.split(' раскрыть роль ')[1]
				dead = False

			elif 'раскрыл роль' in service_message:
				player = service_message.split(' раскрыл роль ')[1]
				dead = False

			elif 'отомщена' in service_message:
				player = service_message.split(' отомщена, ')[1].split(' погиб!')[0]

			elif 'душе' in service_message:
				player = service_message.split(' погиб ')[0]

			elif 'мэр!' in service_message:
				player = service_message.split('Игрок ')[1].split(' - ')[0]

				number, name = player.split(' ')
				number = int(number) - 1
				role = 'Mayor'
				dead = False

			elif 'воскресил' in service_message:
				player = service_message.split(' воскресил ')[1].replace('.', '')

				number, name = player.split(' ')
				number = int(number) - 1
				dead = False

			elif 'сбежал из деревни' in service_message:
				if 'любви' in service_message:
					player = service_message.split('Игрок ')[1].split(' лишился')[0]

				elif 'рекрутом' in service_message:
					player = service_message.split('Игрок ')[1].split(' был')[0]

				else:
					player = service_message.split(' сбежал из деревни.')[0]

			elif 'героически' in service_message:
				player = service_message.split(' героически занял место ')[0].split('Игрок ')[1]
				dead = False

			if player:
				print(player)

				if not number:
					number = int(player.split(' ')[0]) - 1
					name = player.split(' ')[1]

				if role is None and '/' in service_message:
					role = player.split(' / ')[1].split(')')[0]

				print(number, name, role)

				self.set_name(number, name)
				self.PLAYERS[number]['dead'] = dead

				if role:
					self.set_role(number, role)
		input()


	def find_players(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Finding players...')

		for i in range(1, 5):
			for j in range(1, 5):
				try:
					time.sleep(0.5)

					player_base_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[{i}]/div[{j}]/div')
					name_locator = player_base_locator.locator('xpath=/div[1]/div/div[4]/div/div')
					name = name_locator.text_content(timeout=1000).split(' ')[1]

					self.set_name(4 * (i - 1) + j - 1, name)

				except PlaywrightTimeoutError:
					continue

		print(f'{Style.BRIGHT}{Fore.GREEN}Players found!')

	def prepare(self):
		self.ROLES = []
		self.ADVANCED_ROLES = []
		self.ROTATION = []
		self.PLAYERS = []
		self.CARDS = {}
		self.ICONS = {}

		self.load_cards()

		self.ROLES, self.ADVANCED_ROLES = self.get_roles()

		self.last_message_number = 1

		for _ in range(16):
			self.PLAYERS.append({
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set()
			})

		self.day_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div/div/div[1]/div/div/div/div')
		self.dead_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div/div[2]/div/div/div[1]/div/div/div')

	def run(self):
		banner(self.__class__.__name__)

		try:
			with sync_playwright() as playwright:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Opening website...')

				context = playwright.chromium.launch_persistent_context(
					user_data_dir=self.USER_DATA_DIR,
					user_agent=self.user_agent.random,
					viewport={
						'width': 960,
						'height': 972
					},
					headless=False,
					args=['--window-position=-7,40', '--mute-audio'],
					ignore_default_args=['--enable-automation']
				)

				self.page = context.pages[0]

				while True:
					try:
						self.page.goto('https://wolvesville.com', wait_until='commit', timeout=100000)

						break
					except PlaywrightTimeoutError:
						print(f'{Style.BRIGHT}{Fore.RED}Timeout error!{Fore.RESET}')

						continue

				print(f'{Style.BRIGHT}{Fore.GREEN}Website opened!')

				while True:
					banner(self.__class__.__name__)

					self.prepare()

					print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for game start...')

					while True:
						try:
							night_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div[1]/div[1]/div/div[1]')

							if night_chat.text_content(timeout=1000) == 'Дневной чат':
								break
						except:
							continue

					print(f'{Style.BRIGHT}{Fore.GREEN}Game found!')

					self.find_players()

					print(f'{Style.BRIGHT}{Fore.YELLOW}Finding roles...')

					roles_base_locator = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[2]/div')

					icons = roles_base_locator.evaluate('''
						(locator) => {
							let sources = [];

							const icons_1 = locator.childNodes[0].getElementsByTagName("img"),
							icons_2 = locator.childNodes[1].getElementsByTagName("img");

							for (icon of icons_1) sources.push(icon.src);
							for (icon of icons_2) sources.push(icon.src);

							return sources;
						}
					''')

					roles = []

					for icon in icons:
						role = icon.split('icon_')[1].split('_filled')[0]
						role = role.replace('.svg', '').replace('.png', '')
						role = role.replace('_', '-')

						if 'cursed' in role:
							role = 'cursed'

						elif 'harlot' in role:
							role = 'red-lady'

						elif 'rolechanges' in role:
							role = 'random-other'

						elif 'kittenwolf' in role:
							role = 'kitten-wolf'

						for _ in range(2):
							if role in list(self.ROLES) + self.ADVANCED_ROLES.get(role, []):
								break

							role = role[role.find('-') + 1:]

						roles.append(role)

						self.ICONS[role] = icon

					print(f'{Style.BRIGHT}{Fore.GREEN}Roles found!')

					rotations = self.get_rotations()

					print(f'{Style.BRIGHT}{Fore.YELLOW}Finding rotation...')

					self.ROTATION = self.choose_rotation(rotations, roles)

					if self.ROTATION is None:
						input(f'\n{Style.BRIGHT}{Back.RED}Rotation not found!{Back.RESET}')

						return

					print(f'{Style.BRIGHT}{Fore.GREEN}Rotation found!')

					while True:
						self.monitor()

						if self.process():
							break

						self.update_players()
		except KeyboardInterrupt:
			return
		# except Exception as e:
		# 	input(f'\n{Style.BRIGHT}{Back.RED}Browser closed!{Back.RESET}')

		# 	return


class Miner:
	@staticmethod
	def wait(path, confidence=0.9, check_fail=False, check_count=7, click=True):
		fails = 0

		while True:
			coords = pyautogui.locateCenterOnScreen('img/' + path, confidence=confidence)

			if coords:
				if click:
					try:
						pyautogui.click(*coords)
					except pyautogui.FailSafeException:
						continue

				return 0

			if check_fail:
				fails += 1

			if fails == check_count:
				return 1

			time.sleep(5)

	@staticmethod
	def launch_emulator():
		pyautogui.press('win')

		time.sleep(3)

		pyautogui.write('memu', interval=0.2)
		pyautogui.press('enter')

	def shutdown(self, reboot=False):
		self.wait('close.png')

		if reboot:
			self.wait('reboot.png')

		else:
			self.wait('ok.png')

	def back(self):
		self.wait('back.png')

	def home(self):
		self.wait('home.png')

	def launch_vpn(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Launching VPN...')

		while self.wait('vpn_app_icon.png', check_fail=True):
			self.home()

		pyautogui.moveTo(100, 100)

		while self.wait('vpn_header.png', check_fail=True):
			self.back()

			pyautogui.moveTo(100, 100)

		if not self.wait('vpn_connect.png', check_fail=True, check_count=3):
			if self.wait('vpn_on.png', check_fail=True, check_count=10, click=False):
				self.back()

				pyautogui.moveTo(100, 100)

			self.back()

		print(f'{Style.BRIGHT}{Fore.GREEN}VPN launched!')

	def spin(self):
		while True:
			print(f'{Style.BRIGHT}{Fore.GREEN}Spinning...')

			pyautogui.moveTo(100, 100)

			if not self.wait('done.png', confidence=0.8, check_fail=True, check_count=1):
				print(f'{Style.BRIGHT}{Fore.GREEN}DONE!')

				playsound('audio/confusion.mp3')

				return 1

			if self.wait('ad.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Loading takes too long.')

				return

			time.sleep(35)

			self.back()

			if self.wait('spin.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Spin button not found.')

				return

	def prepare(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for MEmu...')

		self.home()

		print(f'{Style.BRIGHT}{Fore.GREEN}MEmu found!')

		time.sleep(3)

		self.launch_vpn()
		self.home()

		print(f'{Style.BRIGHT}{Fore.YELLOW}Launching game...')

		while self.wait('game_app_icon.png', check_fail=True):
			self.home()

		self.wait('profile.png', click=False)
		self.wait('cancel.png', check_fail=True, check_count=3)
		
		while True:
			header = pyautogui.locateCenterOnScreen('img/header.png', confidence=0.8)

			if header:
				break

		pyautogui.click(header[0], header[1] + 35)

		print(f'{Style.BRIGHT}{Fore.GREEN}Game launched!')

	def run(self):
		banner(self.__class__.__name__)

		print(f'{Style.BRIGHT}{Fore.YELLOW}Launching MEmu...')

		self.launch_emulator()

		print(f'{Style.BRIGHT}{Fore.GREEN}MEmu launched!')

		try:
			while True:
				self.prepare()

				if self.spin():
					self.shutdown()

					input(f'\n{Style.BRIGHT}{Fore.GREEN}Press Enter to continue{Fore.RESET}')

					return

				print(f'{Style.BRIGHT}{Fore.YELLOW}Rebooting...')

				self.shutdown(reboot=True)
		except KeyboardInterrupt:
			self.shutdown()

			return


class Grinder:
	def __init__(self):
		self.USER_DATA_DIR = os.getenv('LOCALAPPDATA') + r'\\Google\\Chrome\\User Data\\WolvesGod'
		self.user_agent = UserAgent(verify_ssl=False)
		self.page = None

	def act_villager(self):
		print(f'{Style.BRIGHT}{Fore.GREEN}You are not a werewolf!')

	def act_werewolf(self):
		start_time = time.monotonic()

		print(f'{Style.BRIGHT}{Fore.RED}You are a werewolf!')
		print(f'{Style.BRIGHT}{Fore.YELLOW}Finding players...')

		players = []
		couples = []

		self_number = None
		wolf_seer = False
		vote = True
		tag = False
		target = None

		for i in range(1, 5):
			for j in range(1, 5):
				try:
					time.sleep(0.5)

					player_base_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[{i}]/div[{j}]/div')
					player_img_base_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[{i}]/div[{j}]/div')
					name_locator = player_base_locator.locator('xpath=/div[1]/div/div[4]/div/div')
					name = name_locator.text_content(timeout=1000).split(' ')[1]
					icons = player_img_base_locator.evaluate('''
						(player) => {
							let sources = [];

							const images = player.getElementsByTagName("img");

							for (image of images) sources.push(image.src);

							return sources;
						}
					''')

					player = {
						'locator': player_base_locator,			
						'name': name,
						'self': False,
						'couple': False
					}

					try:
						if name_locator.evaluate('name => name.style.color') == 'rgb(236, 64, 122)':
							player['self'] = True

							self_number = 4 * (i - 1) + j
					except PlaywrightTimeoutError:
						pass

					for icon in icons:
						if 'junior' in icon:
							if player['self']:
								tag = True

							else:
								vote = False

						elif 'wolf_seer' in icon:
							if player['self']:
								vote = False

							else:
								wolf_seer = True

						elif not player['self'] and 'lovers' in icon:
							player['couple'] = True

							couples.append(4 * (i - 1) + j)

					players.append(player)

				except PlaywrightTimeoutError:
					continue

		if wolf_seer:
			vote = True

		print(f'{Style.BRIGHT}{Fore.GREEN}Players found!')

		textarea = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[2]/div/textarea')

		print(f'{Style.BRIGHT}{Fore.YELLOW}Sending message...')

		textarea.fill(' '.join([str(couple) for couple in couples]))
		textarea.press('Enter')

		print(f'{Style.BRIGHT}{Fore.GREEN}Message sent!')

		if vote and couples:
			print(f'{Style.BRIGHT}{Fore.YELLOW}Voting couple...')

			try:
				players[couples[0] - 1]['locator'].click(timeout=10000)

				print(f'{Style.BRIGHT}{Fore.GREEN}Couple voted!')
			except Exception as e:
				print(f'{Style.BRIGHT}{Fore.RED}{e}')

		if tag:
			print(f'{Style.BRIGHT}{Fore.YELLOW}Finding target...')

			remaining_time = 30 - start_time

			if remaining_time - 5 >= 0:
				time.sleep(remaining_time - 5)

			chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[1]/div/div/div/div')

			messages = chat.evaluate('''
				(chat) => {
					let messages = [];

					const blocks = chat.getElementsByTagName("div");

					for (block of blocks) {
						const text = block.textContent;

						if (text && !messages.includes(text)) messages.push(text);
					}

					return messages;
				}
			''')

			for message in messages:
				if ': ' not in message:
					continue

				player, message = message.split(': ')
				number, player = player.split(' ')
				message = ''.join(message)

				number = int(number)

				if number == self_number or number in couples:
					continue

				words = message.split(' ')

				for word in words:
					if word.isdigit() and 1 <= int(word) <= 16:
						target = int(word)

						print(f'{Style.BRIGHT}{Fore.YELLOW}Target found!')

						break

			else:
				print(f'{Style.BRIGHT}{Fore.RED}Target not found!')

			if target:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Tagging player...')
			
				self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/div/img').click(timeout=10000)

				time.sleep(1)

				try:
					players[target - 1]['locator'].click(timeout=10000)

					print(f'{Style.BRIGHT}{Fore.GREEN}Player tagged!')
				except Exception as e:
					print(f'{Style.BRIGHT}{Fore.RED}{e}')

	def play(self):
		while True:
			banner(self.__class__.__name__)

			print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for room join...')

			while True:
				try:
					if self.page.get_by_text('Добро пожаловать в очередную игру в Wolvesville.').is_visible(timeout=10000):
						break
				except PlaywrightTimeoutError:
					continue

			print(f'{Style.BRIGHT}{Fore.GREEN}Joined!')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for game start...')

			start = False
			werewolf = False

			while True:
				try:
					night_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div[1]/div[3]/div/div[1]')

					if night_chat.text_content(timeout=1000) == 'Чат оборотней':
						werewolf = True

					start = True

					break
				except PlaywrightTimeoutError:
					try:
						create_game_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div/div/div/div/div/div[2]/div[2]/div[2]/div[1]/div/div/div')
						
						if create_game_button.text_content(timeout=1000) == 'СОЗДАТЬ ИГРУ':
							try:
								close_popup_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div')
								
								if close_popup_button.text_content(timeout=1000) == 'Окей':
									close_popup_button.click()
							except PlaywrightTimeoutError:
								pass

							break
					except PlaywrightTimeoutError:
						try:
							start_game_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/div[3]/div[2]/div/div/div')
							
							if start_game_button.text_content(timeout=1000) == 'НАЧАТЬ ИГРУ':
								start_game_button.click()
						except PlaywrightTimeoutError:
							pass
				except:
					continue

			if not start:
				continue

			if werewolf:
				self.act_werewolf()

			else:
				self.act_villager()

			print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for game end...')

			while True:
				try:
					continue_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div').get_by_text('Продолжить')
					continue_button.click(timeout=30000)

					break
				except PlaywrightTimeoutError:
					continue

			print(f'{Style.BRIGHT}{Fore.GREEN}End!')


			print(f'{Style.BRIGHT}{Fore.YELLOW}Exiting...')

			time.sleep(1)

			try:
				play_again_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div[3]/div[5]/div[2]/div/div[2]').get_by_text('Играть снова')
				play_again_button.click(timeout=30000)

				try:
					host_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div/div/div[2]/div/div/div[3]/div[2]/div/div')
					
					if host_button.text_content(timeout=1000) == 'Окей':
						host_button.click()
				except PlaywrightTimeoutError:
					pass
			except PlaywrightTimeoutError:
				playsound('audio/glitch.mp3')

				try:
					close_popup_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div/div')
					
					if close_popup_button.text_content(timeout=1000) == 'Окей':
						close_popup_button.click()
				except PlaywrightTimeoutError:
					self.page.get_by_text('\uf015').click(timeout=10000)

				return

	def run(self):
		banner(self.__class__.__name__)

		try:
			with sync_playwright() as playwright:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Opening website...')

				context = playwright.chromium.launch_persistent_context(
					user_data_dir=self.USER_DATA_DIR,
					user_agent=self.user_agent.random,
					viewport={
						'width': 960,
						'height': 972
					},
					headless=False,
					args=['--window-position=-7,40', '--mute-audio'],
					ignore_default_args=['--enable-automation']
				)

				self.page = context.pages[0]
				
				while True:
					try:
						self.page.goto('https://wolvesville.com', wait_until='commit', timeout=100000)

						break
					except PlaywrightTimeoutError:
						print(f'{Style.BRIGHT}{Fore.RED}Timeout error!{Fore.RESET}')

						continue

				try:
					decline_notifications_button = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div/div/div/div/div/div/div[2]/div[2]/div')
				
					if decline_notifications_button.text_content(timeout=10000) == '\uf00d':
						decline_notifications_button.click()
				except PlaywrightTimeoutError:
					pass

				print(f'{Style.BRIGHT}{Fore.GREEN}Website opened!')

				while True:
					print(f'{Style.BRIGHT}{Fore.YELLOW}Opening custom games menu...')

					while True:
						try:
							play_button = self.page.get_by_text('ИГРАТЬ', exact=True)

							if not play_button.is_disabled(timeout=10000):
								play_button.click()

							break
						except PlaywrightTimeoutError:
							continue

					while True:
						try:
							self.page.get_by_text('ПЕРСОНАЛИЗИРОВАННЫЕ ИГРЫ').click(timeout=10000)

							break
						except PlaywrightTimeoutError:
							continue

					print(f'{Style.BRIGHT}{Fore.YELLOW}Menu opened!')

					self.play()
		except KeyboardInterrupt:
			return
		except Exception as e:
			input(f'\n{Style.BRIGHT}{Back.RED}Browser closed!{Back.RESET}')

			return


def banner(module=None):
	os.system('cls')

	message = f'{Style.BRIGHT}{Fore.RED}Wolves{Fore.YELLOW}GOD{Fore.RESET}'

	if module:
		message += f'{Fore.RED} | {module}'

	message += '\n'

	print(message)


def run():
	while True:
		banner()

		modules = [Tracker(), TrackerV2(), Miner(), Grinder()]
		module = None

		for i, module in enumerate(modules):
			module = module.__class__.__name__

			print(f'{Style.BRIGHT}{Fore.GREEN}{i + 1}. {Fore.RESET}{Back.GREEN}{module}')

		while True:
			choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Module to run:{Fore.RESET} ')

			if choice.isdigit() and 1 <= int(choice) <= i + 1:
				module = modules[int(choice) - 1]

				break

			print(f'\n{Style.BRIGHT}{Back.RED}Incorrect choice!{Back.RESET}')

		module.run()


try:
	run()
except KeyboardInterrupt:
	pass
