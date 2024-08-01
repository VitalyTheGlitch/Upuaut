import requests
import threading
import pyautogui
import pygetwindow
import psutil
import ntplib
import copy
import json
import os
import subprocess
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from copy import deepcopy
from playsound import playsound
from colorama import Back, Fore, Style, init
from dotenv import dotenv_values

init(autoreset=True)

requests.packages.urllib3.disable_warnings()


class Tracker:
	def __init__(self):
		self.config = dotenv_values('.env')

		try:
			self.API_KEYS = self.config['API_KEYS'].split(',')
			self.USER_AGENT = self.config['USER_AGENT']
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}API key(s) / User Agent not found!{Back.RESET}')

			os.abort()

		self.API_KEY = self.switch_api_key()

		self.ASSET_PATHS = {
			'see': {
				'html': 'main.html',
				'css': 'main.css'
			},
			'see2': {
				'html': 'main.html'
			},
			'messages': {
				'html': 'main.html',
				'css': 'main.css',
				'js': 'main.js'
			}
		}
		self.ASSETS = {}

		self.load_assets()

		self.BEARER_TOKEN = None
		self.CF_JWT = None

		self.BOT_BASE_URL = 'https://api.wolvesville.com/'
		self.BEARER_BASE_URL = 'https://core.api-wolvesville.com/'

		self.ROTATION = []
		self.PLAYERS = []

		self.ROLES = []
		self.ADVANCED_ROLES = {}

		self.RANDOM_ROLE_TYPES = {
			'random-villager-normal': [
				'aura-seer',
				'beast-hunter',
				'bodyguard',
				'doctor',
				'flower-child',
				'loudmouth',
				'mayor',
				'priest',
				'red-lady',
				'sheriff',
				'witch'
			],
			'random-villager-strong': [
				'detective',
				'jailer',
				'medium',
				'seer',
				'vigilante'
			],
			'random-villager-support': [
				'doctor',
				'bodyguard',
				'ghost-lady',
				'sheriff',
				'beast-hunter',
				'bellringer'
			],
			'random-werewolf-weak': 'WEREWOLF',
			'random-werewolf-strong': 'WEREWOLF',
			'random-support-werewolf': [
				'nightmare-werewolf',
				'wolf-shaman',
				'toxic-wolf'
			],
			'random-killer': [
				'arsonist',
				'bandit',
				'corruptor',
				'serial-killer'
			],
			'random-voting': ['fool'],
			'random-other': ['cupid', 'cursed']
		}

		self.ROTATION_ICONS = {}

		self.PLAYER_CARDS = {}
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
				'not_equal': set(),
				'hero': False,
				'messages': [],
				'mentions': []
			})

		self.DISCOVERED = [False, False]
		self.PLAYER_LAYERS = []

		self.BEARER_HEADERS = {}

		self.USER_DATA_DIR = os.getenv('LOCALAPPDATA') + '\\Google\\Chrome\\User Data\\Upuaut'
		self.EXECUTABLE_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

		self.page = None
		self.day_chat = None
		self.dead_chat = None
		self.last_message_number = 0

	@property
	def bot_headers(self):
		api_key = next(self.API_KEY)

		return {
			'Authorization': f'Bot {api_key}',
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		}

	def switch_api_key(self):
		while True:
			for key in self.API_KEYS:
				yield key
		
	def load_assets(self):
		try:
			for asset in self.ASSET_PATHS:
				self.ASSETS[asset] = {}

				for module in self.ASSET_PATHS[asset]:
					filename = self.ASSET_PATHS[asset][module]

					path = f'assets/{asset}/{filename}'

					with open(path, 'r') as asset_file:
						self.ASSETS[asset][module] = asset_file.read()
		except FileNotFoundError:
			input(f'{Style.BRIGHT}{Back.RED}{path} not found!{Back.RESET}')

			os.abort()

	def load_css(self):
		see_css = self.ASSETS['see']['css']
		messages_css = self.ASSETS['messages']['css']

		self.page.evaluate('''
			([see_css, messages_css]) => {
				const head = document.querySelector("head");

				if (!head.querySelector(".see")) {
					style = document.createElement("style");
					style.type = "text/css";
					style.innerHTML = see_css;

					head.appendChild(style);
				}

				if (!head.querySelector(".modal-dialog")) {
					style = document.createElement("style");
					style.type = "text/css";
					style.innerHTML = messages_css;

					head.appendChild(style);
				}
			}
		''', [see_css, messages_css])

	def load_modal(self):
		messages_html = self.ASSETS['messages']['html']
		messages_js = self.ASSETS['messages']['js']

		field = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/div[2]/div/div[1]')
		field.evaluate('''
			(field, [messages_html, messages_js]) => {
				if (!document.querySelector(".modal-header")) {
					const html = document.createElement("div");
					html.className = "modal-content messages";
					html.innerHTML = messages_html;

					field.appendChild(html);

					const js = document.createElement("script");
					js.innerHTML = messages_js;

					document.body.appendChild(js);
				}
			}
		''', [messages_html, messages_js])

	def load_see(self, number, layer):
		see_html = self.ASSETS['see']['html'].format(number)
		see2_html = self.ASSETS['see2']['html'].format(number)

		layer.evaluate('''
			(layer, [number, see_html, see2_html]) => {
				const html = document.createElement("div");
				html.setAttribute("player", number);
				html.className = "see";
				html.innerHTML = see_html;
				html.addEventListener("click", (e) => {
					let player = e.currentTarget.getAttribute("player");

					if (isNaN(player)) return;

					player = parseInt(player);

					if (player < 0 || player > 15) return;

					const name = window.players[player]["name"];
					const messages = window.players[player]["messages"];

					window.messages.setHeader(player + 1 + ' ' + name);
					window.messages.setBody(messages.join("<br>"));
					window.messages.open();
				});

				layer.appendChild(html);

				const html2 = document.createElement("div");
				html2.setAttribute("player", number);
				html2.className = "see";
				html2.style.top = "25%";
				html2.innerHTML = see2_html;
				html2.addEventListener("click", (e) => {
					let player = e.currentTarget.getAttribute("player");

					if (isNaN(player)) return;

					player = parseInt(player);

					if (player < 0 || player > 15) return;

					const name = window.players[player]["name"];
					const mentions = window.players[player]["mentions"];

					window.messages.setHeader(player + 1 + ' ' + name);
					window.messages.setBody(mentions.join("<br>"));
					window.messages.open();
				});

				layer.appendChild(html2);
			}
		''', [number, see_html, see2_html])

	def load_cards(self):
		try:
			with open('data/cards.json', 'r') as cards_file:
				self.PLAYER_CARDS = json.load(cards_file)
		except:
			self.PLAYER_CARDS = {}

	def write_cards(self, player, cards):
		if player not in self.PLAYER_CARDS:
			self.PLAYER_CARDS[player] = cards

		else:
			self.PLAYER_CARDS[player].update(cards)

	def save_cards(self):
		if not os.path.isdir('data'):
			os.mkdir('data')

		with open('data/cards.json', 'w') as cards_file:
			json.dump(self.PLAYER_CARDS, cards_file)

	def load_icons(self):
		try:
			with open('data/icons.json', 'r') as icons_file:
				self.PLAYER_ICONS = json.load(icons_file)
		except:
			self.PLAYER_ICONS = {}

	def write_icons(self, player, icons):
		if player not in self.PLAYER_ICONS:
			self.PLAYER_ICONS[player] = icons

		else:
			self.PLAYER_ICONS[player].update(icons)

	def save_icons(self):
		if not os.path.isdir('data'):
			os.mkdir('data')

		with open('data/icons.json', 'w') as icons_file:
			json.dump(self.PLAYER_ICONS, icons_file)

	def get_roles(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting roles...')

		ENDPOINT = 'roles'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return None, None

		data = data.json()

		roles = {}

		for role in data['roles']:
			role['id'] = role['id'].replace('random-village', 'random-villager')

			if role['id'] == 'random-villager-normal':
				role['name'] = 'RRV'

			elif role['id'] == 'random-villager-strong':
				role['name'] = 'RSV'

			elif role['id'] == 'random-werewolf':
				role['name'] = 'RW'

			elif role['id'] == 'random-killer':
				role['name'] = 'RK'

			elif role['name'] == 'random-voting':
				role['name'] = 'RV'

			if role['team'] in ['VILLAGER', 'RANDOM_VILLAGER']:
				role['team'] = 'VILLAGER'

			elif role['team'] == ['WEREWOLF', 'RANDOM_WEREWOLF']:
				role['team'] = 'WEREWOLF'

			else:
				role['team'] = 'SOLO'

			roles[role['id']] = {
				'name': role['name'],
				'team': role['team'],
				'aura': role['aura']
			}

			role.pop('id')

		roles['cursed'] = roles.pop('cursed-human')

		roles['red-lady'] = roles.pop('harlot')

		roles['random-villager-support'] = {
			'team': 'VILLAGER',
			'aura': 'GOOD',
			'name': 'RSPV'
		}

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

		roles['random-support-werewolf'] = {
			'team': 'WEREWOLF',
			'aura': 'EVIL',
			'name': 'RSPW'
		}

		roles['random-other'] = {
			'team': 'VILLAGER',
			'aura': 'GOOD',
			'name': 'RO'
		}

		advanced_roles = data['advancedRolesMapping']

		advanced_roles['cursed'] = advanced_roles.pop('cursed-human')

		advanced_roles['red-lady'] = advanced_roles.pop('harlot')

		return roles, advanced_roles

	def get_icons(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting icons...')

		ENDPOINT = 'items/roleIcons'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return

		data = data.json()

		icons = {}

		for icon in data:
			icons[icon['id']] = {
				'filename': icon['image']['url'].split('roleIcons/')[1],
				'role': icon['roleId']
			}

		return icons

	def get_rotations(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Getting role rotations...')

		ENDPOINT = 'roleRotations'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False).json()

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

	def get_player(self, username):
		ENDPOINT = f'players/search?username={username}'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json()

		player_id = data['id']

		cards = {}

		for card in data['roleCards']:
			if card['rarity'] in ['COMMON', 'RARe']:
				continue

			if card['roleId1'] == 'harlot':
				card['roleId1'] = 'red-lady'

			elif card['roleId1'] == 'cursed-human':
				card['roleId1'] = 'cursed'

			elif card['roleId1'] in ['fool', 'headhunter']:
				continue

			if 'roleId2' in card:
				cards[card['roleId1']] = card['roleId2']

		time.sleep(0.1)

		ENDPOINT = f'playerRoleStats/achievements/{player_id}'

		data = requests.get(f'{self.BEARER_BASE_URL}{ENDPOINT}', headers=self.BEARER_HEADERS, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json()

		icons = {}

		for achievement in data:
			if achievement['roleId'] == 'harlot':
				achievement['roleId'] = 'red-lady'

			elif achievement['roleId'] == 'cursed-human':
				achievement['roleId'] = 'cursed'

			if 'roleIconId' in achievement:
				icons[achievement['roleId']] = achievement['roleIconId']

			if achievement['roleId'] in ['fool', 'headhunter', 'zombie']:
				continue

			for role in self.ROLES:
				if achievement['roleId'] in self.ADVANCED_ROLES.get(role, []):
					cards[role] = achievement['roleId']

					break

		return 0, cards, icons

	def clear_player_info(self, player, info):
		if info == 'all':
			hero = self.PLAYERS[player]['hero']
			messages = self.PLAYERS[player]['messages']
			mentions = self.PLAYERS[player]['mentions']

			self.PLAYERS[player] = {
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set(),
				'hero': hero,
				'messages': messages,
				'mentions': mentions
			}

		elif info == 'name':
			self.PLAYERS[player]['name'] = None

		elif info == 'role':
			self.PLAYERS[player]['role'] = None
			self.PLAYERS[player]['team'] = None
			self.PLAYERS[player]['aura'] = None

		elif info == 'team':
			self.PLAYERS[player]['role'] = None
			self.PLAYERS[player]['team'] = None
			self.PLAYERS[player]['teams_exclude'] = set()

		elif info == 'aura':
			self.PLAYERS[player]['role'] = None
			self.PLAYERS[player]['aura'] = None

		elif info == 'equal':
			self.PLAYERS[player]['equal'] = set()
			self.PLAYERS[player]['not_equal'] = set()

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Invalid info!{Back.RESET}')

			return

	def storm(self):
		PLAYERS_OLD = deepcopy(self.PLAYERS)

		self.PLAYERS = []

		for _ in range(16):
			self.PLAYERS.append({
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set(),
				'hero': False,
				'messages': [],
				'mentions': []
			})

		self.find_players()

		for p in range(16):
			for o, old in enumerate(PLAYERS_OLD):
				if self.PLAYERS[p]['name'] == old['name']:
					self.PLAYERS[p] = old

					PLAYERS_OLD.pop(o)

		self.last_message_number = 0

	def revert(self, action):
		if not self.PREV_PLAYERS:
			input(f'\n{Style.BRIGHT}{Back.RED}Last revert reached!{Back.RESET}')

		else:
			self.PLAYERS = deepcopy(self.PREV_PLAYERS[-1])

			if action:
				self.PREV_PLAYERS.pop()

		return -1

	def set_name(self, player, name, threaded=False):
		data = self.get_player(name)

		if data[0] == 404:
			input(f'\n{Style.BRIGHT}{Back.RED}Invalid name!{Back.RESET}')

			return 404

		elif data[0]:
			input(f'\n{Style.BRIGHT}{Back.RED}Error {data[0]}: {data[1]}{Back.RESET}')

			return data[0]

		cards, icons = data[1:]

		self.PLAYERS[player]['name'] = name

		if self.PLAYERS[player]['hero']:
			return

		self.write_cards(name, cards)
		self.write_icons(name, icons)

		role = self.PLAYERS[player]['role']

		if role and role not in self.ADVANCED_ROLES:
			for src_role in self.ADVANCED_ROLES:
				if role in self.ADVANCED_ROLES[src_role]:
					self.write_cards(name, {src_role: role})

					break

		if not threaded:
			self.save_cards()
			self.save_icons()

	def set_role(self, player, role):
		for r in range(len(self.ROTATION)):
			if role.lower() == self.ROTATION[r]['name'].lower():
				break

			elif self.ROTATION[r]['id'] in self.RANDOM_ROLE_TYPES:
				type_roles = self.RANDOM_ROLE_TYPES[self.ROTATION[r]['id']]
				dst_role = None

				if type(type_roles) == str:
					for role1 in self.ROLES:
						if role.lower() == self.ROLES[role1]['name'].lower():
							if self.ROLES[role1]['team'] == type_roles:
								dst_role = self.ROLES[role1]

							break

				else:
					for random_role in type_roles:
						if role.lower() == self.ROLES[random_role]['name'].lower():
							dst_role = self.ROLES[random_role]

							break

						elif random_role in self.ADVANCED_ROLES:
							for advanced_role in self.ADVANCED_ROLES[random_role]:
								if role.lower() == self.ROLES[advanced_role]['name'].lower():
									dst_role = self.ROLES[advanced_role]

									break

							if dst_role:
								break

				if dst_role:
					self.change_role(self.ROTATION[r]['name'], dst_role['name'])

					break

		else:
			return 1

		self.PLAYERS[player]['role'] = self.ROTATION[r]['id']
		self.PLAYERS[player]['team'] = self.ROTATION[r]['team']
		self.PLAYERS[player]['aura'] = self.ROTATION[r]['aura']

		for equal_player in self.PLAYERS[player]['equal']:
			self.PLAYERS[equal_player]['team'] = self.PLAYERS[player]['team']

		for not_equal_player in self.PLAYERS[player]['not_equal']:
			self.PLAYERS[not_equal_player]['teams_exclude'].add(self.PLAYERS[player]['team'])

		if self.PLAYERS[player]['hero'] or self.ROTATION[r]['id'] == 'zombie':
			return

		name = self.PLAYERS[player]['name']

		if name and self.ROTATION[r]['id'] not in self.ADVANCED_ROLES:
			for src_role in self.ADVANCED_ROLES:
				if self.ROTATION[r]['id'] in self.ADVANCED_ROLES[src_role]:
					break

			self.write_cards(name, {src_role: self.ROTATION[r]['id']})
			self.save_cards()

		if self.ROTATION[r]['id'] in self.ROTATION_ICONS:
			self.write_icons(name, {self.ROTATION[r]['id']: self.ROTATION_ICONS[self.ROTATION[r]['id']]})
			self.save_icons()

	def change_role(self, src_role, dst_role):
		is_random = False

		for role in self.ROLES:
			if self.ROLES[role]['name'].lower() == dst_role.lower():
				dst_role = self.ROLES[role]
				dst_role['id'] = role

				break

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect destination role!{Back.RESET}')

			return

		for r, role in enumerate(self.ROTATION):
			if role['name'].lower() == src_role.lower():
				src_role = role['id']

				if 'random' in src_role:
					is_random = True

				break

		else:
			input(f'\n{Style.BRIGHT}{Back.RED}Incorrect source role!{Back.RESET}')

			return

		self.ROTATION[r] = dst_role
		self.ROTATION[r]['id'] = dst_role['id']

		for p, player in enumerate(self.PLAYERS):
			if self.PLAYERS[p]['role'] == src_role:
				self.PLAYERS[p]['role'] = dst_role['id']
				self.PLAYERS[p]['team'] = dst_role['team']
				self.PLAYERS[p]['aura'] = dst_role['aura']

				if player['name'] and not player['hero'] and not is_random and dst_role['id'] not in self.ADVANCED_ROLES:
					self.write_cards(player['name'], {
						src_role: dst_role['id']
					})

				break

		self.save_cards()

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

		elif info.lower() in ['villager', 'werewolf', 'solo']:
			self.PLAYERS[player]['team'] = info.upper()

		elif info.lower().startswith('not'):
			info = info.lower().replace('not ', '', 1)

			if info in ['villager', 'werewolf', 'solo']:
				self.PLAYERS[player]['teams_exclude'].add(info.upper())

		else:
			if self.set_role(player, info):
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect info!{Back.RESET}')

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

		rotations = deepcopy(flatten_rotations)

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

	def get_bearer(self):
		self.BEARER_TOKEN = self.page.evaluate('() => JSON.parse(localStorage.getItem("authtokens"))["idToken"]')
		self.CF_JWT = self.page.evaluate('() => localStorage.getItem("cloudflare-turnstile-jwt")')

		self.BEARER_HEADERS = {
			'Authorization': f'Bearer {self.BEARER_TOKEN}',
			'Cf-Jwt': f'{self.CF_JWT}',
			'Ids': '1'
		}

	def update_players(self):
		updates = 0

		service_messages = []
		player_messages = []

		for chat in (self.day_chat, self.dead_chat):
			try:
				if chat.is_hidden(timeout=1000):
					break

				result = chat.evaluate('''
					(chat, last_message_number) => {
						let service_messages = [],
						player_messages = [],
						messages = chat.querySelectorAll("div [dir=auto]");

						if (messages.length < last_message_number) return;

						for (let m = last_message_number; m < messages.length; ++m) {
							blocks = messages[m].querySelectorAll("div > span");

							if (!blocks.length || blocks.length >= 3) service_messages.push(messages[m].textContent);
							else player_messages.push(messages[m].textContent);
						}

						last_message_number = messages.length;

						return [service_messages, player_messages, last_message_number];
					}
				''', self.last_message_number)

				if result is not None:
					service_messages, player_messages, self.last_message_number = result

					break
			except:
				continue

		if len(service_messages):
			if len(self.PREV_PLAYERS) == 3:
				self.PREV_PLAYERS.pop(0)

			self.PREV_PLAYERS.append(deepcopy(self.PLAYERS))

		for service_message in service_messages:
			player = None
			number = None
			name = None
			role = None
			dead = True

			if 'убил' in service_message:
				if 'дождь' in service_message:
					player = service_message.split(' дождь на ')[1].split(' и убил его.')[0]

				elif 'воду' in service_message:
					if 'себя' in service_message:
						players = service_message.split(' кинул святую воду в ')

						for p in range(2):
							number = int(players[p].split(' ')[0]) - 1
							name = players[p].split(' ')[1]	

							if '/' in players[p]:
								role = players[p].split(' / ')[1].split(')')[0]

							self.set_name(number, name)
							self.PLAYERS[number]['dead'] = not p

							if role:
								self.set_role(number, role)

					else:
						players = service_message.split(' кинул святую воду и убил ')

						for p in range(2):
							number = int(players[p].split(' ')[0]) - 1
							name = players[p].split(' ')[1]	

							if '/' in players[p]:
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

						if '/' in players[p]:
							role = players[p].split(' / ')[1].split(')')[0]

						self.set_name(number, name)
						self.PLAYERS[number]['dead'] = p

						if role:
							self.set_role(number, role)

					continue

				elif 'выстрелить' in service_message:
					players = service_message.split(', но убил')[0].split(' попытался выстрелить в ')

					for p in range(2):
						number = int(players[p].split(' ')[0]) - 1
						name = players[p].split(' ')[1]	

						if '/' in players[p]:
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

			elif 'съел' in service_message:
				player = service_message.split(' съел ')[1]

			elif 'поджёг' in service_message:
				player = service_message.split(' поджёг ')[1]

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

						if '/' in players[p]:
							role = players[p].split(' / ')[1].split(')')[0]

						self.set_name(number, name)
						self.PLAYERS[number]['dead'] = p

						if role:
							self.set_role(number, role)

					continue

			elif 'казнил' in service_message:
				if 'Тюремщик' in service_message:
					player = service_message.split(' ночью. ')[1].split(' умер.')[0]

				else:
					player = service_message.split(' казнил ')[1]

			elif 'Меч' in service_message:
				player = service_message.split(' чтобы убить ')[1]

			elif 'посетил' in service_message and 'Ты' not in service_message:
				player = service_message.split(' посетил ')[0]
				role = 'Red lady'

			elif 'был ранен' in service_message:
				player = service_message.split(' был ')[0][6:]

			elif 'раскрыть роль' in service_message:
				player = service_message.split(' раскрыть роль ')[1]
				dead = False

			elif 'отомщена' in service_message:
				player = service_message.split(' отомщена, ')[1].split(' погиб!')[0]

			elif 'душе' in service_message:
				player = service_message.split(' погиб ')[0]

			elif 'привязан' in service_message:
				player = service_message.split(' был убит ')[0]

			elif 'связал' in service_message:
				player = service_message.split('Роль ')[1].split(' была ')[0]

			elif 'отравлен' in service_message:
				player = service_message.split(' отравлен ')[0]

			elif 'мэр!' in service_message:
				player = service_message.split('Игрок ')[1].split(' - ')[0]

				number, name = player.split(' ')
				number = int(number) - 1
				role = 'Mayor'
				dead = False

			elif 'проповедник!' in service_message:
				player = service_message.split('Игрок ')[1].split(' - ')[0]

				number, name = player.split(' ')
				number = int(number) - 1
				role = 'Preacher'
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
				number = int(player.split(' ')[0]) - 1
				name = player.split(' ')[1]

				self.PLAYERS[number]['dead'] = False
				self.PLAYERS[number]['hero'] = True
				self.set_name(number, name)

				continue

			elif 'победил' in service_message:
				return 1

			if player:
				player = player.replace('.', '').replace('!', '')

				if not number:
					number = int(player.split(' ')[0]) - 1
					name = player.split(' ')[1]

				if role is None and '/' in service_message:
					role = player.split(' / ')[1].split(')')[0]

				self.set_name(number, name)
				self.PLAYERS[number]['dead'] = dead

				if role:
					self.set_role(number, role)

		for player_message in player_messages:
			if 'Приватное' in player_message or 'Сбежавший' in player_message:
				continue

			player_message = player_message.split(': ', 1)

			if len(player_message) != 2:
				continue

			player, message = player_message

			if ' ' not in player:
				continue

			number = int(player.split(' ')[0]) - 1
			name = player.split(' ')[1]

			self.PLAYERS[number]['messages'].append(message)

			for pp in range(len(self.PREV_PLAYERS)):
				self.PREV_PLAYERS[pp][number]['messages'].append(message)

			number = ''

			for s in message:
				if s.isdigit():
					number += s

				elif number:
					if int(number) in range(1, 17):
						self.PLAYERS[int(number) - 1]['mentions'].append(message)

						for pp in range(len(self.PREV_PLAYERS)):
							self.PREV_PLAYERS[pp][int(number) - 1]['mentions'].append(message)

					number = ''

		self.page.evaluate('(players) => window.players = players', self.PLAYERS)

	def set_players_range(self, number=0, start=0, end=16):
		for player in self.PLAYER_LAYERS[start:end]:
			self.set_name(player['number'], player['name'], threaded=True)

		if not number:
			self.DISCOVERED = [True, True]

		else:
			self.DISCOVERED[number - 1] = True

	def find_players(self):
		self.DISCOVERED = [False, False]
		self.PLAYER_LAYERS = []

		print(f'{Style.BRIGHT}{Fore.YELLOW}Finding players...')

		for i in range(1, 5):
			for j in range(1, 5):
				try:
					number = 4 * (i - 1) + j - 1

					player_layer_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[{i}]/div[{j}]/div')
					player_base_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[{i}]/div[{j}]/div')
					name_locator = player_base_locator.locator('xpath=/div[1]/div/div[4]/div/div')
					name = name_locator.text_content(timeout=1000).split(' ')[1]

					self.PLAYER_LAYERS.append({
						'number': number,
						'name': name,
						'locator': player_layer_locator
					})

					time.sleep(0.1)
				except PlaywrightTimeoutError:
					continue

		if len(self.API_KEYS) >= 2:
			threading.Thread(target=self.set_players_range, args=(1, 0, 8), daemon=True).start()
			threading.Thread(target=self.set_players_range, args=(2, 8, 16), daemon=True).start()

		else:
			find_players_range()

		while not all(self.DISCOVERED):
			time.sleep(1)

		for layer in self.PLAYER_LAYERS:
			self.load_see(layer['number'], layer['locator'])

		self.PREV_PLAYERS = [deepcopy(self.PLAYERS)]
		self.page.evaluate('(players) => window.players = players', self.PLAYERS)
		self.save_cards()

		print(f'{Style.BRIGHT}{Fore.GREEN}Players found!')

	def find_roles(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Finding roles...')

		roles_base_locator = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[2]/div')

		rotation_icons = roles_base_locator.evaluate('''
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

		for rotation_icon in rotation_icons:
			rotation_icon = rotation_icon.replace('@3x', '')
			if 'roleIcons' in rotation_icon and 'random' not in rotation_icon:
				rotation_icon = rotation_icon.split('roleIcons/')[1]

				for icon in self.ICONS:
					if self.ICONS[icon]['filename'] == rotation_icon:
						role = self.ICONS[icon]['role']

						if role == 'cursed-human':
							role = 'cursed'

						elif role == 'harlot':
							role = 'red-lady'

						roles.append(role)

						self.ROTATION_ICONS[role] = icon

						break

				else:
					input(rotation_icon, 'not found!')

			else:
				role = rotation_icon.split('icon_')[1].split('_filled')[0]
				role = role.replace('.svg', '').replace('.png', '')
				role = role.replace('_', '-')

				if 'cursed' in role:
					role = 'cursed'

				elif 'harlot' in role:
					role = 'red-lady'

				elif 'flowedchild' in role:
					role = 'flower-child'

				elif 'rolechange' in role:
					role = 'random-other'

				elif 'kittenwolf' in role:
					role = 'kitten-wolf'

				elif 'nightmare' in role:
					role = 'nightmare-werewolf'

				for _ in range(2):
					if role in self.ROLES:
						break

					role = role[role.find('-') + 1:]

				roles.append(role)

		print(f'{Style.BRIGHT}{Fore.GREEN}Roles found!')

		return roles

	def finish(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Finishing...')

		for p in range(1, 17):
			role_icon_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[2]/div/div[3]/div/div/div[{p}]/div/div[1]/div/div/img')
			number_locator = self.page.locator(f'xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/div/div[3]/div/div/div[{p}]/div/div[2]')

			try:
				role_icon = role_icon_locator.evaluate('(locator) => locator.src')
				number = number_locator.evaluate('(locator) => locator.textContent')
			except PlaywrightTimeoutError:
				continue

			if 'roleIcons' in role_icon and 'random' not in role_icon:
				role_icon = role_icon.split('roleIcons/')[1]

				for icon in self.ICONS:
					if self.ICONS[icon]['filename'] == role_icon:
						role = self.ICONS[icon]['role']

						if role == 'cursed-human':
							role = 'cursed'

						elif role == 'harlot':
							role = 'red-lady'

						break

			else:
				role = role_icon.split('icon_')[1].split('_filled')[0]
				role = role.replace('.svg', '').replace('.png', '')
				role = role.replace('_', '-')

				if 'cursed' in role:
					role = 'cursed'

				elif 'harlot' in role:
					role = 'red-lady'

				elif 'flowedchild' in role:
					role = 'flower-child'

				elif 'rolechanges' in role:
					role = 'random-other'

				elif 'kittenwolf' in role:
					role = 'kitten-wolf'

				elif 'nightmare' in role:
					role = 'nightmare-werewolf'

				for _ in range(2):
					if role in self.ROLES:
						break

					role = role[role.find('-') + 1:]

		print(f'{Style.BRIGHT}{Fore.GREEN}Finished!')

	def prepare(self):
		self.ROTATION = []
		self.PLAYERS = []

		self.ROTATION_ICONS = {}

		self.PLAYER_CARDS = {}
		self.PLAYER_ICONS = {}

		self.load_cards()
		self.load_icons()

		self.ROLES, self.ADVANCED_ROLES = self.get_roles()
		self.ICONS = self.get_icons()

		if not any([self.ROLES, self.ADVANCED_ROLES, self.ICONS]):
			return 1

		self.last_message_number = 0

		for _ in range(16):
			self.PLAYERS.append({
				'name': None,
				'role': None,
				'team': None,
				'teams_exclude': set(),
				'aura': None,
				'dead': False,
				'equal': set(),
				'not_equal': set(),
				'hero': False,
				'messages': [],
				'mentions': []
			})

		self.day_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div/div/div[1]/div/div/div').first
		self.dead_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div/div[2]/div/div/div[1]/div/div/div')

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
			messages = player['messages']

			cards = list(self.PLAYER_CARDS.get(name, {}).values())
			icons = self.PLAYER_ICONS.get(name, {})
			possible = []

			if not player['role']:
				for role in self.ROTATION:
					if 'random' in role['id']:
						continue

					player_icon = icons.get(role['id'])
					role_icon = self.ROTATION_ICONS.get(role['id'])

					base_test = [
						role['team'] not in teams_exclude,
						not team or team == role['team'],
						not aura or aura == role['aura'],
						self.ROLES[role['id']]['name'] in remaining[role['aura']]
					]

					role_test = [
						role['id'] in cards,
						not player_icon or player_icon == role_icon
					]

					if all(base_test) and all(role_test):
						possible.append({
							'role': self.ROLES[role['id']]['name'],
							'has_card': role['id'] in cards,
							'has_icon': player_icon == role_icon
						})

			info = f'{i + 1}'

			if name:
				info += f' {name}'

			info += f' ({len(messages)})'

			if player['role']:
				role = self.ROLES[player['role']]['name']
				info += f' - {role}'

			elif team:
				info += f' [{team}]'

			elif teams_exclude:
				teams_exclude = ', '.join(teams_exclude)

				info += f' [NOT {teams_exclude}]'

			if possible:
				info += ' + POSSIBLE '

				for p in range(len(possible)):
					role = possible[p]['role']
					has_card = possible[p]['has_card']
					has_icon = possible[p]['has_icon']

					info += role

					if not has_card and not has_icon:
						info += ' ❌⭕'

					elif not has_card:
						info += ' ❌'

					elif not has_icon:
						info += ' ⭕'

					if p != len(possible) - 1:
						info += ' / '

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

			info += '\n'

			players_info += info

		print(f'{Style.BRIGHT}{players_info}{remaining_info}')

	def process(self):
		cmd = input(f'\n{Style.BRIGHT}{Fore.RED}>{Fore.RESET} ')

		if not cmd:
			return

		elif cmd.lower() == 'end':
			return 1

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

		elif cmd.lower().startswith('name of '):
			cmd = cmd.split(' ')

			if len(cmd) == 5 and cmd[3].lower() == 'is' and cmd[2].isdigit() and 1 <= int(cmd[2]) <= 16:
				player = int(cmd[2]) - 1
				name = cmd[4]

				self.set_name(player, name)

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect number!{Back.RESET}')

		elif cmd.lower().startswith('change '):
			query = cmd.lower().split('change ')[1].split(' to ')

			if len(query) == 2:
				src_role, dst_role = query

				self.change_role(src_role, dst_role)

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Invalid syntax!{Back.RESET}')

		elif cmd.lower() == 'cursed turned':
			self.set_cursed()

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

		elif cmd.lower() == 'storm':
			self.storm()

		elif cmd.lower() in ['undo', 'redo']:
			self.revert(cmd.lower() == 'undo')

			return -1

		else:
			try:
				player, info = cmd.lower().split(' is ')
			except ValueError:
				print(f'\n{Style.BRIGHT}{Fore.RED}Usage:')
				print(f'{Style.BRIGHT}{Fore.RED}[number] is [role / aura / (not) team / dead / alive]')
				print(f'{Style.BRIGHT}{Fore.RED}[number] [= / !=] [number]')
				print(f'{Style.BRIGHT}{Fore.RED}Name of [number] is [name]')
				print(f'{Style.BRIGHT}{Fore.RED}Change [role] to [role]')
				print(f'{Style.BRIGHT}{Fore.RED}Cursed turned')
				print(f'{Style.BRIGHT}{Fore.RED}Clear [number] [all / name / role / team / aura / equal]')
				print(f'{Style.BRIGHT}{Fore.RED}Storm to rediscover')
				print(f'{Style.BRIGHT}{Fore.RED}Enter to update')
				print(f'{Style.BRIGHT}{Fore.RED}Undo to cancel role updates')
				print(f'{Style.BRIGHT}{Fore.RED}Redo to return role updates')
				print(f'{Style.BRIGHT}{Fore.RED}End - stop Tracker')
				input()

				return

			self.set_player_info(player, info)

	def run(self):
		banner(self.__class__.__name__)

		try:
			with sync_playwright() as playwright:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Opening website...')

				context = playwright.chromium.launch_persistent_context(
					user_data_dir=self.USER_DATA_DIR,
					user_agent=self.USER_AGENT,
					viewport={
						'width': 960,
						'height': 972
					},
					executable_path=self.EXECUTABLE_PATH,
					headless=False,
					args=['--window-position=-7,40', '--mute-audio'],
					ignore_default_args=['--enable-automation'],
					chromium_sandbox=True
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

					if self.prepare():
						input(f'\n{Style.BRIGHT}{Back.RED}Invalid API key!{Back.RESET}')

						return

					print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for game start...')

					while True:
						try:
							night_chat = self.page.locator('xpath=/html/body/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[3]/div/div[1]/div[1]/div/div[1]')

							if night_chat.text_content(timeout=1000) == 'Дневной чат':
								break
						except KeyboardInterrupt:
							return
						except:
							continue

					print(f'{Style.BRIGHT}{Fore.GREEN}Game found!')

					self.get_bearer()
					self.load_css()
					self.find_players()
					self.load_modal()

					roles = self.find_roles()
					rotations = self.get_rotations()

					print(f'{Style.BRIGHT}{Fore.YELLOW}Finding rotation...')

					self.ROTATION = self.choose_rotation(rotations, roles)

					if self.ROTATION is None:
						input(f'\n{Style.BRIGHT}{Back.RED}Rotation not found!{Back.RESET}')

						return

					print(f'{Style.BRIGHT}{Fore.GREEN}Rotation found!')

					while True:
						self.monitor()

						result = self.process()

						if result == 1:
							break

						if not result:
							self.update_players()
		except KeyboardInterrupt:
			return
		except KeyboardInterrupt as e:
			input(f'\n{Style.BRIGHT}{Back.RED}Browser closed!{Back.RESET}')

			return


class Booster:
	def __init__(self):
		self.config = dotenv_values('.env')

		try:
			self.USER_AGENT = self.config['USER_AGENT']
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}User Agent not found!{Back.RESET}')

			os.abort()

		self.USER_DATA_DIR = os.getenv('LOCALAPPDATA') + '\\Google\\Chrome\\User Data\\Upuaut'
		self.EXECUTABLE_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
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
					time.sleep(0.1)

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
					user_agent=self.USER_AGENT,
					viewport={
						'width': 960,
						'height': 972
					},
					executable_path=self.EXECUTABLE_PATH,
					headless=False,
					args=['--window-position=-7,40', '--mute-audio'],
					ignore_default_args=['--enable-automation'],
					chromium_sandbox=True
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


class Spinner:
	def __init__(self):
		self.config = dotenv_values('.env')

		try:
			self.BLUESTACKS5_PATH = self.config['BLUESTACKS5_PATH']
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}Path to BlueStacks 5 not found!{Back.RESET}')

			os.abort()

		if not os.path.isfile(self.BLUESTACKS5_PATH):
			input(f'{Style.BRIGHT}{Back.RED}Path to BlueStacks 5 is invalid!{Back.RESET}')

			os.abort()

		try:
			self.BLUESTACKS5_NAME = self.config['BLUESTACKS5_NAME']
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}Name of BlueStacks 5 window not found!{Back.RESET}')

			os.abort()

	@staticmethod
	def wait(filename, confidence=0.9, check_fail=False, check_count=7, click=True):
		fails = 0

		while True:
			coords = pyautogui.locateCenterOnScreen('images/' + filename, confidence=confidence)

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
	def open_wheel():
		time.sleep(1)

		while True:
			header = pyautogui.locateCenterOnScreen('images/header.png', confidence=0.8)

			if header:
				break

		pyautogui.click(header[0], header[1] + 35)

	def kill(self):
		for p in psutil.process_iter():
		    if p.name() == 'HD-Player.exe':
		        p.kill()

		        return

	def back(self):
		self.wait('back.png')

	def home(self):
		self.wait('home.png')

	def close_all(self):
		self.wait('recent.png')
		self.wait('clear.png')

	def spin(self):
		while True:
			print(f'{Style.BRIGHT}{Fore.YELLOW}Checking ad button...')

			pyautogui.moveTo(100, 100)

			if not self.wait('done.png', confidence=0.8, check_fail=True, check_count=2):
				print(f'{Style.BRIGHT}{Fore.GREEN}DONE!')

				playsound('audio/confusion.mp3')

				return 1

			if self.wait('ad.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Loading takes too long.')

				return

			print(f'{Style.BRIGHT}{Fore.YELLOW}Watching ad...')

			time.sleep(35)

			self.back()

			print(f'{Style.BRIGHT}{Fore.YELLOW}Checking spin button...')

			if self.wait('spin.png', confidence=0.8, check_fail=True):
				print(f'{Style.BRIGHT}{Fore.RED}Spin button not found.') 

				return

			else:
				print(f'{Style.BRIGHT}{Fore.GREEN}Spinned!')

	def prepare(self):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for game load...')

		while self.wait('game.png', check_fail=True):
			self.home()

		self.wait('profile.png', click=False)
		self.wait('cancel.png', check_fail=True, check_count=3)
		self.open_wheel()

		print(f'{Style.BRIGHT}{Fore.GREEN}Game loaded!')

	def run(self):
		banner(self.__class__.__name__)

		print(f'{Style.BRIGHT}{Fore.YELLOW}Waiting for BlueStacks 5...')

		subprocess.Popen(self.BLUESTACKS5_PATH, stdout=subprocess.PIPE)

		self.home()

		print(f'{Style.BRIGHT}{Fore.GREEN}BlueStacks 5 found!')

		try:
			window = pygetwindow.getWindowsWithTitle(self.BLUESTACKS5_NAME)[0]
			window.size = (540, 934)
		except IndexError:
			input(f'{Style.BRIGHT}{Back.RED}Name of BlueStacks 5 window is invalid!{Back.RESET}')

			os.abort()

		try:
			while True:
				self.prepare()

				if self.spin():
					self.kill()

					print(f'\n{Style.BRIGHT}{Fore.YELLOW}Press Enter to exit.{Fore.RESET}')
					input()

					return

				print(f'{Style.BRIGHT}{Fore.YELLOW}Restarting...')

				self.close_all()
		except KeyboardInterrupt:
			self.kill()

			return


class Stalker:
	def __init__(self):
		self.config = dotenv_values('.env')

		try:
			self.API_KEYS = self.config['API_KEYS'].split(',')
		except KeyError:
			input(f'{Style.BRIGHT}{Back.RED}API key(s) not found!{Back.RESET}')

			os.abort()

		self.ntp = ntplib.NTPClient()
		self.NTP_SERVER = 'pool.ntp.org'

		self.API_KEY = self.switch_api_key()

		self.BOT_BASE_URL = 'https://api.wolvesville.com/'
		self.TARGETS = {}
		self.updating = False

		self.load_targets()
		
		threading.Thread(target=self.auto_update, daemon=True).start()

	@staticmethod
	def convert_play_time(minutes):
		if minutes == -1:
			return -1

		hours = str(minutes // 60).zfill(2)
		minutes = str(minutes % 60).zfill(2)

		return f'{hours}:{minutes}'

	@property
	def bot_headers(self):
		api_key = next(self.API_KEY)

		return {
			'Authorization': f'Bot {api_key}',
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		}

	def switch_api_key(self):
		while True:
			for key in self.API_KEYS:
				yield key

	def load_targets(self):
		try:
			with open('data/targets.json', 'r', encoding='utf-8') as targets_file:
				self.TARGETS = json.load(targets_file)
		except:
			self.TARGETS = {}

	def write_target(self, target_id, info=None):
		if not os.path.isdir('targets'):
			os.mkdir('targets')

		if info is None:
			self.TARGETS.pop(target_id)

		else:
			if target_id not in self.TARGETS:
				self.TARGETS[target_id] = []

			self.TARGETS[target_id].append(info)

			if len(self.TARGETS[target_id]) == 3:
				self.TARGETS[target_id].pop(0)

		with open('data/targets.json', 'w', encoding='utf-8') as targets_file:
			json.dump(self.TARGETS, targets_file, ensure_ascii=False)

	def get_current_time(self):
		data = self.ntp.request(self.NTP_SERVER)

		return time.ctime(data.tx_time)

	def add_changes(self, prev_target, target, diff, clan=False):
		if not os.path.isdir('targets'):
			os.mkdir('targets')

		target_id = target['id']

		if clan:
			target = target['clan']
			prev_target = prev_target['clan']	

		if diff:
			with open(f'targets/{target_id}.txt', 'a', encoding='utf-8') as f:	
				current_time = self.get_current_time()

				f.write(f'{current_time}\n\n')

				for d in diff:
					if not target[d] or target[d] == -1:
						target[d] = 'HIDDEN'

					if not prev_target[d] or prev_target[d] == -1:
						prev_target[d] = 'HIDDEN'

					if target[d] == prev_target[d]:
						continue

					field = 'Clan ' if clan else ''
					field += d.replace('_', ' ').capitalize()

					prev_value = prev_target[d]
					value = target[d]

					change_info = f'{field}: {prev_value} -> {value}\n'

					f.write(change_info)

				f.write('\n')

	def auto_update(self):
		while True:
			time.sleep(600)

			self.update_targets()

	def get_changes(self, prev_target, target):
		if not all([prev_target, target]):
			return

		d1 = deepcopy(prev_target)
		d2 = deepcopy(target)

		clan1 = d1.pop('clan').items()
		clan2 = d2.pop('clan').items()

		info1 = d1.items()
		info2 = d2.items()

		info_diff = list(dict(info1 - info2))
		clan_diff = list(dict(clan1 - clan2))

		if not any([info_diff, clan_diff]):
			return

		self.add_changes(prev_target, target, clan_diff, True)
		self.add_changes(prev_target, target, info_diff)

		return clan_diff, info_diff

	def get_clan(self, clan_id):
		ENDPOINT = f'clans/{clan_id}/info'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json()

		name = data.get('name', {})
		description = data.get('description')
		created = data.get('creationTime').replace('T', ' ').replace('Z', '')

		if created:
			created = created.split('.')[0]

		xp = data.get('xp')
		language = data.get('language')
		tag = data.get('tag')
		memberCount = data.get('memberCount')

		clan_data = {
			'name': name,
			'description': description,
			'created': created,
			'xp': xp,
			'language': language,
			'tag': tag,
			'memberCount': memberCount,
			'members': {}
		}

		ENDPOINT = f'clans/{clan_id}/members'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json()

		for player in data:
			player_id = player.get('playerId')
			joined = player.get('creationTime')
			xp = player.get('xp')
			co_leader = player.get('isCoLeader')
			flair = player.get('flair')

			clan_data['members'][player_id] = {
				'joined': joined,
				'xp': xp,
				'co_leader': co_leader,
				'flair': flair
			}

		return 0, clan_data

	def get_player_id(self, username):
		ENDPOINT = f'players/search?username={username}'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json().get('id')

		return 0, data

	def get_player(self, player_id):
		ENDPOINT = f'players/{player_id}'

		data = requests.get(f'{self.BOT_BASE_URL}{ENDPOINT}', headers=self.bot_headers, verify=False)

		if not data.ok:
			return data.status_code, data.text

		data = data.json()
		game_stats = data.get('gameStats', {})

		name = data.get('username')
		level = data.get('level')
		bio = data.get('personalMessage')
		status = data.get('status')

		if level == -1:
			level = '?'

		if status == 'PLAY':
			status = '✅'

		elif status == 'DEFAULT':
			status = '⚪'

		elif status == 'DND':
			status = '🔴'

		elif status == 'OFFLINE':
			status = '📵'

		last_online = data.get('lastOnline', '').replace('T', ' ').replace('Z', '')

		if last_online:
			last_online = last_online.split('.')[0].replace('-', '.')

		created = data.get('creationTime', '').replace('-', '.').replace('T', ' ').replace('Z', '')

		if created:
			created = created.split('.')[0].replace('-', '.')

		received_roses = data.get('receivedRosesCount')
		sent_roses = data.get('sentRosesCount')

		win_count = game_stats.get('totalWinCount')
		lose_count = game_stats.get('totalLoseCount')
		tie_count = game_stats.get('totalTieCount')

		play_time = self.convert_play_time(game_stats.get('totalPlayTimeInMinutes', -1))

		village_win_count = game_stats.get('villageWinCount')
		village_lose_count = game_stats.get('villageLoseCount')

		werewolf_win_count = game_stats.get('werewolfWinCount')
		werewolf_lose_count = game_stats.get('werewolfLoseCount')

		voting_win_count = game_stats.get('votingWinCount')
		voting_lose_count = game_stats.get('votingLoseCount')

		solo_win_count = game_stats.get('soloWinCount')
		solo_lose_count = game_stats.get('soloLoseCount')

		clan_id = data.get('clanId')
		clan = {}

		if clan_id:
			clan = self.get_clan(clan_id)

			if not clan[0]:
				clan = clan[1]
				clan.update(clan.pop('members').get(player_id, {}))

		player_data = {
			'id': player_id,
			'name': name,
			'level': level,
			'bio': bio,
			'status': status,
			'last_online': last_online,
			'created': created,
			'received_roses': received_roses,
			'sent_roses': sent_roses,
			'win_count': win_count,
			'lose_count': lose_count,
			'tie_count': tie_count,
			'play_time': play_time,
			'village_win_count': village_win_count,
			'village_lose_count': village_lose_count,
			'werewolf_win_count': werewolf_win_count,
			'werewolf_lose_count': werewolf_lose_count,
			'voting_win_count': voting_win_count,
			'voting_lose_count': voting_lose_count,
			'solo_win_count': solo_win_count,
			'solo_lose_count': solo_lose_count,
			'clan': clan
		}

		return 0, player_data

	def update_targets(self, target_id=None):
		if self.updating:
			return

		self.updating = True

		if target_id:
			targets = [target_id]

		else:
			targets = list(self.TARGETS)

		for target_id in targets:
			data = self.get_player(target_id)

			if data[0]:
				input(f'\n{Style.BRIGHT}{Back.RED}Error {data[0]}: {data[1]}{Back.RESET}')

				continue

			self.write_target(target_id, data[1])

			time.sleep(0.1)

		for i, target in enumerate(self.TARGETS.values()):
			prev_target = deepcopy(target[0]) if len(target) == 2 else {}
			target = deepcopy(target[-1])

			changes = self.get_changes(prev_target, target)

			if changes:
				threading.Thread(target=playsound, args=('audio/illusionist.mp3',), daemon=True).start()
				
				break

		self.updating = False

	def monitor(self):
		banner(self.__class__.__name__)

		targets_info = ''

		for i, target in enumerate(self.TARGETS.values()):
			prev_target = deepcopy(target[0]) if len(target) == 2 else {}
			target = deepcopy(target[-1])

			changes = self.get_changes(prev_target, target)

			if changes:
				clan_changes, info_changes = changes

				for field in target:
					if field == 'status':
						continue

					if field in info_changes:
						target[field] = f'{Fore.GREEN}{target[field]}{Fore.RESET}'

				for field in target['clan']:
					if field in clan_changes:
						target['clan'][field] = f'{Fore.GREEN}{target["clan"][field]}{Fore.RESET}'

			player_id = target['id']
			name = target['name']
			level = target['level']
			bio = target['bio']
			status = target['status']

			last_online = target['last_online']

			received_roses = target['received_roses']
			sent_roses = target['sent_roses']

			win_count = target['win_count']
			lose_count = target['lose_count']
			tie_count = target['tie_count']

			play_time = target['play_time']

			village_win_count = target['village_win_count']
			village_lose_count = target['village_lose_count']

			werewolf_win_count = target['werewolf_win_count']
			werewolf_lose_count = target['werewolf_lose_count']

			voting_win_count = target['voting_win_count']
			voting_lose_count = target['voting_lose_count']

			solo_win_count = target['solo_win_count']
			solo_lose_count = target['solo_lose_count']

			clan = target['clan']
			tag = clan.get('tag')
			xp = clan.get('xp')
			co_leader = clan.get('co_leader')
			flair = clan.get('flair')

			if tag:
				tag += ' |'

			info = f'{i + 1}'.ljust(3) + f'{player_id}\n'
			info += f'{tag}{name} {level} {status} {last_online}\n'

			if clan:
				info += f'🏰  {xp}xp ({flair}) '

				if co_leader:
					info += 'CO-LEADER'

				info += '\n'

			info += f'{bio}\n'
			info += f'🌹 {received_roses} {sent_roses}\n'

			if win_count != -1:
				info += f'🥇 {win_count} ❌ {lose_count} ☠  {tie_count}\n'

			if play_time != -1:
				info += f'⌚ {play_time}\n'

			if village_win_count != -1:
				info += f'🏠 {village_win_count} {village_lose_count}\n'

			if werewolf_win_count != -1:
				info += f'🐺 {werewolf_win_count} {werewolf_lose_count}\n'

			if voting_win_count != -1:
				info += f'👆 {voting_win_count} {voting_lose_count}\n'

			if solo_win_count != -1:
				info += f'🔪 {solo_win_count} {solo_lose_count}\n'

			targets_info += info + '\n'

		if targets_info:
			print(f'{Style.BRIGHT}{targets_info}')

		else:
			print(f'{Style.BRIGHT}{Fore.YELLOW}Usage:')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Add [IN-GAME NAME]')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Delete [ID]')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Update - update all players')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Update [ID] - update chosen player')
			print(f'{Style.BRIGHT}{Fore.YELLOW}Enter to refresh')
			print(f'{Style.BRIGHT}{Fore.YELLOW}End - stop Stalker')
			print()

	def process(self):
		cmd = input(f'{Style.BRIGHT}{Fore.RED}>{Fore.RESET} ')

		if not cmd:
			return

		elif cmd.lower() == 'end':
			return 1

		elif cmd.lower() == 'update':
			self.update_targets()

		else:
			try:
				cmd, target = cmd.split(' ')
			except ValueError:
				print(f'\n{Style.BRIGHT}{Fore.RED}Usage:')
				print(f'{Style.BRIGHT}{Fore.RED}Add [IN-GAME NAME]')
				print(f'{Style.BRIGHT}{Fore.RED}Delete [ID]')
				print(f'{Style.BRIGHT}{Fore.RED}Update - update all players')
				print(f'{Style.BRIGHT}{Fore.RED}Update [ID] - update chosen player')
				print(f'{Style.BRIGHT}{Fore.RED}Enter to refresh')
				print(f'{Style.BRIGHT}{Fore.RED}End - stop Stalker')
				input()

				return

			if cmd.lower() == 'add':
				if len(self.TARGETS) == 20:
					input(f'\n{Style.BRIGHT}{Back.RED}Too many targets!{Back.RESET}')

					return

				data = self.get_player_id(target)

				if data[0] == 404:
					input(f'\n{Style.BRIGHT}{Back.RED}Invalid name!{Back.RESET}')

					return

				elif data[0]:
					input(f'\n{Style.BRIGHT}{Back.RED}Error {data[0]}: {data[1]}{Back.RESET}')

					return

				target_id = data[1]

				if target_id in self.TARGETS:
					input(f'\n{Style.BRIGHT}{Back.RED}The player is already a target!{Back.RESET}')

					return

				data = self.get_player(target_id)

				if data[0]:
					input(f'\n{Style.BRIGHT}{Back.RED}Error {data[0]}: {data[1]}{Back.RESET}')

					return

				self.write_target(target_id, data[1])

			elif cmd.lower() == 'delete':
				try:
					target = int(target) - 1

					if target < 0:
						input(f'\n{Style.BRIGHT}{Back.RED}Invalid ID!{Back.RESET}')

					else:
						target_id = list(self.TARGETS)[target]

						self.write_target(target_id)
				except (ValueError, IndexError):
					input(f'\n{Style.BRIGHT}{Back.RED}Invalid ID!{Back.RESET}')

			elif cmd.lower() == 'update':
				try:
					target = int(target) - 1

					if target < 0:
						input(f'\n{Style.BRIGHT}{Back.RED}Invalid ID!{Back.RESET}')

					else:
						target_id = list(self.TARGETS)[target]

						self.update_targets(target_id)
				except (ValueError, IndexError):
					input(f'\n{Style.BRIGHT}{Back.RED}Invalid ID!{Back.RESET}')

			else:
				input(f'\n{Style.BRIGHT}{Back.RED}Incorrect command!{Back.RESET}')

	def run(self):
		banner(self.__class__.__name__)

		try:
			while True:
				self.monitor()

				if self.process():
					break
		except KeyboardInterrupt:
			return
		except Exception as e:
			input(f'\n{Style.BRIGHT}{Back.RED}{str(e)}{Back.RESET}')

			return


class Browser:
	def run(self):
		banner(self.__class__.__name__)

		print(f'\n{Style.BRIGHT}{Fore.RED}Once the browser opens, open any request to Wolvesville.')
		print(f'{Style.BRIGHT}{Fore.RED}Copy the "User-Agent" header and paste it into the environment file.')
		print(f'{Style.BRIGHT}{Fore.RED}You can then close the browser and use the program.')
		print(f'\n{Style.BRIGHT}{Fore.RED}Press Enter to continue.{Fore.RESET}')
		input()

		subprocess.Popen('start chrome --user-data-dir="%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Upuaut" wolvesville.com', shell=True)

		os.abort()


def banner(module=None):
	os.system('cls')

	message = f'{Style.BRIGHT}{Fore.RED}Upu{Fore.YELLOW}aut{Fore.RESET}'

	if module:
		message += f'{Fore.RED} | {module}'

	message += '\n'

	print(message)


try:
	while True:
		banner()

		modules = [Tracker(), Booster(), Spinner(), Stalker(), Browser()]
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
except KeyboardInterrupt:
	pass
