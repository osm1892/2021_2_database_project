import datetime
import json
from typing import List, Tuple

import haversine
import requests

import database

with open('config.json') as f:
    config = json.load(f)


def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 지점 사이의 거리를 계산하는 함수
    :param lat1: 지점 1의 위도
    :param lon1: 지점 1의 경도
    :param lat2: 지점 2의 위도
    :param lon2: 지점 2의 경도
    :return: 두 지점 사이의 거리(km)
    """

    return haversine.haversine((lat1, lon1), (lat2, lon2), unit='km')


def get_station_list() -> List[dict]:
    """
    모든 측정소의 정보를 리스트로 반환하는 함수
    :return: 측정소 리스트
    """

    return database.Database().query("SELECT * FROM 측정소_정보").fetchall()


def get_station_info(name: str) -> dict:
    """
    측정소 정보를 반환하는 함수
    :param name: 측정소 이름
    :return: 측정소 정보
    """

    return database.Database().query("SELECT * FROM 측정소_정보 WHERE 측정소명 = ?", (name,)).fetchone()


def get_air_list() -> List[dict]:
    """
    측정소의 공기 상태를 리스트로 반환하는 함수
    :return: 측정 결과 리스트
    """

    return database.Database().query("SELECT * FROM 측정_결과").fetchall()


def get_air_info(name: str) -> dict:
    """
    측정소의 공기 상태를 반환하는 함수
    :param name: 측정소 이름
    :return: 측정 결과 정보
    """

    return database.Database().query("SELECT * FROM 측정_결과 WHERE 측정소명 = ?", (name,)).fetchone()


def get_nearby_stations(name: str) -> List[dict]:
    """
    사용자 위치 주변 측정소를 조회하는 함수
    :param name: 사용자 위치 별칭
    :return: 주변 측정소 목록
    """

    return database.Database().query('SELECT * FROM 주변_측정소 WHERE 사용자_위치_별칭 = ?', (name,)).fetchall()


def calc_nearby_stations(lat: float, lon: float, distance: float = 60) -> List[Tuple[dict, float]]:
    """
    가까운 측정소를 찾는 함수
    기본 거리 60km는 임의의 위치에서 측정소까지 걸리는 최소 거리를 계산하였음.
    :param lat: 위도
    :param lon: 경도
    :param distance: 거리
    :return: 가장 가까운 측정소와 거리의 리스트
    """

    station_list = get_station_list()
    station_info = []
    for station in station_list:
        dist = get_distance(lat, lon, station['위도'], station['경도'])
        if dist <= distance:
            station_info.append((station, dist))
    return station_info


def calc_nearest_station(lat: float, lon: float) -> Tuple[dict, float]:
    """
    가장 가까운 측정소를 찾는 함수
    :param lat: 위도
    :param lon: 경도
    :return: 가장 가까운 측정소와 거리
    """

    station_list = get_station_list()

    min_dist = float('inf')
    min_station = None
    for station in station_list:
        dist = get_distance(lat, lon, station['위도'], station['경도'])
        if dist < min_dist:
            min_dist = dist
            min_station = station
    return min_station, min_dist


def air_value_to_grade(air_value: int) -> int:
    """
    통합대기환경지수를 등급으로 변경하는 함수
    :param air_value: 통합대기환경지수
    :return: 등급
    """

    if air_value <= 50:
        return 1
    if air_value <= 100:
        return 2
    if air_value <= 250:
        return 3
    return 4


def update_air_quality():
    """
    측정 결과 테이블을 업데이트하는 함수
    """

    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty'
    params = {'serviceKey': config['air_korea_api_key'],
              'returnType': 'json', 'numOfRows': '1000', 'pageNo': '1', 'sidoName': '전국', 'ver': '1.0'}

    qualities: List[dict] = requests.get(url, params=params).json()['response']['body']['items']

    for quality in qualities:
        try:
            date = quality['dataTime']
            if date is None:
                raise Exception
            datetime.datetime.fromisoformat(date)
        except:
            date = '0000-00-00 00:00'
        date += ':00'

        try:
            kai = quality['khaiValue']
            if kai is None:
                raise Exception
            kai = int(kai)
        except:
            kai = -1

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        database.Database().query('UPDATE 측정_결과 SET 통합대기환경지수 = ?, 측정일 = ?, 업데이트_요청_시각 = ? WHERE 측정소명 = ?',
                                  (kai, date, now, quality['stationName']))


def insert_nearby_stations(user_location_name: str, lat: float, lon: float):
    """
    사용자 위치에 따른 주변 측정소를 추가
    :param lon: 위도
    :param lat: 경도
    :param user_location_name: 사용자 위치명
    """

    nearby_stations = calc_nearby_stations(lat, lon)

    for station in nearby_stations:
        database.Database().query('INSERT INTO 주변_측정소 (사용자_위치_별칭, 측정소명, 거리) VALUES (?, ?, ?)',
                                  (user_location_name, station[0]['측정소명'], station[1]))
