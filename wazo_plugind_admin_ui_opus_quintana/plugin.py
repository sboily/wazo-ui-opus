# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+


import ConfigParser

from flask import render_template
from flask_menu.classy import register_flaskview
from flask_menu.classy import classy_menu_item

from wazo_admin_ui.helpers.plugin import create_blueprint
from wazo_admin_ui.helpers.classful import BaseView
from wazo_admin_ui.helpers.form import BaseForm

from wtforms.fields import SubmitField, StringField, SelectField, BooleanField
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
    packet_loss = StringField('Packet Loss', [NumberRange(min=0, max=100),])
    complexity = StringField('Complexity', [NumberRange(min=0, max=10),]) # 0 - 10
    signal = SelectField('Signal', choices=[('auto', 'Auto'), ('voice', 'Voice'), ('music', 'Music')])
    application = SelectField('Application', choices=[('voip', 'VOIP'), ('audio', 'Audio'), ('low_delay', 'Low Delay')])
    max_playback_rate = StringField('Max Playback Rate', [NumberRange(min=800, max=48000),])
    bitrate = StringField('Bite Rate', [NumberRange(min=500, max=512000),])
    cbr = BooleanField('CBR')
    fec = BooleanField('FEC')
    dtx = BooleanField('DTX')
    submit = SubmitField('Submit')


class OpusConfigurationView(BaseView):

    form = OpusForm
    resource = 'opus'

    @classy_menu_item('.advanced.opus', 'Opus', order=9, icon="compress")
    def index(self):
        return super(OpusConfigurationView, self).index()


class OpusService(object):

    def list(self):
        self._read_sections()
        return {'items': []}

    def create(self, resource):
        print(resource)
        self._create_section(resource)
        return True

    def _read_sections(self):
        config = ConfigParser.RawConfigParser()
        print(config.read(config_file))

    def _create_section(self, resource):
        config = ConfigParser.RawConfigParser()
        section = resource['name']
        config.add_section(section)
        config.set(section, 'type', 'opus')

        with open(config_file, 'wb') as configfile:
            config.write(configfile)
