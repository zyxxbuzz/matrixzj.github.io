#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import os
import json
import requests

raw_data_file = sys.argv[1]

class GenerateKeyCapPage(object):
    
    def __init__(self, keycap_raw_info_file):

        self.info_dict = {"price":{}}
        self.kits_list_index = []

        self.parse_keycap_raw_info(keycap_raw_info_file)
        self.retrieve_exchange_rate()
#        self.info_dict['rate'] = 7.16

        self.profile_path = "%s-keycaps" % self.info_dict['keycapstype'].lower()     
        self.keycap_filename = "%s.md" % self.info_dict['name'].replace(" ","-")
        self.keycap_filename_with_path = os.path.join("docs", self.profile_path, self.keycap_filename)

        self.keycap_asset_path = os.path.join(os.getcwd(), 'assets/images/', self.profile_path, self.info_dict['name'].lower().replace(" ",""))
        print self.keycap_asset_path
        self.keycap_asset_kits_path = os.path.join(os.getcwd(), 'assets/images/', self.profile_path, self.info_dict['name'].lower().replace(" ",""), "kits_pics")
        self.keycap_asset_render_path = os.path.join(os.getcwd(), 'assets/images/', self.profile_path, self.info_dict['name'].lower().replace(" ",""), "rendering_pics")

        self.parse_price_info()
        self.cal_nav_order()

        self.keycap_page_header = "---\n"
        self.generate_keycap_page_header()
        print self.keycap_page_header

        self.keycap_page_price = "## Price  \n"
        self.generate_keycap_page_price()
        print self.keycap_page_price

        self.keycap_page_kit = "## Kits  \n"
        self.generate_keycap_page_kit()
        print self.keycap_page_kit

        self.keycap_page_info = "## Info  \n"
        self.generate_keycap_page_info()
        print self.keycap_page_info

        if os.path.isdir(self.keycap_asset_render_path):
            self.keycap_page_picture = "## Pictures  \n"
            self.generate_keycap_page_picture()
            print self.keycap_page_picture

        keycap_write_to_file = raw_input("Generate Page File? ")
        if keycap_write_to_file.lower().strip() == "y":
            fd_keycap_filename_with_path = open(self.keycap_filename_with_path, "w+")
            fd_keycap_filename_with_path.write(self.keycap_page_header)
            fd_keycap_filename_with_path.write(self.keycap_page_price)
            fd_keycap_filename_with_path.write(self.keycap_page_kit)
            fd_keycap_filename_with_path.write(self.keycap_page_info)
            if os.path.isdir(self.keycap_asset_render_path):
                fd_keycap_filename_with_path.write(self.keycap_page_picture)
            fd_keycap_filename_with_path.close()
            print "%s was generated!" % self.keycap_filename_with_path
            if self.info_dict['cname']:
                print "index entry: * [%s %s](docs/%s-keycaps/%s/)" % (self.info_dict['name'], self.info_dict['cname'], self.info_dict['keycapstype'].lower(), self.info_dict['name'].replace(' ','-'))
            else:
                print "index entry: * [%s](docs/%s-keycaps/%s/)" % (self.info_dict['name'], self.info_dict['keycapstype'].lower(), self.info_dict['name'].replace(' ','-'))

        else:
            sys.exit(0)
	
    def parse_keycap_raw_info(self, keycap_info_file):
        lines = open(keycap_info_file, 'r').readlines()
        self.kits_list_index = [ i.split(":")[0] for i in lines if '|' in i ]  
        for line in lines:
            if len(line) <= 1:
                continue
            else:
                if "|" in line:
                    self.info_dict["price"][line.split(":")[0]] = line.split(":")[1].strip().split("|")
                elif "link" in line:
                    self.info_dict["link"] = line.replace("link:","").replace("'","").strip()
                else:
                    self.info_dict[line.split(":")[0]] = line.split(":")[1].replace("'","").strip()

    def retrieve_exchange_rate(self):
        api_base_url = "http://www.apilayer.net/api/historical?format=1"
        
        f_api_file = open('exchangerate_apikey', 'r')
        exchange_rate_api_key = "access_key=" + f_api_file.read().strip()
        f_api_file.close()
        
        if len(self.info_dict['time'].split('-')) == 3:
            date = "date=%s" % self.info_dict['time']
        elif len(self.info_dict['time'].split('-')) == 2:
            date = "date=%s-01" % self.info_dict['time']
        else:
            print "Something wrong with GB Time!"
            sys.exit(1)

        if self.info_dict['currencyunit'] == 'USD':
            currency_checked = "currencies=%s,CNY" % self.info_dict['currencyunit']
            api_url = "%s&%s&%s&%s" % (api_base_url, exchange_rate_api_key, currency_checked, date)
            exchange_rate_result = requests.get(api_url)
            currency_key = "%sCNY" % self.info_dict['currencyunit']
            exchange_rate = exchange_rate_result.json()['quotes'][currency_key]
        else:
            currency_checked = "currencies=%s,CNY,%s" % ("USD", self.info_dict['currencyunit'])
            api_url = "%s&%s&%s&%s" % (api_base_url, exchange_rate_api_key, currency_checked, date)
            exchange_rate_result = requests.get(api_url)
            currency_key_USDtoCNY = "USDCNY"
            currency_key_USDtoDest = "USD%s" % self.info_dict['currencyunit']
            exchange_rate = float(exchange_rate_result.json()['quotes'][currency_key_USDtoCNY]) / float(exchange_rate_result.json()['quotes'][currency_key_USDtoDest])

        self.info_dict['rate'] = "%.2f" % float(exchange_rate)

    def parse_price_info(self):
        for kit in self.info_dict['price']:
            # Price in USD and CNY is Unknown
            if len(self.info_dict['price'][kit][0]) == 0 and \
                len(self.info_dict['price'][kit][1]) == 0:
                self.info_dict['price'][kit][0] = 'Unknown'
                self.info_dict['price'][kit][1] = 'Unknown'
            # Price in USD is provided and CNY is Unkonwn
            elif len(self.info_dict['price'][kit][0]) > 0 and \
                len(self.info_dict['price'][kit][1]) == 0:
                self.info_dict['price'][kit][0] = float(self.info_dict['price'][kit][0])
                self.info_dict['price'][kit][1] = float(self.info_dict['price'][kit][0]) * float(self.info_dict['rate'])
            # Price in CYN is provided and USD is Unkonwn
            elif len(self.info_dict['price'][kit][0]) == 0 and \
                len(self.info_dict['price'][kit][1]) > 0:
                self.info_dict['price'][kit][0] = float(self.info_dict['price'][kit][1]) / float(self.info_dict['rate'])
                self.info_dict['price'][kit][1] = float(self.info_dict['price'][kit][1])
            else:
                self.info_dict['price'][kit][0] = float(self.info_dict['price'][kit][0])
                self.info_dict['price'][kit][1] = float(self.info_dict['price'][kit][1])

            if len(self.info_dict['price'][kit][2]) == 0:
                self.info_dict['price'][kit][2] = 'Unkonwn'
            else:
                self.info_dict['price'][kit][2] = int(self.info_dict['price'][kit][2])

            price_table_format = "|[%s](#%s)|"
            price_kit_format = ""
            i = 0
            while i < len(self.info_dict['price'][kit]):
                if isinstance(self.info_dict['price'][kit][i], float):
                    item_table_format = "%.2f"
                if isinstance(self.info_dict['price'][kit][i], int):
                    item_table_format = "%d"
                if isinstance(self.info_dict['price'][kit][i], str):
                    item_table_format = "%s"
                price_table_format = price_table_format + item_table_format + "|"

                if i == 0:
                    price_kit_format = "%s**Price(%s):** %s    " % (price_kit_format, self.info_dict['platform'], item_table_format)
                if i == 1:
                    price_kit_format = "%s**Price(CNY):** %s    " % (price_kit_format, item_table_format)
                if i == 2:
                    price_kit_format = "%s**Quantity:** %s  " % (price_kit_format, item_table_format)

                i += 1

            self.info_dict['price'][kit].append(price_table_format)
            self.info_dict['price'][kit].append(price_kit_format)

    def cal_nav_order(self):
        fd_index = open("index.md", "r")
        index_lines = fd_index.readlines()
        fd_index.close()

        profile_list = ['SA', 'GMK', '---']
        profile_current = self.info_dict['keycapstype']

        if os.path.isfile(self.keycap_filename_with_path):
            keycap_page_fd = open(self.keycap_filename_with_path, "r")
            keycap_page_lines = keycap_page_fd.readlines()
            for line in keycap_page_lines:
                if "nav_order" in line:
                    self.info_dict['nav_order'] = int(line.split(":")[1].strip())
        else:
            # Generate Profile Part
            current_profile_index = profile_list.index(profile_current)
            next_profile_index = current_profile_index + 1
            current_profile_marker = "## %s KeyCaps\n" % profile_list[current_profile_index]
            if next_profile_index == len(profile_list) - 1:
                next_profile_marker = "%s\n" % profile_list[-1]
            else:
                next_profile_marker = "## %s KeyCaps\n" % profile_list[next_profile_index]
            current_profile_marker_index = index_lines.index(current_profile_marker)
            next_profile_marker_index = index_lines.index(next_profile_marker)
            if next_profile_index == len(profile_list) - 1: 
                current_profile_list_to_end = index_lines[current_profile_marker_index:]
                next_profile_marker_index = current_profile_list_to_end.index(next_profile_marker)
                current_profile_list = current_profile_list_to_end[:next_profile_marker_index]
            else:
                current_profile_list = index_lines[current_profile_marker_index:next_profile_marker_index]

            # Generate Year Part
            current_year = self.info_dict['time'].split("-")[0]
            previous_year = int(current_year) - 1
            current_year_marker = "### %s\n" % current_year
            if previous_year < 2013:
                previous_year_marker = "---\n"
            else:
                previous_year_marker = "### %d\n" % previous_year
            current_year_marker_index = current_profile_list.index(current_year_marker)
            previous_year_marker_index = current_profile_list.index(previous_year_marker)
            
            currrent_items_count =  len(current_profile_list[current_year_marker_index:previous_year_marker_index]) - 2
            
            nav_order = (2050 - int(current_year)) * 10000 + (1000 - currrent_items_count * 5) - 5
            
            self.info_dict['nav_order'] = nav_order

    def generate_keycap_page_header(self):
    	self.keycap_page_header += "title: %s %s\n" % (self.info_dict['name'], self.info_dict['cname'])
    	self.keycap_page_header += "layout: default\n"
    	self.keycap_page_header += "icon: fa-keyboard-o\n"
    	self.keycap_page_header += "parent: %s Keycaps\n" % self.info_dict['keycapstype']
    	self.keycap_page_header += "nav_order: %d\n" % self.info_dict['nav_order']
    	self.keycap_page_header += "---\n"
    	self.keycap_page_header += "\n"
    	self.keycap_page_header += "# %s %s\n" % (self.info_dict['name'], self.info_dict['cname'])
    	self.keycap_page_header += "\n"
    	self.keycap_page_header += "ref link: [%s %s GB Link](%s)  \n" % (self.info_dict['name'], self.info_dict['platform'], self.info_dict['link'])
    	self.keycap_page_header += "\n"
    	self.keycap_page_header += "* [Price](#price)  \n"
    	self.keycap_page_header += "* [Kits](#kits)  \n"
    	self.keycap_page_header += "* [Info](#info)  \n"
    	self.keycap_page_header += "* [Pictures](#pictures)  \n"
    	self.keycap_page_header += "\n\n"

    def generate_keycap_page_price(self):
        self.keycap_page_price += "NOTE: %s to CNY exchange rate is %.2f\n\n" % (self.info_dict['currencyunit'], float(self.info_dict['rate']))
        self.keycap_page_price += "| Name          | Price(%s)    |  Price(CNY) | Quantity |\n| ------------- | ------------ |  ---------- | -------- |\n" % (self.info_dict['platform'])
        for kit in self.kits_list_index:
            self.keycap_page_price += self.info_dict['price'][kit][3] % (kit, kit.lower().replace(" ", "-").replace(".", ""), self.info_dict['price'][kit][0], self.info_dict['price'][kit][1], self.info_dict['price'][kit][2])
            self.keycap_page_price += "\n"
        self.keycap_page_price += "\n"

        if os.path.isdir(self.keycap_asset_path):
            price_files = [f for f in os.listdir(self.keycap_asset_path) if os.path.isfile(os.path.join(self.keycap_asset_path, f)) and 'price' in f]
            for price_file in price_files:
                price_file_path = os.path.join(self.keycap_asset_path, price_file)
                self.keycap_page_price += '<img src="{{ \'%s\' | relative_url }}" alt="price" class="image featured">' % os.path.relpath(price_file_path, os.getcwd())
                self.keycap_page_price += "\n"
    
            progress_files = [f for f in os.listdir(self.keycap_asset_path) if os.path.isfile(os.path.join(self.keycap_asset_path, f)) and 'progress' in f]
            for progress_file in progress_files:
                progress_file_path = os.path.join(self.keycap_asset_path, progress_file)
                self.keycap_page_price += '<img src="{{ \'%s\' | relative_url }}" alt="progress" class="image featured">' % os.path.relpath(progress_file_path, os.getcwd())
                self.keycap_page_price += "\n"

        self.keycap_page_price += "\n"

    def generate_keycap_page_kit(self):
        for kit in self.kits_list_index:
            self.keycap_page_kit += "### %s  \n" % kit
            self.keycap_page_kit += self.info_dict['price'][kit][4] % (self.info_dict['price'][kit][0], self.info_dict['price'][kit][1], self.info_dict['price'][kit][2])
            self.keycap_page_kit += "\n"
            kit_file_jpg = "%s.jpg" % kit.lower().replace(" ", "-")
            kit_file_png = "%s.png" % kit.lower().replace(" ", "-")
            if os.path.isfile(os.path.join(self.keycap_asset_kits_path, kit_file_jpg)):
                self.keycap_page_kit += '<img src="{{ \'%s\' | relative_url }}" alt="%s" class="image featured">' % (os.path.relpath(os.path.join(self.keycap_asset_kits_path, kit_file_jpg), os.getcwd()), kit.lower().replace(" ", "-"))
                self.keycap_page_kit += "\n\n"

            if os.path.isfile(os.path.join(self.keycap_asset_kits_path, kit_file_png)):
                self.keycap_page_kit += '<img src="{{ \'%s\' | relative_url }}" alt="%s" class="image featured">' % (os.path.relpath(os.path.join(self.keycap_asset_kits_path, kit_file_png), os.getcwd()), kit.lower().replace(" ", "-"))
                self.keycap_page_kit += "\n\n"

        self.keycap_page_kit += "\n"

    def generate_keycap_page_info(self):
        self.keycap_page_info += "* Designer: %s  \n* Profile: %s %s  \n" % (self.info_dict['designer'], self.info_dict['keycapstype'], self.info_dict['profile'])
        self.keycap_page_info += "* GB Time: %s  \n" % self.info_dict['time']
        if "SA" in self.info_dict['keycapstype']:
            if "/" not in self.info_dict['colorcodes']:
                self.keycap_page_info += "* Color Codes: %s  \n\n" % self.info_dict['colorcodes']
            else:
                self.keycap_page_info += "* Color Codes:  \n\n"
                color_files = [f for f in os.listdir(self.keycap_asset_path) if os.path.isfile(os.path.join(self.keycap_asset_path, f)) and 'color' in f]
                for color_file in color_files:
                    color_file_path = os.path.join(self.keycap_asset_path, color_file)
                    self.keycap_page_info += '<img src="{{ \'%s\' | relative_url }}" alt="color" class="image featured">\n' % os.path.relpath(color_file_path, os.getcwd())
                self.keycap_page_info += "<table style=\"width:100%\">\n  <tr>\n    <th>ColorCodes</th>\n    <th>Sample</th>\n  </tr>\n"
                for color in self.info_dict['colorcodes'].split('/'):
                    color_file_png = "assets/images/sa-keycaps/SP_ColorCodes/abs/SP_Abs_ColorCodes_%s.png" % color
                    self.keycap_page_info += "  <tr>\n    <th>%s</th>\n    <th><img src=\"{{ '%s' | relative_url }}\" alt=\"Color_%s\" height=\"75\" width=\"170\"></th>\n  </tr>\n" % (color, color_file_png, color)
                self.keycap_page_info += "</table>\n\n"
        elif "GMK" in self.info_dict['keycapstype']: 
            self.keycap_page_info += "* Color Codes:  \n\n"
            color_files = [f for f in os.listdir(self.keycap_asset_path) if os.path.isfile(os.path.join(self.keycap_asset_path, f)) and 'color' in f]
            for color_file in color_files:
                color_file_path = os.path.join(self.keycap_asset_path, color_file)
                self.keycap_page_info += '<img src="{{ \'%s\' | relative_url }}" alt="color" class="image featured">\n' % os.path.relpath(color_file_path, os.getcwd())
            self.keycap_page_info += "| |Base Color     | Legend Color\n| :-------------: | :-------------: | :------------:\n|Alpha||\n"
        self.keycap_page_info += "\n"

    def generate_keycap_page_picture(self):
        picture_files = [f for f in os.listdir(self.keycap_asset_render_path) if os.path.isfile(os.path.join(self.keycap_asset_render_path, f))]
        for pic in picture_files:
            pic_file_path = os.path.join(self.keycap_asset_render_path, pic)
            pic_file_relpath = os.path.relpath(pic_file_path, os.getcwd())
            self.keycap_page_picture += '<img src="{{ \'%s\' | relative_url }}" alt="%s" class="image featured">\n' % (pic_file_relpath, pic)

GenerateKeyCapPage(raw_data_file)
