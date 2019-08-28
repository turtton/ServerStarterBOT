#!/bin/python3
import subprocess
import asyncio
import json
import logging
# インストールした discord.py を読み込む
import discord
from discord.ext import tasks

# Discordのログを出力するように
logging.basicConfig(level=logging.INFO)

#jsonファイル読み込み準備
with open('config.json') as f:
    jsn = json.load(f)

#TOKEN = open('token.txt').read()
TOKEN = jsn["token"]

f_name = jsn["java"]

# 接続に必要なオブジェクトを生成
client = discord.Client()

#presence用
idle = discord.Game("サーバー停止中")
starting = discord.Game("サーバー起動中")


class server_process:

    def __init__(self, f_name):
        self.f_name = f_name
        self.server = None

    def start(self):
        self.server = subprocess.Popen(self.f_name, stdin=subprocess.PIPE)

    def stop(self):
        input_string = "stop"
        self.server.communicate(input_string.encode())

    def kill(self):
        self.server.terminate()

    def server_is_running(self):
        if self.server is None: return False
        if self.server.poll() is None:
            return True
        elif self.server.poll() is not None:
            return False
        else:
            return False

    def get(self):
        return self.server.poll()

# サーバー操作用
server = server_process(f_name)

#活動監視
@tasks.loop(seconds=1)
async def server_checker():
    while (True):
        if server.server_is_running() is True:
            await client.change_presence(activity=starting, status=discord.Status.online)
        else:
            await client.change_presence(activity=idle, status=discord.Status.idle)
        await asyncio.sleep(1)

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    print(client.user.name)
    print(client.user.id)
    server_checker.start()
    #client.loop.create_task(server_checker())
    #await client.change_presence(activity=idle, status=discord.Status.idle)

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    if message.author.bot:
        return

    global server

    print(f"In Channel {message.channel}:\n{message.author.name} ({message.author}) wrote: {message.content}")
    global server

    if message.content == 'r.start':
        if server.server_is_running() is False:
            #running = True
            #await client.change_presence(activity=starting, status=discord.Status.online)
            await message.channel.send('サーバー起動します...')
            server.start()
            #client.loop.create_task(server_checker(server))
            #await server_checker.start(server)
        else:
            await message.channel.send('既に起動中です')

    elif message.content == 'r.test': # BOTテスト用
        test = await message.channel.send('test')
        if server.server_is_running is True:
            test.edit('起動中です')
    elif message.content == "r.kill": # 緊急停止用
        emoji_o = '🇴'
        kill_ms = await message.channel.send('強制終了しますか？')
        await kill_ms.add_reaction(emoji_o)

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '🇴'

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await kill_ms.edit(content='処理がタイムアウトしました')
        else:
            await kill_ms.edit(content='強制終了しました')
            server.kill()
        await kill_ms.clear_reactions()

    elif message.content == 'r.stop': # 通常停止用
        #if running == True:
        await message.channel.send('終了します')
        server.stop()
        #else:
        #    await message.channel.send('既に終了しています')

    elif message.content == 'r.reset': #runnning変数初期化(通常は使用しないでください)
        await client.change_presence(activity=idle, status=discord.Status.idle)
        await message.channel.send('初期化しました')

    #デバッグ用コマンドのためコメントアウト
    #elif message.content == 'r.get':
        #await message.channel.send('初期化しました')

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)

