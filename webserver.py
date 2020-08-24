from bottle import route, run, static_file, request, response, redirect
import re, random, bs4

class Player():
    def __init__(self, name, numPoints, currentCard=None, currentGame=None):
        self.name = name
        self.numPoints = numPoints
        self.currentCard = currentCard
        self._currentGame = None
        self.currentGame = currentGame
        self.hand = [card for card in random.sample(red_cards, 7)]
        self.new_card = None

    @property
    def currentGame(self):
        return self._currentGame

    @currentGame.setter
    def currentGame(self, val):
        if self._currentGame != val:
            val.players.append(self)
            self._currentGame = val


class Round():
    def __init__(self, number, green_card, players=[]):
        self.number = number
        self.green_card = green_card
        self.players = players

    def allPlayersPlayed(self):
        for player in self.players:
            if player.currentCard is None:
                return False
        return True

class Game():
    def __init__(self, id, players=[]):
        self.id = id
        self.players = players
        self.round = Round(0, random.choice(green_cards), self.players)
    
    def next_round(self):
        for player in self.players:
            player.new_card = random.choice(red_cards)
            player.hand[player.hand.index(player.currentCard)] = player.new_card
            player.currentCard = None
        self.round = Round(self.round.number + 1, random.choice(green_cards), self.players)

class Card():
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class RedCard(Card):
    def __init__(self, name, description):
        self.name = name
        self.description = description

class GreenCard(Card):
    def __init__(self, name, synonyms):
        self.name = name
        self.synonyms = synonyms

red_cards = []

with open('red-cards.txt') as f:
    for line in f.readlines():
        mo = line.split(' - ', 1)
        red_cards.append(RedCard(mo[0], mo[1]))

green_cards = []
greencardregex = re.compile(r'(.*) - \((.*)\)')

with open('green-cards.txt') as f:
    for line in f.readlines():
        mo = greencardregex.search(line)
        synonyms = mo.group(2).split(', ')
        green_cards.append(GreenCard(mo.group(1), synonyms))

players = []
game = Game(0)
@route('/hello')
def hello_again():
    if request.get_cookie("name"):
        return f"Welcome back, {request.get_cookie('name')}! Nice to see you again <button onclick=\"document.cookie='visited=;'\">Forget!</button>"
    else:
        return 

@route('/card_picked/<card>')
def card_picked(card):
    name = request.get_cookie("name")
    if not name:
        return redirect("/set_name")
    for possplayer in players:
        if possplayer.name == name:
            player = possplayer
            break
    else:
        player = Player(name, 0, None, game)
        
    for othercard in red_cards:
        if othercard.name == card:
            print(player.name, 'has picked a card.')
            player.currentCard = othercard

    oldRoundNum = game.round.number

    if game.round.allPlayersPlayed():
        print('People have chosen the following cards:', ', '.join(random.sample([player.currentCard.name for player in game.round.players], len([player.currentCard.name for player in game.round.players]))))
        game.next_round()
    response.body =  oldRoundNum
    return {'roundnum': oldRoundNum}
    

@route('/set_name')
def set_name():
    return static_file('set_name.html', './')

@route('/new_card/<oldRoundNum>')
def new_card(oldRoundNum):
    name = request.get_cookie("name")
    if not name:
        return redirect("/set_name")
    for possplayer in players:
        if possplayer.name == name:
            player = possplayer
            break
    else:
        player = Player(name, 0, None, game)

    oldRoundNum = int(oldRoundNum)
    while game.round.number < oldRoundNum:
        pass
    return {'redname': player.new_card.name, 'reddesc': player.new_card.description, 'greenname': game.round.green_card.name, 'greendesc': ', '.join(game.round.green_card.synonyms)}

@route('/')
def serve_game():
    name = request.get_cookie("name")
    if not name:
        return redirect("/set_name")
    for possplayer in players:
        if possplayer.name == name:
            player = possplayer
            break
    else:
        player = Player(name, 0, None, game)
        players.append(player)
    game_file = open('game.html')
    game_html = game_file.read()
    game_file.close()
    gameSoup = bs4.BeautifulSoup(game_html, features="html.parser")
    i = 0
    for redCard in gameSoup.select('.red-card'):
        cardToUse = player.hand[i]
        for child in redCard.findChildren():
            if child == '\n':
                continue
            if 'card-title' in child['class']:
                child.string = (f'{cardToUse.name}')
            if 'card-description' in child['class']:
                child.string = (f'{cardToUse.description}')
        i += 1
    for child in gameSoup.select('.green-card')[0].findChildren():
        if child == '\n':
            continue
        if 'card-title' in child['class']:
            child.string = (f'{game.round.green_card.name}')
        if 'card-description' in child['class']:
            child.string = ', '.join(game.round.green_card.synonyms)
    return str(gameSoup)
run(host='127.0.0.1', port=8081, debug=True)