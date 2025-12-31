from pathlib import Path

import requests
import pandas as pd
import warnings
import json
import os
import ast
from guss.gussErrors import GussExceptions
import h3
from shapely.geometry import Polygon



from . import BASE_DIR, DATA_INPUT, DATA_OUTPUT, CSV_OUTPUT, GPK_OUTPUT, SHP_OUTPUT


class Guss:

    def __init__(self, **credentials):
        self.__username = credentials['USERNAME']
        self.__hash_value = credentials['HASH_VALUE']
        self.__baseUrl = os.environ['BASE_URL']
        self.__url_endpoint = None
        self.__request_type = None
        self.__request_header = None
        self.__request_param = None
        self.__response = None
        self.category_subcategory = {'Summary': {
            1: "Summary by Geography Type - Census Place",
            2: "Summary by Geography Type - Other Geographies",
            3: "Summary by Geography Type - Census Place"
        },
            "State": {
                1: "Provider List",
                2: "Location Coverage",
                3: "Hexagon Coverage",
            },
            "Provider": {
                1: "Location Coverage",
                2: "Hexagon Coverage",
                3: 'RawCoverage',
                4: 'Supporting Data'
            }
        }
        self.technology_type = {1: 'Fixed Broadband',
                                2: 'Mobile Broadband',
                                3: 'Mobile Voice'
                                }
        self.technology_code = None
        self.FiveG_speed_tier = ["35/3", "7/1"]
        self.challenge_category = (
            ("Fabric Challenge - In Progress", "Fabric Challenge - In Progress"),
            ("Fabric Challenge - Resolved", "Fabric Challenge - Resolved"),
            ("FixedChallenge - Cumulative", "FixedChallenge - Cumulative"),
            ("Fixed Challenge - In Progress", "Fixed Challenge - In Progress"),
            ("Fixed Challenge - Resolved", "Fixed Challenge - Resolved"),
            ("Mobile Challenge - In Progress", "Mobile Challenge - In Progress"),
            ("Mobile Challenge - Resolved", "Mobile Challenge - Resolved"),
        )
        self.__stop = None
        self.__BASE_DIR = BASE_DIR
        self.__CSV_OUTPUT = CSV_OUTPUT
        self.__GPK_OUTPUT = GPK_OUTPUT
        self.__SHP_OUTPUT = SHP_OUTPUT


    def __repr__(self):
        return f"{self.__username}"

    def __str__(self):
        return f"{self.__username})"

    @property
    def baseUrl(self):
        return self.__baseUrl

    @baseUrl.setter
    def baseUrl(self, value):
        self.__baseUrl = value

    @property
    def url_endpoint(self):
        return self.__url_endpoint

    @url_endpoint.setter
    def url_endpoint(self, value):
        self.__url_endpoint = value

    @url_endpoint.getter
    def url_endpoint(self):
        return self.__url_endpoint

    @property
    def request_type(self):
        return self.__request_type

    @request_type.setter
    def request_type(self, value):
        self.__request_type = value

    @property
    def request_header(self):
        return self.__request_header

    @request_header.setter
    def request_header(self, value):
        self.__request_header = value

    @property
    def request_param(self):
        return self.__request_param

    @request_param.setter
    def request_param(self, value):
        self.__request_param = value

    @request_param.getter
    def request_param(self):
        return self.__request_param

    @property
    def response(self):
        return self.__response

    @response.setter
    def response(self, value):
        self.__response = value

    @response.getter
    def response(self):
        return self.__response

    @property
    def stop(self):
        return self.__stop

    @stop.setter
    def stop(self, value):
        self.__stop = value

    @stop.getter
    def stop(self):
        return self.__stop

    @property
    def BASE_DIR(self):
        return self.__BASE_DIR

    @BASE_DIR.setter
    def BASE_DIR(self, value):
        self.__BASE_DIR= value

    @BASE_DIR.getter
    def BASE_DIR(self):
        return self.__BASE_DIR

    @property
    def DATA_DIR(self):
        return self.__DATA_DIR

    @DATA_DIR.setter
    def DATA_DIR(self, value):
        self.__DATA_DIR= value

    @DATA_DIR.getter
    def DATA_DIR(self):
        return self.__DATA_DIR

    @property
    def DATA_INPUT(self):
        return self.__DATA_INPUT

    @DATA_INPUT.setter
    def DATA_INPUT(self, value):
        self.__DATA_INPUT= value

    @DATA_INPUT.getter
    def DATA_INPUT(self):
        return self.__DATA_INPUT

    @property
    def DATA_OUTPUT(self):
        return self.__DATA_OUTPUT

    @DATA_OUTPUT.setter
    def DATA_OUTPUT(self, value):
        self.__DATA_OUTPUT= value

    @DATA_OUTPUT.getter
    def DATA_OUTPUT(self):
        return self.__DATA_OUTPUT

    @property
    def CSV_OUTPUT(self):
        return self.__CSV_OUTPUT

    @CSV_OUTPUT.setter
    def CSV_OUTPUT(self, value):
        self.__CSV_OUTPUT= value

    @CSV_OUTPUT.getter
    def CSV_OUTPUT(self):
        return self.__CSV_OUTPUT

    @property
    def SHP_OUTPUT(self):
        return self.__SHP_OUTPUT

    @SHP_OUTPUT.setter
    def SHP_OUTPUT(self, value):
        self.__SHP_OUTPUT= value

    @SHP_OUTPUT.getter
    def SHP_OUTPUT(self):
        return self.__SHP_OUTPUT

    @property
    def GPK_OUTPUT(self):
        return self.__GPK_OUTPUT

    @GPK_OUTPUT.setter
    def GPK_OUTPUT(self, value):
        self.__GPK_OUTPUT= value

    @GPK_OUTPUT.getter
    def GPK_OUTPUT(self):
        return self.__GPK_OUTPUT


    # saves output file in location
    @classmethod
    def save_file(cls, response, output_path, file_name):
        output = os.path.join(output_path, file_name)
        with open(output, 'wb') as f:
            f.write(response)
        print(f"Saved File to: {output}")

    def api_request(self):
        try:

            self.request_header = {
                'username': self.__username,
                'hash_value': self.__hash_value
            }

            url = f"{self.baseUrl}{self.url_endpoint}"

            if self.request_param is None:

                r = requests.get(url=url, headers=self.request_header)

            else:
                r = requests.request(method=str(self.request_type).upper(), url=url, params=self.request_param, headers=self.request_header)

            # error handling
            status = r.status_code
            if 400 <= status < 500:
                if status == 401:
                    print("Please Check your Credentials!!")
                    r.raise_for_status()
                else:
                    r.raise_for_status()

            return r

        # error handling
        except requests.exceptions.HTTPError as errh:
            raise GussExceptions(message=errh.__str__())
        except requests.exceptions.ConnectionError as errc:
            raise GussExceptions(errc.__str__())
        except requests.exceptions.Timeout as errt:
            raise GussExceptions(errt.__str__())
        except requests.exceptions.RequestException as err:
            raise GussExceptions(err.__str__())

    def get_request(self, return_df=None, gis_data_type=None, save_file=False, file_name=None):

        try:

            self.response = self.api_request()

            if return_df:
                df = pd.json_normalize(self.response.json()["data"])
                if "as_of_date" in df.columns:
                    df['as_of_date'] = [pd.to_datetime(x).strftime("%Y-%m-%d") for x in df['as_of_date']]
                if save_file and file_name:
                    if Path(CSV_OUTPUT).exists():
                        output = os.path.join(CSV_OUTPUT, file_name)
                    else:
                        Path(CSV_OUTPUT).mkdir(parents=True, exist_ok=True)
                        output = os.path.join(CSV_OUTPUT, file_name)
                    df.to_csv(output)



                else:
                    return warnings.warn("please enter a filename")
                return df
            else:
                if (save_file and file_name) and gis_data_type is None:
                    if Path(CSV_OUTPUT).exists():
                        output = os.path.join(CSV_OUTPUT, file_name)
                    else:
                        Path(CSV_OUTPUT).mkdir(parents=True, exist_ok=True)
                        output = os.path.join(CSV_OUTPUT, file_name)

                    self.save_file(self.response.content, output_path=CSV_OUTPUT, file_name=file_name)
                    return output
                else:
                    GussExceptions(message="It looks like you did not provide csv file_name. please provide valid name")

            if save_file and file_name and (str(gis_data_type).lower() == 'gpkg' or str(gis_data_type).lower() == 'shp'):

                if str(gis_data_type).lower() == 'gpkg':
                    if not Path(GPK_OUTPUT).exists():
                        Path(GPK_OUTPUT).mkdir(parents=True, exist_ok=True)

                    self.save_file(response=self.response.content, output_path=GPK_OUTPUT, file_name=file_name)
                    return os.path.join(GPK_OUTPUT, file_name)

                elif str(gis_data_type).lower() == 'shp':
                    if not Path(SHP_OUTPUT).exists():
                        Path(SHP_OUTPUT).mkdir(parents=True, exist_ok=True)

                    self.save_file(response=self.response.content, output_path=SHP_OUTPUT, file_name=file_name)
                    return os.path.join(SHP_OUTPUT, file_name)
                else:
                    return warnings.warn(
                        "please indicate the what type of GIS data that is, options are:\n1)\tGPKG\n2)\tSHP")

            return self.response.json()

        # error handling

        except GussExceptions as e:
            raise GussExceptions(f"error: {e}")

    def get_as_of_dates(self):

        # get as of Dates
        self.url_endpoint = '/api/public/map/listAsOfDates'
        aod_list = self.get_request(return_df=True, save_file=True, file_name="as_of_date.csv")
        return aod_list

    def get_download_reference(self, as_of_date=None):

        # set get method
        self.request_type = "GET"
        # get List of Availability Data for Downloads
        if as_of_date is None:
            as_of_date = '2024-06-30'

        self.url_endpoint = f'/api/public/map/downloads/listAvailabilityData/{as_of_date}'
        reference_df = self.get_request(return_df=True, save_file=True,
                                        file_name=f"download_reference_list_as_of_date_{as_of_date}.csv")
        return reference_df

    def download_file(self, data_type, file_id, file_name, gis_type):

        if str(data_type).lower() == "availability":
            pass
        elif str(data_type).lower() == 'challenge':
            pass
        else:
            raise GussExceptions(f"data_type: {data_type}-- it should be either : availability or challenge")

        file_type = ""
        if gis_type is not None:
            if gis_type.lower() == "shp":
                file_type = '1'
                self.url_endpoint = f"/api/public/map/downloads/downloadFile/{data_type}/{file_id}/{file_type}"
            elif gis_type.lower() == 'gpkg':
                file_type = '2'
                self.url_endpoint = f"/api/public/map/downloads/downloadFile/{data_type}/{file_id}/{file_type}"
        else:
            self.url_endpoint = f"/api/public/map/downloads/downloadFile/{data_type}/{file_id}"
        print(self.url_endpoint)
        saved_output = self.get_request(save_file=True, return_df=False, file_name=file_name, gis_data_type=gis_type)

        return saved_output

    def list_challenge_data(self, as_of_date=None, file_name=None, params=None):

        try:
            self.request_type = 'GET'

            if as_of_date is None:
                as_of_date = '2024-06-30'

            self.url_endpoint = f'/api/public/map/downloads/listChallengeData/{as_of_date}'

            self.request_param = params

            saved_output = self.get_request(save_file=True, return_df=True, file_name=file_name)

            return saved_output

        # error handling
        except GussExceptions as e:
            raise GussExceptions(f"error: {e}")

    def polygonize(self, hex_id):
        coords = h3.cell_to_boundary(hex_id)
        flipped = tuple(coord[::-1] for coord in coords)
        return Polygon(flipped)

    def create_initial_directories(self, base_folder):
        BASE_DIR = Path(base_folder).resolve()
        DATA_DIR = BASE_DIR / "data"
        DATA_INPUT = DATA_DIR / "input"
        DATA_OUTPUT = DATA_DIR / "output"
        CSV_OUTPUT = DATA_OUTPUT / "csv"
        SHP_OUTPUT = DATA_OUTPUT / 'shp'
        GPK_OUTPUT = DATA_OUTPUT / 'gpkg'

        for dir_path in [DATA_DIR, DATA_INPUT, DATA_OUTPUT, CSV_OUTPUT, SHP_OUTPUT, GPK_OUTPUT]:
            if not Path.exists(dir_path):
                Path.mkdir(dir_path)

        return BASE_DIR, DATA_DIR, DATA_INPUT, DATA_OUTPUT, CSV_OUTPUT, SHP_OUTPUT, GPK_OUTPUT