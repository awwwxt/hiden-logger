from requests import Session
from random import choice

from datetime import datetime
from json import dumps
from argparse import ArgumentParser

from typing import Union, List, Dict, Any

parser = ArgumentParser(description='simple ip logger via telegra.ph', add_help=True)
parser.add_argument('-p', '--proxy', nargs='+', help='http(s) proxy')
parser.add_argument('-s', '--short_name', type=str, help="""
                    Account name, helps users with several 
                    accounts remember which they are currently using. 
                    Displayed to the user above the "Edit/Publish" 
                    button on Telegra.ph, other users don't see this name.""", required=True)
parser.add_argument('-t', '--title', type=str, help='title for article', required=True)
parser.add_argument('-txt', '--text', type=str, help='text for article', required=True)
parser.add_argument('-l', '--logger', type=str, help='link on logger', required=True)
parser.add_argument('-v', '--verbose', action='store_true', help='verbose logs')

args = parser.parse_args()

class TelegraphClient:
    def __init__(self, proxy: Union[List[str], None] = None):
        self._proxy = proxy
        self.session = Session()
        self.api_endoint = 'https://api.telegra.ph/{method}'

    @property
    def proxy(self):
        return None if self._proxy is None else choice(self._proxy)
    
    def createAccount(self, name) -> str:
        account = self.make_request('createAccount', {'short_name': name})

        [self.make_log(text, True) for text in (
            f'Created profile for {account["short_name"]}',
            f'Received {account["access_token"]} access token',
            f'You can manually edit page via {account["auth_url"]}'
        )]
        return account["access_token"]

    def createArticle(
            self, 
            title: str,
            text: str, 
            logger: str, 
            token: str
        ) -> None:
        response = self.make_request('createPage', 
                {
                    'title': title,
                    'content': self.make_logger(text, logger),
                    'access_token': token
            }
        )
        self.make_log(f"Created successfuly, link - {response['url']}", True, True)

    def make_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            url = self.api_endoint.format(method=method),
            data = data,
            proxies = self.proxy
        )
        text = f'Received {response.status_code} code when receiving method {method}'
        self.make_log(text, True if response.status_code == 200 else False)   
        
        response = response.json()
        if "error" in response:
            raise Exception(response['error'])
        elif 'ok' in response:
            return response['result']

    @staticmethod
    def make_log(text: str, success: bool, force_print: bool = False) -> None:
        if args.verbose or force_print:
            print('\033[32m' if success else '\033[31m', \
                     datetime.now().strftime('%H:%M:%S.%f '), text, \
                    '\033[0m', sep="")

    @staticmethod
    def make_logger(text: str, logger: str) -> str:
       return dumps([
        {"tag": "p", "children": [text]},
        {"tag": "img", "attrs": {"src": logger, "width": "1", "height": "1"}}
    ])

    def main(self) -> int:
        self.make_log('Started now', True)
        token = self.createAccount(args.short_name)
        self.createArticle(
            title = args.title,
            text = args.text,
            logger = args.logger,
            token = token
        )
        self.make_log('Exiting now', True)
        return 0

client = TelegraphClient(proxy = args.proxy)
client.main()
