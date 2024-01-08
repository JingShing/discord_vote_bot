
import discord
from discord.ext import commands
import json

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

TOKEN = "PUT_YOUR_TOKEN_HERE"
bot = commands.Bot(command_prefix='/', intents=intents)
POLL_DICT = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def vote(ctx, theme, *options):
    if len(options) < 2:
        await ctx.send("至少需要兩個選項才能開始投票！")
        return

    # formatted_options = [f"{i + 1}. {option}" for i, option in enumerate(options)]
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    formatted_options = [f"{alphabet[i]}. {option}" for i, option in enumerate(options)]
    formatted_options_text = "\n".join(formatted_options)

    embed = discord.Embed(title="投票人數：0", description=theme + "：\n" + f"{formatted_options_text}", color=0x00ff00)
    embed.set_author(name=f"投票發起者： {str(ctx.author)}", icon_url=ctx.author.avatar)

    message = await ctx.send(embed=embed)
    POLL_DICT[message.id] = {}
    for i in range(len(options)):
        await message.add_reaction(chr(0x1f1e6 + i))  # Adding number emojis as reactions
    await message.add_reaction(chr(0x274C))  # Cross mark emoji
    await message.add_reaction(chr(0x2705))  # Checkmark emoji

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    if user.name == bot.user.name:
        return
    try:
        if len(message.embeds)>0:
            embed = message.embeds[0]
        else:
            print("add reaction: on other message")
            return
    except Exception as e:
        print("add reaction:"+e)
        return

    if not message.id in POLL_DICT.keys():
        await user.send("投票已經結算")
        return
    if  "投票" in embed.title and user.name != bot.user.name:
        options = [reaction.emoji for reaction in message.reactions if reaction.me]
        # check mark
        if reaction.emoji == chr(0x2705):
            poll_requester = embed._author['name'].replace("投票發起者： ", "")
            # get result
            if poll_requester == user.name:
                if message.id in POLL_DICT.keys():
                    poll_result = get_poll_result(message.id)
                    poll_result_txt = process_result_to_txt(poll_result)

                    result_embed = embed = discord.Embed(title="投票結果\n投票人數："+str(count_poll_result(poll_result)), description=poll_result_txt, color=0x00ff00)
                    await message.reply(embed=result_embed)
                    await user.send("投票已經替您結算")
                    save_dict_to_json(POLL_DICT[message.id], "result/"+str(message.id)+".json")
                    del POLL_DICT[message.id]
                pass
            else:
                await user.send("您不是投票發起者，無法結算投票")
            return
        elif reaction.emoji == chr(0x274C):
            if user.name in POLL_DICT[message.id].keys():
                del POLL_DICT[message.id][user.name]
                await user.send("撤銷了上次的投票結果")
            else:
                await user.send("還未進行投票，無法撤銷")
            return
        
        # if already vote
        if user.name in POLL_DICT[message.id].keys():
            await user.send("已經投給了："+POLL_DICT[message.id][user.name]+"，要撤消上一個投票請按叉")
            return

        # if reaction emoji in the specific options
        elif reaction.emoji in options:
            index = options.index(reaction.emoji)
            option_text = embed.description.split('\n')[index+1].split('. ')[-1]
            POLL_DICT[message.id][user.name] = option_text
            await user.send(f"您投票給了選項：{option_text}")
        # else do nothing
        else:
            return

        new_embed = discord.Embed.from_dict(embed.to_dict())
        new_embed.title = "投票人數："+str(count_poll_result(get_poll_result(message.id)))

        await message.edit(embed=new_embed)

def get_poll_result(id)->dict:
    poll_result = {}
    poll = POLL_DICT[id]
    for i in poll.keys():
        if poll[i] in poll_result.keys():
            poll_result[poll[i]]+=1
        else:
            poll_result[poll[i]]=1
    return poll_result

def process_result_to_txt(result:dict)->str:
    txt = "投票結果：\n"
    for i in result.keys():
        txt+=str(i)+"："+str(result[i])+"人"+"\n"
    return txt

def count_poll_result(result:dict)->int:
    count = 0
    for i in result.keys():
        count+=result[i]
    return count

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("無效的指令！")

def save_dict_to_json(dictionary, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(dictionary, file, ensure_ascii=False, indent=4)
        print(f"字典已儲存到 {file_path}")
    except Exception as e:
        print(f"儲存字典時發生錯誤：{e}")

if __name__ == "__main__":
    bot.run(TOKEN)
