'''
GroupMe NBA Score Alert Bot

Version: 1.0
Author: Brian Walheim

Description: GroupM bot that tracks NBA scores and then messages
    alerts with links for close games

NBA API Reference:
https://github.com/kashav/nba.js/blob/master/docs/api/DATA.md 
http://data.nba.net/ 
- holds nba score board data 

GroupMe API Reference:
https://dev.groupme.com/tutorials/bots 
- used for the messagine
'''


'''
#-----------------------
# Imports
#------------------------
'''

#Handles http requests for group me bot and
# fetching api data
import requests

#Important for ensuring path to config file
import os

#Handles time functions
from datetime import datetime
from datetime import timedelta
import time
import pytz


'''
#-----------------------
# Local Variables
#------------------------
'''

#Dictionary that maps
tricodeToName = {
    'ATL':'Atlanta Hawks',
    'BOS':'Boston Celtics',
    'BKN':'Brooklyn Nets',
    'CHA':'Charlotte Hornets',
    'CHI':'Chicago Bulls',
    'CLE':'Cleveland Cavaliers',
    'DAL':'Dallas Mavericks',
    'DEN':'Denver Nuggets',
    'DET':'Detroit Pistons',
    'GSW':'Golden State Warriors',
    'HOU':'Houston Rockets',
    'IND':'Indiana Pacers',
    'LAC':'Los Angeles Clippers',
    'LAL':'Los Angeles Lakers',
    'MEM':'Memphis Grizzlies',
    'MIA':'Miami Heat',
    'MIL':'Milwaukee Bucks',
    'MIN':'Minnesota Timberwolves',
    'NOP':'New Orleans Pelicans',
    'NYK':'New York Knicks',
    'OKC':'Oklahoma City Thunder',
    'ORL':'Orlando Magic',
    'PHI':'Philadelphia 76ers',
    'PHX':'Phoenix Suns',
    'POR':'Portland Trail Blazers',
    'SAC':'Sacramento Kings',
    'SAS':'San Antonio Spurs',
    'TOR':'Toronto Raptors',
    'UTA':'Utah Jazz',
    'WAS':'Washington Wizards'
}

#Lists for tracking games already notified about
notifiedGames = []
tighterGames = []
OTGames = []

#Holds bot id held from config file
botID = ""

'''
#-----------------------
# Misc Fucntions
#------------------------
'''

#This function fetches the bot id from the config file
#
#	Pre: botid is on the first line of the file
def getConfigBotID():
	path = os.path.dirname(os.path.realpath(__file__))
	file = open(path + "/config.txt")
	return file.readline() 


'''
#-----------------------
# GroupMe Fucntions
#------------------------
'''


#Function makes push request to groupMe API
# To have bot send a message
#
#  Args: botID - group me bot id
#		 message - message you want bot to send
def sendGroupMeMessage(botID, message):
	data = {"bot_id" : botID, "text": message}
	print(data)
	r = requests.post(url = "https://api.groupme.com/v3/bots/post", json = data)

	print(r.status_code)


#Function takes in game data and formats group me message
# and sends formatted message
#
#	Args: botID - groupMe bot id
#		  header - header messsage of text
#		  hTeamTri - home team tricode
#		  vTeamTri - visiting team tricode
#		  hScore - home team score
#		  vScore - visiting team score
def sendAlert(botID, header, hTeamTri, vTeamTri, hScore, vScore):

	#Generates link
	link = getStreamLink(hTeamTri, vTeamTri)

	#Formats message
	message = "{}\n{} ({}) @ {} ({})\n{}".format(header, vTeamTri, vScore, hTeamTri, hScore, link)

	#Sends group me message
	sendGroupMeMessage(botID, message)


'''
#-----------------------
# NBA Data Fucntions
#------------------------
'''

def getCurrentNBAGames(notifiedGames, tighterGames, OTGames):

    #Getting the proper data
    #If connection fails just exits function to prevent error
    try:
        page = requests.get("http://data.nba.net/data/10s/prod/v1/" + getNBADayString() +"/scoreboard.json")
        data = page.json()
    except:
        return None

    #For debugging outputs the json file
    #print(json.dumps(data, indent=2))

    #Flag to see if there are no active games
    activeGames = False

    #Iterates through every game for the day
    for game in data["games"]:

        if game["leagueName"] == "standard":

            gameID = game["gameId"]

            homeTeamCode = game["hTeam"]["triCode"]
            homeTeamScore =  game["hTeam"]["score"]

            visitTeamCode = game["vTeam"]["triCode"]
            visitTeamScore = game["vTeam"]["score"]

            gamePeriod = game["period"]["current"]
            timeInPeriod = game["clock"]

            #Checks to see if game is active
            if (homeTeamScore != "" and visitTeamScore != ""):
                activeGames = True
                print("Q" + str(gamePeriod) + " " + timeInPeriod + ": " + visitTeamCode + "(" + visitTeamScore + ")"  + " @ " +  homeTeamCode + "(" + homeTeamScore + ")")
                
                #Calculates if the game is close
                if (isCloseGame(int(visitTeamScore), int(homeTeamScore), timeInPeriod, gamePeriod)==1):
                    
                    #Checks to make sure that we have not been notified for game
                    if (gameID not in notifiedGames):

                        #Add game to list of notified game
                        notifiedGames.append(gameID)

                        #Sends group me alert about the game
                        sendAlert(botID, "CLUTCH TIME GAME", homeTeamCode, visitTeamCode, homeTeamScore, visitTeamScore)
                        

                elif(isCloseGame(int(visitTeamScore), int(homeTeamScore), timeInPeriod, gamePeriod)==2):
                    #Checks to make sure that we have not been notified for game
                    if (gameID not in tighterGames):

                        #Add game to list of notified game
                        tighterGames.append(gameID)

                        #Sends group me alert about the game
                        sendAlert(botID, "2 MINUTE CLOSE GAME", homeTeamCode, visitTeamCode, homeTeamScore, visitTeamScore)

                elif(isCloseGame(int(visitTeamScore), int(homeTeamScore), timeInPeriod, gamePeriod)==3):
                    #Checks to make sure that we have not been notified for game
                    if (gameID not in OTGames):

                        #Add game to list of notified game
                        OTGames.append(gameID)

                        #Sends group me alert about the game
                        sendAlert(botID, "OVERTIME GAME", homeTeamCode, visitTeamCode, homeTeamScore, visitTeamScore)

    #If games are over clears notified games
    if(not activeGames):
        notifiedGames = []
        tighterGames = []
        OTGames = []

        #Sleeps for 2 hours
        time.sleep(7200)

#Returns formatted string for the current NBA dayString
#   NBA day is defined as day of NBA games
#   Returns: String formatted YYYYMMDD
def getNBADayString():

    tz_NY = pytz.timezone('America/New_York') 
    datetime_NY = datetime.now(tz_NY)
    if(int(datetime_NY.strftime("%H")) <= 3):
        datetime_NY = datetime_NY - timedelta(1)
        return datetime_NY.strftime("%Y%m%d")

    return datetime_NY.strftime("%Y%m%d")


#Takes in the hTeam and vTeam tricodes and generates
# the link to the stream    
def getStreamLink(hTeamCode, vTeamCode):

    #home team and the visiting team
    #http://liveonscore.tv/nba-stream/home-team-vs-away-team/
    homeTeam = tricodeToName[hTeamCode].lower().replace(" ","-")
    awayTeam = tricodeToName[vTeamCode].lower().replace(" ","-")
    return "http://weakstreams.com/nba-stream/"+homeTeam+"-vs-"+awayTeam+"/"

#Returns int if team is clsoe
#   Close game is defined as withing 5 minutes
#   and score diferential of 5 or less
#
#   Input: both team scores
#          time left in the quarter
#          period is quarter of the game
#
#   Returns: 0 - if not close
#            1 - if close within 5 minutes
#            2 - if close within 2 minutes
#            3 - if close within overtime
def isCloseGame(score1, score2, time, period):

    scoreDifferential = abs(score1-score2)

    minutes = 0
    if(":" in time):
        minutes = int(time.split(":")[0])

    #Checks for close game within OT
    if(scoreDifferential <= 5 and period > 4):
        return 3

    #Checks for the close game within 2 minutes
    if(scoreDifferential <= 5 and period == 4 and (":" not in time or minutes<2) and time != ""):
        return 2

    #Checks for theclose game within 5 minutes
    elif(scoreDifferential <= 5 and period == 4 and (":" not in time or minutes<5) and time != ""):
        return 1
    
    #Returns 0 if not close
    return 0


'''
#-----------------------
# Main
#------------------------
'''

#Fetches group me from config file
botID = getConfigBotID()

#Sends bot boot up message
#sendGroupMeMessage(botID, "Bot booting up")
#time.sleep(15)
#sendGroupMeMessage(botID, "Bot booted up")

print(getNBADayString())

#Main loop checks scores every 15 seconds
while True:
    getCurrentNBAGames(notifiedGames, tighterGames, OTGames)
    time.sleep(15)



