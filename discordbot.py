import discord
import datenverarbeitung as dv
import json
import time
import requests

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


#
#       Classes
#

class CharSelect(discord.ui.Select):
    def __init__(self, charlist: list):
        options = []
        for char in charlist:
            options.append(discord.SelectOption(label=char))
        super().__init__(placeholder="Wähle einen Charakter für mehr Details", max_values=1, min_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        lists = getraidlist()
        charlist = lists[1]
        optionlist = lists[2]
        selectedchar = optionlist[charlist.index(self.values[0])]
        for charname, realmname in selectedchar.items():
            name = charname.lower()
            realm = "-".join(realmname.split(" ")).lower().replace("'", "")
        equip = dv.getcharequip(name, realm)
        equip["class"] = dv.getcharclass(name, realm)
        equip["thumbnail"] = dv.getcharmedia(name, realm)["portrait"]
        gearembed = await constructgearembed(charname, realmname, equip)
        await interaction.followup.send(embed = gearembed, ephemeral=True)

class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 7200, select):
        super().__init__(timeout=timeout)
        self.add_item(select)


#
#       Functions
#

def getraidlist() -> list:
    f = open("raidplayerlist.json", "r")
    playerlist = json.load(f)
    f.close()
    charlist = []
    optionlist = []
    for character in playerlist:
        charlist.append(character["name"] + "-" + character["realm"])
        optionlist.append({character["name"]: character["realm"]})
    return [playerlist, charlist, optionlist]

def saveraidlist(playerlist: list):
    f = open("raidplayerlist.json", "w")
    json.dump(playerlist, f, indent = 4)
    f.close

def saveSettings(settings: dict):
    f = open("settings.json", "w")
    json.dump(settings, f, indent = 4)
    f.close()

def loadSettings() -> dict:
    f = open("settings.json", "r")
    settings = json.load(f)
    f.close()
    return settings

def class_to_color(classname: str) -> int:
    colordict = {
        "Druide": 16743434, #FF7C0A
        "Dämonenjäger": 10694857, #A330C9
        "Hexenmeister": 8882414, #8788EE
        "Jäger": 11195250, #AAD372
        "Krieger": 13015917, #C69B6D
        "Magier": 4179947, #3FC7EB
        "Mönch": 65432, #00FF98
        "Paladin": 16026810, #F48CBA
        "Priester": 16777215, #FFFFFF
        "Rufer": 3380095, #33937F
        "Schamane": 28893, #0070DD
        "Schurke": 16774248, #FFF468
        "Todesritter": 12852794 #C41E3A
    }

    color = colordict[classname]
    return color

def makeEmbed(embeddict: dict) -> discord.Embed:
    return discord.Embed().from_dict(embeddict)

def evalgearstatus(status: int) -> str:
    match status:
        case 0:
            body = f"{settings['emotes']['checkmark']} "
        case 1:
            body = f"{settings['emotes']['warning']} "
        case 2:
            body = f"{settings['emotes']['alert']} "
        case 3:
            body = f"{settings['emotes']['none']} "
    return body

def characterexists(name: str, realm: str) -> bool:
    media = dv.getcharmedia(name, realm)
    return not type(media) == int

def getmains() -> list:
    f = open("playermains.json", "r")
    mainlist = json.load(f)
    f.close()
    return mainlist

def savemains(mainlist: list):
    f = open("playermains.json", "w")
    json.dump(mainlist, f, indent = 4)
    f.close()

def removemain(id: int):
    mainlist = getmains()
    if str(id) in mainlist:
        del mainlist[str(id)]
    savemains(mainlist)

def removeraid(id: int):
    raidliste = getraidlist()[0]
    dellist = []
    for character in raidliste:
        if str(id) == character["discordID"]:
            dellist.append(character)
        
    if len(dellist) != 0:
        for character in dellist:
            raidliste.remove(character)
    saveraidlist(raidliste)

def getitemiconid(id: int) -> int:
    f = open("itemiconid.json", "r")
    itemiconidlist = json.load(f)
    f.close
    
    if str(id) in itemiconidlist:
        icondata =  ["", itemiconidlist[str(id)]]
    else:
        icondata = dv.getitemmedia(id)
        itemiconidlist[str(id)] = icondata[1]
    
    f = open("itemiconid.json", "w")
    json.dump(itemiconidlist, f, indent = 4)
    f.close()

    return icondata


#
#       Async Function
#

async def addrole(guild: discord.Guild, member: discord.Member, roleid: int):
    role = await guild.fetch_role(roleid)
    await member.add_roles(role)

async def removerole(guild: discord.Guild, member: discord.Member, roleid: int):
    role = await guild.fetch_role(roleid)
    await member.remove_roles(role)

async def getmember(guild: discord.Guild, id: int) -> discord.Member:
    member = await guild.fetch_member(id)
    return member

async def getusername(guild: discord.Guild, id: int) -> str:
    user = await guild.fetch_member(id)
    return user.display_name

async def createEmoji(name: str, url: str) -> discord.Emoji:
    image = requests.get(url)
    emote = await client.create_application_emoji(name=name,image=image.content)
    return emote

async def getitememote(itemid: int, slot: str) -> str:
    slot = slot.lower().replace("ü", "ue").replace("ä", "ae").replace("ß", "ss").split(" ")[0]
    icondata = getitemiconid(itemid)
    if str(icondata[1]) in settings["emotes"]:
        return settings["emotes"][str(icondata[1])]
    else:
        itememote = await createEmoji(slot+str(icondata[1]), icondata[0])
        settings["emotes"][str(icondata[1])] = str(itememote)
        saveSettings(settings)
        return settings["emotes"][str(icondata[1])]

async def constructgearembed(name: str, realm: str, geardict: dict) -> discord.Embed:
    embed = {
        "description": f"# [**{name}-{realm}**](https://worldofwarcraft.blizzard.com/de-de/character/eu/{geardict['realm']}/{geardict['name']}/)\n### Character Ilvl: {geardict['avgilvl']}",
        "color": class_to_color(geardict["class"]),
        "thumbnail": {
            "url": geardict["thumbnail"]
        },
        "fields": [],
        "author": {
            "name": "GearBot"
        }
    }
    for item in geardict["gear"]:
        embed["fields"].append({})
        embed["fields"][-1]["name"] = "__**" + item["slot"] + "**__"
        emote = await getitememote(item["id"], item["slot"])
        body = emote + " **" + item["name"] + " - " + str(item["ilvl"]) + " "+ item["itemtrack"] + "**\n"

        if item["hassocket"]:
            for socket in item["sockets"]:
                if socket["missing"]:
                    body += f"- Fehlender Sockel {settings['emotes']['warning']}\n"
                else:
                    if socket["hasgem"]:
                        body += f"- {socket['item']} {settings['emotes']['checkmark']}\n"
                    else:
                        body += f"- Fehlender Stein {settings['emotes']['alert']}\n"
        
        if item["hasenchantment"]:
            vz = item["enchantment"][0]
            if vz["missing"]:
                body += f"- Fehlende Verzauberung {settings['emotes']['alert']}\n"
            else:
                if (item["slot"] == "Schildhand" and item["type"] in ["WEAPON", "TWOHWEAPON"]) or item["slot"] != "Schildhand":
                    match vz["tier"]:
                        case "Tier3":
                            tieremoji = settings['emotes']['t3']
                        case "Tier2":
                            tieremoji = settings['emotes']['t2']
                        case "Tier1":
                            tieremoji = settings['emotes']['t1']
                        case _:
                            tieremoji = ""
                    
                    if "item" in vz:
                        if vz["tier"] == "Tier3":
                            body += f"- {vz['item'].title()} {tieremoji} {settings['emotes']['checkmark']}\n"
                        else:
                            body += f"- {vz['item'].title()} {tieremoji} {settings['emotes']['warning']}\n"
                    else:
                        if vz["tier"] == "Tier3":
                            body += f"- {vz['description'].title()} {tieremoji} {settings['emotes']['checkmark']}\n"
                        else:
                            body += f"- {vz['description'].title()} {tieremoji} {settings['emotes']['warning']}\n"
                else:
                    pass
        
        if item["hasembellishment"]:
            body += f"- Verziert\n"
        body += "\n"

        embed["fields"][-1]["value"] = body

    embed["fields"].append({"name": ""})

    match geardict["embellishments"]:
        case 2:
            embed["fields"][-1]["value"] = f"{settings["emotes"]["embellishment"]}**(2/2)** Verzierungen {settings['emotes']['checkmark']}"
        case 1:
            embed["fields"][-1]["value"] = f"{settings["emotes"]["embellishment"]}**(1/2)** Verzierungen {settings['emotes']['warning']}"
        case 0:
            embed["fields"][-1]["value"] = f"{settings["emotes"]["embellishment"]}**(0/2)** Verzierungen {settings['emotes']['warning']}"
        case _:
            pass

    embed = makeEmbed(embed)
    return embed

async def checkgearstats(name: str, realm: str, geardict: dict) -> dict:
    field = {
        "name": f"**{name}-{realm}**"
    }
    body = "🇭 🇳 🇸 🇨 🇧 🇱 🇫 🇼 🇬 🇷 🇷 🇹 🇹 🇺 🇲 🇴 🇻\n"
    for item in geardict["gear"]:

        status = 0
        if item["hassocket"]:
            for socket in item["sockets"]:
                if socket["missing"]:
                    if status < 1:
                        status = 1
                else:
                    if socket["hasgem"]:
                        pass
                    else:
                        status = 2
        
        if item["hasenchantment"]:
            vz = item["enchantment"][0]
            if vz["missing"]:
                status = 2
            else:
                if (item["slot"] == "Schildhand" and item["type"] in ["WEAPON", "TWOHWEAPON"]) or item["slot"] != "Schildhand":
                    if "item" in vz:
                        if vz["tier"] == "Tier3":
                           pass
                        else:
                            if status < 1:
                                status = 1
                    else:
                        if vz["tier"] == "Tier3":
                            pass
                        else:
                            if status < 1:
                                status = 1
                else:
                    pass
        
        body += evalgearstatus(status)
    
    if not geardict["hasshield"]:
        body += evalgearstatus(3)

    match geardict["embellishments"]:
        case 2:
            body += evalgearstatus(0)
        case 1:
            body += evalgearstatus(1)
        case 0:
            body += evalgearstatus(1)
        case _:
            pass
    field["value"] = body

    return field

async def gearcmd(message):
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!gear {Charactername} {Realmname}\n!gear @User```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
        return
    if args[0][0] == "<":
        useDiscordID = True
        discordID = args[0][2:-1]
        mainlist = getmains()
        if discordID in mainlist:
            name = mainlist[discordID]["name"]
            realm = mainlist[discordID]["realm"]
        else:
            await message.channel.send("Dieser Benutzer hat keinen eingetragenen Main-Character.")
            return
    else:
        useDiscordID = False
        name = args[0]
        realm = " ".join(args[1:])
    if len(args) < 2 and not useDiscordID:
        await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!gear {Charactername} {Realmname}\n!gear @User```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
        return
    await message.channel.send("Sammle Spielerdaten...\nDies kann kurz dauern")
    cleanname = name.lower()
    cleanrealm = "-".join(realm.split(" ")).lower().replace("'", "")
    equip = dv.getcharequip(cleanname, cleanrealm)
    if type(equip) == int:
        if equip == 404:
            await message.channel.send(f"{name} wurde nicht auf {realm} gefunden.\nBitte überprüfe die Schreibweise des Character- und Realmnamens.")
    else:
        equip["class"] = dv.getcharclass(cleanname, cleanrealm)
        equip["thumbnail"] = dv.getcharmedia(cleanname, cleanrealm)["portrait"]
        gearembed = await constructgearembed(name, realm, equip)
        await message.channel.send(embed = gearembed)

async def raidcheckcmd(message):
    cleanlist = getraidlist()[0]
    if len(cleanlist) == 0:
        await message.channel.send("Die Spielerliste ist leer.")
        return
    await message.channel.send("Sammle Spielerdaten...\nDies kann kurz dauern")
    fields = []
    embedlist = []
    pinglist = []
    x = 0
    for character in cleanlist:
        name = character["name"]
        realm = character["realm"]
        if x == 5:
            if len(embedlist) == 0:
                embed = {
                    "description": "# Raid Gear-Check",
                    "fields": fields,
                    "author": {
                        "name": "Gearbot"
                    },
                    "color": 7929967
                }
            else:
                embed = {
                    "fields": fields,
                    "color": 7929967
                }
            embedlist.append(makeEmbed(embed))
            fields = []
            fields.append(await checkgearstats(name, realm, dv.getcharequip(name.lower(), "-".join(realm.split(" ")).lower().replace("'", ""))))
            if "alert" in fields[-1]["value"] and character["discordID"] != -1:
                pinglist.append(character["discordID"])
            x = 1
        else:
            fields.append(await checkgearstats(name, realm, dv.getcharequip(name.lower(), "-".join(realm.split(" ")).lower().replace("'", ""))))
            if "alert" in fields[-1]["value"] and character["discordID"] != -1:
                pinglist.append(character["discordID"])
            x += 1
    
    if len(fields) > 0:
        if len(embedlist) == 0:
            embed = {
                "description": "# Raid Gear-Check",
                "fields": fields,
                "author": {
                    "name": "Gearbot"
                },
                "color": 7929967
            }
        else:
            embed = {
                "fields": fields,
                "color": 7929967
                }
        embedlist.append(makeEmbed(embed))

    embednum = 0
    first = True
    for embed in embedlist:
        embednum += 1
        if embednum == len(embedlist):
            if first:
                first = False
                pingtext = ""
                for discordID in pinglist:
                    pingtext += "<@" + str(discordID) + ">"
                await message.channel.send(pingtext, embed = embed, view = SelectView(select=CharSelect(getraidlist()[1])))
            else:
                await message.channel.send(embed = embed, view = SelectView(select=CharSelect(getraidlist()[1])))
        else:
            if first:
                first = False
                pingtext = ""
                for discordID in pinglist:
                    pingtext += "<@" + str(discordID) + ">"
                await message.channel.send(pingtext, embed = embed)
            else:
                await message.channel.send(embed = embed)

async def raidaddcmd(message):
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!raidadd {Charactername} {Realmname}\n!raidadd @User\n!raidadd @User {Charactername} {Realmname}```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
        return
    if args[0][0] == "<":
        discordID = args[0][2:-1]
        if len(args) == 1:
            mainlist = getmains()
            if discordID in mainlist:
                name = mainlist[discordID]["name"]
                realm = mainlist[discordID]["realm"]
            else:
                await message.channel.send("Dieser User hat keinen eingetragenen Main-Charakter")
                return
        else:
            if len(args) < 3:
                await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!raidadd {Charactername} {Realmname}\n!raidadd @User\n!raidadd @User {Charactername} {Realmname}```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
                return
            name = args[1]
            realm = " ".join(args[2:])
        member = await getmember(message.guild, int(discordID))
        await addrole(message.guild, member, settings["raidrolle"])
    else:
        if len(args) < 2:
            await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!raidadd {Charactername} {Realmname}\n!raidadd @User\n!raidadd @User {Charactername} {Realmname}```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
            return
        discordID = -1
        name = args[0]
        realm = " ".join(args[1:])
    
    playerlist = getraidlist()[0]

    for character in playerlist:
        if name == character["name"] and realm == character["realm"]:
            await message.channel.send(f"{name}-{realm} ist bereits in der Liste")
            return
    
    cleanname = name.lower()
    cleanrealm = "-".join(realm.split(" ")).lower().replace("'", "")
    if characterexists(cleanname, cleanrealm):
        playerlist.append({"name": name, "realm": realm, "discordID": discordID})
        saveraidlist(playerlist)
        await message.channel.send(f"{name}-{realm} wurde der Raidliste hinzugefügt")
    else:
        await message.channel.send(f"{name} wurde nicht auf {realm} gefunden.\nBitte überprüfe die Schreibweise des Character- und Realmnamens.")

async def raidremovecmd(message):
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send("Der Befehl wurde falsch verwendet\nDer korrekte Syntax ist\n```!rairemove {Charactername} {Realmname}\n!raidremove @User```\nBei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben. (z.B. \"Der Rat von Dalaran\")")
        return
    playerlist = getraidlist()[0]
    deletelist = []
    if args[0][0] == "<":
        usediscordID = True
        discordID = args[0][2:-1]
        for character in playerlist:
            if discordID == character["discordID"]:
               deletelist.append(character)
        member = await getmember(message.guild, int(discordID))
        await removerole(message.guild, member, settings["raidrolle"])
    else:
        realm = " ".join(args[1:])
        name = args[0]
        usediscordID = False
        isconnected = False
        for character in playerlist:
            if name.lower() == character["name"].lower() and realm.lower() == character["realm"].lower():
               deletelist.append(character)
               if character["discordID"] != -1:
                   isconnected = True
                   discordID = character["discordID"]
    if len(deletelist) == 0:
        await message.channel.send(f"{name}-{realm} ist nicht in der Liste")
        return
    for character in deletelist:
        await message.channel.send(f"{character['name']}-{character['realm']} wurde aus der Raidliste entfernt")
        playerlist.remove(character)
    if not usediscordID and isconnected:
        stillin = False
        for character in playerlist:
            if discordID == character["discordID"]:
                stillin = True
        if not stillin:
            member = await getmember(message.guild, int(discordID))
            await removerole(message.guild, member, settings["raidrolle"])
    saveraidlist(playerlist)

async def raidlistcmd(message):
    playerlist = getraidlist()[0]
    text = "# Raid Spielerliste\n\n"

    if len(playerlist) == 0:
        text += "Die Liste ist aktuell leer"

    for character in playerlist:
        if character["discordID"] == -1:
            text += f"{settings['emotes']['discord']}: {settings['emotes']['cross']} | **{character['name']}-{character['realm']}**\n"
        else:
            text += f"{settings['emotes']['discord']}: {settings['emotes']['checkmark']} | **{character['name']}-{character['realm']}**\n"

    embed = makeEmbed({
        "description": text,
        "author": {
            "name": "Gearbot"
        },
        "color": 7929967
    })

    await message.channel.send(embed = embed)

async def maincmd(message):
    args = message.content.split(" ")[1:]
    discordID = str(message.author.id)
    name = args[0]
    realm = " ".join(args[1:])
    cleanname = name.lower()
    cleanrealm = "-".join(realm.split(" ")).lower().replace("'", "")
    if not characterexists(cleanname, cleanrealm):
        return
    mainlist = getmains()
    mainlist[discordID] = {}
    mainlist[discordID]["name"] = name
    mainlist[discordID]["realm"] = realm
    savemains(mainlist)

async def mainlistcmd(message):
    playerlist = getmains()
    text = "# Main Liste\n\n"

    if len(playerlist) == 0:
        text += "Die Liste ist aktuell leer"

    for discordID, character in playerlist.items():
        username = await getusername(message.guild, discordID)
        text += f"_{username}_ | **{character['name']}-{character['realm']}**\n"

    embed = makeEmbed({
        "description": text,
        "author": {
            "name": "Gearbot"
        },
        "color": 13414813
    })

    await message.channel.send(embed = embed)


#
#       Discord Events
#

@client.event
async def on_ready():
    print(f'Ready')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.id == settings["gearbotchannel"]:
        if message.content.startswith('!gear'):
            await gearcmd(message)
            return
    elif message.channel.id == settings["raidchannel"]:
        if message.content.startswith('!raidcheck'):
            await raidcheckcmd(message)
            return
        elif message.content.startswith('!raidadd'):
            await raidaddcmd(message)
            return
        elif message.content.startswith('!raidremove'):
            await raidremovecmd(message)
            return
        elif message.content.startswith('!raidlist'):
            await raidlistcmd(message)
            return
    elif message.channel.id == settings["mainschannel"]:
        if message.content.startswith('!main') and not message.content.startswith('!mainlist'):
            await maincmd(message)
            return
        elif message.content.startswith('!mainlist'):
            await mainlistcmd(message)
            return

@client.event
async def on_member_remove(member):
    removemain(member.id)

f = open("token.txt", "r")
token = f.read()
f.close

settings = loadSettings()
print(settings["branch"])
print(discord.__version__ + " - " + discord.version_info.releaselevel)

mainlist = getmains()
savemains(mainlist)

client.run(token)
saveSettings(settings)
