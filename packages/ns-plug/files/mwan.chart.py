# -*- coding: utf-8 -*-
# Description: mwan3 python plugin
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import os

from bases.FrameworkServices.SimpleService import SimpleService

priority = 90000
state_dir = "/var/run/mwan3track/"

ORDER = [
    'score',
]

charts = {
    'score': {
        'options': [None, 'WAN status', 'score', 'mwan tracking', 'mwan.score', 'line'],
        'lines': []
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        for dir in os.listdir(state_dir):
            charts['score']['lines'].append([dir])
        self.definitions = charts

    @staticmethod
    def check():
        return os.path.isdir(state_dir)

    def get_data(self):
        data = dict()

        for dir in os.listdir(state_dir):
            file = state_dir + dir + "/SCORE"
            with open(file) as f:
                data[dir] = int(f.read().strip()) + 1

        return data
