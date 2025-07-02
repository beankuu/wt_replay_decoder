import requests, browser_cookie3, json

"""
Get list of warthunder replay from api/replay

* Logging in to Warthunder Replay by browser(chrome/firefox) required first

"""
def list_replay(page_no):
    url = "https://warthunder.com/en/api/replay"
    # default payload
    payload = {
        "gameMode":["arcade","realistic","simulation"], "gameType":"randomBattle",
        "techType":"all", "findMissionValue":"", "findUserValue":"", "findUserType":"USERNAME", "isUserOwnReplays":False,
        "rankRange":"", "timeRangeFrom":"","timeRangeTo":"","timeRangeFromDay":8,"timeRangeFromMonth":2,"timeRangeFromTime":"10:00",
        "timeRangeToDay":10,"timeRangeToMonth":5,"timeRangeToTime":"14:00","limit":50,"page":page_no
    }
    # Get Cookie
    cj = browser_cookie3.chrome(domain_name="warthunder.com")
    if len(cj) == 0: cj = browser_cookie3.firefox(domain_name="warthunder.com")
    if len(cj) == 0: print("No Cookies Found. Log in to 'https://warthunder.com/en/tournament/replay' with Firefox or Chrome first");exit(1)

    s = requests.Session() 
    r = s.post(url, data=json.dumps(payload), cookies=cj)

    if r.status_code == 200:
        return r.json()['items']
    else:
        print("!= 200 OK. Not Successful. Log in to 'https://warthunder.com/en/tournament/replay' or somthing else");exit(1)

"""
return max(config['endTime'])
"""
def latest_replay(config: json):
    latest = 0
    for line in config: 
        if latest < int(line['endTime']): latest = int(line['endTime'])
    return latest

"""
return everything before "latest endTime" & is "latest endTime" not reached
"""
def check_replay(latest: int, lst: list) -> bool:
    replay_lst = []
    for elm in lst:
        if elm['endTime'] >= latest:
            block = {
                "sessionIdHex": elm['sessionIdHex'],
                "statisticGroup": elm['clanBattle'],
                "clanBattle": elm['clanBattle'],
                "gameMode": elm['gameMode'],
                "title": elm['title'],
                "startTime": elm['startTime'],
                "endTime": elm['endTime'],
                "players": { "team_1": [], "team_2": [] }
            }
            for i in range (len(elm['players']['team_1'])):
                block['players']['team_1'] += [{"userId": elm['players']['team_1'][i]['userId'],  "name": elm['players']['team_1'][i]['name']}]
            if 'team_2' in elm['players']:
                for i in range (len(elm['players']['team_2'])):
                    block['players']['team_2'] += [{"userId": elm['players']['team_2'][i]['userId'],  "name": elm['players']['team_2'][i]['name']}]
            print('blk', block)

            replay_lst += [block]
            
    return replay_lst, latest < lst[-1]['endTime']

if __name__ == "__main__":
    data = {}
    replay_list = []
    with open('config.json', 'r+') as file:
        data = json.load(file)

    latest = latest_replay(data)
    

    page_no = 1
    lst = []
    replay_found = False
    
    #lst = list_replay(page_no)
    #lst, replay_found = check_replay(latest, lst)
    
    while not replay_found or len(lst) == 0:
        replay_found += lst
        lst = list_replay(page_no)
        lst, replay_found = check_replay(latest, lst)
        page_no += 1
    
    # compare 1) sessionIdHex, 2) Date 
    print(lst)


    ##[0]{sessionIdHex, statisticGroup, clanBattle, gameMode, title, startTime, endTime, players >  team_1 > [0] > {userId, name}
    with open('config.json', 'r+') as file:
        json.dump(lst, file)
