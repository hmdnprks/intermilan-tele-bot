import requests
from bottle import Bottle, response, request as bottle_request
import os
import dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
  dotenv.load_dotenv(dotenv_file)

bot_token = os.environ['bot_token']
api_football = os.environ['api_football']
global TOKEN
global API_KEY
TOKEN = bot_token
API_KEY = api_football

class BotHandlerMixin:
    BOT_URL = None

    def get_chat_id(self, data):
        chat_id = data['message']['chat']['id']

        return chat_id

    def get_message(self, data):
        message_text = data['message']['text']

        return message_text

    def send_message(self, prepared_data):
        message_url = self.BOT_URL + 'sendMessage'
        requests.post(message_url, json=prepared_data)


class TelegramBot(BotHandlerMixin, Bottle):
    BOT_URL = 'https://api.telegram.org/bot{token}/'.format(token=TOKEN)
    headers_api = {
      'x-rapidapi-host': "v3.football.api-sports.io",
      'x-rapidapi-key': API_KEY
    }
    api_url = 'https://v3.football.api-sports.io/'
    team = 505
    league_id = {
      'serie-a' : 135,
      'coppa' : 137,
    }

    def __init__(self, *args, **kwargs):
        super(TelegramBot, self).__init__()
        self.route('/', callback=self.post_handler, method="POST")

    def default_response(self):
        return 'Maaf, bot tidak mengenali pesan kamu'

    def welcome_message(self, text):
        message = """
Selamat datang di Bot Inter Milan. Silakan gunakan _command_ berikut :

*PERTANDINGAN*
/nextmatch - Pertandingan berikutnya di semua kompetisi

*LIGA*
/ownstanding - Klasemen Inter saat ini dan detailnya
/standings - Klasemen Serie-A
        """

        return message

    def prepare_data_for_answer(self, data):
        message = self.get_message(data)
        if message == '/start':
          answer = self.welcome_message(message)
        elif message == '/nextmatch':
          answer = self.next_match()
        elif message == '/ownstanding':
          answer = self.standings(team=self.team)
        elif message == '/standings':
          answer = self.standings()
        else :
          answer = self.default_response()
        chat_id = self.get_chat_id(data)
        json_data = {
            "chat_id": chat_id,
            "text": answer,
            "parse_mode": 'markdown'
        }

        return json_data

    def post_handler(self):
        data = bottle_request.json
        answer_data = self.prepare_data_for_answer(data)
        self.send_message(answer_data)

        return response

    def send_request(self, endpoint, params, **kwargs):
        r = requests.get(url=self.api_url+endpoint, params=params, headers=self.headers_api)
        return r

    def next_match(self):
        params = {
          "team": self.team,
          "next": "1"
        }
        r = self.send_request('/fixtures', params=params)
        result = r.json()
        home = result['response'][0]['teams']['home']['name']
        away = result['response'][0]['teams']['away']['name']
        return home + ' vs ' + away

    def standings(self, team=None):
        params = {
          "team": team,
          "league": self.league_id['serie-a'],
          "season": "2020"
        }
        r = self.send_request('/standings', params=params)
        result = r.json()
        standing = result['response'][0]['league']['standings'][0]
        if team is not None:
          result = """
Peringkat - {rank}
Poin - {points}
Riwayat - {form}
Statistik :
  Main - {all[played]}
  Menang - {all[win]}
  Seri - {all[draw]}
  Kalah -{all[lose]}
  Goal - {all[goals][for]}:{all[goals][against]}
        """.format(**standing[0])
        else:
          result = ""
          for index, team in enumerate(standing):
            if team['team']['id'] == self.team:
              result += '*{i}. {team} - {points} \n*'.format(i=index+1, points=team['points'], team=team['team']['name'])
            else:
              result += '{i}. {team} - {points} \n'.format(i=index+1, points=team['points'], team=team['team']['name'])
        return result



if __name__ == '__main__':
    app = TelegramBot()
    app.run(debug=os.environ['debug'])