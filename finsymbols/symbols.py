import datetime
from bs4 import BeautifulSoup

from finsymbols.symbol_helper import *


def merge_historical(existing, row):
    # handle the add
    if row['add_sym'] not in existing.keys():
        existing[row['add_sym']] = {
            "symbol": row['add_sym'],
            "company": row['add_co'],
            "sector": None,
            "industry": None,
            "headquaters": None,
            "start": None,
            "end": None,
            "current": False
        }
    current = existing[row['add_sym']]
    if current['start']:
        print 'Unexpected: {0} had start date'.format(current['symbol'])
    current['start'] = row['date']

    # handle the remove
    if row['rm_sym'] not in existing.keys():
        existing[row['rm_sym']] = {
            "symbol": row['rm_sym'],
            "company": row['rm_co'],
            "sector": None,
            "industry": None,
            "headquaters": None,
            "end": None,
            "start": None,
            "current": False
        }
    current = existing[row['rm_sym']]
    if current['end']:
        print 'Unexpected: {0} had end date'.format(current['symbol'])
    current['end'] = row['date']
    return existing


def get_sp500_symbols(historical=False):
    page_html = wiki_html('List_of_S%26P_500_companies', 'SP500.html')
    wiki_soup = BeautifulSoup(page_html)
    symbol_tables = wiki_soup.find_all(attrs={'class': 'wikitable sortable'})
    current_table = symbol_tables[0]
    changes_table = symbol_tables[1]

    symbol_data_list = {}
    for symbol in current_table.find_all("tr")[1:]:
        symbol_data_content = dict()
        symbol_raw_data = symbol.find_all("td")
        td_count = 0
        for symbol_data in symbol_raw_data:
            if td_count == 0:
                sym = symbol_data.text.encode('utf-8')
                symbol_data_content['symbol'] = sym
            elif td_count == 1:
                symbol_data_content['company'] = symbol_data.text.encode('utf-8')
            elif td_count == 3:
                symbol_data_content['sector'] = symbol_data.text.encode('utf-8')
            elif td_count == 4:
                symbol_data_content['industry'] = symbol_data.text.encode('utf-8')
            elif td_count == 5:
                symbol_data_content['headquaters'] = symbol_data.text.encode('utf-8')

            td_count += 1

        if historical:
            symbol_data_content['start'] = None
            symbol_data_content['end'] = None
            symbol_data_content['current'] = True
        symbol_data_list[sym] = symbol_data_content

    # Find add/remove data
    if historical:
        change_date = None
        change_reason = None
        fields = ["date", "add_sym", "add_co", "rm_sym", "rm_co", "reason"]
        for row in changes_table.find_all('tr')[2:]:
            data = [e.text.encode('utf-8') for e in row.find_all('td')]
            # Multiple rows for a given date exist
            if len(data) == 4:
                data.insert(0, change_date)
                data.insert(-1, change_reason)
            else:
                try:
                    data[0] = datetime.datetime.strptime(data[0], "%B %d, %Y")
                except ValueError:
                    data[0] = datetime.datetime.strptime(data[0], "%B %Y")

            data = dict(zip(fields, data))
            symbol_data_list = merge_historical(symbol_data_list, data)

    return symbol_data_list.values()


def get_nyse_symbols():
    return _get_exchange_data("NYSE")


def get_amex_symbols():
    return _get_exchange_data("AMEX")


def get_nasdaq_symbols():
    return _get_exchange_data("NASDAQ")


def _get_exchange_data(exchange):
    url = get_exchange_url(exchange)
    file_path = os.path.join(os.path.dirname(finsymbols.__file__), exchange)
    if is_cached(file_path):
        with open(file_path, "r") as cached_file:
            symbol_data = cached_file.read()
    else:
        symbol_data = fetch_file(url)
        save_file(file_path,symbol_data)

    return get_symbol_list(symbol_data,exchange)
