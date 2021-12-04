import os
from typing import *

import schedule
import win32api

import air_station
import google_map_api
import user_location


def __main__():
    print("정보를 업데이트하고 있습니다. 잠시만 기다려주시길 바랍니다...")
    scheduled_function()
    clear_console()
    # 공기질 데이터 업데이트 스케쥴러 시작
    schedule.every().hour.do(scheduled_function)
    while True:
        # 공기질 업데이트
        schedule.run_pending()
        # 시작 페이지
        start_page()


def start_page():
    clear_console()

    print("1. 사용자 위치 조회")
    print("2. 사용자 위치 추가")
    print("3. 지역 미세먼지 조회")
    print('')

    print("원하는 번호를 입력하세요: ", end='')
    num = input()

    if num == '1':
        manage_location_list()
    elif num == '2':
        edit_location(None)
    elif num == '3':
        print_nearest_air_quality()
    else:
        print("잘못 입력하셨습니다.")
        input()


def manage_location_list():
    clear_console()

    locations = user_location.get_user_location_list()

    for i in range(len(locations)):
        print("{}. {} [{}, {}]".format(i, locations[i]['별칭'], locations[i]['위도'], locations[i]['경도']))

    print("\n위치 번호를 선택하세요: ", end='')

    try:
        num = int(input())
    except:
        num = -1

    if num < 0 or len(locations) <= num:
        print("잘못 입력하셨습니다.")
        input()
        return

    print("1. 상세 정보 ", end='')
    print("2. 위치 수정 ", end='')
    print("3. 위치 삭제")

    print("원하는 번호를 입력하세요: ", end='')

    try:
        operation = int(input())
    except:
        operation = -1

    if operation == 1:
        clear_console()
        print_location_info(locations[num]['별칭'])
    elif operation == 2:
        edit_location(locations[num]['별칭'])
    elif operation == 3:
        user_location.delete_user_location(locations[num]['별칭'])
    else:
        print("잘못 입력하셨습니다.")
        input()


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def edit_location(location_name: Optional[str]):
    clear_console()

    if location_name is None:
        while True:
            print("추가할 위치 이름을 입력하세요: ", end='')
            location_name = input()
            if location_name == "":
                continue
            break
    else:
        user_location.delete_user_location(location_name)

    while True:
        print("주소를 입력하세요: ", end='')
        address = input()
        locations = google_map_api.get_google_map_api_result(google_map_api.get_google_geocode_api_url(address))

        if len(locations) != 0:
            break

        print("입력하신 주소에 대한 위치 정보를 찾을 수 없습니다.")
        input()

    while True:
        for i in range(len(locations)):
            print("{}. {}".format(i, locations[i]['formatted_address']))

        print("\n위치 번호를 선택하세요: ", end='')
        try:
            num = int(input())
        except:
            num = -1

        if num < 0 or len(locations) <= num:
            print("잘못된 번호를 입력하셨습니다.")
            continue
        break

    user_location.insert_user_location(location_name, locations[num]['geometry']['location']['lat'],
                                       locations[num]['geometry']['location']['lng'])

    air_station.insert_nearby_stations(location_name, locations[num]['geometry']['location']['lat'],
                                       locations[num]['geometry']['location']['lng'])

    print("추가되었습니다.")
    input()


def print_location_info(name: str):
    location = user_location.get_user_location(name)

    print(f"별칭: {location['별칭']}")
    print(f"좌표: {location['위도']}, {location['경도']}")
    print('')

    stations = air_station.get_nearby_stations(name)
    stations.sort(key=lambda x: x['거리'])
    station = stations[0]

    air_info = air_station.get_air_info(station['측정소명'])

    print(f"인접 측정소명: {station['측정소명']}")
    print(f"거리: {station['거리']}")
    print(f"공기질: {air_info['통합대기환경지수']}")
    print(f"등급: {air_station.air_value_to_grade(air_info['통합대기환경지수'])}")
    input()


def print_nearest_air_quality():
    clear_console()

    print("지역을 입력하세요: ", end='')
    address = input().strip()
    locations = google_map_api.get_google_map_api_result(google_map_api.get_google_geocode_api_url(address))

    if locations is None:
        print("오류가 발생하였습니다. 관리자에게 문의 바랍니다.")
        input()
        return

    if len(locations) == 0:
        print("입력하신 주소에 대한 위치 정보를 찾을 수 없습니다.")
        input()
        return

    lat, lon = locations[0]['geometry']['location']['lat'], locations[0]['geometry']['location']['lng']

    station, _ = air_station.calc_nearest_station(lat, lon)

    print('')
    print_air_quality(station['측정소명'])


def print_air_quality(name: str):
    """
    해당 측정소의 측정 정보를 출력합니다.
    :param name: 측정소명
    """

    station = air_station.get_station_info(name)
    air_quality = air_station.get_air_info(name)

    print("측정소 이름: {}".format(station['측정소명']))
    print("측정소 위치: {}".format(station['주소']))
    print("통합대기환경수치: {}".format(air_quality['통합대기환경지수']))
    print("통합대기환경지수: {}".format(air_station.air_value_to_grade(air_quality['통합대기환경지수'])))
    input()


def alerter():
    """
    사용자 위치 주변의 공기질을 체크하고, 3, 4단계 경보를 울리는 함수
    """

    user_locations = user_location.get_user_location_list()

    warning_locations: List[str] = []
    caution_locations: List[str] = []

    for location in user_locations:
        max_grade = 1

        stations = air_station.calc_nearby_stations(location['위도'], location['경도'])

        for station in stations:
            air_info = air_station.get_air_info(station[0]['측정소명'])
            kai_grade = air_station.air_value_to_grade(air_info['통합대기환경지수'])
            max_grade = max(max_grade, kai_grade)

        if max_grade == 3:
            warning_locations.append(location['별칭'])
        elif max_grade == 4:
            caution_locations.append(location['별칭'])

    if warning_locations == [] and caution_locations == []:
        return

    alert_title = "오염 경보!!!"
    alert_message = f"3단계: {warning_locations}\n4단계: {caution_locations}"
    win32api.MessageBox(0, alert_message, alert_title)


def scheduled_function():
    air_station.update_air_quality()
    alerter()


if __name__ == '__main__':
    __main__()
