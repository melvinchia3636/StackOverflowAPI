import requests, re
from tkinter import *
from tkinter.font import Font
from bs4 import BeautifulSoup
import json

class StackOverFlow(requests.Session):
    def __init__(self):
        super().__init__()
        self.DOMAIN = 'https://stackoverflow.com'
        self.BASE_URL = 'https://stackoverflow.com/questions?sort={}&filters={}&page={}'
        self.TAGGED_URL = 'https://stackoverflow.com/questions/tagged/{}?sort={}&filters={}&page={}'

    def _getAuthor(self, i):
        raw = i.findAll('div', class_='user-details')
        if len(raw) == 2:
            history, original_author = raw[1].findAll('a')
            return {
                'name': raw[0].find('span', class_="community-wiki").text.strip(),
                'original_author': {
                    'id': original_author['href'].split('/')[-2],
                    'link': self.DOMAIN+original_author['href'],
                    'name': original_author.text
                },
                'history': {
                    'details': history.text.strip(),
                    'link': self.DOMAIN+history['href']
                }
            }
        else:
            author = raw[0].find('a')
            try:
                rep1 = raw[0].find('span', class_='reputation-score')['title'].split()[-1].replace(',', '')
                rep2 = raw[0].find('span', class_='reputation-score').text.split()[-1].replace(',', '')
            except:
                rep1 = rep2 = None
            badges = [i['title'].split() for i in raw[0].find('div', class_='-flair').findAll('span') if 'title' in i.attrs and 'badge' in i['title']]
            return {
                'id': author['href'].split('/')[-1] if author else None,
                'link': self.DOMAIN+author['href'] if author else None,
                'name': author.text if author else raw[0].text.strip(),
                'avatar': i.find('img')['src'] if author else None,
                'reputation_score': int(rep1 if rep1.isdigit() else rep2) if author else None,
                'badges': dict(map(lambda i: (i[1], int(i[0])), badges))
            }

    def browse_questions(self, page=1, sort_by='Newest', filter_by=[], tags=[]):
        if not tags: target_url = self.BASE_URL.format(sort_by, ','.join(filter_by), page)
        else: target_url = self.TAGGED_URL.format(' '.join(tags), sort_by, ','.join(filter_by), page)
        soup = BeautifulSoup(self.get(target_url).content, 'lxml')
        return {
            'request': {
                'url': target_url,
                'method': 'GET',
                'params': {
                    'page': page,
                    'sort_by': sort_by,
                    'filter_by': filter_by,
                    'tags': tags
                }   
            },
            'response': {
                'result_count': int(soup.find('div', {'data-controller':"se-uql"}).find('div', class_='grid--cell').text.strip().split()[0].replace(',', '')),
                'contents': [
                    {
                        'id': int(i['id'].split('-')[-1]),
                        'link': self.DOMAIN+i.find('h3').find('a')['href'],
                        'title': i.find('h3').text,
                        'excerpt': i.find('div', class_='excerpt').text.strip(),
                        'status': i.find('div', class_='status')['class'][-1].replace('-', ' '),
                        'tags': [j.text for j in i.find('div', class_='tags').findAll('a', class_='post-tag')],
                        'time_posted': i.find('span', class_='relativetime')['title'] if i.find('span', class_='relativetime') else None,
                        'vote_count': int(i.find('span', class_='vote-count-post').text),
                        'answer_count': int(i.find('div', class_='status').find('strong').text),
                        'view_count': int(i.find('div', class_='views')['title'].replace(',', '').split()[0]),
                        'author': self._getAuthor(i)
                    } for i in soup.findAll('div', class_='question-summary')
                ]
            }
    }

if __name__ == '__main__':
    api = StackOverFlow()
    json.dump(api.browse_questions(sort_by='MostVotes', tags=['html', 'css', 'javascript']), open('stackoverflow.json', 'w'), indent=4)