import discord
from discord.ext import tasks, commands
import os
import traceback
import subprocess
import paramiko
import time
import random
import re


# ARKサーバーのインスタンスidを指定してください
INSTANCEID = 'i-0cc31d2cc8dd3f649'
# Minecraftサーバーのインスタンスidを指定してください
M_INSTANCEID = 'i-0444e29e022cea113'

# 接続に必要なオブジェクトを生成
#client = discord.Client()

#bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']

intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
client = discord.Client(intents=intents)


#@bot.command()
#async def ping(ctx):
#    await ctx.send('pong')

# ***************************
# ***    処理関数
# ***************************
class DiscordBOT:
    #クラス変数を定義
    send_text = ""
    arkSSHClient = None
    mcSSHClient = None
    arkServerFlag = False
    mcServerFlag = False
    mc_stdin = None
    mc_stdout = None
    mc_stderr = None
    mc_proc = None
    mc_timer = 0
    dMessage = None

    def __init__(self):
        self.mcMonitor.start()

    async def main(self, discord_event):
        get_text = discord_event.content
        print('init完了')

        if get_text == "$help":
            await discordbot.reaction(discord_event)
            DiscordBOT.send_text = "現在使用可能なコマンドリストです。\n**$dice**\n　１～６の中でランダムな数字を発表します。\n**$dice**\n**候補１**\n**候補n**\n　複数の候補からランダムに選んで発表します。diceの後ろは改行してください。\n**$team**\n　接続中のボイスチャンネルのメンバーをチーム分けします。\n**$team n**\n　接続中のボイスチャンネルのメンバーをn個のチームに分けます。\n**$start minecraft**\n　現在利用不可。マインクラフトのサーバーを起動します。\n**$stop minecraft**\n　現在利用不可。マインクラフトのサーバーを停止します。"
        elif get_text == "$start ark":
            if DiscordBOT.arkServerFlag == True:
                DiscordBOT.send_text = "Arkサーバー起動は実行済みです。接続を確認してください。\nサーバーに接続できない場合は、サーバーを一度終了させてから、再びサーバー起動をお試しください。"
            else:
                DiscordBOT.arkServerFlag = True
                await discordbot.reaction(discord_event)
                discordbot.startArk()

        elif get_text == "$stop ark":
            if DiscordBOT.arkSSHClient is None:
                DiscordBOT.send_text = "Arkサーバーへの接続情報が失われています。\nサーバーが既に停止済みであるか、予期せぬ動作の可能性があります。"
            else:
                DiscordBOT.arkServerFlag = False
                await discordbot.reaction(discord_event)
                discordbot.stopArk()
                DiscordBOT.arkSSHClient = None

        elif get_text == "$start minecraft":
            if DiscordBOT.mcServerFlag == True:
                DiscordBOT.send_text = "Minecraftサーバー起動は実行済みです。接続を確認してください。\nサーバーに接続できない場合は、サーバーを一度終了させてから、再びサーバー起動をお試しください。"
            else:
                #DiscordBOT.mcServerFlag = True
                DiscordBOT.dMessage = discord_event
                await discordbot.reaction(discord_event)
                discordbot.startMc()

        elif get_text == "$stop minecraft":
            if DiscordBOT.mcSSHClient is None:
                DiscordBOT.send_text = "Minecraftサーバーへの接続情報が失われています。\nサーバーが既に停止済みであるか、予期せぬ動作の可能性があります。"
            else:
                #DiscordBOT.mcServerFlag = False
                await discordbot.reaction(discord_event)
                discordbot.stopMc()

        elif get_text.startswith("$dice"):
            await discordbot.reaction(discord_event)
            discordbot.dice(get_text)

        elif get_text == "$list minecraft":
            if DiscordBOT.mcSSHClient is None:
                DiscordBOT.send_text = "Minecraftサーバーへの接続情報が失われています。\nサーバーが既に停止済みであるか、予期せぬ動作の可能性があります。"
            else:
                await discordbot.reaction(discord_event)
                discordbot.listMc()
                
        elif get_text.startswith("$team"):
            await discordbot.reaction(discord_event)
            discordbot.createTeam(discord_event)


        if DiscordBOT.send_text != "":
            await discord_event.channel.send(DiscordBOT.send_text)
            DiscordBOT.send_text = ""


    #メッセージ取得時にユーザに対してリアクションをつけるクラス関数
    async def reaction(self, message):
        reactions = ["\U0001F600", "\U0001F609", "\U0001F914", "\U0001F62A", "\U0001F60E"]
        await message.add_reaction(random.choice(reactions))


    #メッセージ分岐で実行されるクラス関数
    #ダイスを振るクラス関数
    def dice(self, get_text):
        areas = get_text.splitlines()
        if len(areas) == 1:
            time.sleep(1)
            DiscordBOT.send_text = "ダイスの結果は...**「" + str(random.randint(1,6)) + "」**です！"
            return

        for i in range(len(areas)):
            if i != len(areas) - 1:
                time.sleep(1)
                areas[i] = areas[i+1]
                print(areas[i])

        DiscordBOT.send_text = "選ばれたのは**「" + str(random.choice(areas)) + "」**です！"
        
    #チームを作成するクラス関数
    def createTeam(self, discord_event):
        get_text = discord_event.content
        vcstate = discord_event.author.voice
        if vcstate is None:
            DiscordBOT.send_text = "チーム振り分け機能は、ボイスチャンネルに接続してからご利用ください。"
            return
        vcmember = [member.name for member in vcstate.channel.members]
        
        areas = get_text.split()
        if len(areas) == 1:
            if len(vcmember) % 2 == 0:
                teamlist = "\n".join(discordbot.createTeamList(vcmember, 2))
                DiscordBOT.send_text = teamlist
                return
            else:
                DiscordBOT.send_text = "ボイスチャンネルに接続中のメンバー数を2で割り切れません。"
                return
        
        else:
            if not discordbot.is_int(areas[1]):
                DiscordBOT.send_text = "チーム数は半角数字の整数を入力してください。例：$team 3"
                return
            teamnum = int(areas[1])
            if len(vcmember) % teamnum == 0:
                teamlist = "\n".join(discordbot.createTeamList(vcmember, teamnum))
                DiscordBOT.send_text = teamlist
                return
            else:
                DiscordBOT.send_text = "ボイスチャンネルに接続中のメンバー数を" + str(teamnum) + "で割り切れません。"
                return
        
    def is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False
        
    def createTeamList(self, memberlist, teamnum):
        membernum = len(memberlist) / teamnum
        random.shuffle(memberlist)
        
        count = 0
        teamcount = 1
        output = ["Team 1"]
        for mem in memberlist:
            count += 1
            output.append(mem)
            if count >= membernum and teamcount != teamnum:
                count = 0
                teamcount += 1
                output.append("Team " + str(teamcount))
        
        return output

    #Minecraftサーバーを起動するクラス関数
    def startMc(self):
        print('start minecraft 受け付けました')
        # Minecraftサーバー インスタンスの起動
        subprocess.call("aws ec2 start-instances --instance-ids {}".format(M_INSTANCEID), shell=True)
        time.sleep(1)
        print('インスタンス起動処理完了')

        # Minecraftサーバー インスタンスが起動するまで待機
        subprocess.call("aws ec2 wait instance-status-ok --instance-ids {}".format(M_INSTANCEID), shell=True)
        time.sleep(1)
        print('インスタンス起動待機終了')

        # Minecraftサーバー インスタンスのホスト名を取得
        proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicDnsName' --output text".format(M_INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(1)
        #print('Minecraftサーバー インスタンスのホスト名取得完了')
        proc = proc.stdout.decode("utf-8")
        proc = proc.replace("\n","")
        print('Minecraftサーバー インスタンスのホスト名：', proc)

        # Minecraftサーバー インスタンスのipアドレスを取得
        ip_proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicIpAddress' --output text".format(M_INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        ip_add = ip_proc.stdout.decode("utf-8")
        ip_add = ip_add.replace("\n", "")
        #print('Minecraftサーバー インスタンスのホスト名：', ip_add)


        # SSH接続クライアント作成
        DiscordBOT.mcSSHClient = paramiko.SSHClient()
        DiscordBOT.mcSSHClient.set_missing_host_key_policy(paramiko.WarningPolicy())
        DiscordBOT.mcSSHClient.connect(proc, username='ec2-user', password='', key_filename='.ssh/discordbot_key')
        time.sleep(1)
        print('SSH接続クライアント作成終了')

        # SSHでMinecraftサーバー起動
        #print('********sudo su実行')
        DiscordBOT.mc_stdin, DiscordBOT.mc_stdout, DiscordBOT.mc_stderr = DiscordBOT.mcSSHClient.exec_command('sudo su')
        time.sleep(1)
        print('********rootログイン完了')
        #print('********Minecraftフォルダへ移動')
        DiscordBOT.mc_stdin.write('cd minecraft\n')
        DiscordBOT.mc_stdin.flush()
        time.sleep(1)
        print('********Minecraftフォルダへ移動完了')
        #print('********サーバー起動処理実施')
        DiscordBOT.mc_stdin.write('./server.sh\n')
        DiscordBOT.mc_stdin.flush()
        time.sleep(60)
        print('********Minecraftサーバー起動処理完了')

        DiscordBOT.mcServerFlag = True
        DiscordBOT.mc_timer = 0
        # サーバー起動処理完了のメッセージをdiscordに送信
        DiscordBOT.send_text = "<@&627367515646853120> インスタンスの起動とMinecraftサーバーへの接続に成功しました。\n サーバー情報　：　1.16.3 Vanilla\n 接続方法　　　：　マルチプレイ→ダイレクト接続\n IPアドレス　　：　`{}`".format(ip_add)


    #Minecraftサーバーを停止するクラス関数
    def stopMc(self):
        # SSHでminecraftサーバー停止
        print('********サーバー停止処理実施')
        #DiscordBOT.mc_stdin, DiscordBOT.mc_stdout, DiscordBOT.mc_stderr = DiscordBOT.mcSSHClient.exec_command('./serverstop.sh')
        DiscordBOT.mc_stdin.write('./serverstop.sh\n')
        DiscordBOT.mc_stdin.flush()
        #out = DiscordBOT.mc_stdout.readlines()
        #print(out)
        #err = DiscordBOT.mc_stderr.readlines()
        #print(err)


        #print('********サーバー停止処理完了、60秒後にインスタンス停止実行')
        time.sleep(120)

        # インスタンスの停止
        subprocess.call("aws ec2 stop-instances --instance-ids {}".format(M_INSTANCEID), shell=True)
        DiscordBOT.mcServerFlag = False
        DiscordBOT.mc_timer = 0
        DiscordBOT.mcSSHClient = None
        DiscordBOT.send_text = "<@&627367515646853120> サーバー及びインスタンスの停止が完了しました。\nまたのご来訪をお待ちしております。"


    #Arkサーバーを起動するクラス関数
    def startArk(self):
        print('start ark 受け付けました')
        # ARKサーバー インスタンスの起動
        subprocess.call("aws ec2 start-instances --instance-ids {}".format(INSTANCEID), shell=True)
        time.sleep(3)
        print('インスタンス起動処理完了')

        # ARKサーバー インスタンスが起動するまで待機
        subprocess.call("aws ec2 wait instance-status-ok --instance-ids {}".format(INSTANCEID), shell=True)
        time.sleep(3)
        print('インスタンス起動待機終了')

        # ARKサーバー インスタンスのホスト名を取得
        proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicDnsName' --output text".format(INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(3)
        print('ARKサーバー インスタンスのホスト名取得完了')
        proc = proc.stdout.decode("utf-8")
        proc = proc.replace("\n","")
        print('ARKサーバー インスタンスのホスト名：', proc)

        # SSH接続クライアント作成
        DiscordBOT.arkSSHClient = paramiko.SSHClient()
        DiscordBOT.arkSSHClient.set_missing_host_key_policy(paramiko.WarningPolicy())
        DiscordBOT.arkSSHClient.connect(proc, username='ec2-user', password='', key_filename='.ssh/discordbot_key')
        time.sleep(2)
        print('SSH接続クライアント作成終了')

        # SSHでarkサーバー起動
        print('********su-steam実行')
        stdin, stdout, stderr = DiscordBOT.arkSSHClient.exec_command('su - steam')
        time.sleep(2)
        print('********パスワード入力実行')
        stdin.write('Std0v0mgsSF5\n')
        stdin.flush()
        time.sleep(2)
        print('********arkmanagerstart実行')
        stdin.write('arkmanager start\n')
        stdin.flush()
        time.sleep(2)
        print('********ARKサーバー起動処理完了')

        # サーバー起動処理完了のメッセージをdiscordに送信
        DiscordBOT.send_text = "<@&746619641706709003> インスタンスの起動とARKサーバーへの接続に成功しました。\n サーバー起動までお待ちください。"


    #Arkサーバーを停止するクラス関数
    def stopArk(self):
        # ARKサーバー インスタンスのホスト名を取得
        proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicDnsName' --output text".format(INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(3)
        print('ARKサーバー インスタンスのホスト名取得完了')
        proc = proc.stdout.decode("utf-8")
        proc = proc.replace("\n","")
        print('ARKサーバー インスタンスのホスト名：', proc)

        # SSH接続クライアント作成
        #DiscordBOT.SSHClient = paramiko.SSHClient()
        #DiscordBOT.SSHClient.set_missing_host_key_policy(paramiko.WarningPolicy())
        #DiscordBOT.SSHClient.connect(proc, username='ec2-user', password='', key_filename='.ssh/discordbot_key')
        time.sleep(2)
        print('SSH接続クライアント作成終了')

        # SSHでarkサーバー停止
        print('********su-steam実行')
        stdin, stdout, stderr = DiscordBOT.arkSSHClient.exec_command('su - steam')
        time.sleep(2)
        print('********パスワード入力実行')
        stdin.write('Std0v0mgsSF5\n')
        stdin.flush()
        time.sleep(2)
        print('********arkmanagerstop実行')
        stdin.write('arkmanager stop\n')
        stdin.flush()
        time.sleep(2)
        print('********サーバー停止処理完了、15秒後にインスタンス停止実行')
        time.sleep(11)
        stdin.write('exit\n')
        stdin.flush()
        time.sleep(2)

        #SSH接続終了
        DiscordBOT.arkSSHClient.close()
        time.sleep(2)
        print('SSH接続終了')

        # インスタンスの停止
        subprocess.call("aws ec2 stop-instances --instance-ids {}".format(INSTANCEID), shell=True)
        DiscordBOT.send_text = "<@&746619641706709003> サーバー及びインスタンスの停止が完了しました。\nまたのご来訪をお待ちしております。"

    #Minecraftの各種接続情報を取得する（定期監視用）
    def connectMc(self):
        #print('********Minecraftの各種接続情報を取得')
        proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicDnsName' --output text".format(M_INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(1)
        print('Minecraftサーバー インスタンスのホスト名取得完了')
        proc = proc.stdout.decode("utf-8")
        proc = proc.replace("\n","")
        #print('Minecraftサーバー インスタンスのホスト名：', proc)

        # Minecraftサーバー インスタンスのipアドレスを取得
        ip_proc = subprocess.run(["aws ec2 describe-instances --instance-ids {} --query 'Reservations[*].Instances[*].PublicIpAddress' --output text".format(M_INSTANCEID)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        ip_add = ip_proc.stdout.decode("utf-8")
        ip_add = ip_add.replace("\n", "")
        #print('Minecraftサーバー インスタンスのホスト名：', ip_add)


        # SSH接続クライアント作成
        DiscordBOT.mcSSHClient = paramiko.SSHClient()
        DiscordBOT.mcSSHClient.set_missing_host_key_policy(paramiko.WarningPolicy())
        DiscordBOT.mcSSHClient.connect(proc, username='ec2-user', password='', key_filename='.ssh/discordbot_key')
        time.sleep(1)
        print('SSH接続クライアント作成終了')

        # SSHでMinecraftサーバー起動
        #print('********sudo su実行')
        DiscordBOT.mc_stdin, DiscordBOT.mc_stdout, DiscordBOT.mc_stderr = DiscordBOT.mcSSHClient.exec_command('sudo su')
        time.sleep(1)
        print('********rootログイン完了')
        #print('********Minecraftフォルダへ移動')
        DiscordBOT.mc_stdin.write('cd minecraft\n')
        DiscordBOT.mc_stdin.flush()
        time.sleep(1)
        print('********Minecraftフォルダへ移動完了')


    def listMc(self):
        DiscordBOT.mc_stdin.write('screen -p 0 -S minecraft -X eval \'stuff \"list\"\\015\'\n')
        DiscordBOT.mc_stdin.flush()
        time.sleep(1)

        sftp = DiscordBOT.mcSSHClient.open_sftp()

        with sftp.open('/home/ec2-user/minecraft/logs/latest.log') as f:
            #for log in f:
            #    log = log.rstrip('\r\n')
            #    print(log)
            logs = f.read()
        return logs


    @tasks.loop(seconds=60)
    async def mcMonitor(self):
        #print('mcMonitorループ中...')
        #minecraftサーバーが建っている場合、監視処理実行
        if DiscordBOT.mcServerFlag == True:
            log = discordbot.listMc()
            log = log.decode()
            #print(log)

            match = re.findall(r'There are \d of a max of 20 players online:', log)[-1]
            #print('サーバー接続数取得')
            print(match)
            if 'There are 0 of a max of 20 players online:' in match:
                DiscordBOT.mc_timer += 1
                print(DiscordBOT.mc_timer)
                #10分以上経過していたら、サーバー終了処理
                if DiscordBOT.mc_timer >= 10:
                    DiscordBOT.mc_timer = 0
                    discordbot.stopMc()
                    #サーバーストップのお知らせ送信
                    DiscordBOT.send_text = "<@&627367515646853120> 10分以上無人のため、サーバーを自動停止しました。\n私がいる限り、切り忘れても安心です。"
                    await DiscordBOT.dMessage.channel.send(DiscordBOT.send_text)
                    DiscordBOT.send_text = ""
            #サーバー接続人数が0でない場合、mc_timerを0に
            else:
                DiscordBOT.mc_timer = 0
                #print('timerリセット:' + str(DiscordBOT.mc_timer))

    #botの準備が整うまでループを待機
    @mcMonitor.before_loop
    async def before_mcMonitor(self):
        print('waiting for mcMonitor...')
        await client.wait_until_ready()




#print('インスタンス生成')
discordbot = DiscordBOT()



@client.event
async def on_ready():
    print('ログインしました')
    #await client.change_presence(activity=discord.CustomActivity(type = discord.ActivityType.custom, name = "$helpで使用可能なコマンドリストをお伝えします。"))
    await client.change_presence(activity=discord.Activity(name="$helpで使用可能なコマンドリストをお伝えします。お手伝い係", type=5))

# on get message
@client.event
async def on_message(message):
    if message.author.bot:
        return
    #DiscordBOT.dMessage = message
    await discordbot.main(message)
    
@client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

# Botの起動とDiscordサーバーへの接続
client.run(token)
