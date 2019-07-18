# -*- coding: utf-8 -*-

import logging
import re
import requests
import time
import datetime
import pytz
from telescope_interface import TelescopeInterface
from astropy.coordinates import SkyCoord, Angle, AltAz
import astropy.units as u
from astropy.time import Time
from sky import Satellite, Celestial, SolarSystem
import json

find_format_string = \
"""[
	{{
		"type": "section",
		"fields": [
     		{{
				"type": "mrkdwn",
				"text": "*{Index}*. `Name`: {Name}"
            }},
            {{
				"type": "mrkdwn",
				"text": "`Type:` {Type}"
			}},
			{{
				"type": "mrkdwn",
				"text": "`RA/DEC:` {RA}/{DEC}"
			}},
  			{{
				"type": "mrkdwn",
				"text": "`Altitude:` {Altitude}"
			}},
    		{{
				"type": "mrkdwn",
				"text": "`Azimuth:` {Azimuth}"
			}},
            {{
				"type": "mrkdwn",
				"text": "`Magnitude (V):` {V}"
			}}
		]
	}}
]"""


class IxchelCommand:

    commands = []
    skyObjects = []

    def __init__(self, ixchel):
        self.logger = logging.getLogger('IxchelCommand')
        self.ixchel = ixchel
        self.config = ixchel.config
        self.channel = self.config.get('slack', 'channel')
        self.username = self.config.get('slack', 'username')
        self.slack = ixchel.slack
        self.telescope = ixchel.telescope
        # build list of backslash commands
        self.init_commands()
        # init the Sky interface
        self.satellite = Satellite(ixchel)
        self.celestial = Celestial(ixchel)
        self.solarSystem = SolarSystem(ixchel)

    def parse(self, message):
        text = message['text'].strip()
        for cmd in self.commands:
            command = re.search(cmd['regex'], text, re.IGNORECASE)
            if command:
                user = self.slack.get_user_by_id(message.get('user'))
                self.logger.debug('Received the command: %s from %s.' % (
                    command.group(0), user.get('name')))
                cmd['function'](command, user)
                return
        self.slack.send_message(
            '%s does not recognize your command (%s).' % (self.username, text))

    def handle_error(self, text, error):
        self.logger.error('Command failed (%s). %s' % (text, error))
        self.slack.send_message('Error. Command (%s) failed.' % text)

    def plot(self, command, user):
        #get object id; assume 1 if none
        if command.group(1):
            id = int(command.group(1).strip())
        else:
            id = 1
        #ensure object id is valid
        if id < 1 or id > len(self.skyObjects):
            self.slack.send_message('%s does not recognize that object id (%d).' % (self.config.get('slack', 'username'), id))
            return
        #find corresponding object
        skyObject = self.skyObjects[id-1]
        if skyObject.type == 'Solar System':
            self.solarSystem.plot(skyObject)
        elif skyObject.type == "Celestial":
            self.celestial.plot(skyObject)            
        #self.slack.send_message('Name of object is %s.'%skyObject.name)    

    def find(self, command, user):
        try:
            search_string = command.group(1)
            satellites = self.satellite.find(search_string)
            celestials = self.celestial.find(search_string)
            solarSystems = self.solarSystem.find(search_string)
            # process total search restults
            self.skyObjects = satellites + celestials + solarSystems
            telescope = self.ixchel.telescope.earthLocation
            if len(self.skyObjects) > 0:
                report = ''
                index = 1
                # calculate local time of observatory
                telescope_now = Time(datetime.datetime.utcnow(), scale='utc')
                for skyObject in self.skyObjects:
                    # create SkyCoord instance from RA and DEC
                    c = SkyCoord(skyObject.ra, skyObject.dec, unit=(u.hour, u.deg))
                    # transform RA,DEC to alt, az for this object from the observatory
                    altaz = c.transform_to(
                        AltAz(obstime=telescope_now, location=telescope))
                    # report += '%d.\t%s object (%s) found at RA=%s, DEC=%s, ALT=%f, AZ=%f, VMAG=%s.\n' % (
                    #    index, skyObject.type, skyObject.name, skyObject.ra, skyObject.dec, altaz.alt.degree, altaz.az.degree, skyObject.vmag)
                    report = find_format_string.format(Index=str(index), Name=skyObject.name, Type=skyObject.type, RA=skyObject.ra,
                                                       DEC=skyObject.dec, Altitude='%.1f°' % altaz.alt.degree, Azimuth='%.1f°' % altaz.az.degree, V=skyObject.vmag)
                    self.slack.send_block_message(report)
                    index += 1
            else:
                self.slack.send_message(
                    'Sorry, %s knows all but *still* could not find "%s".' % (self.config.get('slack', 'username'), search_string))
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)        

    def get_help(self, command, user):
        help_message = 'Here are some helpful tips:\n' + '>Please report %s issues here: https://github.com/mcnowinski/seo/issues/new\n' % self.username + \
            '>A more detailed %s tutorial can be found here: https://stoneedgeobservatory.com/guide-to-using-itzamna/\n' % self.username
        for cmd in sorted(self.commands, key = lambda i: i['regex']):
            if not cmd['hide']:
                help_message += '>%s\n' % cmd['description']
        self.slack.send_message(help_message)

    def get_where(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_where')
            # query telescope
            self.telescope.get_precipitation(telescope_interface)
            # assign values
            ra = telescope_interface.get_output_value('ra')
            dec = telescope_interface.get_output_value('dec')
            alt = telescope_interface.get_output_value('alt')
            az = telescope_interface.get_output_value('az')
            slewing = telescope_interface.get_output_value('slewing')
            # send output to Slack
            self.slack.send_message('Telescope Pointing:')
            self.slack.send_message('>RA: %s' % ra)
            self.slack.send_message('>DEC: %s' % dec)
            self.slack.send_message(u'>Alt: %.1f°' % alt)
            self.slack.send_message(u'>Az: %.1f°' % az)
            if slewing == 1:
                self.slack.send_message('>Slewing? Yes')
            else:
                self.slack.send_message('>Slewing? No')
            # get a DSS image of this part of the sky
            ra_decimal = Angle(ra + '  hours').hour
            dec_decimal = Angle(dec + '  degrees').degree
            url = self.config.get('misc', 'dss_url').format(ra=ra_decimal, dec=dec_decimal)
            self.slack.send_message("", [{"image_url": "%s" %url, "title": "Sky Position (DSS2):"}])
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_clouds(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_precipitation')
            # query telescope
            self.telescope.get_precipitation(telescope_interface)
            # assign values
            clouds = telescope_interface.get_output_value('clouds')
            # send output to Slack
            self.slack.send_message('Cloud cover is %d%%.' % int(clouds*100))
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_sun(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_sun')
            # query telescope
            self.telescope.get_precipitation(telescope_interface)
            # assign values
            alt = telescope_interface.get_output_value('alt')
            # send output to Slack
            self.slack.send_message('Sun:')            
            self.slack.send_message('>Altitude: %.1f°' % alt)
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_ccd(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_ccd')
            # query telescope
            self.telescope.get_ccd(telescope_interface)
            # assign values
            ncol = telescope_interface.get_output_value('ncol')
            nrow = telescope_interface.get_output_value('nrow')
            name = telescope_interface.get_output_value('name')
            tchip = telescope_interface.get_output_value('tchip')
            setpoint = telescope_interface.get_output_value('setpoint')
            # send output to Slack
            self.slack.send_message('CCD:')   
            self.slack.send_message('>Type: %s' %name)
            self.slack.send_message('>Pixels: %d x %d' %(nrow, ncol))
            self.slack.send_message('>Temperature: %.1f° C'%tchip)
            self.slack.send_message('>Set Point: %.1f° C'%setpoint)
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_moon(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_moon')
            # query telescope
            self.telescope.get_precipitation(telescope_interface)
            # assign values
            alt = telescope_interface.get_output_value('alt')
            phase = int(telescope_interface.get_output_value('phase')*100)
            # send output to Slack
            self.slack.send_message('Moon:')            
            self.slack.send_message('>Altitude: %.1f°' % alt)
            self.slack.send_message('>Phase: %d%%' % phase)         
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_focus(self, command, user):
        try:
            telescope_interface = TelescopeInterface('get_focus')
            # query telescope
            self.telescope.get_precipitation(telescope_interface)
            # assign values
            pos = telescope_interface.get_output_value('pos')
            # send output to Slack
            self.slack.send_message('Focus position is %d.' % pos)
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def set_focus(self, command, user):
        if not self.is_locked_by(user):
            self.slack.send_message('Please lock the telescope before calling this command.')
            return            
        try:
            telescope_interface = TelescopeInterface('set_focus')
            # assign values
            pos = int(command.group(1))
            telescope_interface.set_input_value('pos', pos)
            # create a command that applies the specified values
            self.telescope.set_focus(telescope_interface)
            # send output to Slack
            pos = telescope_interface.get_output_value('pos')
            self.slack.send_message('Focus position is %d.' % pos)
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def get_who(self, command, user):
        if not self.is_locked():
            self.slack.send_message('Telescope is not locked.')
            return        
        try:
            self.slack.send_message('Telescope is locked by %s.'%self.locked_by())
            return             
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def set_lock(self, command, user):
        if self.is_locked():
            self.slack.send_message('Telescope is locked by %s.'%self.locked_by())
            return 
        try:
            telescope_interface = TelescopeInterface('set_lock')
            # assign values
            user = user['id']
            telescope_interface.set_input_value('user', user)
            # query telescope
            self.telescope.set_lock(telescope_interface)
            # assign values
            user = telescope_interface.get_output_value('user')
            # send output to Slack
            self.slack.send_message(
                'Telescope is locked.')
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def unlock(self, command, user):
        if not self.is_locked():
            self.slack.send_message('Telescope is not locked.')
            return
        if not self.is_locked_by(user):
            self.slack.send_message('Telescope is locked by %s.'%self.locked_by())
            return       
        try:
            telescope_interface = TelescopeInterface('unlock')
            # assign values
            # query telescope
            self.telescope.unlock(telescope_interface)
            # send output to Slack
            self.slack.send_message(
                'Telescope is unlocked.')
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def clear_lock(self, command, user):    
        try:
            telescope_interface = TelescopeInterface('clear_lock')
            # assign values
            # query telescope
            self.telescope.clear_lock(telescope_interface)
            # send output to Slack
            self.slack.send_message(
                'Telescope is unlocked.')
        except Exception as e:
            self.handle_error(command.group(0), 'Exception (%s).'%e)

    def locked_by(self):
        try:
            telescope_interface = TelescopeInterface('get_lock')
            # query telescope
            self.telescope.get_lock(telescope_interface)
            # assign values
            _user = telescope_interface.get_output_value('user')
            self.logger.debug(
                'Telescope is locked by %s.' % _user)
            # assign values
            return self.slack.get_user_by_id(_user).get('name', _user)
        except Exception as e:
            self.logger.error('Could not get telescope lock info. Exception (%s).'%e)
        return 'unknown'

    def is_locked_by(self, user):
        try:
            telescope_interface = TelescopeInterface('get_lock')
            # query telescope
            self.telescope.get_lock(telescope_interface)
            # assign values
            _user = telescope_interface.get_output_value('user')
            self.logger.debug(
                'Telescope is locked by %s.' % _user)
            # assign values
            return _user == user['id']
        except Exception as e:
            self.logger.error('Could not get telescope lock info. Exception (%s).'%e)
        return False

    def is_locked(self):
        try:
            telescope_interface = TelescopeInterface('get_lock')
            # query telescope
            self.telescope.get_lock(telescope_interface)
            # assign values
            _user = telescope_interface.get_output_value('user')
            self.logger.debug(
                'Telescope is locked by %s.' % _user)
            # assign values
            return _user is not None
        except Exception as e:
            self.logger.error('Could not get telescope lock info. Exception (%s).'%e)
        return True

    # https://openweathermap.org/weather-conditions
    def get_weather(self, command, user):
        base_url = self.config.get('weatherbit', 'base_url')
        icon_base_url = self.config.get('weatherbit', 'icon_base_url')
        api_key = self.config.get('weatherbit', 'api_key')
        latitude = self.config.get('telescope', 'latitude')
        longitude = self.config.get('telescope', 'longitude')
        # user the OpenWeatherMap API
        url = '%scurrent?lat=%s&lon=%s&units=I&key=%s' % (base_url, latitude, longitude, api_key)
        try:
            r = requests.post(url)
            if r.ok:
                data = r.json()
                weather = data.get('data')[0]
                station = weather.get('city_name')
                clouds = weather.get('clouds')
                conditions = weather.get('weather').get('description')
                temp = weather.get('temp')
                wind_speed = weather.get('wind_spd')
                wind_direction = weather.get('wind_cdir')
                humidity = weather.get('rh')
                icon_url = icon_base_url + weather.get('weather').get('icon') + '.png'
                # send weather report to Slack
                self.slack.send_message(
                    "", [{"image_url": "%s" % icon_url, "title": "Current Weather:"}])
                self.slack.send_message('>Station: %s' % station)
                self.slack.send_message('>Conditions: %s' % conditions)
                self.slack.send_message(
                    '>Temperature: %.1f° F' % temp)
                self.slack.send_message('>Clouds: %0.1f%%' % clouds)
                self.slack.send_message('>Wind Speed: %.1f mph' % wind_speed)
                self.slack.send_message(
                    '>Wind Direction: %s' % wind_direction)
                self.slack.send_message(
                    '>Humidity: %.1f%%' % humidity)
            else:
                self.handle_error(command.group(0), 'Weatherbit API request (%s) failed (%d).' % (url, r.status_code))
        except Exception as e:
            self.logger.error(
                'Weatherbit API request (%s) failed.' % url)
            self.handle_error(command.group(0), 'Weatherbit API request (%s) failed. Exception (%s).' % (url, e))

    # # https://openweathermap.org/weather-conditions
    # def get_weather(self, command, user):
    #     base_url = self.config.get('openweathermap', 'base_url')
    #     icon_base_url = self.config.get('openweathermap', 'icon_base_url')
    #     api_key = self.config.get('openweathermap', 'api_key')
    #     latitude = self.config.get('telescope', 'latitude')
    #     longitude = self.config.get('telescope', 'longitude')
    #     # user the OpenWeatherMap API
    #     url = '%sweather?lat=%s&lon=%s&units=imperial&APPID=%s' % (
    #         base_url, latitude, longitude, api_key)
    #     try:
    #         r = requests.post(url)
    #     except Exception as e:
    #         self.logger.error(
    #             'OpenWeatherMap API request (%s) failed.' % url)
    #         self.handle_error(command.group(0), 'Exception (%s).'%e)
    #         return
    #     if r.ok:
    #         data = r.json()
    #         station = data.get('name', 'Unknown')
    #         clouds = data.get('clouds').get('all', 0)
    #         conditions = data.get('weather')[0].get('main', 'Unknown')
    #         temp = data.get('main').get('temp', 0)
    #         wind_speed = data.get('wind').get('speed', 0)
    #         wind_direction = data.get('wind').get('deg', 0)
    #         humidity = data.get('main').get('humidity', 0)
    #         icon_url = icon_base_url + \
    #             data.get('weather')[0].get('icon', '01d') + '.png'
    #         # send weather report to Slack
    #         self.slack.send_message(
    #             "", [{"image_url": "%s" % icon_url, "title": "Current Weather:"}])
    #         self.slack.send_message('>Station: %s' % station)
    #         self.slack.send_message('>Conditions: %s' % conditions)
    #         self.slack.send_message(
    #             '>Temperature: %.1f° F' % temp)
    #         self.slack.send_message('>Clouds: %0.1f%%' % clouds)
    #         self.slack.send_message('>Wind Speed: %.1f mph' % wind_speed)
    #         self.slack.send_message(
    #             '>Wind Direction: %.1f°' % wind_direction)
    #         self.slack.send_message(
    #             '>Humidity: %.1f%%' % humidity)
    #     else:
    #         self.logger.error(
    #             'OpenWeatherMap API request (%s) failed (%d).' % (url, r.status_code))
    #         self.handle_error(command.group(0), 'Exception (%s).'%e)

    # https://api.weatherbit.io/v2.0/
    def get_forecast(self, command, user):
        base_url = self.config.get('weatherbit', 'base_url')
        icon_base_url = self.config.get('weatherbit', 'icon_base_url')
        api_key = self.config.get('weatherbit', 'api_key')
        max_forecasts = int(self.config.get(
            'weatherbit', 'max_forecasts', 5))
        latitude = self.config.get('telescope', 'latitude')
        longitude = self.config.get('telescope', 'longitude')
        timezone = self.config.get('telescope', 'timezone', 'GMT')
        # user the weatherbit API
        url = '%sforecast/hourly?lat=%s&lon=%s&units=I&key=%s' % (base_url, latitude, longitude, api_key)
        try:
            r = requests.post(url)
            if r.ok:
                data = r.json()
                forecasts = data.get('data')
                station = data.get('city_name')
                self.slack.send_message('Weather Forecast:')
                self.slack.send_message('>Station: %s' % station)
                for forecast in forecasts[:max_forecasts]:
                    dt = datetime.datetime.strptime(forecast.get('timestamp_utc', '1970-01-01T00:00:00'), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
                    dt_local = dt.astimezone(pytz.timezone(timezone))
                    icon_url = icon_base_url + forecast.get('weather').get('icon') + '.png'
                    weather = forecast.get('weather').get('description')
                    clouds = int(forecast.get('clouds'))
                    dt_string = '%s (%s)' % (dt_local.strftime(
                        '%I:%M%p'), dt.strftime('%I:%M%p UTC'))
                    if clouds > 0:
                        self.slack.send_message(
                            "", [{"image_url": "%s" % icon_url, "title": "%s (%d%%) @ %s" % (weather, clouds, dt_string)}])
                    else:
                        self.slack.send_message(
                            "", [{"image_url": "%s" % icon_url, "title": "%s @ %s" % (weather, dt_string)}])
                    time.sleep(1)  # don't trigger the Slack bandwidth threshold
            else:
                self.handle_error(command.group(0), 'Weatherbit API request (%s) failed (%d).' % (url, r.status_code))
        except Exception as e:
            self.logger.error(
                'Weatherbit API request (%s) failed.' % url)
            self.handle_error(command.group(0), 'Weatherbit API request (%s) failed. Exception (%s).' % (url, e))

    # # https://openweathermap.org/forecast5
    # def get_forecast(self, command, user):
    #     base_url = self.config.get('openweathermap', 'base_url')
    #     icon_base_url = self.config.get('openweathermap', 'icon_base_url')
    #     api_key = self.config.get('openweathermap', 'api_key')
    #     max_forecasts = int(self.config.get(
    #         'openweathermap', 'max_forecasts', 5))
    #     latitude = self.config.get('telescope', 'latitude')
    #     longitude = self.config.get('telescope', 'longitude')
    #     timezone = self.config.get('telescope', 'timezone', 'GMT')
    #     # user the OpenWeatherMap API
    #     url = '%sforecast?lat=%s&lon=%s&units=imperial&APPID=%s' % (
    #         base_url, latitude, longitude, api_key)
    #     try:
    #         r = requests.post(url)
    #     except Exception as e:
    #         self.logger.error(
    #             'OpenWeatherMap API request (%s) failed.' % url)
    #         self.handle_error(command.group(0), e)
    #         return
    #     if r.ok:
    #         data = r.json()
    #         station = data.get('city').get('name', 'Unknown')
    #         forecasts = data.get('list')
    #         self.slack.send_message('Weather Forecast:')
    #         self.slack.send_message('>Station: %s' % station)
    #         for forecast in forecasts[:max_forecasts]:
    #             dt = datetime.datetime.utcfromtimestamp(
    #                 forecast.get('dt', time.time())).replace(tzinfo=pytz.utc)
    #             dt_local = dt.astimezone(pytz.timezone(timezone))
    #             icon_url = icon_base_url + \
    #                 forecast.get('weather')[0].get('icon', '01d') + '.png'
    #             weather = forecast.get('weather')[0].get('main', 'Unknown')
    #             clouds = int(forecast.get('clouds').get('all', 0))
    #             # self.slack.send_message('Date/Time: %s (%s)' % (dt_local.strftime(
    #             #    "%A, %B %d, %Y %I:%M%p"), dt.strftime("%A, %B %d, %Y %I:%M%p UTC")))
    #             dt_string = '%s (%s)' % (dt_local.strftime(
    #                 '%I:%M%p'), dt.strftime('%I:%M%p UTC'))
    #             #self.slack.send_message('Clouds: %0.1f%%' % clouds)
    #             if clouds > 0:
    #                 self.slack.send_message(
    #                     "", [{"image_url": "%s" % icon_url, "title": "%s (%d%%) @ %s" % (weather, clouds, dt_string)}])
    #             else:
    #                 self.slack.send_message(
    #                     "", [{"image_url": "%s" % icon_url, "title": "%s @ %s" % (weather, dt_string)}])
    #             time.sleep(1)  # don't trigger the Slack bandwidth threshold
    #     else:
    #         self.logger.error(
    #             'OpenWeatherMap API request (%s) failed (%d).' % (url, r.status_code))
    #         self.handle_error(command.group(0), e)

    def init_commands(self):
        self.commands = [

            {
                'regex': r'^\\find\s(.+)$',
                'function': self.find,
                'description': '`\\find <object>` finds <object> in the sky (add wildcard `*` to widen the search)',
                'hide': False
            },

            {
                'regex': r'^\\plot(\s[0-9]+)?$',
                'function': self.plot,
                'description': '`\\plot <object #>` shows if/when <object> is observable (run `\\find` first!)',
                'hide': False
            },

            {
                'regex': r'^\\focus$',
                'function': self.get_focus,
                'description': '`\\focus` shows the telescope focus position',
                'hide': False
            },

            {
                'regex': r'^\\focus\s([0-9]+)$',
                'function': self.set_focus,
                'description': '`\\focus <integer>` sets the telescope focus position to <integer>',
                'hide': False
            },

            {
                'regex': r'^\\forecast$',
                'function': self.get_forecast,
                'description': '`\\forecast` shows the hourly weather forecast',
                'hide': False
            },

            {
                'regex': r'^\\help$',
                'function': self.get_help,
                'description': '`\\help` shows this message',
                'hide': False
            },

            {
                'regex': r'^\\lock$',
                'function': self.set_lock,
                'description': '`\\lock` locks the telescope for use by you',
                'hide': False
            },

            {
                'regex': r'^\\unlock$',
                'function': self.unlock,
                'description': '`\\unlock` unlocks the telescope for use by others',
                'hide': False
            },

            {
                'regex': r'^\\clear$',
                'function': self.clear_lock,
                'description': '`\\clear` clears the telescope lock',
                'hide': True
            },

            {
                'regex': r'^\\who$',
                'function': self.get_who,
                'description': '`\\who` shows who has the telescope locked',
                'hide': False
            },

            {
                'regex': r'^\\weather$',
                'function': self.get_weather,
                'description': '`\\weather` shows the current weather conditions',
                'hide': False
            },

            {
                'regex': r'^\\clouds$',
                'function': self.get_clouds,
                'description': '`\\clouds` shows the current cloud cover',
                'hide': False
            },

            {
                'regex': r'^\\sun$',
                'function': self.get_sun,
                'description': '`\\sun` shows the sun altitude',
                'hide': False
            },

            {
                'regex': r'^\\moon$',
                'function': self.get_moon,
                'description': '`\\moon` shows the moon altitude and phase',
                'hide': False
            },

            {
                'regex': r'^\\where$',
                'function': self.get_where,
                'description': '`\\where` shows where the telescope is pointing',
                'hide': False
            },

            {
                'regex': r'^\\ccd$',
                'function': self.get_ccd,
                'description': '`\\ccd` shows CCD information',
                'hide': False
            }

        ]
