# bot.py
import os

import discord
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from datetime import date

from discord.ext import commands

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
dbpass = os.getenv('DBPASS')

bot = commands.Bot(command_prefix='!')
conn = psycopg2.connect(host="localhost", database="OeSL_team", user="postgres", password=dbpass)

@bot.event
async def on_ready():
	print(f'{bot.user.name} is here to fuck shit up')

@bot.command(name='test')
async def test(ctx, arg):
	await ctx.send('ack')

@bot.command(name='opgg')
async def opgg(ctx, *args):
	url = ''.join(args)
	await ctx.send('https://na.op.gg/summoner/userName='+url)

@bot.command(name='pool')
async def pool(ctx, *args):
	if ";" in str(args):
		await ctx.send('no sql injection plz ty')
		return
	message = ""
	cur = conn.cursor()
	try:
		if len(args) > 0:
			if args[0] == 'help':
				message = 'Use !pool to add, remove, or list champions\n!pool add [champion name] will add that champion to your pool\n!pool remove [champion name] will remove that champion from your pool\n!pool list <option:name> will list your champion pool or the pool of whoever you selected'
			elif args[0] == 'list':
				if len(args) < 2:
					poolName = ''.join(ctx.author.nick) + '_pool'
				else:
					poolName = args[1] + '_pool'
				cur.execute('SELECT * from ' + poolName + ';')
				champlist = cur.fetchall()
				if champlist == None:
					await ctx.send('Invalid user specifiec')
					return
				for champ in champlist:
					message += champ[0].strip() + ", "
				message = message[:-2]
			elif args[0] == 'add' and len(args) > 1:
				champion = args[1:]
				cur.execute("INSERT INTO " + ''.join(ctx.author.nick) + "_pool VALUES (%s);", (' '.join(champion), ))
				#SQL = 'INSERT INTO %s VALUES (%s);'
				#data = (''.join(ctx.author.nick), ' '.join(champion))
				#cur.execute(SQL, data)
				message = 'Added '+' '.join(champion)+' to ' + ctx.author.nick + '\'s champion pool!'
			elif args[0] == 'remove' and len(args) > 1:
				champion = args[1:]
				cur.execute('DELETE FROM '+''.join(ctx.author.nick)+'_pool where champ = \''+' '.join(champion)+'\';')
				message = 'Removed '+' '.join(champion)+' from ' + ctx.author.nick + '\'s champion pool!'
			else:
				message = 'Invalid syntax'
		else:
			message = 'need args yo'
	except IndexError:
		message = 'Invalid number of arguments, see help message'
	conn.commit()
	cur.close()	
	await ctx.send(message)

@bot.command(name='upcoming')
async def upcoming(ctx):
	#maybe take optional arg for specific team?
	cur = conn.cursor()
	cur.execute('SELECT * from schedule order by game_date asc;')
	for game in cur.fetchall():
		if game[0] >= date.today():
			await ctx.send('Next game is against ' + game[1].strip() + ' on ' + game[0].strftime('%B %d, %Y') + ' at ' + str(game[2]))
			return
	await ctx.send('No upcoming games scheduled')
	cur.commit()
	cur.close()

@bot.command(name='teaminfo')
async def teaminfo(ctx, *args):
	if len(args) < 1:
		await ctx.send ('Must specify a team')
		return
	if ";" in str(args):
		await ctx.send('no sql injection plz ty')
		return
	arg = ' '.join(args[0:]).strip().upper()
	message = ""
	cur = conn.cursor()
	cur.execute('SELECT * from teams where upper(team)=%s;', (arg, ))
	teamTuple = cur.fetchone()
	if teamTuple == None:
		await ctx.send('Invalid team name "' + arg + '"')
		cur.close()
		cur.commit()
		return
	cur.execute('SELECT * from players where upper(team)=%s;', (arg, ))
	message = 'Team ' + teamTuple[0].strip() + ' has the following players: \n'
	for player in cur.fetchall():
		message += player[0].strip() + ', '
	message = message[:-2] + '\n'
	message += 'Here is the op.gg link: ' + teamTuple[1].strip()
	#add when next game is?
	cur.execute('SELECT * from schedule where upper(team)=%s order by game_date asc;', (arg, ))
	for game in cur.fetchall():
		if game[0] >= date.today():
			message += '\nYour next game against them is on ' + game[0].strftime('%B %d, %Y') + ' at ' + str(game[2])
	await ctx.send(message)
	cur.commit()
	cur.close()

@bot.command(name='playerinfo')
async def playerinfo(ctx, *args):
	playername = '';
	if len(args) < 1:
		playername = ctx.author.nick.upper()
	else:
		playername = ' '.join(args[0:]).strip().upper()
	if ";" in str(args):
		await ctx.send('no sql injection plz ty')
		return
	message = ""
	cur = conn.cursor()
	cur.execute('SELECT * from players where upper(name)=%s;', (playername, ))
	playerTuple = cur.fetchone()
	if playerTuple == None:
		await ctx.send('Invalid player name "' + args + '"')
		cur.close()
		cur.commit()
		return
	message = 'Player ' + playerTuple[0].strip() + ' plays ' + playerTuple[3].strip() + ' for team ' + playerTuple[1].strip() + '.\nHere is their op.gg link:\n' + playerTuple[2].strip()
	await ctx.send(message)
	cur.commit()
	cur.close()

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.errors.MissingRequiredArgument):
		await ctx.send('Incorrect number of arguments')

bot.run(token)
