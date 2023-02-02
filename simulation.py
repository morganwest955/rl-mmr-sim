from dataclasses import dataclass
import statistics
import math
import random

#####
# Class for the ranked mmr simulation
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
    players: list = []
    mmr: int = 0
    realSkill: int = 0
    result: bool = False # win = True, loss = False

@dataclass
class Game:
    teams: list = []
    
class Simulation:

    def __init__(self, numGames, playersPerTeam, MaxNewPlayers, maxMmrDistance):
        self.numPlayers = 0
        self.numGames = numGames
        self.playersPerTeam = playersPerTeam
        self.players = []
        self.maxMmrDistance = maxMmrDistance

    # When matched against an equally rated opponent, you will gain or lose the average amount of MMR (e.g win 9, lose 9).
    # When matched against a higher rated opponent, you will gain more or lose less than the average amount of MMR (e.g. win 11, lose 7).
    # When matched against a lower rated opponent, you will gain less or lose more than the average amount of MMR (e.g. win 7, lose 11).
    def calcPostGameElo(self, game):
        # expectedScore = 1 / (1 + pow(10, (wTeamMMR - lTeamMMR) / 400))
        for team in game.teams:
            for player in team:
                if team.result:
                    player.mmr = round(((player.sigma - 1.5) * 9) + team.mmr)
                    player.realSkill = round(((player.sigma - 1.5) * 9) + team.mmr)
                    if player.streak < 0:
                        player.streak = 1
                    else:
                        player.streak += 1
                else:
                    player.mmr = round(team.mmr - ((player.sigma - 1.5) * 9))
                    player.realSkill = round(team.mmr - ((player.sigma - 1.5) * 9))
                    if player.streak > 0:
                        player.streak = -1
                    else:
                        player.streak -= 1
                player.gamesPlayed += 1
                self.calcSigma(player)
                if player.streak > 2:
                    player.realSkill += 1
    
    def calcSigma(self, player):
        if player.gamesPlayed < 15:
            player.sigma = ((-1/15) * player.numGames) + 3.5
        else:
            player.sigma = pow((1/2) * player.streak, 2) + 2.5

    # pulls all players' MMR closer to the median
    # NewMMR = TargetMMR + (OldMMR - MedianMMR) * SquishFactor
    def newReset(self, targetMMR, squishFactor):
        mmrList = []
        for player in self.players:
            mmrList.append(player.mmr)
        mmrList.sort()
        mmrMedian = statistics.median(mmrList)
        for player in self.players:
            player.mmr = targetMMR + (player.mmr - mmrMedian) * squishFactor

    # resets all players above X MMR to X
    def oldReset(self, resetMMR):
        for player in self.players:
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
        team1CombinedSkill = (game.teams[0].mmr + game.teams[0].realSkill) / 2
        team2CombinedSkill = (game.teams[1].mmr + game.teams[1].realSkill) / 2
        gameSummedSkill = team1CombinedSkill + team2CombinedSkill
        team1Percent = team1CombinedSkill / gameSummedSkill * 100
        if team1Percent > random.randint(1, 100):
            game.teams[0].result = True
        else:
            game.teams[1].result = True
        self.calcPostGameElo(game)

    def addNewPlayers(self, numPlayers, startingMMR):
        for i in range(0, numPlayers):
            newplayer = Player
            newplayer.number = self.numPlayers
            self.numPlayers += 1
            newplayer.mmr = startingMMR
            newplayer.realSkill = startingMMR
            self.players.append(newplayer)

    # run a ranked season
    def runSeason(self, startingMMR, numGamesPerPlayer):
        # make a big for loop that runs for numGames
        # add new players based on max number that are mostly low ranked with some variance in realskill and high desiretoplay
        # for every player that has desire to play, put them in teams and then runGame
        # calculate desireToPlay with a formula that accounts for streak and a random indicator. higher ranked players more likely to grind despite results as well
        for i in range(0, numGamesPerPlayer * len(self.players)):
            self.addNewPlayers(random.randint(0, 2), startingMMR)
            self.runGame(3)
        return 0

    # run the full simulation
    def runSim(self):
        # run 10 ranked seasons followed by the old MMR reset. starting MMR is low. capture MMR curves in graphs
        # add a massive wave of new low skilled players
        # run 10 ranked seasons followed by new MMR reset. starting MMR is high. capture MMR curves in graphs
        
        return 0