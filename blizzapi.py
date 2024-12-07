# I'd not recommend using aliases for standard packages, which are commonly known and have a short name anyway.. thats just confusing for the reader
import requests as rq
import json
# pep8 rule: imports should be followed by two blank lines (same as between classes)
# you should not name a function with commonly used strings as "api" (same applies to variables like "data" or "response" which could be used by the language/side packages itself, better be more specific to avoid interdependancies)
# further the function name should reflect the specific goal of the function, in this case eg. "call_blizz_api"
def api(url: str, namespace: str):
    # - although python supports it, the parameter types normally are kept open
    # - you should define docstrings within triple invertes commas for each of your functions, which describe the functional use of it and optionally describe important parameters
    # - "blizzardapi.txt" should be a variable
    f = open("blizzardapi.txt", "r")
    # don' repeat your code.. betther use a value cleaner function for this
    clientID = f.readline().replace("\n", "")
    secret = f.readline().replace("\n", "")
    f.close()
    # better put all your constant variables (locale, data, blizzapi.txt) to the beginning of your function for an easier overview
    locale = "de_DE"

    data = {"grant_type": "client_credentials"}
    # same here as above: put the url to a variable
    response = rq.post("https://oauth.battle.net/token", data=data, auth=(clientID, secret))
    # don't use "magic numbers" like 200 to do checks. Either use your own variable like "status_ok = 200" and check against that, or simply use responce.ok here
    if response.status_code != 200:
        return response.status_code
    # your function should always do one thing! should be another function "get_bearer_token" from here on..
    response = json.loads(response.text)
    # why all these blank lines? you should use them to seperate blocks of code, but not after each step
    accesstoken = response["access_token"]
    # these lonely brackerts are supported by python but it looks like java ;) better and more pythonic would be one line as headers = {'Authorization': f'Bearer {accesstoken}'}
    headers = {
        'Authorization': f'Bearer {accesstoken}',
    }
    # same as above.. dont waste lines and make it pythonic
    params = {
        'namespace': namespace,
        'locale': locale,
    }

    response = rq.get(url, params=params, headers=headers)

    if response.status_code != 200:
        return response.status_code
    # Better do a try/except here, instead of just hoping this always works
    # Further I'd recommend you never return something directly as this is harder to debug later
    return json.loads(response.text)

def characterequip(name: str, realm: str):
    # your prints should be in english ;)
    print(f"Anfrage an Characterequip: {name}-{realm}")
    # the base part of the api string should be variable -> never copy stuff like that 
    # I'd recommend to use a variable for the realm/name thing too
    # Further you could combine characterequip, getcharspec and getcharmedia into one function and make the last part of the url a parameter
    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{name}/equipment"
    return api(url, "profile-eu")

def getcharspec(name: str, realm: str):
    print(f"Anfrage an Characterspec: {name}-{realm}")
    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{name}/specializations"
    return api(url, "profile-eu")

def getcharmedia(name: str, realm: str):
    print(f"Anfrage an Charactermedien: {name}-{realm}")
    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{name}/character-media"
    return api(url, "profile-eu")

# as python doesn't use camel case you should make your functions readable by using underscores -> this should be named get_item_media
def getitemmedia(itemid: int):
    print(f"Anfrage an Itemmedia: {itemid}")
    url = f"https://eu.api.blizzard.com/data/wow/media/item/{itemid}"
    return api(url, "static-eu")

            
