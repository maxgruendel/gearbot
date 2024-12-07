import requests as rq
import json

def api(url: str, namespace: str):

    f = open("blizzardapi.txt", "r")
    clientID = f.readline().replace("\n", "")
    secret = f.readline().replace("\n", "")
    f.close()
    locale = "de_DE"

    data = {"grant_type": "client_credentials"}

    response = rq.post("https://oauth.battle.net/token", data=data, auth=(clientID, secret))

    if response.status_code != 200:
        return response.status_code

    response = json.loads(response.text)

    accesstoken = response["access_token"]

    headers = {
        'Authorization': f'Bearer {accesstoken}',
    }

    params = {
        'namespace': namespace,
        'locale': locale,
    }

    response = rq.get(url, params=params, headers=headers)

    if response.status_code != 200:
        return response.status_code

    return json.loads(response.text)

def characterequip(name: str, realm: str):
    print(f"Anfrage an Characterequip: {name}-{realm}")
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

def getitemmedia(itemid: int):
    print(f"Anfrage an Itemmedia: {itemid}")
    url = f"https://eu.api.blizzard.com/data/wow/media/item/{itemid}"
    return api(url, "static-eu")

            