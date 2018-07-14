from NamesUpdater import NamesUpdater
from settings import *

namesUpdater = NamesUpdater(CREDS_FILE_NAME, CLIENT_SECRET_FILE_NAME, SPREADSHEET_ID, SPREADSHEETS_SCOPES, PAGE_NAME,
                            START_ROW, ACCOUNT_ID_COLUMN, NAME_COLUMN, OLD_NAMES_COLUMN, RIOT_API_TOKEN,
                            RIOT_API_REQUEST_DELAY)
namesUpdater.update_account_ids()
namesUpdater.update_summoner_names()
