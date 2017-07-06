import xbmc,xbmcaddon,xbmcvfs,xbmcgui,xbmcplugin
import subprocess
from subprocess import Popen
from xbmcswift2 import Plugin
import StringIO
import os
import re
import requests
import sys
import json
import urllib2
import time
import ast


plugin = Plugin()
dialog = xbmcgui.Dialog()

try:
    tvh_url_get = xbmcaddon.Addon('pvr.hts').getSetting("host")
    if tvh_url_get:
        tvh_url_set = xbmcaddon.Addon().setSetting(id='tvhurl', value=tvh_url_get)
    else:
        tvh_url_set = xbmcaddon.Addon().setSetting(id='tvhurl', value="127.0.0.1")
    tvh_port_get = xbmcaddon.Addon('pvr.hts').getSetting("http_port")
    if tvh_port_get:
        tvh_port_set = xbmcaddon.Addon().setSetting(id='tvhport', value=tvh_port_get)
    else:
        tvh_port_set = xbmcaddon.Addon().setSetting(id='tvhport', value="9981")
except:
    pass

tvh_url = xbmcaddon.Addon().getSetting('tvhurl')
tvh_port = xbmcaddon.Addon().getSetting('tvhport')
truefalse = ['true', 'false']
enabledisable = ['Enabled', 'Disabled']

def get_icon_path(icon_name):
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")

def find_param(d, param_id):
    for param in d['entries'][0]['params']:
        if param['id'] == param_id:
            try:
                value = param['value']
            except:
                value = ""
            break
        else:
            value = "NO PARAMATER FOUND"
    return value

def find_param_dict(d, param_id, param_id2):
    param_value = find_param(d, param_id)
    for param in d['entries'][0]['params']:
        if param['id'] == param_id:
            param_dict = param[param_id2]
            break
        else:
            param_dict = "NO PARAMATER FOUND"
    param_key = []
    param_val = []
    for param_k in param_dict:
        param_key.append(param_k['key'])
    for param_v in param_dict:
        param_val.append(param_v['val'])
    try:
        param_index = param_key.index(param_value)
        return (param_val[param_index], param_key, param_val)
    except:
        return (param_value, param_key, param_val)

def find_param_list(d, param_id, param_id2):
    param_value = find_param(d, param_id)
    for param in d['entries'][0]['params']:
        if param['id'] == param_id:
            param_list = param[param_id2]
            break
        else:
            param_list = "NO PARAMATER FOUND"
    return (param_value, param_list)

def find_list(d, param_id, param_id2):
    for param in d['entries'][0]['params']:
        if param['id'] == param_id:
            param_list = param[param_id2]
            break
        else:
            param_list = []
    return param_list

def find_prop(d, param_id):
    for param in d['props']:
        if param['id'] == param_id:
            try:
                value = param['default']
            except:
                value = ""
            break
        else:
            value = "NO PARAMATER FOUND"
    return value

def find_props_dict(d, param_id, param_id2):
    for param in d['props']:
        if param['id'] == param_id:
            param_dict = param[param_id2]
            break
        else:
            param_dict = "NO PARAMATER FOUND"
    param_key = []
    param_val = []
    for param_k in param_dict:
        param_key.append(param_k['key'])
    for param_v in param_dict:
        param_val.append(param_v['val'])
    return (param_key, param_val)

def dvr_param_load(dvr_uuid_sel):
    dvr_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + dvr_uuid_sel
    dvr_load = requests.get(dvr_url).json()
    dvr_name = dvr_load['entries'][0]['text']
    dvr_enabled = find_param(dvr_load, 'enabled')
    dvr_keep, dvr_keep_key, dvr_keep_val = find_param_dict(dvr_load, 'removal-days', 'enum')
    dvr_profile_value = find_param(dvr_load, 'profile')
    dvr_profile_dict_url = 'http://' + tvh_url + ':' + tvh_port + '/api/profile/list'
    dvr_profile_dict_load = requests.get(dvr_profile_dict_url).json()
    dvr_profile_dict = dvr_profile_dict_load['entries']
    dvr_profile_key = []
    dvr_profile_val = []
    for dvr_k in dvr_profile_dict:
        dvr_profile_key.append(dvr_k['key'])
    for dvr_v in dvr_profile_dict:
        dvr_profile_val.append(dvr_v['val'])
    dvr_profile_index = dvr_profile_key.index(dvr_profile_value)
    dvr_profile = dvr_profile_val[dvr_profile_index]
    dvr_clone = find_param(dvr_load, 'clone')
    dvr_storage = find_param(dvr_load, 'storage')
    xbmcaddon.Addon().setSetting(id='dvrstorage', value=dvr_storage)
    dvr_info_list = ["Name: " + str(dvr_name), "Enabled: " + str(dvr_enabled), "Storage: " + str(dvr_storage), "Days to Keep Recordings: " + str(dvr_keep), "Duplicate Recording Timer If Error Occurs: " + str(dvr_clone), "Stream Profile: " + str(dvr_profile), "Recording File and Folder options"]
    dvr_param_edit(dvr_uuid_sel, dvr_info_list, dvr_keep_key, dvr_keep_val, dvr_name, dvr_enabled, dvr_storage, dvr_keep, dvr_clone, dvr_profile_key, dvr_profile_val, dvr_profile)

def dvr_param_edit(dvr_uuid_sel, dvr_info_list, dvr_keep_key, dvr_keep_val, dvr_name, dvr_enabled, dvr_storage, dvr_keep, dvr_clone, dvr_profile_key, dvr_profile_val, dvr_profile):
    sel_param = dialog.select('DVR Configuration - Select parameter to edit', list=dvr_info_list)
    if sel_param < 0:
        dvr()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_dvr_name = dialog.input('Edit the DVR profile name', defaultt=dvr_name,type=xbmcgui.INPUT_ALPHANUM)
            param_update = '"name":"' + sel_dvr_name + '"'
        if sel_param == 1:
            sel_enabled = dialog.select('Enable or disable the DVR profile', list=enabledisable)
            if sel_enabled >= 0:
                dvr_enabled = truefalse[sel_enabled]
                param_update = '"enabled":' + dvr_enabled
        if sel_param == 2:
            if tvh_url == "127.0.0.1":
                plugin.open_settings()
                dvr_storage_update_tvh = xbmcaddon.Addon().getSetting('dvrstorage')
                param_update = '"storage":"' + str(dvr_storage_update_tvh) + '"'
            else:
                dialog.ok('Tvheadend backend on network location', 'Your Tvheadend backend is located on a network. Currently Kodi cannot browse network folders.', 'Please enter the DVR recording location manually.')
                dvr_storage_update_tvh = dialog.input('Edit the DVR recording location', defaultt=dvr_storage,type=xbmcgui.INPUT_ALPHANUM)
                xbmcaddon.Addon().setSetting(id='dvrstorage', value=dvr_storage_update_tvh)
                param_update = '"storage":"' + str(dvr_storage_update_tvh) + '"'
        if sel_param == 3:
            sel_enabled = dialog.select('Select the number of days to keep DVR recordings', list=dvr_keep_val)
            if sel_enabled >= 0:
                dvr_keep = dvr_keep_key[sel_enabled]
                param_update = '"removal-days":' + str(dvr_keep)
        if sel_param == 4:
            sel_enabled = dialog.select('Enable or disable the re-recording of a timer if an error occurs', list=enabledisable)
            if sel_enabled >= 0:
                dvr_clone = truefalse[sel_enabled]
                param_update = '"clone":' + dvr_clone
        if sel_param == 5:
            sel_enabled = dialog.select('Select the stream profile for DVR playback', list=dvr_profile_val)
            if sel_enabled >= 0:
                dvr_keep = dvr_profile_key[sel_enabled]
                param_update = '"profile":' + str(dvr_profile)
        if sel_param == 6:
            dvr_file_param_load(dvr_uuid_sel)
        param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + dvr_uuid_sel + '"}'
        param_save = requests.get(param_url)
        dvr_param_load(dvr_uuid_sel)

def dvr_file_param_load(dvr_uuid_sel):
    dvr_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + dvr_uuid_sel
    dvr_load = requests.get(dvr_url).json()
    dvr_day_dir = find_param(dvr_load, 'day-dir')
    dvr_channel_dir = find_param(dvr_load, 'channel-dir')
    dvr_title_dir = find_param(dvr_load, 'title-dir')
    dvr_channel_title = find_param(dvr_load, 'channel-in-title')
    dvr_date_title = find_param(dvr_load, 'date-in-title')
    dvr_time_title = find_param(dvr_load, 'time-in-title')
    dvr_episode_title = find_param(dvr_load, 'episode-in-title')
    dvr_subtitle_title = find_param(dvr_load, 'subtitle-in-title')
    dvr_omit_title = find_param(dvr_load, 'omit-title')
    dvr_clean_title = find_param(dvr_load, 'clean-title')
    dvr_whitespace_title = find_param(dvr_load, 'whitespace-in-title')
    dvr_windows_title = find_param(dvr_load, 'windows-compatible-filenames')
    dvr_file_info_list = ["Make subdirectories per day: " + str(dvr_day_dir), "Make subdirectories per channel: " + str(dvr_channel_dir), "Make subdirectories per title: " + str(dvr_title_dir), "Include channel name in filename: " + str(dvr_channel_title), "Include date in filename: " + str(dvr_date_title), "Include time in filename: " + str(dvr_time_title), "Include episode in filename: " + str(dvr_episode_title), "Include subtitle in filename: " + str(dvr_subtitle_title), "Don't include title in filename: " + str(dvr_omit_title), "Remove all unsafe characters from filename: " + str(dvr_clean_title), "Replace whitespace in title with '-': " + str(dvr_whitespace_title), "Use Windows-compatible filenames: " + str(dvr_windows_title)]
    dvr_file_param_edit(dvr_uuid_sel, dvr_file_info_list, dvr_day_dir, dvr_channel_dir, dvr_title_dir, dvr_channel_title, dvr_date_title, dvr_time_title, dvr_episode_title, dvr_subtitle_title, dvr_omit_title, dvr_clean_title, dvr_whitespace_title, dvr_windows_title)

def dvr_file_param_edit(dvr_uuid_sel, dvr_file_info_list, dvr_day_dir, dvr_channel_dir, dvr_title_dir, dvr_channel_title, dvr_date_title, dvr_time_title, dvr_episode_title, dvr_subtitle_title, dvr_omit_title, dvr_clean_title, dvr_whitespace_title, dvr_windows_title):
    sel_param = dialog.select('DVR File and Folder Options - Select parameter to edit', list=dvr_file_info_list)
    if sel_param < 0:
        dvr_param_load(dvr_uuid_sel)
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_enabled = dialog.select('Make subdirectories per day', list=enabledisable)
            if sel_enabled >= 0:
                dvr_day_dir = truefalse[sel_enabled]
                param_update = '"day-dir":' + dvr_day_dir
        if sel_param == 1:
            sel_enabled = dialog.select('Make subdirectories per channel', list=enabledisable)
            if sel_enabled >= 0:
                dvr_channel_dir = truefalse[sel_enabled]
                param_update = '"channel-dir":' + dvr_channel_dir
        if sel_param == 2:
            sel_enabled = dialog.select('Make subdirectories per title', list=enabledisable)
            if sel_enabled >= 0:
                dvr_title_dir = truefalse[sel_enabled]
                param_update = '"title-dir":' + dvr_title_dir
        if sel_param == 3:
            sel_enabled = dialog.select('Include channel name in filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_channel_title = truefalse[sel_enabled]
                param_update = '"channel-in-title":' + dvr_channel_title
        if sel_param == 4:
            sel_enabled = dialog.select('Include date in filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_date_title = truefalse[sel_enabled]
                param_update = '"date-in-title":' + dvr_date_title
        if sel_param == 5:
            sel_enabled = dialog.select('Include time in filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_time_title = truefalse[sel_enabled]
                param_update = '"time-in-title":' + dvr_time_title
        if sel_param == 6:
            sel_enabled = dialog.select('Include episode in filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_episode_title = truefalse[sel_enabled]
                param_update = '"episode-in-title":' + dvr_episode_title
        if sel_param == 7:
            sel_enabled = dialog.select('Include subtitle in filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_subtitle_title = truefalse[sel_enabled]
                param_update = '"subtitle-in-title":' + dvr_subtitle_title
        if sel_param == 8:
            sel_enabled = dialog.select("Don't include title in filename", list=enabledisable)
            if sel_enabled >= 0:
                dvr_omit_title = truefalse[sel_enabled]
                param_update = '"omit-title":' + dvr_omit_title
        if sel_param == 9:
            sel_enabled = dialog.select('Remove all unsafe characters from filename', list=enabledisable)
            if sel_enabled >= 0:
                dvr_clean_title = truefalse[sel_enabled]
                param_update = '"clean-title":' + dvr_clean_title
        if sel_param == 10:
            sel_enabled = dialog.select("Replace whitespace in title with '-'", list=enabledisable)
            if sel_enabled >= 0:
                dvr_whitespace_title = truefalse[sel_enabled]
                param_update = '"whitespace-in-title":' + dvr_whitespace_title
        if sel_param == 11:
            sel_enabled = dialog.select('Use Windows-compatible filenames', list=enabledisable)
            if sel_enabled >= 0:
                dvr_windows_title = truefalse[sel_enabled]
                param_update = '"windows-compatible-filenames":' + dvr_windows_title
        param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + dvr_uuid_sel + '"}'
        param_save = requests.get(param_url)
        dvr_file_param_load(dvr_uuid_sel)

def mux_param_load_atsct(mux_uuid_sel):
    mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + mux_uuid_sel
    mux_load = requests.get(mux_url).json()
    mux_name = mux_load['entries'][0]['text']
    mux_enabled, mux_enabled_key, mux_enabled_val = find_param_dict(mux_load, 'enabled', 'enum')
    mux_modulation, mux_modulation_key, mux_modulation_val = find_param_dict(mux_load, 'modulation', 'enum')
    mux_delsys, mux_delsys_list = find_param_list(mux_load, 'delsys', 'enum')
    mux_scanstate, mux_scanstate_key, mux_scanstate_val = find_param_dict(mux_load, 'scan_state', 'enum')
    mux_frequency = find_param(mux_load, 'frequency')
    mux_services = find_param(mux_load, 'num_svc')
    mux_channels = find_param(mux_load, 'num_chn')
    mux_info_list = ["Enabled: " + str(mux_enabled), "Delivery System: " + str(mux_delsys), "Frequency: " + str(mux_frequency), "Modulation: " + str(mux_modulation), "Scan Status: " + str(mux_scanstate), "Number of Services: " + str(mux_services), "Number of Channels: " + str(mux_channels), "DELETE THE MUX"]
    mux_param_edit_atsct(mux_uuid_sel, mux_info_list, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels)

def mux_param_edit_atsct(mux_uuid_sel, mux_info_list, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels):
    if mux_scanstate == "ACTIVE":
        sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list, autoclose=4000)
        mux_param_load_atsct(mux_uuid_sel)
    sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list)
    if sel_param < 0:
        muxes()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_enabled = dialog.select('Enable or disable the mux', list=mux_enabled_val)
            if sel_enabled <0:
                mux_param_load_atsct(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_enabled = mux_enabled_key[sel_enabled]
                param_update = '"enabled":' + str(mux_enabled)
        if sel_param == 1:
            sel_enabled = dialog.select('Select the mux delivery system', list=mux_delsys_list)
            if sel_enabled <0:
                mux_param_load_atsct(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_delsys = mux_delsys_list[sel_enabled]
                param_update = '"delsys":"' + str(mux_delsys + '"')
        if sel_param == 2:
            sel_mux_frequency = dialog.input('Edit the mux frequency', defaultt=str(mux_frequency),type=xbmcgui.INPUT_NUMERIC)
            param_update = '"frequency":' + sel_mux_frequency
        if sel_param == 3:
            sel_mux_modulation = dialog.select('Select the modulation of the mux', list=mux_modulation_val)
            if sel_mux_modulation <0:
                mux_param_load_atsct(mux_uuid_sel)
            if sel_mux_modulation >= 0:
                mux_modulation = mux_modulation_key[sel_mux_modulation]
                param_update = '"modulation":"' + str(mux_modulation) + '"'
        if sel_param == 4:
            sel_mux_scanstate = dialog.select('Set the scan state of the mux', list=mux_scanstate_val)
            if sel_mux_scanstate <0:
                mux_param_load_atsct(mux_uuid_sel)
            if sel_mux_scanstate >= 0:
                mux_scanstate = mux_scanstate_key[sel_mux_scanstate]
                param_update = '"scan_state":' + str(mux_scanstate)
        if sel_param == 7:
            confirm_del = dialog.yesno('Confirm mux delete', 'Are you sure want to delete the ' + mux_name + ' mux?')
            if not confirm_del:
                return
            delete_mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/delete?uuid=["' + mux_uuid_sel +'"]'
            delete_mux = requests.get(delete_mux_url)
            muxes()
        if sel_param < 7:
            param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + mux_uuid_sel + '"}'
            param_save = requests.get(param_url)
            mux_param_load_atsct(mux_uuid_sel)

def mux_param_load_atscc(mux_uuid_sel):
    mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + mux_uuid_sel
    mux_load = requests.get(mux_url).json()
    mux_name = mux_load['entries'][0]['text']
    mux_enabled, mux_enabled_key, mux_enabled_val = find_param_dict(mux_load, 'enabled', 'enum')
    mux_modulation, mux_modulation_key, mux_modulation_val = find_param_dict(mux_load, 'constellation', 'enum')
    mux_delsys, mux_delsys_list = find_param_list(mux_load, 'delsys', 'enum')
    mux_scanstate, mux_scanstate_key, mux_scanstate_val = find_param_dict(mux_load, 'scan_state', 'enum')
    mux_frequency = find_param(mux_load, 'frequency')
    mux_symbolrate = find_param(mux_load, 'symbolrate')
    mux_services = find_param(mux_load, 'num_svc')
    mux_channels = find_param(mux_load, 'num_chn')
    mux_info_list = ["Enabled: " + str(mux_enabled), "Delivery System: " + str(mux_delsys), "Frequency: " + str(mux_frequency), "Symbol Rate: " + str(mux_symbolrate), "Modulation: " + str(mux_modulation), "Scan Status: " + str(mux_scanstate), "Number of Services: " + str(mux_services), "Number of Channels: " + str(mux_channels), "DELETE THE MUX"]
    mux_param_edit_atscc(mux_uuid_sel, mux_info_list, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_symbolrate, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels)

def mux_param_edit_atscc(mux_uuid_sel, mux_info_list, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_symbolrate, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels):
    if mux_scanstate == "ACTIVE":
        sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list, autoclose=4000)
        mux_param_load_atscc(mux_uuid_sel)
    sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list)
    if sel_param < 0:
        muxes()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_enabled = dialog.select('Enable or disable the mux', list=mux_enabled_val)
            if sel_enabled <0:
                mux_param_load_atscc(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_enabled = mux_enabled_key[sel_enabled]
                param_update = '"enabled":' + str(mux_enabled)
        if sel_param == 1:
            sel_enabled = dialog.select('Select the mux delivery system', list=mux_delsys_list)
            if sel_enabled <0:
                mux_param_load_atscc(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_delsys = mux_delsys_list[sel_enabled]
                param_update = '"delsys":"' + str(mux_delsys + '"')
        if sel_param == 2:
            sel_mux_frequency = dialog.input('Edit the mux frequency', defaultt=str(mux_frequency),type=xbmcgui.INPUT_NUMERIC)
            param_update = '"frequency":' + sel_mux_frequency
        if sel_param == 3:
            sel_mux_frequency = dialog.input('Edit the mux symbol rate', defaultt=str(mux_symbolrate),type=xbmcgui.INPUT_NUMERIC)
            param_update = '"symbolrate":' + sel_mux_symbolrate
        if sel_param == 4:
            sel_mux_modulation = dialog.select('Select the modulation of the mux', list=mux_modulation_val)
            if sel_mux_modulation <0:
                mux_param_load_atscc(mux_uuid_sel)
            if sel_mux_modulation >= 0:
                mux_modulation = mux_modulation_key[sel_mux_modulation]
                param_update = '"constellation":"' + str(mux_modulation) + '"'
        if sel_param == 5:
            sel_mux_scanstate = dialog.select('Set the scan state of the mux', list=mux_scanstate_val)
            if sel_mux_scanstate <0:
                mux_param_load_atscc(mux_uuid_sel)
            if sel_mux_scanstate >= 0:
                mux_scanstate = mux_scanstate_key[sel_mux_scanstate]
                param_update = '"scan_state":' + str(mux_scanstate)
        if sel_param == 8:
            confirm_del = dialog.yesno('Confirm mux delete', 'Are you sure want to delete the ' + mux_name + ' mux?')
            if not confirm_del:
                mux_param_load_atscc(mux_uuid_sel)
            delete_mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/delete?uuid=["' + mux_uuid_sel +'"]'
            delete_mux = requests.get(delete_mux_url)
            muxes()
        if sel_param < 8:
            param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + mux_uuid_sel + '"}'
            param_save = requests.get(param_url)
            mux_param_load_atscc(mux_uuid_sel)

def mux_param_load_dvbt(mux_uuid_sel):
    mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + mux_uuid_sel
    mux_load = requests.get(mux_url).json()
    mux_name = mux_load['entries'][0]['text']
    mux_enabled, mux_enabled_key, mux_enabled_val = find_param_dict(mux_load, 'enabled', 'enum')
    mux_modulation, mux_modulation_key, mux_modulation_val = find_param_dict(mux_load, 'constellation', 'enum')
    mux_delsys, mux_delsys_list = find_param_list(mux_load, 'delsys', 'enum')
    mux_scanstate, mux_scanstate_key, mux_scanstate_val = find_param_dict(mux_load, 'scan_state', 'enum')
    mux_frequency = find_param(mux_load, 'frequency')
    mux_bandwidth, mux_bandwidth_key, mux_bandwidth_val = find_param_dict(mux_load, 'bandwidth', 'enum')
    mux_transmission, mux_transmission_key, mux_transmission_val = find_param_dict(mux_load, 'transmission_mode', 'enum')
    mux_guard, mux_guard_key, mux_guard_val = find_param_dict(mux_load, 'guard_interval', 'enum')
    mux_hierarchy, mux_hierarchy_key, mux_hierarchy_val = find_param_dict(mux_load, 'hierarchy', 'enum')
    mux_fec_hi, mux_fec_hi_key, mux_fec_hi_val = find_param_dict(mux_load, 'fec_hi', 'enum')
    mux_fec_lo, mux_fec_lo_key, mux_fec_lo_val = find_param_dict(mux_load, 'fec_lo', 'enum')
    mux_plp_id = find_param(mux_load, 'plp_id')
    mux_services = find_param(mux_load, 'num_svc')
    mux_channels = find_param(mux_load, 'num_chn')
    mux_info_list = ["Enabled: " + str(mux_enabled), "Delivery System: " + str(mux_delsys), "Frequency: " + str(mux_frequency), "Bandwidth: " + str(mux_bandwidth), "COFDM Modulation: " + str(mux_modulation), "Transmission Mode: " + str(mux_transmission), "Guard Interval: " + str(mux_guard), "Hierarchy: " + str(mux_hierarchy), "FEC High: " + str(mux_fec_hi), "FEC Low: " + str(mux_fec_lo), "PLP ID: " + str(mux_plp_id), "Scan Status: " + str(mux_scanstate), "Number of Services: " + str(mux_services), "Number of Channels: " + str(mux_channels), "DELETE THE MUX"]
    mux_param_edit_dvbt(mux_uuid_sel, mux_info_list, mux_plp_id, mux_fec_lo, mux_fec_lo_key, mux_fec_lo_val, mux_fec_hi, mux_fec_hi_key, mux_fec_hi_val, mux_hierarchy, mux_hierarchy_key, mux_hierarchy_val, mux_guard, mux_guard_key, mux_guard_val, mux_transmission, mux_transmission_key, mux_transmission_val, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_bandwidth, mux_bandwidth_key, mux_bandwidth_val, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels)

def mux_param_edit_dvbt(mux_uuid_sel, mux_info_list, mux_plp_id, mux_fec_lo, mux_fec_lo_key, mux_fec_lo_val, mux_fec_hi, mux_fec_hi_key, mux_fec_hi_val, mux_hierarchy, mux_hierarchy_key, mux_hierarchy_val, mux_guard, mux_guard_key, mux_guard_val, mux_transmission, mux_transmission_key, mux_transmission_val, mux_scanstate, mux_scanstate_key, mux_scanstate_val, mux_frequency, mux_bandwidth, mux_bandwidth_key, mux_bandwidth_val, mux_modulation, mux_modulation_key, mux_modulation_val, mux_enabled, mux_enabled_key, mux_enabled_val, mux_delsys, mux_delsys_list, mux_name, mux_services, mux_channels):
    if mux_scanstate == "ACTIVE":
        sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list, autoclose=4000)
        mux_param_load_dvbt(mux_uuid_sel)
    sel_param = dialog.select(str(mux_name) + ' - Select parameter to edit', list=mux_info_list)
    if sel_param < 0:
        muxes()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_enabled = dialog.select('Enable or disable the mux', list=mux_enabled_val)
            if sel_enabled <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_enabled = mux_enabled_key[sel_enabled]
                param_update = '"enabled":' + str(mux_enabled)
        if sel_param == 1:
            sel_enabled = dialog.select('Select the mux delivery system', list=mux_delsys_list)
            if sel_enabled <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_enabled >= 0:
                mux_delsys = mux_delsys_list[sel_enabled]
                param_update = '"delsys":"' + str(mux_delsys + '"')
        if sel_param == 2:
            sel_mux_frequency = dialog.input('Edit the mux frequency', defaultt=str(mux_frequency),type=xbmcgui.INPUT_NUMERIC)
            param_update = '"frequency":' + sel_mux_frequency
        if sel_param == 3:
            sel_mux_bandwidth = dialog.select('Select the mux bandwidth', list=mux_bandwidth_val)
            if sel_mux_bandwidth <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_bandwidth >= 0:
                mux_bandwidth = mux_bandwidth_key[sel_mux_bandwidth]
                param_update = '"bandwidth":"' + str(mux_bandwidth) + '"'
        if sel_param == 4:
            sel_mux_modulation = dialog.select('Select the COFDM modulation of the mux', list=mux_modulation_val)
            if sel_mux_modulation <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_modulation >= 0:
                mux_modulation = mux_modulation_key[sel_mux_modulation]
                param_update = '"modulation":"' + str(mux_modulation) + '"'
        if sel_param == 5:
            sel_mux_transmission = dialog.select('Select the mux transmission mode', list=mux_transmission_val)
            if sel_mux_transmission <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_transmission >= 0:
                mux_transmission = mux_transmission_key[sel_mux_transmission]
                param_update = '"transmission_mode":"' + str(mux_transmission) + '"'
        if sel_param == 6:
            sel_mux_guard = dialog.select('Select the mux guard interval', list=mux_guard_val)
            if sel_mux_guard <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_guard >= 0:
                mux_guard = mux_guard_key[sel_mux_guard]
                param_update = '"guard_interval":"' + str(mux_guard) + '"'
        if sel_param == 7:
            sel_mux_hierarchy = dialog.select('Select the mux hierarchy', list=mux_hierarchy_val)
            if sel_mux_hierarchy <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_hierarchy >= 0:
                mux_hierarchy = mux_hierarchy_key[sel_mux_hierarchy]
                param_update = '"hierarchy":"' + str(mux_hierarchy) + '"'
        if sel_param == 8:
            sel_mux_fec_hi = dialog.select('Select the mux forward error correction high', list=mux_fec_hi_val)
            if sel_mux_fec_hi <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_fec_hi >= 0:
                mux_fec_hi = mux_fec_hi_key[sel_mux_fec_hi]
                param_update = '"fec_hi":"' + str(mux_fec_hi) + '"'
        if sel_param == 9:
            sel_mux_fec_lo = dialog.select('Select the mux forward error correction low', list=mux_fec_lo_val)
            if sel_mux_fec_lo <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_fec_lo >= 0:
                mux_fec_lo = mux_fec_lo_key[sel_mux_fec_lo]
                param_update = '"fec_lo":"' + str(mux_fec_lo) + '"'
        if sel_param == 10:
            sel_mux_plp_id = dialog.input('Edit the mux PLP ID', defaultt=str(mux_plp_id),type=xbmcgui.INPUT_ALPHANUM)
            param_update = '"plp_id":' + sel_mux_plp_id
        if sel_param == 11:
            sel_mux_scanstate = dialog.select('Set the scan state of the mux', list=mux_scanstate_val)
            if sel_mux_scanstate <0:
                mux_param_load_dvbt(mux_uuid_sel)
            if sel_mux_scanstate >= 0:
                mux_scanstate = mux_scanstate_key[sel_mux_scanstate]
                param_update = '"scan_state":' + str(mux_scanstate)
        if sel_param == 14:
            confirm_del = dialog.yesno('Confirm mux delete', 'Are you sure want to delete the ' + mux_name + ' mux?')
            if not confirm_del:
                return
            delete_mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/delete?uuid=["' + mux_uuid_sel +'"]'
            delete_mux = requests.get(delete_mux_url)
            muxes()
        if sel_param < 14:
            param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + mux_uuid_sel + '"}'
            param_save = requests.get(param_url)
            mux_param_load_dvbt(mux_uuid_sel)

def mux_new():
    new_mux_net_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?class=mpegts_network'
    new_mux_net_load = requests.get(new_mux_net_url).json()
    new_mux_net_name = []
    new_mux_net_uuid = []
    new_mux_net_class = []
    for net_n in new_mux_net_load['entries']:
        new_mux_net_name.append(net_n['text'])
    for net_u in new_mux_net_load['entries']:
        new_mux_net_uuid.append(net_u['uuid'])
    for net_c in new_mux_net_load['entries']:
        new_mux_net_class.append(net_c['class'])
    sel_new_mux_network = dialog.select('Select a network for new mux', list=new_mux_net_name)
    if sel_new_mux_network < 0:
        muxes()
    if sel_new_mux_network >= 0:
        new_mux_net_uuid_sel = new_mux_net_uuid[sel_new_mux_network]
        new_mux_net_class_sel = new_mux_net_class[sel_new_mux_network]
        new_mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/mux_class?uuid=' + new_mux_net_uuid_sel
        new_mux_load = requests.get(new_mux_url).json()
        sel_freq = dialog.input('Enter the frequency of the new mux', defaultt="",type=xbmcgui.INPUT_NUMERIC)
        if sel_freq == "":
            return
        else:
            if new_mux_net_class_sel == "dvb_network_atsc_t":
                mux_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/mux_create?conf={"enabled":1,"epg":1,"delsys":"ATSC-T","frequency":' + str(sel_freq) + ',"modulation":"AUTO","scan_state":0,"charset":"","tsid_zero":false,"pmt_06_ac3":0,"eit_tsid_nocheck":false,"sid_filter":0}&uuid=' + str(new_mux_net_uuid_sel)
                new_mux_create = requests.get(mux_create_url).json()
                mux_uuid_sel = new_mux_create['uuid']
                mux_param_load_atsct(mux_uuid_sel)
            if new_mux_net_class_sel == "dvb_network_atsc_c":
                mux_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/mux_create?conf={"enabled":1,"epg":1,"delsys":"ATSC-C","frequency":' + str(sel_freq) + ',"symbolrate":0,"constellation":"AUTO","fec":"AUTO","scan_state":0,"charset":"","tsid_zero":false,"pmt_06_ac3":0,"eit_tsid_nocheck":false,"sid_filter":0}&uuid=' + str(new_mux_net_uuid_sel)
                new_mux_create = requests.get(mux_create_url).json()
                mux_uuid_sel = new_mux_create['uuid']
                mux_param_load_atscc(mux_uuid_sel)
            if new_mux_net_class_sel == "dvb_network_dvbc":
                mux_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/mux_create?conf={"enabled":1,"epg":1,"delsys":"DVB-C","frequency":' + str(sel_freq) + ',"symbolrate":0,"constellation":"AUTO","fec":"AUTO","scan_state":0,"charset":"","tsid_zero":false,"pmt_06_ac3":0,"eit_tsid_nocheck":false,"sid_filter":0}&uuid=' + str(new_mux_net_uuid_sel)
                new_mux_create = requests.get(mux_create_url).json()
                mux_uuid_sel = new_mux_create['uuid']
                mux_param_load_atscc(mux_uuid_sel)
            if new_mux_net_class_sel == "dvb_network_dvbt":
                mux_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/mux_create?conf={"enabled":1,"epg":1,"delsys":"DVBT","frequency":' + str(sel_freq) + ',"bandwidth":"AUTO","constellation":"AUTO","transmission_mode":"AUTO","guard_interval":"AUTO","hierarchy":"AUTO","fec_hi":"AUTO","fec_lo":"AUTO","plp_id":-1,"scan_state":0,"charset":"","tsid_zero":false,"pmt_06_ac3":0,"eit_tsid_nocheck":false,"sid_filter":0}&uuid=' + str(new_mux_net_uuid_sel)
                new_mux_create = requests.get(mux_create_url).json()
                mux_uuid_sel = new_mux_create['uuid']
                mux_param_load_dvbt(mux_uuid_sel)
            if new_mux_net_class_sel == "dvb_network_dvbs":
                dialog.ok("Not available yet!", "DVB-S configuration is not yet available in this program.")
            muxes()

def ch_param_load(ch_uuid_sel):
    ch_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + ch_uuid_sel
    ch_load = requests.get(ch_url).json()
    ch_enabled = find_param(ch_load, 'enabled')
    ch_autoname = find_param(ch_load, 'autoname')
    ch_name = find_param(ch_load, 'name')
    ch_number = find_param(ch_load, 'number')
    ch_icon = find_param(ch_load, 'icon')
    ch_epg_list = find_list(ch_load, 'epggrab', 'value')
    ch_epg_text = []
    for ch_epg_y in ch_epg_list:
        ch_epg_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + ch_epg_y
        ch_epg_get = requests.get(ch_epg_url).json()
        ch_epg_text.append(ch_epg_get['entries'][0]['text'])
    ch_epg = ', '.join(ch_epg_text)
    ch_info_list = ["Name: " + str(ch_name), "Number: " + str(ch_number), "Enabled: " + str(ch_enabled), "Autoname: " + str(ch_autoname), "Icon URL: " + str(ch_icon), "EPG Source: " + str(ch_epg), "DELETE THE CHANNEL"]
    ch_param_edit(ch_uuid_sel, ch_info_list, ch_enabled, ch_autoname, ch_name, ch_number, ch_icon, ch_epg)

def ch_param_edit(ch_uuid_sel, ch_info_list, ch_enabled, ch_autoname, ch_name, ch_number, ch_icon, ch_epg):
    sel_param = dialog.select('Channels Configuration - Select parameter to edit', list=ch_info_list)
    if sel_param < 0:
        channels()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_ch_name = dialog.input('Edit the channel name', defaultt=ch_name,type=xbmcgui.INPUT_ALPHANUM)
            param_update = '"name":"' + sel_ch_name + '"'
        if sel_param == 1:
            sel_ch_number = dialog.input('Edit the channel number', defaultt=ch_number,type=xbmcgui.INPUT_NUMERIC)
            param_update = '"number":"' + sel_ch_number + '"'
        if sel_param == 2:
            sel_enabled = dialog.select('Enable or disable channel', list=enabledisable)
            if sel_enabled >= 0:
                ch_enabled = truefalse[sel_enabled]
                param_update = '"enabled":' + ch_enabled
        if sel_param == 3:
            sel_autoname = dialog.select('Select True/False to automatically name the channel with the service name', list=truefalse)
            if sel_autoname >= 0:
                ch_autoname = truefalse[sel_autoname]
                param_update = '"autoname":' + ch_autoname
        if sel_param == 4:
            sel_ch_icon = dialog.input('Edit the channel icon URL', defaultt=ch_icon,type=xbmcgui.INPUT_ALPHANUM)
            param_update = '"icon":"' + sel_ch_icon + '"'
        if sel_param == 5:
            epg_grid_url =  'http://' + tvh_url + ':' + tvh_port + '/api/epggrab/channel/grid?sort=names&dir=ASC&all=1'
            epg_grid_load = requests.get(epg_grid_url).json()
            epg_list_text = [x['names'] for x in epg_grid_load['entries']]
            epg_list_id = [x['id'] for x in epg_grid_load['entries']]
            epg_list_uuid = [x['uuid'] for x in epg_grid_load['entries']]
            epg_list_full = zip(epg_list_text, epg_list_id)
            epg_list_list = ["%s  -  %s" % x for x in epg_list_full]
            sel_epg = dialog.select('Select EPG source for channel: ' + str(ch_number) + " " + str(ch_name), list=epg_list_list)
            if sel_epg < 0:
                ch_param_edit(ch_uuid_sel, ch_info_list, ch_enabled, ch_autoname, ch_name, ch_number, ch_icon, ch_epg)
            if sel_epg >= 0:
                epg_uuid_sel = epg_list_uuid[sel_epg]
                param_update = '"epggrab":["' + epg_uuid_sel + '"]'
        if sel_param == 6:
            confirm_del = dialog.yesno('Confirm delete channel', 'Are you sure want to delete the ' + ch_name + ' channel?')
            if not confirm_del:
                ch_param_load(ch_uuid_sel)
            delete_ch_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/delete?uuid=["' + ch_uuid_sel +'"]'
            delete_ch = requests.get(delete_ch_url)
            channels()
        if sel_param < 6:
            param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + ch_uuid_sel + '"}'
            param_save = requests.get(param_url)
            ch_param_load(ch_uuid_sel)


def epg_param(sel_epg, epg_rename, epg_renumber, epg_reicon, epg_dbsave, epg_intcron, epg_otainit, epg_otacron, epg_otatime):
    if sel_epg == 1:
        sel_epg_rename = dialog.select('Update channel name with EPG provider name', list=enabledisable)
        if sel_epg_rename >= 0:
            epg_rename = truefalse[sel_epg_rename]
            param_update = '"channel_rename":' + epg_rename
    if sel_epg == 2:
        sel_epg_renumber = dialog.select('Update channel number with EPG provider number', list=enabledisable)
        if sel_epg_renumber >= 0:
            epg_renumber = truefalse[sel_epg_renumber]
            param_update = '"channel_renumber":' + epg_renumber
    if sel_epg == 3:
        sel_epg_reicon = dialog.select('Update channel icon with EPG provider icon', list=enabledisable)
        if sel_epg_reicon >= 0:
            epg_reicon = truefalse[sel_epg_reicon]
            param_update = '"channel_reicon":' + epg_reicon
    if sel_epg == 4:
        sel_epg_dbsave = dialog.input('Save EPG data to disk every X hours (set 0 to disable)', defaultt=str(epg_dbsave),type=xbmcgui.INPUT_NUMERIC)
        if sel_epg_dbsave == "":
            sel_epg_dbsave = epg_dbsave
        param_update = '"epgdb_periodicsave":' + str(sel_epg_dbsave)
    if sel_epg == 5:
        sel_epg_intcron = dialog.input('Edit the cron multiline for internal grabbers', defaultt=epg_intcron,type=xbmcgui.INPUT_ALPHANUM)
        if sel_epg_intcron == "":
            sel_epg_intcron = epg_intcron
        param_update = '"cron":"' + sel_epg_intcron + '"'
    if sel_epg == 6:
        sel_epg_otainit = dialog.select('Enable or disable initial EPG grab at startup', list=enabledisable)
        if sel_epg_otainit >= 0:
            epg_otainit = truefalse[sel_epg_otainit]
            param_update = '"ota_initial":' + epg_otainit
    if sel_epg == 7:
        sel_epg_otacron = dialog.input('Edit the cron multiline for over-the-air grabbers', defaultt=epg_otacron,type=xbmcgui.INPUT_ALPHANUM)
        if sel_epg_otacron == "":
            sel_epg_otacron = epg_otacron
        param_update = '"cron":"' + sel_epg_otacron + '"'
    if sel_epg == 8:
        sel_epg_otatime = dialog.input('OTA EPG scan timeout in seconds (30-7200)', defaultt=str(epg_otatime),type=xbmcgui.INPUT_NUMERIC)
        if sel_epg_otatime == "":
            sel_epg_otatime = epg_otatime
        param_update = '"ota_timeout":' + str(sel_epg_otatime)
    param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/epggrab/config/save?node={' + param_update + '}'
    param_save = requests.get(param_url)
    epg()

def epgmod_list_load():
    epg_modlist_url = 'http://' + tvh_url + ':' + tvh_port + '/api/epggrab/module/list'
    epg_modlist_load = requests.get(epg_modlist_url).json()
    epg_modlist_name = []
    epg_modlist_uuid = []
    epg_modlist_enabled = []
    for n in epg_modlist_load['entries']:
        epg_modlist_name.append(n['title'])
    for u in epg_modlist_load['entries']:
        epg_modlist_uuid.append(u['uuid'])
    for e in epg_modlist_load['entries']:
        epg_modlist_enabled.append(str(e['status']))
    epg_modlist_enabled = [w.replace('epggrabmodNone', ' ** DISABLED **') for w in epg_modlist_enabled]
    epg_modlist_enabled = [w.replace('epggrabmodEnabled', ' ') for w in epg_modlist_enabled]
    epg_modlist_full = zip(epg_modlist_name, epg_modlist_enabled)
    epg_modlist_list = ["%s %s" % x for x in epg_modlist_full]
    epg_modlist_list, epg_modlist_uuid = (list(t) for t in zip(*sorted(zip(epg_modlist_list, epg_modlist_uuid))))
    sel_epgmod = dialog.select('Select an EPG grabber module to configure', list=epg_modlist_list)
    if sel_epgmod < 0:
        epg()
    if sel_epgmod >= 0:
        epgmod_uuid_sel = epg_modlist_uuid[sel_epgmod]
        epgmod_param_load(epgmod_uuid_sel)

def epgmod_param_load(epgmod_uuid_sel):
    epgmod_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + epgmod_uuid_sel
    epgmod_load = requests.get(epgmod_url).json()
    epgmod_enabled = find_param(epgmod_load, 'enabled')
    epgmod_name = find_param(epgmod_load, 'text')
    epgmod_priority = find_param(epgmod_load, 'priority')
    epgmod_type = find_param(epgmod_load, 'type')
    epgmod_dnchnum = ""
    epgmod_dnchnum_key = ""
    epgmod_dnchnum_val = ""
    epgmod_args = ""
    if epgmod_type == "External":
        epgmod_dnchnum = find_param(epgmod_load, 'dn_chnum')
        epgmod_args = ""
        epgmod_info_list = ["Enabled: " + str(epgmod_enabled), "Priority: " + str(epgmod_priority), "Channel Numbers (heuristic): " + str(epgmod_dnchnum)]
    if epgmod_type == "Internal":
        epgmod_dnchnum, epgmod_dnchnum_key, epgmod_dnchnum_val = find_param_dict(epgmod_load, 'dn_chnum', 'enum')
        epgmod_args = find_param(epgmod_load, 'args')
        epgmod_info_list = ["Enabled: " + str(epgmod_enabled), "Priority: " + str(epgmod_priority), "Channel Numbers (heuristic): " + str(epgmod_dnchnum), "Extra Arguments: " + str(epgmod_args)]
    if epgmod_type == "Over-the-air":
        epgmod_info_list = ["Enabled: " + str(epgmod_enabled), "Priority: " + str(epgmod_priority)]
    epgmod_param_edit(epgmod_uuid_sel, epgmod_info_list, epgmod_enabled, epgmod_name, epgmod_priority, epgmod_type, epgmod_dnchnum, epgmod_dnchnum_key, epgmod_dnchnum_val, epgmod_args)

def epgmod_param_edit(epgmod_uuid_sel, epgmod_info_list, epgmod_enabled, epgmod_name, epgmod_priority, epgmod_type, epgmod_dnchnum, epgmod_dnchnum_key, epgmod_dnchnum_val, epgmod_args):
    sel_param = dialog.select('EPG Module Configuration - Select parameter to edit', list=epgmod_info_list)
    if sel_param < 0:
        epgmod_list_load()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_enabled = dialog.select('Enable or disable the EPG grabber module', list=enabledisable)
            if sel_enabled <0:
                epgmod_param_load(epgmod_uuid_sel)
            if sel_enabled >= 0:
                epgmod_enabled = truefalse[sel_enabled]
                param_update = '"enabled":' + epgmod_enabled
        if sel_param == 1:
            sel_epgmod_priority = dialog.input('Edit the EPG grabber priority - higher number gets used first', defaultt=str(epgmod_priority),type=xbmcgui.INPUT_NUMERIC)
            param_update = '"priority":"' + sel_epgmod_priority + '"'
        if sel_param == 2 and epgmod_type == "External":
            sel_epgmod_dnchnum = dialog.select('Enable or disable trying to read channel number from xml tag', list=enabledisable)
            if sel_epgmod_dnchnum <0:
                epgmod_param_load(epgmod_uuid_sel)
            if sel_enabled >= 0:
                epgmod_dnchnum = truefalse[sel_epgmod_dnchnum]
                param_update = '"dn_chnum":' + epgmod_dnchnum
        if sel_param == 2 and epgmod_type == "Internal":
            sel_epgmod_dnchnum = dialog.select('Select the mode for readingchannel number from displayname xml tafg', list=epgmod_dnchnum_val)
            if sel_epgmod_dnchnum <0:
                epgmod_param_load(epgmod_uuid_sel)
            if sel_epgmod_dnchnum >= 0:
                epgmod_dnchnum = epgmod_dnchnum_key[sel_epgmod_dnchnum]
                param_update = '"dn_chnum":"' + str(epgmod_dnchnum) + '"'
        if sel_param == 3:
            sel_epgmod_args = dialog.input('Additional arguments to pass to the grabber', defaultt=epgmod_args,type=xbmcgui.INPUT_ALPHANUM)
            param_update = '"args":"' + sel_epgmod_args + '"'
        param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + epgmod_uuid_sel + '"}'
        param_save = requests.get(param_url)
        epgmod_param_load(epgmod_uuid_sel)

def adapt_param_load(adapter_uuid_sel):
    adapt_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + adapter_uuid_sel
    adapt_load = requests.get(adapt_url).json()
    adapt_enabled = find_param(adapt_load, 'enabled')
    adapt_priority = find_param(adapt_load, 'priority')
    adapt_name = find_param(adapt_load, 'displayname')
    adapt_otaepg = find_param(adapt_load, 'ota_epg')
    adapt_init = find_param(adapt_load, 'initscan')
    adapt_idle = find_param(adapt_load, 'idlescan')
    adapt_network = find_param(adapt_load, 'networks')
    if adapt_network == []:
        adapt_network = ""
    else:
        adapt_network_uuid = adapt_load['entries'][0]['params'][10]['value'][0]
        adapt_network_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + str(adapt_network_uuid)
        adapt_network_load = requests.get(adapt_network_url).json()
        adapt_network = adapt_network_load['entries'][0]['text']
    adapt_info_list = ["Name: " + str(adapt_name), "Enabled: " + str(adapt_enabled), "Networks: " + str(adapt_network), "Priority: " + str(adapt_priority), "Enable OTA EPG scanning: " + str(adapt_otaepg), "Allow initial scanning on startup: " + str(adapt_init), "Allow idle scanning: " + str(adapt_idle)]
    adapt_param_edit(adapter_uuid_sel, adapt_info_list, adapt_enabled, adapt_name, adapt_network, adapt_priority, adapt_otaepg, adapt_init, adapt_idle)

def adapt_param_edit(adapter_uuid_sel, adapt_info_list, adapt_enabled, adapt_name, adapt_network, adapt_priority, adapt_otaepg, adapt_init, adapt_idle):
    sel_param = dialog.select('Adapters Configuration - Select parameter to edit', list=adapt_info_list)
    if sel_param < 0:
        adapt_param_load(adapter_uuid_sel)
    if sel_param >= 0:
        truefalse = ['true', 'false']
        enabledisable = ['Enabled', 'Disabled']
        param_update = ""
        if sel_param == 0:
            sel_adapt_name = dialog.input('Edit the adapter name', defaultt=adapt_name,type=xbmcgui.INPUT_ALPHANUM)
            if sel_adapt_name == "":
                sel_adapt_name = adapt_name
            param_update = '"displayname":"' + sel_adapt_name + '"'
        if sel_param == 1:
            sel_adapt_enabled = dialog.select('Enable or disable the adapter', list=enabledisable)
            if sel_adapt_enabled >= 0:
                adapt_enabled = truefalse[sel_adapt_enabled]
                param_update = '"enabled":' + adapt_enabled
        if sel_param == 2:
            networks_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/grid'
            networks = requests.get(networks_url).json()
            net_name = ["Setup New Network"]
            net_uuid = [0]
            if networks['entries'] == []:
                if dialog.yesno("No Networks found!", "", "Would you like to setup a new Network?"):
                    net_uuid_sel = network_new()
                    param_update = '"networks":["' + net_uuid_sel + '"]'
            else:
                net_name = ["Setup New Network"]
                net_uuid = [0]
                for net_n in networks['entries']:
                    net_name.append(net_n['networkname'])
                for net_u in networks['entries']:
                    net_uuid.append(net_u['uuid'])
                sel_network = dialog.select('Select a network to assign to this adapter', list=net_name)
                if sel_network == 0:
                    network_new()
                    param_update = '"networks":["' + net_uuid_sel + '"]'
                if sel_network > 0:
                    net_uuid_sel = net_uuid[sel_network]
                    param_update = '"networks":["' + net_uuid_sel + '"]'
        if sel_param == 3:
            sel_adapt_priority = dialog.input('Edit the adapter priority (higher used first)', defaultt=str(adapt_priority),type=xbmcgui.INPUT_NUMERIC)
            if sel_adapt_priority == "":
                sel_adapt_priority = adapt_priority
            param_update = '"priority":"' + str(sel_adapt_priority) + '"'
        if sel_param == 4:
            sel_adapt_otaepg = dialog.select('Enable or disable OTA EPG scanning', list=enabledisable)
            if sel_adapt_otaepg >= 0:
                adapt_otaepg = truefalse[sel_adapt_otaepg]
                param_update = '"ota_epg":' + adapt_otaepg
        if sel_param == 5:
            sel_adapt_init = dialog.select('Enable or disable initial startup scanning', list=enabledisable)
            if sel_adapt_init >= 0:
                adapt_init = truefalse[sel_adapt_init]
                param_update = '"initscan":' + adapt_init
        if sel_param == 6:
            sel_adapt_idle = dialog.select('Enable or disable idle scanning', list=enabledisable)
            if sel_adapt_idle >= 0:
                adapt_idle = truefalse[sel_adapt_idle]
                param_update = '"idlescan":' + adapt_idle
        param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + adapter_uuid_sel + '"}'
        param_save = requests.get(param_url)
        adapt_param_load(adapter_uuid_sel)

def network_new():
    net_type_name = ["ATSC-T","ATSC-C","DVB-S","DVB-C","DVB-T","ISDB-S","ISDB-C","ISDB-T","IPTV Automatic"]
    net_type_class = ["dvb_network_atsc_t","dvb_network_atsc_c","dvb_network_dvbs","dvb_network_dvbc","dvb_network_dvbt","dvb_network_isdb_s","dvb_network_isdb_c","dvb_network_isdb_t","iptv_auto_network"]
    sel_net_type = dialog.select('Select a network type to create', list=net_type_name)
    if sel_net_type >= 0:
        net_type = net_type_name[sel_net_type]
        net_class = net_type_class[sel_net_type]
        new_net_name = dialog.input('Name of the network', defaultt=net_type,type=xbmcgui.INPUT_ALPHANUM)
        if new_net_name == "":
            new_net_name = net_type
        dvb_list_url = 'http://' + tvh_url + ':' + tvh_port + '/api/dvb/scanfile/list?type=' + net_type.lower()
        dvb_list = requests.get(dvb_list_url).json()
        scan_key = []
        scan_val = []
        for scan_k in dvb_list['entries']:
            scan_key.append(scan_k['key'])
        for scan_v in dvb_list['entries']:
            scan_val.append(scan_v['val'])
        sel_scan = dialog.select('Select a pre-defined mux list for the ' + new_net_name + " network", list=scan_val)
        scan_val_sel = scan_key[sel_scan]
        net_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/create?class=' + net_class + '&conf={"networkname":"' + new_net_name + '","bouquet":false,"scanfile":"' + scan_val_sel + '","pnetworkname":"","nid":0,"autodiscovery":1,"ignore_chnum":false,"satip_source":0,"charset":""}'
        net_create = requests.get(net_create_url).json()
        net_uuid_sel = net_create['uuid']
        return net_uuid_sel

def net_param_load(net_uuid_sel):
    net_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + str(net_uuid_sel)
    net_load = requests.get(net_url).json()
    net_name = find_param(net_load, 'networkname')
    net_bouquet = find_param(net_load, 'bouquet')
    net_type = net_load['entries'][0]['params'][17]['enum']['params']['type']
    net_num_mux = find_param(net_load, 'num_mux')
    net_num_svc = find_param(net_load, 'num_svc')
    net_num_ch = find_param(net_load, 'num_chn')
    if net_num_svc == 0 and net_num_mux == 0:
        net_num_svc_disp = "0 - add muxes before scanning for services"
    if net_num_mux != 0 and net_num_svc == 0:
        net_num_svc_disp = "0 - select to scan muxes for services"
    else:
        net_num_svc_disp = net_num_svc
    if net_num_mux == 0:
        net_num_mux_disp = "0 - select from list of pre-defined muxes"
    else:
        net_num_mux_disp = net_num_mux
    net_info_list = ["Name: " + net_name, "Create bouquet: " + str(net_bouquet), "Number of muxes: " + str(net_num_mux_disp), "Number of services: " + str(net_num_svc_disp), "Number of channels: " + str(net_num_ch), "DELETE THE NETWORK"]
    net_param_edit(net_uuid_sel, net_info_list, net_name, net_bouquet, net_type, net_num_mux, net_num_svc, net_num_ch)

def net_param_edit(net_uuid_sel, net_info_list, net_name, net_bouquet, net_type, net_num_mux, net_num_svc, net_num_ch):
    sel_param = dialog.select('Network Configuration - Select parameter to edit', list=net_info_list)
    if sel_param < 0:
        networks()
    if sel_param >= 0:
        param_update = ""
        if sel_param == 0:
            sel_net_name = dialog.input('Edit the network name', defaultt=net_name,type=xbmcgui.INPUT_ALPHANUM)
            if sel_net_name == "":
                sel_net_name = net_name
            param_update = '"networkname":"' + sel_net_name + '"'
        if sel_param == 1:
            sel_net_bouquet = dialog.select('Enable or disable to automatically create a bouquet from all services', list=enabledisable)
            if sel_net_bouquet >= 0:
                net_bouquet_enabled = truefalse[sel_net_bouquet]
                param_update = '"bouquet":' + net_bouquet_enabled
        if sel_param == 2 and net_num_mux != 0:
            muxes()
        if sel_param == 2 and net_num_mux == 0:
            dvb_list_url = 'http://' + tvh_url + ':' + tvh_port + '/api/dvb/scanfile/list?type=' + net_type
            dvb_list = requests.get(dvb_list_url).json()
            scan_key = []
            scan_val = []
            for scan_k in dvb_list['entries']:
                scan_key.append(scan_k['key'])
            for scan_v in dvb_list['entries']:
                scan_val.append(scan_v['val'])
            sel_scan = dialog.select('Select a pre-defined mux list for the ' + net_name + " network", list=scan_val)
            scan_val_sel = scan_val[sel_scan]
            param_update = '"scanfile":"' + scan_val_sel + '"'
            param_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={' + param_update + ',"uuid":"' + net_uuid_sel + '"}'
            param_save = requests.get(param_url)
            net_param_load(net_uuid_sel)
        if sel_param == 3 and net_num_mux != 0 and net_num_svc != 0:
            if dialog.yesno(str(net_num_svc) + " services found!", "Would you like to scan muxes for new services?"):
                start_scan(net_uuid_sel)
        if sel_param == 3 and net_num_mux == 0:
            dialog.ok("No muxes found!", "Add muxes before scanning for services.")
        if sel_param == 3 and net_num_mux != 0 and net_num_svc == 0:
            if dialog.yesno("No services found!", "Would you like to scan muxes for new services?"):
                start_scan(net_uuid_sel)
        if sel_param == 4 and net_num_svc != 0 and net_num_ch == 0:
            if dialog.yesno(str(net_num_svc) + " services found!", "Would you like to map services to channels?"):
                services()
        if sel_param == 4 and net_num_svc != 0 and net_num_ch != 0:
            channels()
        if sel_param == 4 and net_num_svc == 0 and net_num_mux != 0:
            if dialog.yesno("No services found!", "Would you like to scan muxes for new services?"):
                start_scan(net_uuid_sel)
        if sel_param == 4 and net_num_mux == 0:
            dialog.ok("No muxes found!", "Add muxes before scanning for services and mapping channels.")
        if sel_param == 5:
            confirm_del = dialog.yesno('Confirm delete network', 'Are you sure want to delete the ' + net_name + ' network?')
            if not confirm_del:
                return
            delete_net_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/delete?uuid=["' + net_uuid_sel +'"]'
            delete_net = requests.get(delete_net_url)
            networks()
        if sel_param < 5:
            net_param_load(net_uuid_sel)

def start_scan(net_uuid_sel):
    adapters_url = 'http://' + tvh_url + ':' + tvh_port + '/api/hardware/tree?uuid=root'
    adapters_get = requests.get(adapters_url).json()
    if adapters_get == []:
        dialog.ok("No adapters found!", "Please make sure your TV adapter is connected.")
        return
    scan_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/scan?uuid=' + net_uuid_sel
    update_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/grid'
    mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/mux/grid'
    stream_url = 'http://' + tvh_url + ':' + tvh_port + '/api/status/inputs'
    mux_list_get = requests.get(mux_url).json()
    mux_list = [x['uuid'] for x in mux_list_get['entries']]
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Scanning muxes for new services')
    scan = requests.get(scan_url).json()
    time.sleep(1)
    update = requests.get(update_url).json()
    update_scan = [x['scanq_length'] for x in update['entries'] if x['uuid'] == net_uuid_sel]
    update_scan_num = update_scan[0]
    update_mux = [x['num_mux'] for x in update['entries'] if x['uuid'] == net_uuid_sel]
    update_mux_num = update_mux[0]
    orig_serv = [x['num_svc'] for x in update['entries'] if x['uuid'] == net_uuid_sel]
    orig_serv_num = orig_serv[0]
    while update_scan_num > 0:
        update = requests.get(update_url).json()
        update_scan = [x['scanq_length'] for x in update['entries'] if x['uuid'] == net_uuid_sel]
        update_scan_num = update_scan[0]
        update_serv = [x['num_svc'] for x in update['entries'] if x['uuid'] == net_uuid_sel]
        update_serv_num = (update_serv[0] - orig_serv_num)
        update_scan_perc = 100 - ((float(update_scan_num) / float(update_mux_num)) * 100)
        update_stream = requests.get(stream_url).json()
        stream_freq_list = []
        stream_freq_list = [x.get('stream') for x in update_stream['entries']]
        stream_freq = '  &  '.join(str(s) for s in stream_freq_list)
        pDialog.update(int(update_scan_perc), "Scanning: " + str(stream_freq), "New services found: " + str(update_serv_num))
        time.sleep(1)
        if (pDialog.iscanceled()):
            mux_list_str = str(mux_list)
            mux_list_str = re.sub("u\'","\"",mux_list_str)
            mux_list_str = re.sub("\'","\"",mux_list_str)
            mux_stop_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={"scan_state":0,"uuid":' + mux_list_str + '}'
            mux_stop =  requests.get(mux_stop_url)
            dialog.ok('Scanning muxes cancelled', 'New services will not be mapped.')
            return
    pDialog.close()
    if update_serv_num == 0:
        dialog.ok('Scanning complete.', "New services found: " + str(update_serv_num), "There are no new services to map to channels.")
        return
    goto_map = dialog.yesno('Scanning complete.', "New services found: " + str(update_serv_num), "Would you like to continue and map new services to channels?")
    if not goto_map:
        return
    services()

def wizard_start():
    adapters_url = 'http://' + tvh_url + ':' + tvh_port + '/api/hardware/tree?uuid=root'
    adapters_get = requests.get(adapters_url).json()
    if adapters_get == []:
        dialog.ok("No adapters found!", "Please make sure your TV adapter is connected.")
        return
    adapters_uuid = []
    for adapter_fe in adapters_get:
        adapters_uuid.append(adapter_fe['uuid'])
    adapter_uuid = []
    adapter_list = []
    for adapter_y in adapters_uuid:
        adapter_url = 'http://' + tvh_url + ':' + tvh_port + '/api/hardware/tree?uuid=' + adapter_y
        adapter_get = requests.get(adapter_url).json()
        for adapter_x in adapter_get:
            adapter_uuid.append(adapter_x['uuid'])
        for adapter_t in adapter_get:
            adapter_list.append(adapter_t['text'])
    sel_adapter = dialog.select('Select which adapter you would like to setup', list=adapter_list)
    if sel_adapter < 0:
        return
    if sel_adapter >= 0:
        adapter_uuid_sel = adapter_uuid[sel_adapter]
        adapter_text_sel = adapter_list[sel_adapter]
        adapt_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + adapter_uuid_sel
        adapt_load = requests.get(adapt_url).json()
        adapt_network = find_param(adapt_load, 'networks')
        net_create = ""
        if adapt_network == []:
            if "ATSC-T" in adapter_text_sel:
                net_class = "dvb_network_atsc_t"
                scanfile_type = "atsc-t"
                net_name_create = "ATSC-T"
            if "ATSC-C" in adapter_text_sel:
                net_class = "dvb_network_atsc_c"
                scanfile_type = "atsc-c"
                net_name_create = "ATSC-C"
            if "DVB-S" in adapter_text_sel:
                net_class = "dvb_network_dvbs"
                scanfile_type = "dvbs"
                net_name_create = "DVB-S"
            if "DVB-T" in adapter_text_sel:
                net_class = "dvb_network_dvbt"
                scanfile_type = "dvbt"
                net_name_create = "DVB-T"
            if "DVB-C" in adapter_text_sel:
                net_class = "dvb_network_dvbc"
                scanfile_type = "dvbc"
                net_name_create = "DVB-C"
            networks_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/grid'
            networks = requests.get(networks_url).json()
            net_name = []
            net_uuid = []
            for net_n in networks['entries']:
                net_name.append(net_n['networkname'])
            for net_u in networks['entries']:
                net_uuid.append(net_u['uuid'])
            if not any (net_name_create in s for s in net_name):
                dvb_list_url = 'http://' + tvh_url + ':' + tvh_port + '/api/dvb/scanfile/list?type=' + scanfile_type
                dvb_list = requests.get(dvb_list_url).json()
                scan_key = []
                scan_val = []
                for scan_k in dvb_list['entries']:
                    scan_key.append(scan_k['key'])
                for scan_v in dvb_list['entries']:
                    scan_val.append(scan_v['val'])
                sel_scan = dialog.select('Select a pre-defined mux list for the ' + net_name_create + " network", list=scan_val)
                scan_val_sel = scan_key[sel_scan]
                net_create_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/create?class=' + net_class + '&conf={"networkname":"' + net_name_create + '","scanfile":"' + scan_val_sel + '"}'
                net_create_new = requests.get(net_create_url).json()
                net_create = net_create_new['uuid']
            else:
               net_create_index = (net_name.index(net_name_create) if net_name_create in net_name else None)
               net_create = net_uuid[net_create_index]
        else:
            net_create = adapt_network[0]
        adapt_net_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={"enabled":true,"networks":["' + str(net_create) + '"],"uuid":"' + str(adapter_uuid_sel) + '"}'
        adapt_update = requests.get(adapt_net_url).json()
        scan_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/scan?uuid=' + net_create
        update_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/grid'
        mux_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/mux/grid'
        stream_url = 'http://' + tvh_url + ':' + tvh_port + '/api/status/inputs'
        mux_list_get = requests.get(mux_url).json()
        mux_list = [x['uuid'] for x in mux_list_get['entries']]
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Scanning muxes for new services')
        scan = requests.get(scan_url).json()
        time.sleep(1)
        update = requests.get(update_url).json()
        update_scan = [x['scanq_length'] for x in update['entries'] if x['uuid'] == net_create]
        update_scan_num = update_scan[0]
        update_mux = [x['num_mux'] for x in update['entries'] if x['uuid'] == net_create]
        update_mux_num = update_mux[0]
        orig_serv = [x['num_svc'] for x in update['entries'] if x['uuid'] == net_create]
        orig_serv_num = orig_serv[0]
        while update_scan_num > 0:
            update = requests.get(update_url).json()
            update_scan = [x['scanq_length'] for x in update['entries'] if x['uuid'] == net_create]
            update_scan_num = update_scan[0]
            update_serv = [x['num_svc'] for x in update['entries'] if x['uuid'] == net_create]
            update_serv_num = (update_serv[0] - orig_serv_num)
            update_scan_perc = 100 - ((float(update_scan_num) / float(update_mux_num)) * 100)
            update_stream = requests.get(stream_url).json()
            stream_freq_list = []
            stream_freq_list = [x.get('stream') for x in update_stream['entries']]
            stream_freq = '  &  '.join(str(s) for s in stream_freq_list)
            pDialog.update(int(update_scan_perc), "Scanning: " + str(stream_freq), "New services found: " + str(update_serv_num))
            time.sleep(1)
            if (pDialog.iscanceled()):
                mux_list_str = str(mux_list)
                mux_list_str = re.sub("u\'","\"",mux_list_str)
                mux_list_str = re.sub("\'","\"",mux_list_str)
                mux_stop_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/save?node={"scan_state":0,"uuid":' + mux_list_str + '}'
                mux_stop =  requests.get(mux_stop_url)
                dialog.ok('Scanning muxes cancelled', 'New services will not be mapped.')
                return
        pDialog.close()
        if update_serv_num == 0:
            dialog.ok('Scanning complete.', "New services found: " + str(update_serv_num), "There are no new services to map to channels.")
            return
        serv_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/service/grid?limit=999999999&sort=multiplex'
        services = requests.get(serv_url).json()
        serv_total = services['total']
        serv_uuid = []
        for serv_id in services['entries']:
            if serv_id['channel'] == []:
                serv_uuid.append(serv_id['uuid'])
        serv_uuid_str = str(serv_uuid)
        serv_uuid_str = re.sub("u\'","\"",serv_uuid_str)
        serv_uuid_str = re.sub("\'","\"",serv_uuid_str)
        map_url = 'http://' + tvh_url + ':' + tvh_port + '/api/service/mapper/save?node={"services":' + serv_uuid_str + ',"encrypted":false,"merge_same_name":false,"check_availability":false,"type_tags":true,"provider_tags":false,"network_tags":false}'
        map_ch =  requests.get(map_url)
        status_url = 'http://' + tvh_url + ':' + tvh_port + '/api/service/mapper/status'
        time.sleep(3)
        map_status = requests.get(status_url).json()
        map_total_num = map_status['total']
        map_ok_num = map_status['ok']
        map_fail_num = map_status['fail']
        map_ignore_num = map_status['ignore']
        map_complete = (map_ok_num + map_fail_num + map_ignore_num)
        map_total_perc = ((float(map_complete) / float(serv_total)) * 100)
        dialog.ok("Wizard complete!", str(map_ok_num) + " new channels.", str(map_ignore_num) + " services ignored.", str(map_fail_num) + " services failed.")

@plugin.route('/adapters')
def adapters():
    adapters_url = 'http://' + tvh_url + ':' + tvh_port + '/api/hardware/tree?uuid=root'
    adapters_get = requests.get(adapters_url).json()
    if adapters_get == []:
        dialog.ok("No adapters found!", "Please make sure your TV adapter is connected.")
        return
    adapters_uuid = []
    for adapter_fe in adapters_get:
        adapters_uuid.append(adapter_fe['uuid'])
    adapter_uuid = []
    adapter_text = []
    adapter_enabled = []
    for adapter_y in adapters_uuid:
        adapter_url = 'http://' + tvh_url + ':' + tvh_port + '/api/hardware/tree?uuid=' + adapter_y
        adapter_get = requests.get(adapter_url).json()
        for adapter_x in adapter_get:
            adapter_uuid.append(adapter_x['uuid'])
        for adapter_t in adapter_get:
            adapter_text.append(adapter_t['text'])
        for adapter_e in adapter_get:
            adapter_enabled.append(str(adapter_e['params'][0]['value']))
    adapter_enabled = [w.replace('False', ' ** DISABLED **') for w in adapter_enabled]
    adapter_enabled = [w.replace('True', ' ') for w in adapter_enabled]
    adapters_full = zip(adapter_text, adapter_enabled)
    adapters_list = ["%s %s" % x for x in adapters_full]
    sel_adapter = dialog.select('Select which adapter you would like to configure', list=adapters_list)
    if sel_adapter >= 0:
        adapter_uuid_sel = adapter_uuid[sel_adapter]
        adapt_param_load(adapter_uuid_sel)

@plugin.route('/networks')
def networks():
    networks_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/network/grid'
    networks = requests.get(networks_url).json()
    net_name = ["Setup New Network"]
    net_uuid = [0]
    for net_n in networks['entries']:
        net_name.append(net_n['networkname'])
    for net_u in networks['entries']:
        net_uuid.append(net_u['uuid'])
    sel_network = dialog.select('Select a network to configure', list=net_name)
    if sel_network == 0:
        net_uuid_sel = network_new()
        net_param_load(net_uuid_sel)
    if sel_network >= 0:
        net_uuid_sel = net_uuid[sel_network]
        net_param_load(net_uuid_sel)

@plugin.route('/muxes')
def muxes():
    muxes_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/mux/grid?limit=999999999'
    muxes = requests.get(muxes_url).json()
    muxes_name = []
    muxes_uuid = []
    muxes_enabled = []
    muxes_network = []
    muxes_frequency = []
    for mux_n in muxes['entries']:
        muxes_name.append(mux_n['name'])
    for mux_u in muxes['entries']:
        muxes_uuid.append(mux_u['uuid'])
    for mux_w in muxes['entries']:
        muxes_network.append(" in " + mux_w['network'])
    for mux_f in muxes['entries']:
        muxes_frequency.append(mux_f['frequency'])
    muxes_full = zip(muxes_name, muxes_network,)
    muxes_list = ["%s %s" % x for x in muxes_full]
    muxes_frequency, muxes_list, muxes_uuid = zip(*sorted(zip(muxes_frequency, muxes_list, muxes_uuid)))
    create_mux = "CREATE NEW MUX"
    muxes_list = list(muxes_list)
    muxes_list.insert(0,create_mux)
    muxes_list = tuple(muxes_list)
    muxes_frequency = list(muxes_frequency)
    muxes_frequency.insert(0,create_mux)
    muxes_frequency = tuple(muxes_frequency)
    muxes_uuid = list(muxes_uuid)
    muxes_uuid.insert(0,create_mux)
    muxes_uuid = tuple(muxes_uuid)
    sel_mux = dialog.select('Select a mux to configure', list=muxes_list)
    if sel_mux == 0:
        mux_new()
    if sel_mux >= 0:
        mux_uuid_sel = muxes_uuid[sel_mux]
        sel_mux_class_url = 'http://' + tvh_url + ':' + tvh_port + '/api/idnode/load?uuid=' + mux_uuid_sel
        sel_mux_class_load = requests.get(sel_mux_class_url).json()
        sel_mux_class = sel_mux_class_load['entries'][0]['class']
        if sel_mux_class == "dvb_mux_atsc_t":
            mux_param_load_atsct(mux_uuid_sel)
        if sel_mux_class == "dvb_mux_atsc_c":
            mux_param_load_atscc(mux_uuid_sel)
        if sel_mux_class == "dvb_mux_dvbc":
            mux_param_load_atscc(mux_uuid_sel)
        if sel_mux_class == "dvb_mux_dvbt":
            mux_param_load_dvbt(mux_uuid_sel)
        if sel_mux_class == "dvb_mux_dvbs":
            mux_param_load_dvbs(mux_uuid_sel)

@plugin.route('/mux_scan')
def mux_scan():
    api_path = 'mpegts/network/grid'
    api_url = 'http://' + tvh_url + ':' + tvh_port + '/api/' + api_path
    networks = requests.get(api_url).json()
    net_name = []
    net_uuid = []
    for net_n in networks['entries']:
        net_name.append(net_n['networkname'])
    for net_u in networks['entries']:
        net_uuid.append(net_u['uuid'])
    sel = dialog.select('Select a network to scan', list=net_name)
    if sel >= 0:
        net_uuid_sel = net_uuid[sel]
        start_scan(net_uuid_sel)

@plugin.route('/services')
def services():
    if dialog.yesno("Map Services to Channels", "Would you like to try to map all services to channels?"):
        serv_url = 'http://' + tvh_url + ':' + tvh_port + '/api/mpegts/service/grid?limit=999999999&sort=multiplex'
        services = requests.get(serv_url).json()
        serv_total = services['total']
        serv_uuid = []
        for serv_id in services['entries']:
            if serv_id['channel'] == []:
                serv_uuid.append(serv_id['uuid'])
        serv_uuid_str = str(serv_uuid)
        serv_uuid_str = re.sub("u\'","\"",serv_uuid_str)
        serv_uuid_str = re.sub("\'","\"",serv_uuid_str)
        map_url = 'http://' + tvh_url + ':' + tvh_port + '/api/service/mapper/save?node={"services":' + serv_uuid_str + ',"encrypted":false,"merge_same_name":false,"check_availability":false,"type_tags":true,"provider_tags":false,"network_tags":false}'
        map_ch =  requests.get(map_url)
        status_url = 'http://' + tvh_url + ':' + tvh_port + '/api/service/mapper/status'
        time.sleep(3)
        map_status = requests.get(status_url).json()
        map_total_num = map_status['total']
        map_ok_num = map_status['ok']
        map_fail_num = map_status['fail']
        map_ignore_num = map_status['ignore']
        map_complete = (map_ok_num + map_fail_num + map_ignore_num)
        map_total_perc = ((float(map_complete) / float(serv_total)) * 100)
        dialog.ok("Channel mapping complete.", str(map_ok_num) + " new channels added.", str(map_ignore_num) + " services ignored.", str(map_fail_num) + " services failed.")


@plugin.route('/channels')
def channels():
    channels_url = 'http://' + tvh_url + ':' + tvh_port + '/api/channel/grid?all=1&limit=999999999&sort=name'
    channels = requests.get(channels_url).json()
    channels_name = []
    channels_uuid = []
    channels_enabled = []
    for ch_n in channels['entries']:
        channels_name.append(ch_n['name'])
    for ch_u in channels['entries']:
        channels_uuid.append(ch_u['uuid'])
    for ch_e in channels['entries']:
        channels_enabled.append(str(ch_e['enabled']))
    channels_enabled = [w.replace('False', ' ** DISABLED **') for w in channels_enabled]
    channels_enabled = [w.replace('True', ' ') for w in channels_enabled]
    channels_full = zip(channels_name, channels_enabled)
    channels_list = ["%s %s" % x for x in channels_full]
    sel_ch = dialog.select('Select a channel to configure', list=channels_list)
    if sel_ch >= 0:
        ch_uuid_sel = channels_uuid[sel_ch]
        ch_param_load(ch_uuid_sel)

@plugin.route('/dvr')
def dvr():
    dvr_config_url = 'http://' + tvh_url + ':' + tvh_port + '/api/dvr/config/grid'
    dvr_config = requests.get(dvr_config_url).json()
    dvr_config_name = []
    dvr_config_uuid = []
    for dvr_n in dvr_config['entries']:
        if dvr_n['name'] == "":
            dvr_n = "(Default profile)"
        dvr_config_name.append(dvr_n)
    for dvr_u in dvr_config['entries']:
        dvr_config_uuid.append(dvr_u['uuid'])
    sel_dvr = dialog.select('Select a DVR configuration to edit', list=dvr_config_name)
    if sel_dvr < 0:
        return
    if sel_dvr >= 0:
        dvr_uuid_sel = dvr_config_uuid[sel_dvr]
        dvr_param_load(dvr_uuid_sel)

@plugin.route('/epg')
def epg():
    epg_url = 'http://' + tvh_url + ':' + tvh_port + '/api/epggrab/config/load'
    epg_load = requests.get(epg_url).json()
    epg_rename = find_param(epg_load, 'channel_rename')
    epg_renumber = find_param(epg_load, 'channel_renumber')
    epg_reicon = find_param(epg_load, 'channel_reicon')
    epg_dbsave = find_param(epg_load, 'epgdb_periodicsave')
    epg_intcron = find_param(epg_load, 'cron')
    epg_otainit = find_param(epg_load, 'ota_initial')
    epg_otacron = find_param(epg_load, 'ota_cron')
    epg_otatime = find_param(epg_load, 'ota_timeout')
    epg_info_list = ["EDIT EPG GRABBER MODULES", "Update channel name: " + str(epg_rename), "Update channel number: " + str(epg_renumber), "Update channel icon: " + str(epg_reicon), "Periodically save EPG to disk (hours): " + str(epg_dbsave), "Internal Cron multi-line: " + str(epg_intcron), "Force initial OTA EPG grab at start-up: " + str(epg_otainit), "Over-the-air Cron multi-line: " + str(epg_otacron), "OTA EPG scan timeout in seconds (30-7200): " + str(epg_otatime)]
    sel_epg = dialog.select('Select an EPG Grabber configuration to edit', list=epg_info_list)
    if sel_epg < 0:
        return
    if sel_epg == 0:
        epgmod_list_load()
    if sel_epg > 0:
        epg_param(sel_epg, epg_rename, epg_renumber, epg_reicon, epg_dbsave, epg_intcron, epg_otainit, epg_otacron, epg_otatime)

@plugin.route('/wizard')
def wizard():
    start = dialog.yesno("TVheadend Wizard - Start", "This wizard will walk you through the initial setup for TVheadend. Running this wizard on an already configured system could cause issues.", "Do you wish to continue?")
    if not start:
        return
    else:
        wizard_start()

@plugin.route('/tvhclient')
def tvhclient():
    plugin.open_settings()
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/')
def index():
    items = []
    items.append(
    {
        'label': 'Adapters Configuration',
        'path': plugin.url_for(u'adapters'),
        'thumbnail':get_icon_path('adapter'),
    })
    items.append(
    {
        'label': 'Networks Configuration',
        'path': plugin.url_for(u'networks'),
        'thumbnail':get_icon_path('antenna'),
    })
    items.append(
    {
        'label': 'Muxes Configuration',
        'path': plugin.url_for(u'muxes'),
        'thumbnail':get_icon_path('signal'),
    })
    items.append(
    {
        'label': 'Channels Configuration',
        'path': plugin.url_for(u'channels'),
        'thumbnail':get_icon_path('numlist'),
    })
    items.append(
    {
        'label': 'Scan for New Channels',
        'path': plugin.url_for(u'mux_scan'),
        'thumbnail':get_icon_path('frequency'),
    })
    items.append(
    {
        'label': 'Map Services to Channels',
        'path': plugin.url_for(u'services'),
        'thumbnail':get_icon_path('folder'),
    })
    items.append(
    {
        'label': 'EPG Grabber Configuration',
        'path': plugin.url_for(u'epg'),
        'thumbnail':get_icon_path('list'),
    })
    items.append(
    {
        'label': 'DVR Configuration',
        'path': plugin.url_for(u'dvr'),
        'thumbnail':get_icon_path('dvr'),
    })
    items.append(
    {
        'label': 'Start Wizard',
        'path': plugin.url_for(u'wizard'),
        'thumbnail':get_icon_path('wand'),
    })
    items.append(
    {
        'label': 'Tvheadend Backend: ' + tvh_url + ':' + tvh_port,
        'path': plugin.url_for(u'tvhclient'),
        'thumbnail':get_icon_path('settings'),
    })

    return items


if __name__ == '__main__':
    plugin.run()
