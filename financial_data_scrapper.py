from datetime import datetime
import requests
import json
import hashlib
import urllib
import pandas as pd
from dataclasses import dataclass
import dataclasses


@dataclass
class HistoricalDataPoint():
	isin: str
	date: datetime.date
	close_rate: float

class FinanceDataScraper():
	def __init__(self):

		self._HEADER_LINKS = {"authority": "api.boerse-frankfurt.de",
	        "origin": "https://www.boerse-frankfurt.de",
	        "referer": "https://www.boerse-frankfurt.de/"
	    }
		self._BASEURL = "https://api.boerse-frankfurt.de/v1/data/"
		self._SALT = "w4ivc1ATTGta6njAZzMbkL3kJwxMfEAKDa3MNr"
		self._REQUEST_CLEAN_PARAMS = {"cleanSplit": False,
			"cleanPayout": False,
			"cleanSubscription": False
		}

	def _get_data_url(self, function: str, params:dict) -> str:

	    p_string = urllib.parse.urlencode(params)
	    return self._BASEURL + function + "?" + p_string

	def _create_ids(self, url) -> dict:
	    
	    timeutc=datetime.utcnow()
	    timelocal=datetime.now()
	    timestr = timeutc.isoformat(timespec="milliseconds") + "Z"

	    traceidbase = timestr + url + self._SALT
	    encoded = traceidbase.encode()
	    traceid = hashlib.md5(encoded).hexdigest()

	    xsecuritybase = timelocal.strftime("%Y%m%d%H%M") 
	    encoded = xsecuritybase.encode()
	    xsecurity = hashlib.md5(encoded).hexdigest()
	    
	    return {"client-date":timestr, "x-client-traceid":traceid, "x-security":xsecurity}

	def _create_header(self, url: str) -> dict:

	    headers = self._HEADER_LINKS | self._create_ids(url=url)

	    return headers

	def _data_request(self, function: str, params: dict):
	    
	    url = self._get_data_url(function, params)
	    header = self._create_header(url)

	    header["accept"] = "application/json, text/plain, */*"
	    req = requests.get(url, headers=header, timeout=(3.5, 15))
	    data = json.loads(req.text)

	    return data

	def fetch_historical_data_points(self, isin: str, from_date: datetime.date, to_date: datetime.date, exchange: str = "XETR"):
		"""request historical Xetra data via scraping"""

		date_delta = to_date - from_date

		params_request = {
	    	"isin": isin, 
	    	"mic": exchange, 
			"minDate": from_date.strftime("%Y-%m-%d"), 
			"maxDate": to_date.strftime("%Y-%m-%d"), 
			"limit": date_delta.days
		}

		request_return_dict = self._data_request("price_history", params=(params_request | self._REQUEST_CLEAN_PARAMS))

		historical_data_point_list = []
		for data_point in request_return_dict["data"]:
			date = datetime.strptime(data_point["date"], "%Y-%m-%d")
			close_rate = data_point["close"]

			historical_data_point_list.append(HistoricalDataPoint(isin,
				date,
				close_rate))

		df = pd.DataFrame([dataclasses.asdict(data_point) for data_point in historical_data_point_list])

		df.set_index(["date"], inplace=True)
		df.sort_index(inplace=True)

		df_left = pd.DataFrame(index=pd.date_range(start=from_date, end=to_date))

		df_joined = df_left.join(other=df).fillna(method="ffill")

		return df_joined["close_rate"]


	def fetch_isin_name(self, isin: str):
		"""request information about isin"""

		params_request = {"isin": isin}

		request_return_dict = self._data_request("instrument_information", params=params_request)

		return request_return_dict["instrumentName"]["originalValue"]
