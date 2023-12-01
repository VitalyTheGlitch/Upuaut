import requests
import pyautogui
import json
import os
import time
from colorama import Back, Fore, Style, init
from pprint import pprint


init(autoreset=True)


class Tracker:
	def __init__(self):
		self.API_KEY = 'GT1PMvA8ZFsi2y7cN8ZjPoDay4DTXGEF3sGoisuaD5zI5imBwFGCbYDFGmVQkSEG'
		self.BASE_URL = 'https://api.wolvesville.com/'

		self.ROLES = []
		self.ADVANCED_ROLES = []
		self.ROTATION = []
		self.PLAYERS = []
		self.PLAYER_CARDS = []

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

	def load_player_cards(self):
		try:
			with open('cards.json', 'r') as cards_file:
				self.PLAYER_CARDS = json.load(cards_file)
		except:
			self.PLAYER_CARDS = {}

	def write_player_cards(self, player, cards):
		if player not in self.PLAYER_CARDS:
			self.PLAYER_CARDS[player] = cards

		else:
			self.PLAYER_CARDS[player].update(cards)

		with open('cards.json', 'w') as cards_file:
			json.dump(self.PLAYER_CARDS, cards_file)

	def get_roles(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting roles...')

		ENDPOINT = 'roles'

		data = requests.get(f'{self.BASE_URL}{ENDPOINT}', headers=self.HEADERS).json()

		roles = {}

		for role in data['roles']:
			if role['name'] == 'Random regular villager':
				role['name'] = 'RRV'

			if role['name'] == 'Random strong villager':
				role['name'] = 'RSV'

			if role['name'] == 'Random werewolf':
				role['name'] = 'RW'

			if role['name'] == 'Random killer':
				role['name'] = 'RK'

			if role['name'] == 'Random voting':
				role['name'] = 'RV'

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

		return rotations

	def get_player_cards(self, username):
		ENDPOINT = f'players/search?username={username}'

		data = requests.get(f'{self.BASE_URL}{ENDPOINT}', headers=self.HEADERS)

		if not data.ok:
			return

		cards = {c['roleId1']: c['roleId2'] for c in data.json()['roleCards'] if 'roleId2' in c}

		if 'harlot' in cards:
			cards['red-lady'] = cards.pop('harlot')

		if 'cursed-human' in cards:
			cards['cursed'] = cards.pop('cursed-human')

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

				left_roles.extend(rotations[j])

			for role in rotations[i]:
				if role not in left_roles and len(role) == 1:
					role = self.ROLES[role[0]['role']]

					diff_roles.append(role)

					break

		print()

		for i, role in enumerate(diff_roles):
			role = role['name']

			print(f'{Style.BRIGHT}{Fore.GREEN}{i + 1}. {Fore.RESET}{Back.GREEN}{role}')

		while True:
			choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Which of these roles is in the game:{Fore.RESET} ')

			if choice.isdigit() and 1 <= int(choice) <= i + 1:
				rotation = rotations[int(choice) - 1]

				break

			print(f'\n{Style.BRIGHT}{Back.RED}Incorrect choice!{Back.RESET}')

		for i in range(len(rotation)):
			if len(rotation[i]) > 1:
				print()

				for j, role in enumerate(rotation[i]):
					role = self.ROLES[role['role']]['name']

					print(f'{Style.BRIGHT}{Fore.GREEN}{j + 1}. {Fore.RESET}{Back.GREEN}{role}')

				while True:
					choice = input(f'\n{Style.BRIGHT}{Fore.YELLOW}Which of these roles is in the game:{Fore.RESET} ')

					if choice.isdigit() and 1 <= int(choice) <= j + 1:
						role = rotation[i][j - 1]['role']

						if role == 'cursed-human':
							role = 'cursed'

						rotation[i] = self.ROLES[role]
						rotation[i]['id'] = role

						break

					print(f'\n{Style.BRIGHT}{Back.RED}Incorrect choice!{Back.RESET}')

			else:
				role = rotation[i][0]['role']

				if role == 'cursed-human':
					role = 'cursed'

				rotation[i] = self.ROLES[role]
				rotation[i]['id'] = role

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
		cards = self.get_player_cards(name)

		if cards is None:
			input(f'\n{Style.BRIGHT}{Back.RED}Invalid name!{Back.RESET}')

			return

		else:
			self.PLAYERS[player]['name'] = name

			self.write_player_cards(name, cards)

			role = self.PLAYERS[player]['role']

			if role and role not in self.ADVANCED_ROLES:
				for src_role in self.ADVANCED_ROLES:
					if role in self.ADVANCED_ROLES[src_role]:
						break

				self.write_player_cards(name, {src_role: role})

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

		if type(src_role) == list:
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

		for i, role in enumerate(self.ROTATION):
			if role['id'] == src_role:
				self.ROTATION[i] = self.ROLES[dst_role]
				self.ROTATION[i]['id'] = dst_role

				break

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role!{Back.RESET}')

			return

		for i, player in enumerate(self.PLAYERS):
			if self.PLAYERS[i]['role'] == src_role:
				self.PLAYERS[i]['role'] = dst_role
				self.PLAYERS[i]['team'] = self.ROLES[src_role]['team']
				self.PLAYERS[i]['aura'] = self.ROLES[src_role]['aura']

				for equal_player in self.PLAYERS[i]['equal']:
					self.PLAYERS[equal_player]['team'] = self.PLAYERS[i]['team']

				for not_equal_player in self.PLAYERS[i]['not_equal']:
					self.PLAYERS[not_equal_player]['teams_exclude'].add(self.PLAYERS[i]['team'])

				if player['name'] and src_role in self.ADVANCED_ROLES:
					self.write_player_cards(player['name'], {
						src_role: dst_role
					})

				break

	def set_cursed(self):
		for i, role in enumerate(self.ROTATION):
			if role['id'] == 'cursed':
				self.ROTATION[i] = self.ROLES['werewolf']
				self.ROTATION[i]['id'] = role['id']

				break

		for i, player in enumerate(self.PLAYERS):
			if player['role'] == 'cursed':
				self.PLAYERS[i]['role'] = 'werewolf'
				self.PLAYERS[i]['team'] = 'WEREWOLF'
				self.PLAYERS[i]['aura'] = 'EVIL'

				for equal_player in self.PLAYERS[i]['equal']:
					self.PLAYERS[equal_player]['equal'].remove(i)

				for not_equal_player in self.PLAYERS[i]['not_equal']:
					self.PLAYERS[not_equal_player]['not_equal'].remove(i)

				self.PLAYERS[i]['equal'] = set() 
				self.PLAYERS[i]['not_equal'] = set() 

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
			for role in self.ROTATION:
				if info.lower() == role['name'].lower():
					name = self.PLAYERS[player]['name']

					self.PLAYERS[player]['role'] = role['id']
					self.PLAYERS[player]['team'] = role['team']
					self.PLAYERS[player]['aura'] = role['aura']

					for equal_player in self.PLAYERS[player]['equal']:
						self.PLAYERS[equal_player]['team'] = self.PLAYERS[player]['team']

					for not_equal_player in self.PLAYERS[player]['not_equal']:
						self.PLAYERS[not_equal_player]['teams_exclude'].add(self.PLAYERS[player]['team'])

					if name and role['id'] not in self.ADVANCED_ROLES:
						for src_role in self.ADVANCED_ROLES:
							if role['id'] in self.ADVANCED_ROLES[src_role]:
								break

						self.write_player_cards(name, {src_role: role['id']})

					break

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect role or aura!{Back.RESET}')

	def monitor(self):
		banner()

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

			cards = list(self.PLAYER_CARDS.get(name, {}).values())

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

	def run(self):
		banner()

		self.ROLES, self.ADVANCED_ROLES = self.get_roles()

		self.load_player_cards()

		rotations = self.get_rotations()

		self.ROTATION = self.choose_rotation(rotations)

		try:
			while True:
				self.monitor()

				cmd = input(f'\n{Style.BRIGHT}{Fore.RED}>{Fore.RESET} ')

				if cmd.lower() == 'end':
					return

				if cmd.lower().startswith('clear '):
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

						continue

					equal = '!=' if '!=' in cmd else '='

					players = cmd.split(f' {equal} ')

					if len(players) == 2 and players[0].isdigit() and players[1].isdigit():
						players = list(map(int, players))

						if not (1 <= players[0] <= 16 and 1 <= players[1] <= 16):
							input(f'\n{Style.BRIGHT}{Back.RED}Invalid number(s)!{Back.RESET}')

							continue

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

						continue

					self.set_player_info(player, info)
		except KeyboardInterrupt:
			return

class Miner:
	@staticmethod
	def wait_click(path, confidence=0.95, check_fail=False, check_count=7):
		fails = 0

		while True:
			coords = pyautogui.locateCenterOnScreen(path, confidence=confidence)

			if coords:
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

	def shutdown(self, reboot=False):
		self.wait_click('img/close.png')

		if reboot:
			self.wait_click('img/reboot.png')

		else:
			self.wait_click('img/ok.png')

	def back(self):
		self.wait_click('img/back.png')

	def home(self):
		self.wait_click('img/home.png')

	def launch_vpn(self):
		print(f'{Style.BRIGHT}{Fore.GREEN}Launching VPN...')

		self.wait_click('img/vpn_app_icon.png')

		pyautogui.moveTo(100, 100)

		self.wait_click('img/vpn_connect.png')

		pyautogui.moveTo(100, 100)

		while not pyautogui.locateCenterOnScreen('img/vpn_on.png', confidence=0.9):
			time.sleep(5)

	def spin(self):
		while True:
			print(f'{Style.BRIGHT}{Fore.GREEN}Spinning...')

			pyautogui.moveTo(100, 100)

			if not self.wait_click('img/done.png', confidence=0.8, check_fail=True, check_count=1):
				print(f'{Style.BRIGHT}{Fore.GREEN}DONE!')

				return 1

			if self.wait_click('img/ad.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Loading takes too long. Pause for 5 minutes started...')

				time.sleep(300)

				return

			if self.wait_click('img/close_mark.png', confidence=0.99, check_fail=True):
				self.back()

			if self.wait_click('img/spin.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Spin button not found. Restarting...')

				return

	def prepare(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for the emualtor...')

		time.sleep(2)

		self.shutdown(reboot=True)

		time.sleep(30)

		self.back()

		pyautogui.moveTo(100, 100)

		self.back()

		print(f'{Style.BRIGHT}{Fore.GREEN}Preparing...')

		pyautogui.moveTo(100, 100)

		time.sleep(2)

		self.home()

		time.sleep(5)

		self.launch_vpn()
		self.home()

		pyautogui.moveTo(100, 100)

		time.sleep(2)

		self.home()

		time.sleep(5)

		print(f'{Style.BRIGHT}{Fore.GREEN}Launching game...')

		self.wait_click('img/game_app_icon.png')
		self.wait_click('img/cancel.png', check_fail=True)
		
		header = pyautogui.locateCenterOnScreen('img/header.png', confidence=0.8)

		pyautogui.click(header[0], header[1] + 35)

	def run(self):
		banner()

		try:
			while True:
				self.prepare()

				if self.spin():
					self.shutdown()

					input(f'\n{Style.BRIGHT}{Fore.GREEN}Press Enter to continue{Fore.RESET}')

					return
		except KeyboardInterrupt:
			self.shutdown()

			return


def banner():
	os.system('cls')

	print(f'{Style.BRIGHT}{Fore.RED}Wolves{Fore.YELLOW}GOD\n')


def run():
	while True:
		banner()

		modules = [Tracker(), Miner()]
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


run()
