#!/usr/bin/env
# bot.py
from urllib import parse
import pickle
import os
import sys
import asyncio
import discord
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
from datetime import date
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
import requests
from threading import Thread
from discord.ext import commands
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from asgiref.sync import async_to_sync
from urllib.parse import urlparse
from urllib.parse import unquote
import signal

from io import BytesIO

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
dbpass = os.getenv('DBPASS')
admin = os.getenv('BOTADMIN')
clientId = os.getenv('CLIENTID')
accessToken = os.getenv('ACCESS_TOKEN')
ericChannel = os.getenv('ERIC_CHANNEL')
ericId = os.getenv('ERIC_ID')
squishyId = os.getenv('SQUISHY_ID')
lasId = os.getenv('LAS_ID')
las2Id = os.getenv('LAS2_ID')
debugChannel = os.getenv('DEBUG_CHANNEL')
giantChannel = os.getenv('GIANT_CHANNEL')
clientToken = os.getenv('CLIENT_ACCESS_TOKEN')
lasChannel = os.getenv('LAS_CHANNEL')
ericSub = int(os.getenv('ERIC_SUB'))
squishySub = int(os.getenv('SQUISHY_SUB'))
ericEmoji = int(os.getenv('ERIC_EMOJI'))
squishyEmoji = int(os.getenv('SQUISHY_EMOJI'))
ericGuild = int(os.getenv('ERIC_GUILD'))
ericSubChannel = int(os.getenv('ERIC_SUB_CHANNEL'))
ericNotifRole = int(os.getenv('ERIC_NOTIF_ROLE'))
squishyNotifRole = int(os.getenv('SQUISHY_NOTIF_ROLE'))

bot = commands.Bot(command_prefix='!')
conn = psycopg2.connect(host="localhost", database="OeSL_team", user="postgres", password=str(dbpass))
client = discord.Client()

@bot.event
async def on_ready():
    print(f'{bot.user.name} is here to fuck shit up')

@bot.event
async def on_raw_reaction_remove(payload):
    messageId = payload.message_id
    if(messageId == ericSub):
        if payload.emoji.id != ericEmoji:
            return
        rbGuild = bot.get_guild(ericGuild)
        ericRole = rbGuild.get_role(ericNotifRole)
        member = rbGuild.get_member(payload.user_id)
        userRoles = member.roles
        if ericRole in userRoles:
            return
        userRoles.append(ericRole)
        await member.edit(roles=userRoles)
    elif(messageId == squishySub):
        rbGuild = bot.get_guild(ericGuild)
        squishyRole = rbGuild.get_role(squishyNotifRole)
        member = rbGuild.get_member(payload.user_id)
        userRoles = member.roles
        if squishyRole in userRoles:
            return
        userRoles.append(squishyRole)
        await member.edit(roles=userRoles)

@bot.event
async def on_raw_reaction_add(payload):
    messageId = payload.message_id
    if(messageId == ericSub):
        rbGuild = bot.get_guild(ericGuild)
        ericRole = rbGuild.get_role(ericNotifRole)
        member = rbGuild.get_member(payload.user_id)
        userRoles = member.roles
        if payload.emoji.id == ericEmoji:
            if ericRole in userRoles:
                userRoles.remove(ericRole)
            await member.edit(roles=userRoles)
        else:
            message = await bot.get_channel(ericSubChannel).fetch_message(messageId)
            await message.remove_reaction(payload.emoji, member)
    if(messageId == squishySub):
        rbGuild = bot.get_guild(ericGuild)
        squishyRole = rbGuild.get_role(squishyNotifRole)
        member = rbGuild.get_member(payload.user_id)
        userRoles = member.roles
        if payload.emoji.id == squishyEmoji:
            if squishyRole in userRoles:
                userRoles.remove(squishyRole)
            await member.edit(roles=userRoles)
        else:
            message = await bot.get_channel(ericSubChannel).fetch_message(messageId)
            await message.remove_reaction(payload.emoji, member)

@bot.command(name='manual')
async def manual(ctx):
    """ rbGuild = bot.get_guild(ericGuild)
    ericRole = rbGuild.get_role(ericNotifRole)
    squishyRole = rbGuild.get_role(squishyNotifRole)
    async for member in rbGuild.fetch_members(limit=100):
        userRoles = member.roles
        userRoles.append(ericRole)
        userRoles.append(squishyRole)
        await member.edit(roles=userRoles) """
    channel = bot.get_channel(ericSubChannel)
    message = await channel.fetch_message(ericSub)
    await message.edit(content = 'Add the {} emoji here to unsubscribe from receiving live notifications for RB_Eric, or remove your reaction to resubscribe!'.format(bot.get_emoji(ericEmoji)))
    return

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
    author = ""
    if ctx.author.nick == None:
        author = ctx.author.name
    else:
        author = ctx.author.nick
    message = ""
    cur = conn.cursor()
    try:
        if len(args) > 0:
            if args[0] == 'help':
                message = 'Use !pool to add, remove, or list champions\n!pool add [champion name] will add that champion to your pool\n!pool remove [champion name] will remove that champion from your pool\n!pool list <option:name> will list your champion pool or the pool of whoever you selected'
            elif args[0] == 'list':
                if len(args) < 2:
                    poolName = ''.join(author).lower().replace(" ", "") + '_pool'
                else:
                    poolName = ''.join(args[1:]).lower() + '_pool'
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
                try:
                    cur.execute("INSERT INTO " + ''.join(author).lower().replace(" ", "") + "_pool VALUES (%s);", (' '.join(champion), ))
                except Exception as error:
                    await ctx.send('Error: ' + str(error) + ' type: ' + type(error))
                #SQL = 'INSERT INTO %s VALUES (%s);'
                #data = (''.join(ctx.author.nick), ' '.join(champion))
                #cur.execute(SQL, data)
                message = 'Added '+' '.join(champion)+' to ' + author + '\'s champion pool!'
            elif args[0] == 'remove' and len(args) > 1:
                champion = args[1:]
                cur.execute('DELETE FROM '+''.join(author).lower().replace(" ", "") +'_pool where champ = \''+' '.join(champion)+'\';')
                message = 'Removed '+' '.join(champion)+' from ' + author + '\'s champion pool!'
            else:
                message = 'Invalid syntax'
        else:
            message = 'need args yo'
    except IndexError:
        message = 'Invalid number of arguments, see help message'
    except Exception as error:
        message = 'Error: ' + str(error) + ' type: ' + type(error)
    conn.commit()
    cur.close() 
    await ctx.send(message)

@bot.command(name='multigg')
async def multigg(ctx, *args):
    inputStr = ''.join(args)
    playerNames = inputStr.replace(" ", "")
    try:
        await ctx.send('https://na.op.gg/multi/query='+(parse.quote(playerNames)))
    except Exception as error:
        await ctx.send('Error, check with @bartowski')
        debug("Error " + str(error) + " type " + type(error))

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
    playername = ''
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
    if playerTuple == None: #figure  out why this isn't none or something ? it's just dying instead
        await ctx.send('Invalid player name "' + args + '"')
        cur.close()
        cur.commit()
        return
    message = 'Player ' + playerTuple[0].strip() + ' plays ' + playerTuple[3].strip() + ' for team ' + playerTuple[1].strip() + '.\nHere is their op.gg link:\n' + playerTuple[2].strip()
    await ctx.send(message)
    cur.commit()
    cur.close()

@bot.command(name='reboot')
async def reboot(ctx):
    userid = str(ctx.author.id)
    if userid !=str(admin):
        return
    
    #process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    #output, error = process.communicate()
    await ctx.send('Rebooting...')
    os.execl(sys.executable, sys.executable, *sys.argv)
    await ctx.send('failed')

@bot.command(name='subscribe')
async def subscribe(ctx, arg):
    userid = str(ctx.author.id)
    if userid !=str(admin):
        return
    if(arg.strip() == 'eric'):
        pload = { 'hub.callback':'http://174.112.140.199:8000',  'hub.mode':'subscribe', 'hub.topic':'https://api.twitch.tv/helix/streams?user_id=' + ericId, 'hub.lease_seconds':'864000'}
        pheaders = { 'Client-ID':clientId, 'Authorization':'Bearer ' + accessToken, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' }
        r = requests.post('https://api.twitch.tv/helix/webhooks/hub', headers=pheaders, data=pload)
    elif(arg.strip() == 'squishy'):
        pload = { 'hub.callback':'http://174.112.140.199:8000',  'hub.mode':'subscribe', 'hub.topic':'https://api.twitch.tv/helix/streams?user_id=' + squishyId, 'hub.lease_seconds':'864000'}
        pheaders = { 'Client-ID':clientId, 'Authorization':'Bearer ' + accessToken, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' }
        r = requests.post('https://api.twitch.tv/helix/webhooks/hub', headers=pheaders, data=pload)
    elif(arg.strip() == 'las1'):
        pload = { 'hub.callback':'http://174.112.140.199:8000',  'hub.mode':'subscribe', 'hub.topic':'https://api.twitch.tv/helix/streams?user_id=' + lasId, 'hub.lease_seconds':'864000'}
        pheaders = { 'Client-ID':clientId, 'Authorization':'Bearer ' + accessToken, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' }
        r = requests.post('https://api.twitch.tv/helix/webhooks/hub', headers=pheaders, data=pload)
    elif(arg.strip() == 'las2'):
        pload = { 'hub.callback':'http://174.112.140.199:8000',  'hub.mode':'subscribe', 'hub.topic':'https://api.twitch.tv/helix/streams?user_id=' + las2Id, 'hub.lease_seconds':'864000'}
        pheaders = { 'Client-ID':clientId, 'Authorization':'Bearer ' + accessToken, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' }
        r = requests.post('https://api.twitch.tv/helix/webhooks/hub', headers=pheaders, data=pload)

    await ctx.send(r.text)

@bot.command(name='twitchid')
async def twitch(ctx, arg):
    userid = str(ctx.author.id)
    if userid != str(admin):
        return
    pload = { 'login':arg }
    pheaders = { 'Client-ID':clientId, 'Authorization':'Bearer ' + clientToken, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' }
    r = requests.get('https://api.twitch.tv/helix/users', headers=pheaders, params=pload)
    await ctx.send(r.text)

@bot.command(name='file')
async def file(ctx, arg):
    userid = str(ctx.author.id)
    if userid != str(admin):
        return
    #livetime = datetime.strptime("2020-05-14T17:40:55Z", "%Y-%m-%dT%H:%M:%SZ")
    #f = open('laslive', 'wb')
    #pickle.dump(livetime, f)
    #f.close()
    f = open('laslive', 'rb')
    try:
        #f.seek(0)
        time = pickle.load(f)
        await ctx.send(time)
    except Exception as e:
        await ctx.send(str(e))

    f.close()

@bot.command(name='render')
async def render(ctx):
    channel = ctx.channel.id
    if channel == int(giantChannel):
        pidFile = open('/home/ckealty/overviewer/render_save_pid.txt', 'r')
        pid = pidFile.read()
        try:
            os.kill(int(pid), signal.SIGCONT)
        except OSError:
            subprocess.call('/home/ckealty/scripts/renderoverworld.sh', shell=True)
            await ctx.send('starting render')
        else:
            await ctx.send('render already running')
    else:
        await ctx.send('wrong channel ' + channel)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Incorrect number of arguments')

@async_to_sync
async def ericLiveNotification():
    ericRole = bot.get_guild(ericGuild).get_role(ericNotifRole)
    channel = bot.get_channel(int(ericChannel))
    await channel.send('{} Eric has gone live! https://twitch.tv/RB_Eric'.format(ericRole.mention))

@bot.command(name='ericlive')
async def ericlive(ctx):
    ericRole = bot.get_guild(ericGuild).get_role(ericNotifRole)
    channel = bot.get_channel(int(ericChannel))
    await channel.send('{} Eric has gone live! https://twitch.tv/RB_Eric'.format(ericRole.mention))

@bot.command(name='squishylive')
async def squishylive(ctx):
    squishyRole = bot.get_guild(ericGuild).get_role(squishyNotifRole)
    channel = bot.get_channel(int(ericChannel))
    await channel.send('{} RB_Squishy has gone live! https://twitch.tv/RB_Squishy'.format(squishyRole.mention))

@bot.command(name='laslive')
async def laslive(ctx):
    channel = bot.get_channel(int(lasChannel))
    print(lasChannel)
    print(channel)
    await channel.send('@here LAS Esports has gone live! https://twitch.tv/LAS_esports')

@async_to_sync
async def squishyLiveNotification():
    squishyRole = bot.get_guild(ericGuild).get_role(squishyNotifRole)
    channel = bot.get_channel(int(ericChannel))
    await channel.send('{} RB_Squishy has gone live! https://twitch.tv/RB_Squishy'.format(squishyRole.mention))

@async_to_sync
async def lasLiveNotification():
    channel = bot.get_channel(int(lasChannel))
    await channel.send('@here LAS_esports has gone live! https://twitch.tv/LAS_esports')

@async_to_sync
async def las2LiveNotification():
    channel = bot.get_channel(int(lasChannel))
    await channel.send('@here LAS_esports2 has gone live! https://twitch.tv/LAS_esports2')

@async_to_sync
async def debug(message):
    channel = bot.get_channel(int(debugChannel))
    if not message:
        await channel.send("no message")
    else:
        await channel.send("@everyone " + message)

class BotHttpRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
  #      query = urlparse(self.path).query
        query_components = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
 #       query_components = dict(qc.split("=") for qc in query.split("&"))
        topic = query_components.get("hub.topic", "")

        if unquote(topic) == 'https://api.twitch.tv/helix/streams?user_id=50430698':
            debug("received correct response")

        self.send_response(200)
        self.end_headers()
        challenge = query_components.get("hub.challenge", "")
        if challenge != "":
            self.wfile.write(challenge.encode())
        debug(urlparse(self.path).query)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        info = json.loads(body)
        debug(body.decode("utf-8"))
        try:
            if len(info["data"]) == 0:
                return
            if "type" in info["data"][0]:
                if info["data"][0]["type"] == "live":
                    livetime = datetime.strptime(info["data"][0]["started_at"], "%Y-%m-%dT%H:%M:%SZ")
                    if(int(info["data"][0]["user_id"]) == int(ericId)):
                        try:
                            with open('ericlive', 'rb') as picklefile:
                                oldLivetime = pickle.load(picklefile)
                        except (OSError, IOError, EOFError):
                            with open('ericlive', 'wb') as picklefile:
                                ericLiveNotification()
                                pickle.dump(livetime, picklefile)
                        else:
                            if (oldLivetime + timedelta(hours=1)) < livetime:
                                ericLiveNotification()
                                with open('ericlive', 'wb') as picklefile:
                                    pickle.dump(livetime, picklefile)
                            else:
                                debug("eric not new live, timestamp: " + str(livetime))
                    if(int(info["data"][0]["user_id"]) == int(squishyId)):
                        try:
                            with open('squishylive', 'rb') as picklefile:
                                oldLivetime = pickle.load(picklefile)
                        except (OSError, IOError, EOFError) as er:
                            debug("error " + str(er))
                            with open('squishylive', 'wb') as picklefile:
                                squishyLiveNotification()
                                pickle.dump(livetime, picklefile)
                        else:
                            if ((oldLivetime + timedelta(hours=1)) < livetime):
                                squishyLiveNotification()
                                with open('squishylive', 'wb') as picklefile:
                                    pickle.dump(livetime, picklefile)
                            else:
                                debug("squishy not new live, timestamp: " + str(livetime))
                    if(int(info["data"][0]["user_id"]) == int(lasId)):
                        debug("LAS esports notif live at " + str(livetime))
                        try:
                            with open('laslive', 'rb') as picklefile:
                                oldLivetime = pickle.load(picklefile)
                        except (OSError, IOError, EOFError) as er:
                            debug("error" + str(er))
                            lasLiveNotification()
                            with open('laslive', 'wb') as picklefile:
                                pickle.dump(livetime, picklefile)
                        else:
                            if (oldLivetime + timedelta(hours=1)) < livetime:
                                lasLiveNotification()
                                with open('laslive', 'wb') as picklefile:
                                    pickle.dump(livetime, picklefile)
                            else:
                                debug("las not new live, timestamp: " + str(livetime))
                    if(int(info["data"][0]["user_id"]) == int(las2Id)):
                        debug("LAS esports 2 notif live at " + str(livetime))
                        try:
                            with open('las2live', 'rb') as picklefile:
                                oldLivetime = pickle.load(picklefile)
                        except (OSError, IOError, EOFError):
                            las2LiveNotification()
                            with open('las2live', 'wb') as picklefile:
                                pickle.dump(livetime, picklefile)
                        else:
                            if oldLivetime < livetime:
                                lasLiveNotification()
                                with open('las2live', 'wb') as picklefile:
                                    pickle.dump(livetime, picklefile)
                            else:
                                debug("las not new live, timestamp: " + livetime)
        except Exception as e:
            debug("error " + str(e))

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def serve_on_port(port):
    server = ThreadingHTTPServer(("",port), BotHttpRequestHandler)
    server.serve_forever()

x = Thread(target=serve_on_port, args=[8000])
x.start()
#x.join()
bot.run(token)
print('here1')
#httpd.serve_forever()
