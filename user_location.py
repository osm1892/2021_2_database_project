from typing import *

import database


def insert_user_location(location_name: str, latitude: float, longitude: float):
    database.Database().query("INSERT INTO 사용자_위치 (별칭, 위도, 경도) VALUES (?, ?, ?)",
                              (location_name, latitude, longitude))


def update_user_location(location_name: str, latitude: float, longitude: float):
    database.Database().query("UPDATE 사용자_위치 SET 위도=?, 경도=? WHERE 별칭=?", (latitude, longitude, location_name))


def delete_user_location(location_name: str):
    database.Database().query("DELETE FROM 사용자_위치 WHERE 별칭=?", (location_name,))


def get_user_location(location_name: str) -> Optional[dict]:
    return database.Database().query("SELECT * FROM 사용자_위치 WHERE 별칭=?", (location_name,)).fetchone()


def get_user_location_list() -> List[dict]:
    return database.Database().query("SELECT * FROM 사용자_위치").fetchall()
