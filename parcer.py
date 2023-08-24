import requests
from typing import Dict, List, Tuple, Any
import re
import sqlite3
import numpy as np
from fuzzywuzzy import fuzz
from parcer_beeautiful_soup.parcer_bs import Parcer_bs


class Site:
    def __init__(self, url: str,
                 metaproperties: List[Dict[str, str]],
                 titles: List[str],
                 text: List[str] = None,
                 headers: Dict[str, Any] = None, keywords: Dict[str, float] = None):
        self.url = url
        self.metaproperties = metaproperties
        self.titles = [title[0] for title in titles] if type(titles[0]) == type([]) else titles
        self.text = text
        self.keywords = keywords
        self.headers = headers

    def __eq__(self, url: str):
        return self.url == url

    def __str__(self):
        return f'Site`s Titles :{", ".join([title for title in self.titles])}, URL:{self.url}'


class Index:
    def __init__(self):
        self.keywords_to_sites = dict()  # dict[str, list(tuple(double, Site))]
        # self.keywords = list()
        self.sites_num = 0
        self.sites = []

    def add_to_index(self, keyword: Tuple[str, float], site: Site):

        if not keyword[0] in self.keywords_to_sites.keys():
            self.keywords_to_sites[keyword[0]] = []

        # for maintaining sorted state by priority of keyword
        index = 0
        for i, elem in enumerate(self.keywords_to_sites[keyword[0]]):
            if keyword[1] >= elem[0]:
                index = i
                break
        self.keywords_to_sites[keyword[0]].insert(index, (keyword[1], site))

    def search_similar(self, keyword: str):
        keywords = list(self.keywords_to_sites.keys())
        similarity = np.zeros(shape=len(keywords))

        # we compute similarity to each word using Levenshtein distance
        for i, candidate in enumerate(keywords):
            similarity[i] = fuzz.ratio(keyword, candidate)
        # choose 5 most similar
        indx = np.argsort(similarity)[-1:-5:-1]
        similar = [[str(j[1]) for j in self.keywords_to_sites[keywords[i]]] for i in indx]
        return similar, [keywords[i] for i in indx]

    def search_by_keyword(self, keyword: str):
        if not keyword in self.keywords_to_sites.keys():
            return [None]
        else:
            return [str(i[1]) for i in self.keywords_to_sites[keyword]]

    def search_by_url(self, url: str):
        for site in self.sites:
            if site == url:
                return site
        return None


class Cursor:
    def __init__(self, database_file: str = r"D:\\prog\\python learning\\pytorch\\pythonProject\\urlbase.db"):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

        # extracting "keyword->site" data for existing objects in database

        command = 'select Keywords.id, keyword, group_concat(SitesToKeywords.id), ' \
                  'group_concat(SitesToKeywords.priority),' \
                  ' group_concat(SitesToKeywords.siteid), group_concat(sites.url) from Keywords join SitesToKeywords ' \
                  'on keywordid = Keywords.id join Sites on Sites.id = SitesToKeywords.siteid ' \
                  'group by Keywords.id order by keyword asc, priority desc'
        res = self.cursor.execute(command).fetchall()
        titles_command = 'select group_concat(Titles.title), Sites.url, Sites.id from Titles join Sites ' \
                         'on Titles.siteid = Sites.id group by Sites.url;'
        titles_res = self.cursor.execute(titles_command).fetchall()
        self.index = Index()

        # downloading existing in database sites to index
        self.get_start_state(res, titles_res)

    def get_start_state(self, res, titles_res):
        url_titles = {titles_res[i][1]: titles_res[i][0] for i in range(len(titles_res))}
        for (keyw_id, keyw, sites_to_keyw_ids, sites_to_keyw_priorities, siteids, siteurls) in res:
            keyw_priorities, siteurls = sites_to_keyw_priorities.split(',') if ',' in sites_to_keyw_priorities else [
                sites_to_keyw_priorities], \
                                        siteurls.split(',') if ',' in siteurls else [siteurls]
            for i, siteurl in enumerate(siteurls):
                site = self.index.search_by_url(siteurl)
                if site is None:
                    site = Site(siteurl, None, url_titles[siteurl].split(','), None, None,
                                {keyw: float(keyw_priorities[i])})
                    self.index.sites.append(site)
                else:
                    site.keywords[keyw] = float(keyw_priorities[i])
                self.index.add_to_index((keyw, float(keyw_priorities[i])), site)

    # functions for inserting into database

    def insert_site(self, url, text):
        tt = ""
        for w in text:
            tt += '\n' + w
        tt = tt.replace("'", "<quotemark>")
        tt = tt.replace('"', "<quotemark>")
        insert_command = f'insert or ignore into Sites (url, text_data_raw) values ("{url}","{tt}");'
        id_command = f"select id from Sites where url = '{url}';"
        self.cursor.execute(insert_command)
        self.connection.commit()
        id = self.cursor.execute(id_command).fetchone()[0]
        return id

    # functions for inserting into database

    def insert_keywords(self, keywords: Dict[str, float], url, siteid, site):
        for keyword, tf_idf in keywords.items():
            if not keyword in self.index.keywords_to_sites.keys():
                command = f"insert or ignore into Keywords (keyword) values ('{keyword}')"
                self.cursor.execute(command)
                self.connection.commit()
            id_command = f"select id from Keywords where keyword='{keyword}'"
            id = self.cursor.execute(id_command).fetchone()[0]
            command = f"insert or ignore into SitesToKeywords(siteid, keywordid, priority) " \
                      f"values ('{siteid}',{id}, '{tf_idf}')"
            self.cursor.execute(command)
            self.connection.commit()
            self.index.add_to_index((keyword, tf_idf), site)

    # functions for inserting into database

    def insert_metadata(self, metaproperties: List[Dict[str, str]], headers: Dict[str, Any], siteid):
        for props_values in metaproperties:
            for prop, value in props_values.items():
                command = f"insert or ignore into Metadatas (key, value, siteid) values ('{prop}', '{value}', {siteid})"
                try:
                    self.cursor.execute(command)
                except:
                    print('bad metadata, skipping...')
        for prop, value in headers.items():
            command = f"insert or ignore into Metadatas (key, value, siteid) values ('{prop}', '{value}', {siteid})"
            try:
                self.cursor.execute(command)
            except:
                print('bad metadata, skipping...')
        self.connection.commit()

    # functions for inserting into database

    def insert_titles(self, titles: List['str'], siteid):
        for title in titles:
            title = title[0].replace("'", "<quotemark>")
            title = title.replace('"', "<quotemark>")
            command = f"insert or ignore into Titles (title, siteid) values ('{title}', {siteid})"
            self.cursor.execute(command)
        self.connection.commit()

    def insert_page(self, url: str,
                    metaproperties: List[Dict[str, str]],
                    titles: List[str],
                    text: List[str],
                    headers: Dict[str, Any], keywords: Dict[str, float]):
        # creating a new web-page object for adding into index and printing
        newsite = Site(url=url,
                       metaproperties=metaproperties,
                       titles=titles,
                       text=text,
                       headers=headers,
                       keywords=keywords)
        siteid = self.insert_site(url, text)
        self.insert_titles(titles, siteid)
        self.insert_keywords(keywords, url, siteid, newsite)
        self.insert_metadata(metaproperties, headers, siteid)
        for kw_pr in keywords.items():
            self.index.add_to_index(keyword=kw_pr, site=newsite)
        self.index.sites_num += 1
        print(f"Parced {str(newsite)}")
        return True


class Parcer:
    def __init__(self):
        # if a tag has been opened, but has not been closed yet, then self.opened will be True
        self.opened = False

    def parse_request(self, req_text: List[str]):
        # divide text of a request into body and head list of chunks
        s = -1
        e = -1
        for i, chunk in enumerate(req_text):
            if 'head>' in chunk and s == -1:
                s = i
            if '</head>' in chunk and e == -1:
                e = i

        if s != -1 and e != -1:
            head = req_text[s: e if e != s else e + 1]
        else:
            head = req_text[req_text.index(r'<head>') + 1: req_text.index(r'</head>') - 1]

        s = -1
        e = -1
        for i, chunk in enumerate(req_text):
            if 'body>' in chunk and s == -1:
                s = i
            if '</body>' in chunk and e == -1:
                e = i

        if s != -1 and e != -1:
            body = req_text[s: e if e != s else e + 1]
        else:
            body = req_text[req_text.index(r'<body>') + 1: req_text.index(r'</body>') - 1]

        metaproperties, titles = self.parse_head(head)
        text = self.parse_body(body)

        return metaproperties, titles, text

    def parse_head(self, head):  # head - list('str')
        # using cur pos in a text for identifying position in a chunk of head
        cur_pos = 0
        metaproperties_titles = {'meta': [dict()], 'title': []}
        for i, chunk in enumerate(head):
            if i == 2:
                pass
            cur_pos = 0
            while cur_pos < len(chunk) - 1:
                try:
                    # if we meet an opening tag
                    if chunk[cur_pos] == '<' and chunk[cur_pos + 1] != '/':
                        # self.opened = True
                        # a = len(chunk)
                        self.opened = True

                        if '>' in chunk[cur_pos:]:
                            tag_end = cur_pos + chunk[cur_pos:].index('>')
                        else:
                            tag_end = len(chunk) - 1
                        tag = chunk[cur_pos + 1:tag_end]
                        # if the tag has the closing slash in the end, we close a tag
                        if tag[-1] == '/':
                            self.opened = False
                            tag = tag[:-1:].rstrip()
                        tag_props = tag.split(' ')
                        # we write down all meta properties of meta tags in the dict
                        if tag_props[0] == 'meta':
                            metaproperties_titles[tag_props[0]].append(dict())
                            for prop in tag_props[1:]:
                                if '=' in prop:
                                    key_val = prop.split('=')
                                    metaproperties_titles[tag_props[0]][-1][key_val[0]] = key_val[1]
                                else:
                                    metaproperties_titles[tag_props[0]][-1][key_val[0]] += (' ' + prop)
                            cur_pos = cur_pos + chunk[cur_pos:].index('>')
                            self.opened = False
                        else:
                            # if we have other tag than meta and title, we skip it
                            if '<' in chunk[tag_end:]:
                                closing_tag = chunk[tag_end:].index('<') if tag_end != len(chunk) - 1 else tag_end
                            else:
                                closing_tag = tag_end
                            # if we have title tag, we skip to the beginning of the title's text and mark tag as closed
                            if tag_props[0] == 'title':
                                metaproperties_titles['title'].append([])
                                cur_pos = tag_end + 1
                                self.opened = False
                            else:
                                cur_pos = tag_end + 1
                    # if current tag is closed and current position is on alphabetical symbol,
                    # than it's title and we write it down
                    elif str.isalpha(chunk[cur_pos]) and not self.opened:
                        closing_tag = cur_pos + chunk[cur_pos:].index('<')
                        metaproperties_titles['title'][-1].append(chunk[cur_pos:closing_tag])
                        cur_pos = closing_tag + 1
                    # if some random tag isn't closed or current position
                    # is not an alphabetical symbol, than we skip it
                    else:
                        if '>' in chunk[cur_pos:]:
                            cur_pos = cur_pos + chunk[cur_pos:].index('>') + 1
                            self.opened = False
                        else:
                            cur_pos = len(chunk) - 1

                except ValueError:
                    print(f'tried to reach closing or opening of the tag at chunk {i} of length {len(chunk)},'
                          f' current position in chunk {cur_pos} \n chunk body {chunk}')

                except IndexError():
                    print(f'Wrong index at chunk {i} of length {len(chunk)}, current position in chunk {cur_pos} \n '
                          f'chunk body {chunk}')

        return metaproperties_titles['meta'], metaproperties_titles['title']

    def parse_body(self, body):
        # works in similar manner to def parse_head(), writes down text between tags
        cur_pos = 0
        text = []
        for i, chunk in enumerate(body):
            cur_pos = 0
            while cur_pos < len(chunk) - 1:
                a = len(chunk)
                try:
                    if chunk[cur_pos] == '<':
                        self.opened = not (chunk[cur_pos + 1] == '/')
                        if '>' in chunk[cur_pos:]:
                            tag_end = cur_pos + chunk[cur_pos:].index('>') + 1
                            self.opened = False
                        else:
                            tag_end = len(chunk) - 1
                        cur_pos = tag_end
                    elif chunk[cur_pos] == '>':
                        self.opened = False
                        if '<' in chunk[cur_pos:]:
                            cur_pos = cur_pos + chunk[cur_pos:].index('<')
                        else:
                            cur_pos = len(chunk) - 1
                    elif not self.opened:
                        if '<' in chunk[cur_pos:]:
                            closing_tag = cur_pos + chunk[cur_pos:].index('<')
                            self.opened = False
                        else:
                            closing_tag = len(chunk)
                        text.append(chunk[cur_pos:closing_tag])
                        cur_pos = closing_tag
                    else:
                        if '>' in chunk[cur_pos:]:
                            cur_pos = cur_pos + chunk[cur_pos:].index('>') + 1
                            self.opened = False
                        else:
                            cur_pos = len(chunk) - 1
                except ValueError:
                    print(f'tried to reach closing or opening of the tag at chunk {i} of length {len(chunk)},'
                          f' current position in chunk {cur_pos} \n chunk body {chunk}')
                except IndexError():
                    print(f'Wrong index at chunk {i} of length {len(chunk)}, current position in chunk {cur_pos} \n '
                          f'chunk body {chunk}')
        return text

    def parse_keywords(self, titles: List[str], text: List[str],
                       index: Index, alpha: float = 0.1):
        # parse keywords using term frequency, inverse document frequency

        expr = "[A-Za-z][A-Za-z0-9]+"
        wordbag = []
        for charbag in text:
            occurences = re.findall(expr, charbag)
            wordbag += occurences
        for title in titles:
            occurences = re.findall(expr, title[0])
            wordbag += occurences
        words, freqs = np.unique(np.asarray(wordbag), return_counts=True)
        tf = freqs / freqs.sum()
        doc_freq = []
        for i in words:
            if i in index.keywords_to_sites.keys():
                doc_freq.append(len(index.keywords_to_sites[i]))
            else:
                doc_freq.append(0)
        a = np.asarray(doc_freq) + 1
        b = index.sites_num + 1 + alpha * (index.sites_num + 1)
        idf = np.log2(b / a)
        tf_idf = tf * idf
        inds = tf_idf.argsort()
        # returning 5 most important words
        return dict(list(zip(list(words[inds][:5]), list(tf_idf[inds][:5]))))


class Requester:
    def __init__(self):
        self.parcer = Parcer()
        self.parcer2 = Parcer_bs(None)

    def make_request2(self, url: str, headers: Dict[str, Any] = None,
                      parameters: Dict[str, Any] = None):
        try:
            res = requests.get(url=url, headers=headers, params=parameters)
            if res.status_code != requests.codes.ok:
                res.raise_for_status()
            text = res.text  # .split('<!DOCTYPE html>')[1]
            # text = text[text.index('<'):]
            headers = res.headers
            return text, headers
        except:
            print("Bad connection", res.status_code)

    def parse2(self, text, index):
        titles, h1headers, text = self.parcer2.get_soup(text)
        keywords = self.parcer2.parse_keywords(titles, h1headers, text, index)
        return titles, h1headers, text, keywords

    # making a request
    def make_request(self, url: str, headers: Dict[str, Any] = None,
                     parameters: Dict[str, Any] = None):
        try:
            res = requests.get(url=url, headers=headers, params=parameters)
            if res.status_code != requests.codes.ok:
                res.raise_for_status()
            text = [i.strip() for i in res.text.split('\n')]
            headers = res.headers
            return text, headers
        except:
            print("Bad connection", res.status_code)

    # calling parcing procedures
    def parse(self, text, index):
        metaproperties, titles, text = self.parcer.parse_request(text)
        keywords = self.parcer.parse_keywords(titles, text, index)
        return metaproperties, titles, text, keywords
