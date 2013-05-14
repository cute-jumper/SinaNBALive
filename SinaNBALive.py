#! /usr/bin/env python
#-*- coding: utf-8 -*-
# Author: qjp
# Date: <2013-05-14 Tue>

import sys
import urllib2
import webbrowser
from datetime import datetime
from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator

nbalive_url = 'http://nba.sports.sina.com.cn/js/2007live.js'
video_live_url = 'http://live.video.sina.com.cn/room/nba'
text_live_url = 'http://sports.sina.com.cn/nba/live.html?id='

game_info_fields = ['visiting_en',
                    'visiting_zh',
                    'home_en',
                    'home_zh',
                    'play_date',
                    'play_time',
                    'visiting_score',
                    'home_score',
                    'game_id',
                    'status',
                    'tv_name_zh',
                    'game_report',
                    'has_video_live',
                    ]

game_status_zh = {'In-Progress': '进行中',
                  'Pre-Game': '未赛',
                  'Pg': '未赛',
                  'Postponed': '延期',
                  'Cancelled': '取消',
                  'Final': '完场'
                  }

class Game(object):
    def __init__(self, game_info):
        self.game_info = game_info
        for name, value in zip(game_info_fields, game_info):
            setattr(self, name, value)
            
    def get_game_status_zh(self):
        return game_status_zh[self.status]

def get_today_games():
    js = urllib2.urlopen(nbalive_url).read()
    py = js.replace('var ', '').replace('show_today();', '').decode('gbk')
    exec py in globals(), locals()
    return map(lambda x: Game(x.split(',')), today.split('|')[:-1])

class PreferenceDialog(Gtk.Dialog):
    def __init__(self, initval):
        Gtk.Dialog.__init__(self, 'Preferences', None, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK,
                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_default_size(150, 100)
        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(Gtk.Label('Refresh Interval:'), False, False, 0)
        adj = Gtk.Adjustment(initval, 1, 100, 1)
        self.spinbutton = Gtk.SpinButton()
        self.spinbutton.set_adjustment(adj)
        hbox.pack_start(self.spinbutton, False, False, 0)
        panel = self.get_content_area()
        panel.add(hbox)
        self.show_all()
    def get_new_value(self):
        return self.spinbutton.get_value_as_int()
    
class GameMenuItem(object):
    def __init__(self, game):
        self.game_title = Gtk.MenuItem()
        self.game_scores = Gtk.MenuItem()
        self.sep = Gtk.SeparatorMenuItem()
        self.game_scores.set_sensitive(False)
        self.game_title.connect('activate', self.open_game_url)
        self.game_title.show()
        self.game_scores.show()
        self.sep.show()
        # Dynamic part
        self.set_game_menu_items(game)
        
    def set_game_title(self):
        self.game_title.set_label('%s vs %s (%s)'
                                  %(self.game.visiting_zh,
                                    self.game.home_zh,
                                    self.game.get_game_status_zh()))
    
    def set_game_scores(self):
        self.game_scores.set_label('%s : %s'
                                   %(self.game.visiting_score,
                                     self.game.home_score))
    
    def get_game_menu_items(self):
        return self.sep, self.game_title, self.game_scores
    
    def set_game_menu_items(self, game):
        self.game = game
        self.set_game_title()
        self.set_game_scores()

    def open_game_url(self, widget):
        status = self.game.status
        if status == 'In-Progress' and self.game.has_video_live:
            webbrowser.open(video_live_url)
        elif status == 'Final' and len(self.game.game_report) > 1:
            webbrowser.open(self.game.game_report)
        else:
            webbrowser.open(text_live_url + game.game_id)
            
def get_today_string():
    today = datetime.today()
    return '%d-%2d-%2d' %(today.year, today.month, today.day)

class NBALiveIndicator(object):
    def __init__(self):
        self.refresh_interval = 2
        self.today_string = '1990-00-00'
        self.ind = appindicator.Indicator.new(
            "example-simple-client",
            "indicator-messages",
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon("indicator-messages-new")
        self.game_menu_item_list = []
        self.menu = Gtk.Menu()
        self.static_menu_item_setup()
        self.ind.set_menu(self.menu)

    def static_menu_item_setup(self):
        self.quit_item = Gtk.MenuItem("Quit")
        self.quit_item.connect('activate', Gtk.main_quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)
        self.preference_item = Gtk.MenuItem("Preferences...")
        self.preference_item.connect('activate', self.show_preference)
        self.preference_item.show()
        self.menu.append(self.preference_item)
        
    def dynamic_menu_item_setup(self):
        for game in self.games:
            item = GameMenuItem(game)
            self.game_menu_item_list.append(item)
            for i in item.get_game_menu_items():
                self.menu.append(i)

    def dynamic_menu_item_update(self):
        for game, item in zip(self.games, self.game_menu_item_list):
            item.set_game_menu_items(game)        
    
    def show_preference(self,widget):
        dialog = PreferenceDialog(self.refresh_interval)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.refresh_interval = dialog.get_new_value()
            print 'New refresh interval: %ds' %self.refresh_interval
        dialog.destroy()
        
    def main(self):
        self.do_update()
        GLib.timeout_add_seconds(self.refresh_interval, self.do_update)
        Gtk.main()
        
    def do_update(self):
        print '\033[0;32mupdate...\033[0m'
        # self.games = get_today_games()
        # if get_today_string() > self.today_string:
        #     for i in self.game_menu_item_list:
        #         for j in i.get_game_menu_items():
        #             self.menu.remove(j)
        #     self.dynamic_menu_item_setup()
        # else:
        #     self.dynamic_menu_item_update()
    
if __name__ == '__main__':
    NBALiveIndicator().main()
