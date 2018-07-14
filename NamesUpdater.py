from __future__ import print_function

import time

import requests
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


class NamesUpdater:
    def __init__(self,
                 creds_file_name: str,
                 client_secret_file_name: str,
                 spreadsheet_id: str,
                 spreadsheets_scopes: str,
                 page_name: str,
                 start_row: int,
                 account_id_column: str,
                 name_column: str,
                 old_names_column: str,
                 riot_api_token: str,
                 riot_api_delay: float):
        creds_file = file.Storage(creds_file_name)
        creds = creds_file.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(client_secret_file_name, spreadsheets_scopes)
            creds = tools.run_flow(flow, creds_file)
        self.service = build('sheets', 'v4', http=creds.authorize(Http()))
        self.spreadsheet_id = spreadsheet_id
        self.page_name = page_name
        self.start_row = start_row
        self.account_id_column = account_id_column
        self.name_column = name_column
        self.old_names_column = old_names_column

        self.headers = {'Origin': 'null',
                        'Accept-Charset': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Riot-Token': riot_api_token,
                        'Accept-Language': 'ru,en-US;q=0.7,en;q=0.3'}
        self.riot_api_delay = riot_api_delay
        self.getUserByNameUrlTemplate = 'https://ru.api.riotgames.com/lol/summoner/v3/summoners/by-name/%s'
        self.getUserByAccountIdUrlTemplate = 'https://ru.api.riotgames.com/lol/summoner/v3/summoners/by-account/%s'
        pass

    def __get_from_lol_api(self, url: str, var: str, field_name: str) -> str:
        time.sleep(self.riot_api_delay)
        return requests.get(url % var, headers=self.headers).json().get(field_name)

    def __read_from_sheet(self,
                          spreadsheet_id: str,
                          sheet_name: str,
                          start_column: str,
                          end_column: str,
                          start_row: int) -> list:
        read_range = sheet_name + '!' + start_column + str(start_row) + ':' + end_column
        return self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                        range=read_range
                                                        ).execute().get('values', [])

    def __write_to_cell(self,
                        spreadsheet_id: str,
                        sheet_name: str,
                        column: str,
                        row: int,
                        value: str) -> object:
        return self.service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,
                                                           range=sheet_name + '!' + column + str(row),
                                                           valueInputOption='USER_ENTERED',
                                                           body={'values': [[value]]}
                                                           ).execute()

    def update_account_ids(self):
        rows = self.__read_from_sheet(
            self.spreadsheet_id, self.page_name, self.account_id_column, self.old_names_column, self.start_row)
        if not rows:
            print('No data found.')
        else:
            current_row = self.start_row
            for columns in rows:
                account_id = columns[0]
                in_doc_name = columns[1]
                if account_id == '' and in_doc_name != '':
                    account_id = self.__get_from_lol_api(self.getUserByNameUrlTemplate, in_doc_name, 'accountId')
                    account_id_str = str(account_id) if account_id else ''
                    self.__write_to_cell(
                        self.spreadsheet_id, self.page_name, self.account_id_column, current_row, account_id_str)
                current_row += 1

    def update_summoner_names(self):
        rows = self.__read_from_sheet(
            self.spreadsheet_id, self.page_name, self.account_id_column, self.old_names_column, self.start_row)
        if not rows:
            print('No data found.')
        else:
            current_row = self.start_row
            for columns in rows:
                account_id = columns[0]
                in_doc_name = columns[1]
                if account_id != '':
                    summoner_name = self.__get_from_lol_api(self.getUserByAccountIdUrlTemplate, account_id, 'name')
                    if summoner_name != in_doc_name:
                        old_names_str = columns[4]
                        if old_names_str != '':
                            old_names_set = set(old_names_str.split("; "))
                            if in_doc_name == '' or in_doc_name in old_names_set:
                                self.__write_to_cell(
                                    self.spreadsheet_id, self.page_name, self.name_column, current_row, summoner_name)
                            else:
                                old_names_set.add(in_doc_name)
                                old_names_str = "; ".join(old_names_set)
                                self.__write_to_cell(self.spreadsheet_id, self.page_name, self.old_names_column,
                                                     current_row, old_names_str)
                                self.__write_to_cell(self.spreadsheet_id, self.page_name, self.name_column,
                                                     current_row, summoner_name)
                        else:
                            if in_doc_name != '':
                                self.__write_to_cell(self.spreadsheet_id, self.page_name, self.old_names_column,
                                                     current_row, in_doc_name)
                            self.__write_to_cell(
                                self.spreadsheet_id, self.page_name, self.name_column, current_row, summoner_name)
                current_row += 1