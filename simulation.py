from dataclasses import dataclass, field, replace
import statistics
import math
import random
import matplotlib.pyplot as plt

#####
# Classes for the ranked mmr simulation
#
### References ###
# dataclass: https://stackoverflow.com/questions/35988/c-like-structures-in-python
# mmr system: https://www.reddit.com/r/RocketLeagueYtzi/comments/ilcmcc/how_mmr_and_the_matchmaking_system_works/


@dataclass
class Player:
    number: int = 0
    mmr: int = 0
    realSkill: int = 0
    gamesPlayed: int = 0
    sigma: float = 3.5 # 3.5 max, 2.5 is normalized. Is higher at start of season and normalizes around 15 to 20 games in.
    desireToPlay: float = 0.0
    streak: int = 0

@dataclass
class Team:
    players: list = field(default_factory=list)
    mmr: int = 0
    realSkill: int = 0
    result: bool = False # win = True, loss = False

@dataclass
class Game:
    teams: list = field(default_factory=list)
    
class Simulation:

    def __init__(self, playersPerTeam, maxMmrDistance):
        self.numPlayers = 0
        self.playersPerTeam = playersPerTeam
        self.players = []
        self.maxMmrDistance = maxMmrDistance
        self.callNewPlayers = 0

    # When matched against an equally rated opponent, you will gain or lose the average amount of MMR (e.g win 9, lose 9).
    # When matched against a higher rated opponent, you will gain more or lose less than the average amount of MMR (e.g. win 11, lose 7).
    # When matched against a lower rated opponent, you will gain less or lose more than the average amount of MMR (e.g. win 7, lose 11).
    def calcPostGameElo(self, game):
        # expectedScore = 1 / (1 + pow(10, (wTeamMMR - lTeamMMR) / 400))
        for team in game.teams:
            for player in team.players:
                player.realSkill += 1
                if team.result:
                    newMMR = round(((player.sigma - 1.5) * 9) + player.mmr)
                    if newMMR - player.mmr > 18:
                        player.mmr += 18
                    else:
                        player.mmr = newMMR
                    # player.realSkill = round(((player.sigma - 1.5) * 9) + player.realSkill)
                    player.realSkill = round(9 + player.realSkill)
                    if player.streak < 0:
                        player.streak = 1
                    else:
                        player.streak += 1
                else:
                    newMMR = round(player.mmr - ((player.sigma - 1.5) * 9))
                    if player.mmr - newMMR > 18:
                        player.mmr -= 18
                    else:
                        player.mmr = newMMR
                    if player.mmr < 0: player.mmr = 0
                    player
                    # player.realSkill = round(player.realSkill - ((player.sigma - 1.5) * 9))
                    player.realSkill = round(player.realSkill - 9)
                    # player.realSkill -= 5
                    if player.streak > 0:
                        player.streak = -1
                    else:
                        player.streak -= 1
                player.gamesPlayed += 1
                self.calcSigma(player)
                # self.realSkillDecay(player)
                if abs(player.streak) > 1: player.realSkill += player.streak
                if player.realSkill < 30: player.realSkill = 100

    def realSkillDecay(self, player):
        player.realSkill -= random.randint(0, 3)
    
    def calcSigma(self, player):
        if player.gamesPlayed < 15:
            player.sigma = ((-1/15) * player.gamesPlayed) + 3.5
        else:
            if pow((1/2) * player.streak, 2) + 2.5 > 3.5:
                player.sigma = 3.5
            else:
                player.sigma = pow((1/2) * player.streak, 2) + 2.5

    def fixRealSkill(self, player):
        if player.mmr / player.realSkill < 0.9:
            player.realSkill = round(player.mmr * 1.1)
        elif player.mmr / player.realSkill > 1.1:
            player.realSkill = round(player.mmr * 0.9)
        if player.realSkill < 30: player.realSkill = 100

    # pulls all players' MMR closer to the median
    # NewMMR = TargetMMR + (OldMMR - MedianMMR) * SquishFactor
    def newReset(self, squishFactor):
        mmrList = []
        for player in self.players:
            mmrList.append(player.mmr)
        mmrList.sort()
        mmrMedian = statistics.median(mmrList)
        for player in self.players:
            self.fixRealSkill(player)
            player.mmr = mmrMedian + (player.mmr - mmrMedian) * squishFactor


    # resets all players above X MMR to X
    def oldReset(self, resetMMR):
        for player in self.players:
            self.fixRealSkill(player)
            if player.mmr > resetMMR:
                player.mmr = resetMMR

    # set team MMR and team realSkill by averaging those stats from each player
    def calcTeamMMR(self, team):
        for player in team.players:
            team.mmr += player.mmr
            team.realSkill += player.realSkill
        team.mmr = int(team.mmr / len(team.players))
        team.realSkill = int(team.realSkill / len(team.players))
        return team

    # find the players for the game, then build the teams and the game
    def buildGame(self, playersPerTeam):
        initialPlayer = random.choice(self.players)
        playerList = [initialPlayer]
        while len(playerList) < playersPerTeam * 2:
            potentialPlayer = random.choice(self.players)
            if abs(potentialPlayer.mmr - initialPlayer.mmr) < self.maxMmrDistance:
                playerList.append(potentialPlayer)
        team1 = Team()
        team2 = Team()
        while len(playerList) > 0:
            team1.players.append(playerList.pop(0))
            team2.players.append(playerList.pop(0))
        team1 = self.calcTeamMMR(team1)
        team2 = self.calcTeamMMR(team2)
        game = Game()
        game.teams.append(team1)
        game.teams.append(team2)
        return game

    # run a ranked game
    def runGame(self, playersPerTeam):
        # pick two similarly rated teams to face off
        # figure out probabilities of each team winning with MMR and realskill.
        # generate a random number between 1 and 100. if it's less than team1Percent, team1 wins. Otherwise, team2 wins.
        # calculate new MMRs and other stats for players
        game = self.buildGame(playersPerTeam)
        team1CombinedSkill = ((game.teams[0].mmr * 0.2) + (game.teams[0].realSkill * 0.8)) / 2
        team2CombinedSkill = ((game.teams[1].mmr * 0.2) + (game.teams[1].realSkill * 0.8)) / 2
        gameSummedSkill = team1CombinedSkill + team2CombinedSkill
        team1Percent = team1CombinedSkill / gameSummedSkill * 100
        # print("Team 1 combined skill: " + str(team1CombinedSkill))
        # print("Team 2 combined skill: " + str(team2CombinedSkill))
        if team1Percent > random.randint(1, 100):
            game.teams[0].result = True
            # print("Game result: Team 1 wins!")
        else:
            game.teams[1].result = True
            # print("Game result: Team 2 wins!")
        self.calcPostGameElo(game)

    def addNewPlayers(self, numPlayersAdding, startingMMR, startingSkill):
        if self.numPlayers > 10000: exit(-1)
        for i in range(0, numPlayersAdding):
            newplayer = Player()
            newplayer.number = self.numPlayers
            self.numPlayers += 1
            newplayer.mmr = startingMMR
            newplayer.realSkill = startingSkill + random.randint(-50, 50)
            self.players.append(newplayer)

    # run a ranked season
    def runSeason(self, startingMMR, startingSkill, numGamesPerPlayer, numPlayersBetweenGames):
        # make a big for loop that runs for numGames
        # add new players based on max number that are mostly low ranked with some variance in realskill and high desiretoplay
        # for every player that has desire to play, put them in teams and then runGame
        # calculate desireToPlay with a formula that accounts for streak and a random indicator. higher ranked players more likely to grind despite results as well
        for i in range(0, numGamesPerPlayer * len(self.players)):
            self.runGame(self.playersPerTeam)
            # print("Running game " + str(i) + " of " + str(numGamesPerPlayer * len(self.players)))
            # print(numGamesPerPlayer)
            # print(len(self.players))
        
    def preparePlot(self, title, dataName):
        realSkillList = []
        mmrList = []
        gamesPlayedList = []
        sigmaList = []
        desireToPlayList = []
        streakList = []
        for player in self.players:
            if "realSkill" in dataName:
                realSkillList.append(player.realSkill)
            if "mmr" in dataName:
                mmrList.append(player.mmr)
            if "gamesPlayed" in dataName:
                gamesPlayedList.append(player.gamesPlayed)
            if "sigma" in dataName:
                sigmaList.append(player.sigma)
            if "desireToPlay" in dataName:
                desireToPlayList.append(player.desireToPlay)
            if "streak" in dataName:
                streakList.append(player.streak)
        if len(realSkillList) > 0:
            self.drawPlot(title, realSkillList, "realSkill")
        if len(mmrList) > 0:
            self.drawPlot(title, mmrList, "mmr")
        if len(gamesPlayedList) > 0:
            self.drawPlot(title, gamesPlayedList, "gamesPlayed")
        if len(sigmaList) > 0:
            self.drawPlot(title, sigmaList, "sigma")
        if len(desireToPlayList) > 0:
            self.drawPlot(title, desireToPlayList, "desireToPlay")
        if len(streakList) > 0:
            self.drawPlot(title, streakList, "streak")

    def drawPlot(self, title, data, dataName):
        plt.figure(figsize = (6, 6))
        plotTitle = title + "_" + dataName
        plt.title(plotTitle)
        plt.hist(data, bins = 30)
        savePath = "C:/Users/mdog9/source/graphs/mmr/"
        saveName = savePath + plotTitle + "_plot.png"
        plt.savefig(saveName)

    # run the full simulation
    def runSim(self):
        # run 10 ranked seasons followed by the old MMR reset. starting MMR is low. capture MMR curves in graphs
        # add a massive wave of new low skilled players
        # run 10 ranked seasons followed by new MMR reset. starting MMR is high. capture MMR curves in graphs
        self.addNewPlayers(1000, 200, 200)
        for i in range(1, 11):
            self.addNewPlayers(random.randint(20,30),200,200)
            self.runSeason(200, 200, 100, 0)
            self.preparePlot("Old Season " + str(i), ["realSkill", "mmr", "gamesPlayed"])
            self.oldReset(1200)
            print("Finished season " + str(i) + " of old Ranked")
        self.addNewPlayers(3000, 600, 200)
        for i in range(1, 11):
            self.addNewPlayers(random.randint(40,50), 600, 200)
            self.runSeason(600, 200, 50, 0)
            self.preparePlot("New Season " + str(i), ["realSkill", "mmr", "gamesPlayed"])
            self.newReset(0.8)
            print("Finished season " + str(i) + " of new Ranked")
        return 0

simulation = Simulation(3, 20)
simulation.runSim()

# players = []
# numPlayers = 0
# newplayer = Player()
# newplayer.number = numPlayers
# numPlayers += 1
# newplayer.mmr = 200
# newplayer.realSkill = 200
# print("new player 0 real skill: " + str(newplayer.realSkill))
# print("new player 0 number: " + str(newplayer.number))
# players.append(newplayer)

# newplayer1 = Player()
# newplayer1.number = numPlayers
# numPlayers += 1
# newplayer1.mmr = 205
# newplayer1.realSkill = 205
# print("new player 1 real skill: " + str(newplayer1.realSkill))
# players.append(newplayer1)

# print(players[0].number)
# print(players[1].number)

# i = 0
# for p in players:
#     print(i)
#     print("Player " + str(i) + " mmr: " + str(p.mmr))
#     if i == 1: p.mmr = 300
#     print("Player " + str(i) + " mmr: " + str(p.mmr))
#     i += 1