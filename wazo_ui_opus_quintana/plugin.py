# -*- coding: utf-8 -*-
# Copyright 2017-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+


import configparser
import requests 
import json

from flask import render_template
from flask_menu.classy import register_flaskview
from flask_babel import lazy_gettext as l_

from wazo_ui.helpers.plugin import create_blueprint
from wazo_ui.helpers.form import BaseForm
from wazo_ui.helpers.menu import menu_item
from wazo_ui.helpers.view import BaseIPBXHelperView

from wtforms.fields import SubmitField, StringField, SelectField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired, Length, NumberRange

opus = create_blueprint('opus', __name__)

config_file = '/etc/asterisk/codecs.d/opus_via_ui.conf'


class Plugin(object):

    def load(self, dependencies):
        core = dependencies['flask']

        OpusConfigurationView.service = OpusService()
        OpusConfigurationView.register(opus, route_base='/opus_configuration')
        register_flaskview(opus, OpusConfigurationView)

        core.register_blueprint(opus)


class OpusForm(BaseForm):
    name = StringField('Name', [InputRequired, Length(max=128)])
    packet_loss = IntegerField('Packet Loss', [NumberRange(min=0, max=100)])
    complexity = IntegerField('Complexity', [NumberRange(min=0, max=10)])
    signal = SelectField('Signal', choices=[('', 'Select...'), ('auto', 'Auto'), ('voice', 'Voice'), ('music', 'Music')])
    application = SelectField('Application', choices=[('', 'Select...'), ('voip', 'VOIP'), ('audio', 'Audio'), ('low_delay', 'Low Delay')])
    max_playback_rate = IntegerField('Max Playback Rate', [NumberRange(min=8000, max=48000)])
    max_bandwidth = SelectField('Max Bandwidth', choices=[('', 'Select...'), ('narrow','Narrow'), ('medium', 'Medium'), ('wide', 'Wide'), ('super_wide', 'Super Wide'), ('full', 'Full')])
    bitrate = IntegerField('Bite Rate', [NumberRange(min=500, max=512000)])
    cbr = SelectField('CBR', choices=[('', 'Select...'), ('no', 'No'), ('yes', 'Yes')])
    fec = SelectField('FEC', choices=[('', 'Select...'), ('no', 'No'), ('yes', 'Yes')])
    dtx = SelectField('DTX', choices=[('', 'Select...'), ('no', 'No'), ('yes', 'Yes')])
    submit = SubmitField('Submit')


class OpusConfigurationView(BaseIPBXHelperView):
    form = OpusForm
    resource = 'opus'

    @menu_item('.ipbx.advanced.opus', l_('Opus'), icon="compress")
    def index(self):
        return super().index()


class OpusService(object):

    def list(self):
        return {'items': self._read_sections()}

    def create(self, resource):
        self._create_section(resource)
        self._reload_asterisk()
        return True

    def delete(self, section):
        self._remove_section(section)
        self._reload_asterisk()

    def get(self, section):
        return self._get_section(section)

    def update(self, resource):
        self._update_section(resource)
        self._reload_asterisk()

    def _read_sections(self):
        config = configparser.ConfigParser()
        config.read(config_file)
        return [dict(config.items(s), name=s, id=s) for s in config.sections()]

    def _create_section(self, resource):
        config = configparser.ConfigParser()
        section = resource['name']
        config.add_section(section)
        config.set(section, 'type', 'opus')
        config.set(section, 'name', section)
        options = [
            'packet_loss',
            'complexity',
            'signal',
            'application',
            'max_playback_rate',
            'max_bandwidth',
            'bitrate',
            'cbr',
            'fec',
            'dtx'
        ]
        for option in options:
            self._add_option(config, section, option, resource)

        with open(config_file, 'a+') as configfile:
            config.write(configfile)

    def _add_option(self, config, section, name, resource):
        if resource.get(name):
            config.set(section, name, str(resource.get(name)))

    def _remove_section(self, section):
        config = configparser.ConfigParser()
        config.read(config_file)
        config.remove_section(section)

        with open(config_file, 'w+') as configfile:
            config.write(configfile)

    def _get_section(self, section):
        config = configparser.ConfigParser()
        config.read(config_file)
        return config[section]

    def _update_section(self, resource):
        config = configparser.ConfigParser()
        config.read(config_file)
        section = resource['name']
        config.set(section, 'type', 'opus')
        for option in resource:
            if option is not 'uuid':
                if resource[option] is not None:
                    config[section][option] = str(resource[option])

        with open(config_file, 'w+') as configfile:
            config.write(configfile)

    def _reload_asterisk(self):
        uri = 'http://localhost:8668/services'
        headers = {'content-type': 'application/json'}
        services = [
            {'asterisk': 'reload'}
        ]
        for service in services:
            req = requests.post(uri, data=json.dumps(service), headers=headers)
