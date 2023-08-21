from parcer import Requester
from parcer import Cursor

def parce_url(connection:Cursor, prcr:Requester, url:str, headers=None, parameters=None):
    text, headers = prcr.make_request(url=url,
                                      headers=headers,
                                      parameters=parameters)
    metaproperties, titles, text, keywords = prcr.parse(text, conn.index)
    connection.insert_page(url=url, metaproperties=metaproperties, titles=titles, text=text, headers=headers,
                     keywords=keywords)

def search_by_keyword(keyword:str, connection:Cursor):
    exact_matches = connection.index.search_by_keyword(keyword)
    # if no exact matches, search by similar keywords
    if exact_matches == [None]:
        similar, closestwords = connection.index.search_similar(keyword)
        return exact_matches, similar, closestwords
    else:
        return exact_matches, [None], [None]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #print_hi('PyCharm')
    conn = Cursor()
    prcr = Requester()

    '''
        uncomment below for console interaction
    '''

    # option = input('Input options:\n\t\t input 1 if you want to parse an url'
    #               '\n\t\t 2 if you want to perform a search by keywords\n'
    #               'input 3 to exit or press CTRL+C\n')
    # while (option != '3'):
    #     if option == '1':
    #         url = input('Input url: ')
    #         parce_url(connection=conn, prcr=prcr, url=url)
    #     elif option == '2':
    #         # keyword = 'file'
    #         keyword = input(f'Input keyword, first 25 available keywords {list(conn.index.keywords_to_sites.keys())}:')
    #         exact_matches, similar, closestwords = search_by_keyword(keyword, conn)
    #         print(f'\nExact match to {keyword}:')
    #         for ex in exact_matches:
    #             print(f'{ex}')
    #         if exact_matches == [None]:
    #             print(f'Similar:')
    #             for i, sim in enumerate(similar):
    #                 for site in sim:
    #                     print(f'closest word {closestwords[i]}')
    #                     print(f'{site}\n')
    #     option = input('Input options:\n\t\t input 1 if you want to parse an url'
    #                    '\n\t\t 2 if you want to perform a search by keywords\n'
    #                    'input 3 to exit or press CTRL+C\n')



    url = r'https://docs.python.org/3/library/typing.html#the-any-type'
    text, headers = prcr.make_request(url=url,
                      headers=None,
                      parameters=None)
    metaproperties, titles, text, keywords = prcr.parse(text, conn.index)
    conn.insert_page(url= url, metaproperties=metaproperties, titles=titles,text=text,headers=headers,keywords=keywords)
    url1 = r'https://en.wikipedia.org/wiki/Esplanade_MRT_station'
    text1, headers1 = prcr.make_request(url=r'https://en.wikipedia.org/wiki/Esplanade_MRT_station',
                      headers=None,
                      parameters=None)
    metaproperties1, titles1, text1, keywords1 = prcr.parse(text1, conn.index)
    conn.insert_page(url=url1, metaproperties=metaproperties1, titles=titles1, text=text1, headers=headers1,
                     keywords=keywords1)
    url2 = r'https://www.geeksforgeeks.org/python-measure-similarity-between-two-sentences-using-cosine-similarity/'
    text2, headers2 = prcr.make_request(url=url2,
                                        headers=None,
                                        parameters=None)
    metaproperties2, titles2, text2, keywords2 = prcr.parse(text2, conn.index)
    conn.insert_page(url=url1, metaproperties=metaproperties2, titles=titles2, text=text2, headers=headers2,
                     keywords=keywords2)
