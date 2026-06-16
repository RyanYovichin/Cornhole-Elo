import csv
class elo:
    def __init__(self):
        self.base = 400
        self.players = {}
        self.games = {}
        self.zscore = {}
    
    def addgame(self):
        print("Enter game details: ")
        a1 = input("P1: ")
        a2 = input("P2: ")
        b1 = input("P3: ")
        b2 = input("P4: ")
        g = input("Game number: ")
        g = int(g)
        team1  = {"w1": a1, "w2": a2}
        team2  = {"l1": b1, "l2": b2}
        with open("games.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([g, a1, a2, b1, b2])
    
    def readgames(self):
        with open("games.csv", "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                g, a1, a2, b1, b2 = row
                g = int(g)
                team1  = {"w1": a1, "w2": a2}
                team2  = {"l1": b1, "l2": b2}
                self.games[g] = {"team1": team1, "team2": team2}
    
    def gamescore(self, P1, P2, P3, P4):
        ranks = {}
        for player in [P1, P2, P3, P4]:
            if player not in self.players:
                self.players[player] = self.base
                self.zscore[player] = 11
            ranks[player] = self.players[player]
            self.zscore[player] -=1 if self.zscore[player] > 0 else 0
        rt1 = (ranks[P1] + ranks[P2]) / 2
        rt2 = (ranks[P3] + ranks[P4]) / 2
        # expected probability that team2 (losers) wins — always between 0 and 1
        exp = 1 + (rt2-rt1)/300
        expected_t2 = exp if exp > 0 else 0
        expected_t2 = expected_t2 if expected_t2 < 1 else 1
        if P1 >P3 and P1 > P4 and P2 > P3 and P2 > P4:

            ad = .8
        elif P1 < P3 and P1 < P4 and P2 < P3 and P2 < P4:
            ad = 1.25
        else:
            ad = 1
        for p in [P1, P2]:
            self.players[p] = self.players[p] +  16 * (expected_t2) * (1 + self.zscore[p] / 20) * ad
        for p in [P3, P4]:
            self.players[p] = self.players[p] -  16 * (expected_t2) * (1 + self.zscore[p] / 20) *ad
                
    
    def Elo(self):
        for game in self.games:
            t1 = [self.games[game]["team1"]["w1"], self.games[game]["team1"]["w2"]]
            t2 = [self.games[game]["team2"]["l1"], self.games[game]["team2"]["l2"]]
            
            self.gamescore(t1[0], t1[1], t2[0], t2[1])
            
            



if __name__ == "__main__":
    e = elo()
    e.readgames()
    e.Elo()
    print(e.players)