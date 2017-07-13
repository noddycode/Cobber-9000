import sys
import discord
import asyncio
import json
import signal
import pytumblr
import threading
from pprint import pprint
import time

class UpdateHandler:

	def __init__(self, discordClient, updateChannel):
		self.discordClient = discordClient
		self.lastUpdate = 0
		self.updateEnabled = True
		self.lastPost = 0
		self.updateChannel = updateChannel

	def tumblrLogin(self, token):
		# self.tumblrClient = pytumblr.TumblrRestClient(
		# 	token,
		# 	secret,
		# 	oauthToken,
		# 	oauthSecret)

		self.tumblrClient = pytumblr.TumblrRestClient(token)

	async def initUpdate(self, timeInterval, username, tag):

		# Grabs the most recent post from the target blog at startup
		initialPost = self.tumblrClient.posts(f"{username}.tumblr.com", limit = 1)
		self.lastPost = initialPost['posts'][0]['id']
		print(self.lastPost)

		# This loop schedules an update cycle once per timeInterval
		while self.updateEnabled:
			print("Updating...")
			asyncio.ensure_future(self.update(username, tag))
			print("Time loop sleeping, zzz....")
			await asyncio.sleep(timeInterval)


	async def update(self, username, tag):

		print("Starting update...")

		posts = self.tumblrClient.posts(f"{username}.tumblr.com", tag = tag, limit = 10)['posts']

		# Filters out posts that are older than the last update post
		newPosts = list(filter(lambda post: post['id'] > self.lastPost, posts))

		if len(newPosts) <= 0:
			return

		print("Update found!")

		# Reverses the order of any new posts so the oldest is posted first
		newPosts.reverse()

		for post in newPosts:
			url = post['post_url']
			await self.discordClient.send_message(
				self.discordClient.get_channel(self.updateChannel),
				f"**Update:** {url}")
			self.lastPost = post['id']

configFile = sys.argv[1]

with open(configFile) as cFile:
	config = json.load(cFile)

####### STARTING DISCORD CLIENT #######
client = discord.Client()

@client.event
async def on_ready():
	print('Logged into update process as')
	print(client.user.name)
	print('------')


	####### INITIALIZING TUMBLR CLIENT #######
	uh = UpdateHandler(client, config['ids']['updatech'])
	tumblrConfig = config['update']
	uh.tumblrLogin(tumblrConfig['tumblr_token'])

	####### CREATING AND RUNNING ASYNCIO LOOP #######
	loop = asyncio.get_event_loop()

	try:
		asyncio.run_coroutine_threadsafe(uh.initUpdate(
			60.0, 
			tumblrConfig['username'], 
			tumblrConfig['tag']),
			loop)

	except KeyboardInterrupt as e:
		gracefulExit()

####### KEYBOARD INTERRUPT HANDLING #######
def gracefulExit(signal, frame):
	print("Exiting...")
	client.logout()
	sys.exit(0)

signal.signal(signal.SIGINT, gracefulExit)

client.run(config['token'])




