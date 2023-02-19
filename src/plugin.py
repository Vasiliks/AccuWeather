# -*- coding: utf-8 -*-
from . import _, getSkin, getFullPath
import os
import requests
from six import ensure_str as STR
from bs4 import BeautifulSoup
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigSubsection, ConfigText, configfile
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap
from Components.ScrollLabel import ScrollLabel

FullPath = os.path.dirname(os.path.realpath(__file__))
HEADERS = {'User-Agent': 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV; Maple2012) AppleWebKit/534.7 (KHTML, like Gecko) SmartTV Safari/534.7', 'Accept-Encoding': 'gzip, deflate'}
URL = 'https://www.accuweather.com'

lang = language.getLanguage()[:2]
city_list = '/etc/enigma2/accuweather_city.list'
precip_svg = LoadPixmap(cached=True, path="{}{}".format(FullPath, "/images/weathericons/humidity.svg"))
plugin_version = '1.0'


# Set default configuration
accuweathercfg = config.plugins.accuweather = ConfigSubsection()
accuweathercfg.city = ConfigText(default='Tokyo, Tokyo, JP, 226396')


def show_svg(svg_file, svg):
    svg.instance.setScale(1)
    svg.instance.setPixmapFromFile(svg_file)
    svg.instance.show()


def sunrise_moonrise(j):
    a = "{}\n{}".format(j[0], j[1])
    b = "{}:{}\n".format(j[2], j[3])
    b += "{}:{}".format(j[4], j[5])
    return a, b


def full_link(forecast):
    country = accuweathercfg.city.value.split(",")[2].strip().lower()
    code = accuweathercfg.city.value.split(",")[-1].strip()
    url = "{url}/{lang}/{country}/p/{code}/{forecast}/{code}".format(url=URL, lang=lang, forecast=forecast, country=country, code=code)
    return url


"""###############################  AccuWeather  ###############################"""


class AccuWeather(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = getSkin("AccuWeather")
        self.setTitle(_("Enigma2 AccuWeather  ver. %s") % plugin_version)
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Hourly"))
        self["key_blue"] = Label(_("Select City"))
        self["period"] = Label()
        self["city"] = Label()
        self["head"] = ScrollLabel("")
        self["extra"] = ScrollLabel("")
        self["detail-left"] = ScrollLabel("")
        self["detail-right"] = ScrollLabel("")
        self["sunrise"] = ScrollLabel("")
        self["moonrise"] = ScrollLabel("")
        self["temp"] = Label()
        self["phrase"] = Label()
        self["sun_dur"] = Label()
        self["moon_dur"] = Label()
        self["cur_icon"] = Pixmap()
        self.lang = language.getLanguage()[:2]
        self.forecast = []
        self["forecast"] = List(self.forecast, enableWrapAround=True)
        self['actions'] = ActionMap(["AccuWeatherActions"], {
            "cancel": self.cancel,
            "red": self.cancel,
            "green": self.ok,
            "blue": self.select_city,
            "ok": self.ok,
            "info": self.about,
            }, -1)
        self.onLayoutFinish.append(self.weather)

    def weather(self):
        self.Daily_Weather_Forecast()
        resp = self.Current_Weather()
        self["head"].setText(resp[0].replace("\n", ":"))
        self["temp"].setText(resp[2])
        self["phrase"].setText(resp[3])
        j = resp[4].split('\t')
        self["extra"].setText("{}:{}".format(j[0].strip(), j[-1].strip()))
        R = L = ''
        a = resp[5]
        for i, j in enumerate(a):
            if i >= (len(a)+1)//2:
                R += "{}:{}\n".format(j[0], j[1])
            else:
                L += "{}:{}\n".format(j[0], j[1])
        self["detail-left"].setText(L)
        self["detail-right"].setText(R)

        show_svg("{}{}".format(FullPath, resp[1]), self["cur_icon"])

        self["sun_dur"].setText(sunrise_moonrise(resp[6])[0])
        self["sunrise"].setText(sunrise_moonrise(resp[6])[1])

        self["moon_dur"].setText(sunrise_moonrise(resp[7])[0])
        self["moonrise"].setText(sunrise_moonrise(resp[7])[1])

    def Daily_Weather_Forecast(self):
        self.forecast = []
        link_city = full_link("daily-weather-forecast")
        response = requests.get(link_city, headers=HEADERS)
        bs = BeautifulSoup(response.text, "html.parser")
        self['city'].setText(STR(bs.find('h1', class_='header-loc').text))
        self['period'].setText(STR(bs.find('p', class_='module-title').text))
        daily_weather_forecast = bs.find('div', class_='page-column-1')
        page_content = daily_weather_forecast.findAll('div', class_='daily-wrapper')
        for dailyCard in page_content:
            daily_forecast_card_link = URL + dailyCard.find('a', class_='daily-forecast-card').get('href')
            dow_date = STR(dailyCard.find('span', class_='module-header dow date').text.upper())
            sub_date = STR(dailyCard.find('span', class_='module-header sub date').text)
            iconsvg = LoadPixmap(cached=True, path="{}{}".format(FullPath, dailyCard.find('svg', class_='icon').get('data-src')))
            temp = dailyCard.find('div', class_='temp')
            temp_low = STR(temp.find('span', class_='low').text)
            temp_high = STR(temp.find('span', class_='high').text)
            phrase = STR(dailyCard.find('div', class_='phrase').text.strip())
            precip = STR(dailyCard.find('div', class_='precip').text.strip())
            self.forecast.append((dow_date, sub_date, iconsvg, temp_high, temp_low, phrase, precip, precip_svg))
        self["forecast"].setList(self.forecast)

    def cancel(self):
        self.close()

    def ok(self):
        day = [self['forecast'].getIndex()+1, self["forecast"].getCurrent()[0], self["forecast"].getCurrent()[1]]
        self.session.openWithCallback(self.weather, AccuWeatherHours, day)

    def about(self):
        self.session.open(MessageBox, _('Enigma2 Weather Forecast\n AccuWeather ©2023'),
                          MessageBox.TYPE_INFO, simple=True)

    def Current_Weather(self):
        link_city = full_link("current-weather")
        response = requests.get(link_city, headers=HEADERS)
        bs = BeautifulSoup(response.text, "html.parser")
        current_weather = []
        CWF = bs.find('div', class_='page-column-1')
        current = CWF.find('div', class_='card-header spaced-content')
        current_weather.append(STR(current.text.strip()))
        current_icon = CWF.find('svg', class_='icon').get('data-src')
        current_weather.append(STR(current_icon))
        temp = CWF.find('div', class_='temp')
        current_weather.append(STR(temp.text.strip()))
        phrase = CWF.find('div', class_='phrase').text
        current_weather.append(STR(phrase.strip()))
        extra = CWF.find('div', class_='current-weather-extra').text
        current_weather.append(STR(extra.strip()))
        current_weather_details = CWF.find('div', class_='current-weather-details').find_all('div', class_='detail-item spaced-content')
        detail = []
        for item in current_weather_details:
            detail.append(item.text.strip().split("\n"))
        current_weather.append(detail)
        sunrise_sunset = CWF.find('h2', class_='title module-title').text
        panel_left = CWF.find('div', class_='panel left')
        sun_icon = panel_left.find('svg', class_='weather-icon').get('data-src')
        sun_duration = panel_left.find_all('p')
        sun_info = []
        for i in sun_duration:
            sun_info.append(STR(i.text.strip()))
        sunset = panel_left.find_all('span')
        for i in sunset:
            sun_info.append(STR(i.text.strip()))
        panel_right = CWF.find('div', class_='panel right')
        moon_icon = panel_right.find('svg', class_='weather-icon').get('data-src')
        moon_duration = panel_right.find_all('p')
        moon_info = []
        for i in moon_duration:
            moon_info.append(STR(i.text.strip()))
        moonset = panel_right.find_all('span')
        for i in moonset:
            moon_info.append(STR(i.text.strip()))
        current_weather.append(sun_info)
        current_weather.append(moon_info)
        return current_weather

    def select_city(self):
        self.session.openWithCallback(self.weather, AccuWeatherSelect)


"""############################### AccuWeatherConf  ###############################"""


class AccuWeatherHours(Screen):
    def __init__(self, session, day):
        Screen.__init__(self, session)
        self.skin = getSkin("AccuWeatherHours")
        self.day = day
        self["period"] = Label()
        self["city"] = Label()
        self['city'].setText(day[1] + "   " + day[2])
        self["head"] = ScrollLabel("")
        self["extra"] = ScrollLabel("")
        self["detail-left"] = ScrollLabel("")
        self["detail-right"] = ScrollLabel("")
        self["sunrise"] = ScrollLabel("")
        self["moonrise"] = ScrollLabel("")
        self["temp"] = Label()
        self["phrase"] = Label()
        self["sun_dur"] = Label()
        self["moon_dur"] = Label()
        self["cur_icon"] = Pixmap()
        self.lang = language.getLanguage()[:2]
        self.forecast = []
        self["forecast"] = List(self.forecast, enableWrapAround=True)
        self['actions'] = ActionMap(["AccuWeatherActions"], {
            "cancel": self.cancel,
            "down": self.keyDown,
            "up": self.keyUp,
            "left": self.keyLeft,
            "right": self.keyRight
            }, -1)
        self.onLayoutFinish.append(self.Hours_Weather_Forecast)


    def Hours_Weather_Forecast(self):
        self.forecast = []
        link = full_link("hourly-weather-forecast")
        link_city = "{}?day={}".format(link, self.day[0])
        response = requests.get(link_city, headers=HEADERS)
        bs = BeautifulSoup(response.text, "html.parser")
        hourly = bs.find(attrs={"data-qa": "hourly"})
        self['period'].setText(STR(hourly.text.strip()))
        hour_weather = []
        hour_forecast = bs.find('div', class_='page-column-1')
        currents = hour_forecast.find_all('div', 'accordion-item hourly-card-nfl hour')
        for current in currents:
            hour = STR(current.find('h2', class_='date').text)
            iconsvg = LoadPixmap(cached=True, path="{}{}".format(FullPath, current.find('svg', class_='icon').get('data-src')))
            temp = STR(current.find('div', class_='temp').text)
            precip = STR(current.find('div', class_='precip').text)
            phrase = STR(current.find('div', class_='phrase').text)
            odd = current.find_all('div', class_="hourly-content-container")
            extra = []
            for i in odd[1].stripped_strings:
                extra.append(i)
            self.forecast.append((hour, iconsvg, temp, phrase, precip.strip(), extra))
        self["forecast"].setList(self.forecast)
        self.cross()

    def keyRight(self):
        self["forecast"].pageDown()
        self.cross()

    def keyLeft(self):
        self["forecast"].pageUp()
        self.cross()

    def keyUp(self):
        self["forecast"].selectPrevious()
        self.cross()

    def keyDown(self):
        self["forecast"].selectNext()
        self.cross()

    def cross(self):
        b = self["forecast"].getCurrent()[5]
        h = []
        for i, j in enumerate(b):
            if i%2 == 0:
                h.append([b[i], b[i+1]])
        R = L = ''
        for i, j in enumerate(h):
            if i >= (len(h)+1)//2:
                R += "{}:{}\n".format(j[0],j[1])
            else:
                L += "{}:{}\n".format(j[0],j[1])
        self["detail-left"].setText(L)
        self["detail-right"].setText(R)

    def cancel(self):
        self.close()


"""############################### AccuWeatherSelect  ###############################"""


class AccuWeatherSelect(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = getSkin("AccuWeatherSearch")
        self['key_red'] = Label(_('Cancel'))
        self['key_green'] = Label(_('Select'))
        self['description'] = Label()
        self['key_blue'] = Label()
        self.citylist = []
        self["citylist"] = List(self.citylist)
        self['actions'] = ActionMap(["AccuWeatherActions"], {
            'ok': self.ok,
            'cancel': self.exit,
            "blue": self.openVirtualKeyBoard,
            'red': self.exit
        }, -2)
        self.City_List()


    def City_List(self):
        self['description'].setText(_('Select City'))
        self['key_blue'].setText(_('Search'))
        self.citylist = []
        self.ST = False
        if os.path.isfile(city_list):
            with open(city_list, "r") as f:
                for d in f.readlines():
                    c = d.split(",")
                    self.citylist.append(("{},{},{}".format(c[0], c[1], c[2]), c[-1]))
        self["citylist"].setList(self.citylist)

    def openVirtualKeyBoard(self):
        self.session.openWithCallback(self.search, VirtualKeyBoard, title=_('Enter the name of the locality'))

    def ok(self):
        nc = '{}, {}'.format(self["citylist"].getCurrent()[0], self["citylist"].getCurrent()[1])
        if self.ST == False:
            accuweathercfg.city.setValue(nc.strip())
            accuweathercfg.save()
            configfile.save()
            self.close()
        else:
            with open(city_list, "a") as f:
                f.write('%s\n' % nc)
            self.City_List()

    def search(self, city):
        self.citylist = []
        self['description'].setText(_('Result Search for " %s "') % city)
        self['key_blue'].setText(_(' '))
        try:
            search_url = "{url}/{lang}/search-locations?query={city}".format(url=URL, lang=lang, city=city)
            response_search = requests.get(search_url, headers=HEADERS)
            loc_bs = BeautifulSoup(response_search.text, "html.parser")
            loc = loc_bs.find('div', class_='locations-list content-module')
            if loc:
                list_loc = loc.findAll('a', class_='')
                for one in list_loc:
                    name = one.text.split("(")[0].strip()
                    ref = one.get('href').strip()[32:-8]
                    self.citylist.append((STR(name), STR(ref)))
            else:
                name = loc_bs.find('p', class_='recent-location__name').text
                admin = loc_bs.find('p', class_='recent-location__admin').text
                loc = loc_bs.find('div', class_='page-content content-module')
                l1 = loc.find('a', class_='cur-con-weather-card card-module content-module lbar-panel')
                count = l1.get('href').split('/')[2].upper()
                ref = l1.get('href').split('/')[4]
                n = "{}, {}, {}".format(name, admin, count)
                self.citylist.append((STR(n), STR(ref)))

        except:
            print('wrong config settings!')
        self.ST = True
        self["citylist"].setList(self.citylist)

    def exit(self):
        self.close()

##################################################################


def main(session, **kwargs):
    session.open(AccuWeather)


def Plugins(**kwargs):
    return [
        PluginDescriptor(name=_("AccuWeather"),
                         where=[PluginDescriptor.WHERE_PLUGINMENU],
                         description=_("Forecast AccuWeather"),
                         fnc=main)
    ]
