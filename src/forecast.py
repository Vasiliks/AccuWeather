# -*- coding: utf-8 -*-
# created by Vasiliks 01.2023

from six import ensure_str as STR


def sun_moon(WF):
    panel_left = WF.find('div', class_='panel left')
    sun_icon = panel_left.find('svg', class_='weather-icon').get('data-src')
    sun_duration = panel_left.find_all('p')
    sun_info = []
    for i in sun_duration:
        sun_info.append(STR(i.text.strip()))
    sunset = panel_left.find_all('span')
    for i in sunset:
        sun_info.append(STR(i.text.strip()))
    panel_right = WF.find('div', class_='panel right')
    moon_icon = panel_right.find('svg', class_='weather-icon').get('data-src')
    moon_duration = panel_right.find_all('p')
    moon_info = []
    for i in moon_duration:
        moon_info.append(STR(i.text.strip()))
    moonset = panel_right.find_all('span')
    for i in moonset:
        moon_info.append(STR(i.text.strip()))
    return sun_info, moon_info


def ToD_Weather_Forecast(bs):
    current_weather = []
    ToDWF = bs.find('div', class_='page-column-1')
    day = ToDWF.find('div', class_='content-module subnav-pagination').text.strip()
    time_of_day = ToDWF.find('h2', class_='title').text.strip()
    current = "{}:{}\n".format(time_of_day, day)
    current_weather.append(STR(current))
    current_icon = ToDWF.find('svg', class_='icon').get('data-src')
    current_weather.append(STR(current_icon))
    temp = ToDWF.find('div',  class_='temperature').text
    current_weather.append(STR(temp.strip()))
    phrase = ToDWF.find('div', class_='phrase').text
    current_weather.append(STR(phrase.strip()))
    extra = ToDWF.find('div', class_='real-feel').text
    current_weather.append(STR(extra.strip()))
    detail = []
    nodes = ToDWF.find_all('div', class_="half-day-card-content")
    for node in nodes:
        if node.attrs["class"][0] == "half-day-card-content":
            subnodes = node.find_all('p', class_="panel-item")
            for sub in subnodes:
                val = sub.find("span", class_="value")
                detail.append((sub.contents[0].strip(), val.contents[0].strip()))
    current_weather.append(detail)
    info = sun_moon(ToDWF)
    current_weather.extend(info)
    sunrise_sunset = ToDWF.find('h2', class_='title module-title').text.strip()
    current_weather.append(sunrise_sunset)
    return current_weather


def Current_Weather(bs):
    current_weather = []
    CWF = bs.find('div', class_='page-column-1')
    current = CWF.find('div', class_='card-header spaced-content').text
    current_weather.append(STR(current.strip().replace("\n", ":")))
    current_icon = CWF.find('svg', class_='icon').get('data-src')
    current_weather.append(STR(current_icon))
    temp = CWF.find('div', class_='temp').text
    current_weather.append(STR(temp.strip()))
    phrase = CWF.find('div', class_='phrase').text
    current_weather.append(STR(phrase.strip()))
    extra = CWF.find('div', class_='current-weather-extra').text
    current_weather.append(STR(extra.strip()))
    current_weather_details = CWF.find('div', class_='current-weather-details').find_all('div', class_='detail-item spaced-content')
    detail = []
    for item in current_weather_details:
        detail.append(item.text.strip().split("\n"))
    current_weather.append(detail)
    info = sun_moon(CWF)
    current_weather.extend(info)
    sunrise_sunset = CWF.find('h2', class_='title module-title').text.strip()
    current_weather.append(sunrise_sunset)
    return current_weather
