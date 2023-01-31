from dataclasses import dataclass
import math

#####
# Class for the ranked mmr simulation
#
### References ###
# dataclass: https://stackoverflow.com/questions/35988/c-like-structures-in-python
# mmr system: https://www.reddit.com/r/RocketLeagueYtzi/comments/ilcmcc/how_mmr_and_the_matchmaking_system_works/


@dataclass
class Player:
    number: int
    mmr: int
    realSkill: int
    gamesPlayed: int
    sigma: float # 3.5 max, 2.5 is normalized. Is higher at start of season and normalizes around 15 to 20 games in.
    desireToPlay: float
    streak: int
    
class Simulation:

    def __init__(self, numPlayers, numGames, playersPerTeam, MaxNewPlayers):
        self.numPlayers = numPlayers
        self.numGames = numGames
        self.playersPerTeam = playersPerTeam
        self.players = []

    # When matched against an equally rated opponent, you will gain or lose the average amount of MMR (e.g win 9, lose 9).
    # When matched against a higher rated opponent, you will gain more or lose less than the average amount of MMR (e.g. win 11, lose 7).
    # When matched against a lower rated opponent, you will gain less or lose more than the average amount of MMR (e.g. win 7, lose 11).
    def calcPostGameElo(self, wTeam, lTeam):
        wTeamMMR = self.calcTeamMMR(wTeam)
        lTeamMMR = self.calcTeamMMR(lTeam)
        # expectedScore = 1 / (1 + pow(10, (wTeamMMR - lTeamMMR) / 400))
        for player in wTeam:
            player.mmr = round(((player.sigma - 1.5) * 9) + wTeamMMR)
            player.realSkill = round(((player.sigma - 1.5) * 9) + wTeamMMR)
            player.gamesPlayed += 1
            if player.streak < 0:
                player.streak = 1
            else:
                player.streak += 1

        for player in lTeam:
            player.mmr = round(lTeamMMR - ((player.sigma - 1.5) * 9))
            player.realSkill = round(lTeamMMR - ((player.sigma - 1.5) * 9))
            player.gamesPlayed += 1
            if player.streak > 0:
                player.streak = -1
            else:
                player.streak -= 1

    # team mmr is the average of each player
    def calcTeamMMR(self, team):
        mmr = 0
        for player in team:
            mmr += player.mmr
        return round(mmr / len(team))
    
    # pulls all players' MMR closer to the median
    # NewMMR = TargetMMR + (OldMMR - MedianMMR) * SquishFactor
    def oldReset(self):
        return 0

    # resets all players above X MMR to X
    def newReset(self, resetMMR):
        for player in self.players:
            if player.mmr > resetMMR:
                player.mmr = resetMMR
    
    # run a ranked season
    def runSeason(self, startingMMR):
        # make a big for loop that runs for numGames
        # add new players based on max number that are mostly low ranked with some variance in realskill and high desiretoplay
        # for every player that has desire to play, put them in teams and then runGame
        # calculate desireToPlay with a formula that accounts for streak and a random indicator. higher ranked players more likely to grind despite results as well
        # adjust player sigmas. start at 3.5 and then get it to 2.5 by 15 games. increase with big streaks and decrease with low streaks

        return 0

    # run a ranked game
    def runGame(self):
        # pick two similarly rated teams to face off
        # figure out probabilities of each team winning with MMR, realskill, and some small random indicator. one better player with two worse players will get dragged.
        # decide the winner and then calculate player mmr and realskill with the same formula
        return 0

    # run the full simulation
    def runSim(self):
        # run 10 ranked seasons followed by the old MMR reset. starting MMR is low. capture MMR curves in graphs
        # add a massive wave of new low skilled players
        # run 10 ranked seasons followed by new MMR reset. starting MMR is high. capture MMR curves in graphs