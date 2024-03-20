import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timezone


class Mtd_Api:
    def __init__(self):
        load_dotenv()
        self.api = os.getenv("MTD_API_KEY")
        self.data_format = "JSON"
        self.version = "v2.2"
        self.pt = 60
        self.base_url = "https://developer.mtd.org/api/{}/{}/{{}}?key={}".format(
            self.version, self.data_format, self.api
        )
        self.stop_json = json.load(open("mtd bus stop data/stops.json"))
        self.stop_name_to_id_json = json.load(
            open("mtd bus stop data/stop_name_to_id.json")
        )
        self.changeset_id = None
        self.cache = {}
        self.last_api_hit = 0
        self.favorite_stop = None

    def get_departures_by_stop(self, stop_name: str) -> list:
        if datetime.now(timezone.utc).timestamp() - self.last_api_hit < 60:
            print("\nhit cache \n")
            # data not modified, check in cache and return existing data
            return self.cache["getdeparturesbystop"][stop_name]
        param = {
            "stop_id": self.stop_name_to_id_json[stop_name],
            "changeset_id": self.changeset_id,
            "pt": self.pt,
        }
        response = requests.get(
            mtd.base_url.format("getdeparturesbystop"), params=param
        )
        response_json = response.json()
        if response.status_code == 200:
            print("\n New cache \n")
            self.last_api_hit = datetime.now(timezone.utc).timestamp()
            bus_arrival_time_list = []
            for departure in response_json["departures"]:
                bus_arrival_time_list.append(
                    [departure["headsign"], departure["expected_mins"]]
                )
            self.cache.setdefault("getdeparturesbystop", {}).setdefault(stop_name, {})
            self.cache["getdeparturesbystop"][stop_name] = bus_arrival_time_list
            return bus_arrival_time_list

        else:
            return {}

    def set_favorite_stop(self, stop_name: str):
        if stop_name in self.stop_name_to_id_json.keys():
            self.favorite_stop = stop_name
        else:
            raise ValueError("Invalid stop name")

    def save_stops_json(self) -> None:
        response = requests.get(mtd.base_url.format("getstops"))
        response_json = response.json()
        with open("mtd bus stop data/stops.json", "w") as outfile:
            json.dump(response_json, outfile, indent=4)

    def save_name_to_id_json(self) -> None:
        stop_name_to_id_dict = {}
        for stop in self.stop_json["stops"]:
            stop_name_to_id_dict[stop["stop_name"]] = stop["stop_id"]
        with open("mtd bus stop data/stop_name_to_id.json", "w") as outfile:
            json.dump(stop_name_to_id_dict, outfile, indent=4)

    def pretty_print(self, data: dict):
        return json.dumps(data, indent=4)


if __name__ == "__main__":
    mtd = Mtd_Api()

    print(mtd.pretty_print(mtd.get_departures_by_stop("Fourth and Chalmers")))
