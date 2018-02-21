from mastodon import Mastodon
from getpass import getpass
from os import path
from bs4 import BeautifulSoup
import json
import re

api_base_url = "https://botsin.space"

if not path.exists("clientcred.secret"):
    print("No clientcred.secret, registering application")
    Mastodon.create_app("ebooks", api_base_url=api_base_url, to_file="clientcred.secret")

if not path.exists("usercred.secret"):
    print("No usercred.secret, registering application")
    email = input("Email: ")
    password = getpass("Password: ")
    client = Mastodon(client_id="clientcred.secret", api_base_url=api_base_url)
    client.log_in(email, password, to_file="usercred.secret")

def parse_toot(toot):
    soup = BeautifulSoup(toot.content, "html.parser")
    if toot.spoiler_text != "": return
    if toot.reblog is not None: return
    if toot.visibility not in ["public", "unlisted"]: return
    
    # remove all mentions
    for mention in soup.select("span"):
        mention.decompose()
    
    # make all linebreaks actual linebreaks
    for lb in soup.select("br"):
        lb.insert_after("\n")
        lb.decompose()

    # put each p element its own line because sometimes they decide not to be
    for p in soup.select("p"):
        p.insert_after("\n")
        p.unwrap()
    
    # unwrap all links (i like the bots posting links)
    links = []
    for link in soup.select("a"):
        links += [link["href"]]
        link.decompose()

    text = map(lambda a: a.strip(), soup.get_text().strip().split("\n"))

    mentions = [mention.acct for mention in toot.mentions]

    # next up: store this and patch markovify to take it
    # return {"text": text, "mentions": mentions, "links": links}
    # it's 4am though so we're not doing that now, but i still want the parser updates
    return "\0".join(list(text) + links)

def get_toots(client, id):
    i = 0
    toots = client.account_statuses(id)
    while toots is not None:
        for toot in toots:
            t = parse_toot(toot)
            if t != None:
                yield t
        toots = client.fetch_next(toots)
        i += 1
        if i%10 == 0:
            print(i)

client = Mastodon(
        client_id="clientcred.secret", 
        access_token="usercred.secret", 
        api_base_url=api_base_url)

me = client.account_verify_credentials()
following = client.account_following(me.id)

with open("corpus.txt", "w+") as fp:
    for f in following:
        print(f.username)
        for t in get_toots(client, f.id):
            fp.write(t + "\n")
