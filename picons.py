#!/usr/bin/env python
################################################################################
#      This file is part of LibreELEC - https://libreelec.tv
#      Copyright (C) 2016-2017 Team LibreELEC
#      Copyright (C) 2017 Tnds82 (tndsrepo@gmail.com)
#
#  LibreELEC is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  LibreELEC is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with LibreELEC.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import os, xbmc, xbmcaddon, xbmcgui
import json, urllib, urllib2, subprocess, time, zipfile
import shutil, datetime, sys
from urlparse import urlparse
from os.path import splitext


addon       = xbmcaddon.Addon(id='script.module.tvh2kodi')
addonname   = addon.getAddonInfo('name')
addonfolder = addon.getAddonInfo('path')
addonicon   = os.path.join(addonfolder, 'resources/icon.png')
addondata   = xbmc.translatePath(addon.getAddonInfo('profile'))
logfile     = os.path.join(addondata, 'data/')
tempfolder  = os.path.join(addondata, 'temp/')
picons_dest = xbmc.translatePath(xbmcaddon.Addon().getSetting('pdest'))
pdest       = os.path.join(picons_dest)
zstd        = os.path.join(addonfolder, 'bin', 'zstd')
url_latest  = 'http://cvh.libreelec.tv/picons/latest2.json'
latest_json = urllib.urlopen(url_latest)
snp_json    = os.path.join(addondata, 'data/snp.json')
srp_json    = os.path.join(addondata, 'data/srp.json')
log3rdparty = os.path.join(addondata, 'data/3rdparty.log')
logfile     = os.path.join(addondata, 'data')
log3rdparty = os.path.join(logfile, '3rdparty.log')
logsnpjson  = os.path.join(logfile, 'snp.json')
logsrpjson  = os.path.join(logfile, 'srp.json')
exturl      = addon.getSetting('purl')
dialog      = xbmcgui.Dialog()
header      = 'Picons Downloader'
dp          = xbmcgui.DialogProgress()
pathpicons  = xbmc.translatePath(xbmcaddon.Addon().getSetting('pdest'))
exturl      = xbmcaddon.Addon().getSetting('purl')
now         = datetime.datetime.now()
date        = '%s-%s-%s' % (now.year,now.month,now.day)

def compare_release_snp(path):
    ljson = json.loads(latest_json.read())
    for key in ljson['Picons']['latest'].keys():
        latest = key
    if os.path.exists(snp_json):
        with open(snp_json) as release_json:
            rjson = json.load(release_json)
        for key1 in rjson['Picons']['latest'].keys():
            release = key1
        if latest == release:
            if dialog.yesno('Picons Downloader Update', 'Already on latest version.', 'Do you want to download anyway?'):
                delete_file(path)
                urlpicons = ljson['Picons']['url']
                snpname   = ljson['Picons']['latest'][latest]['snp']['name'] + ".tar.xz"
                url = "%s%s" % (urlpicons, snpname)
                picons_snp(url, url_latest)
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 2000, addonicon))
            else:
                return
        else:
            if dialog.yesno('Picons Downloader Update', 'There is a newer version of the icons pack available.', 'Do you want to download anyway?'):
                delete_file(path)
                urlpicons = ljson['Picons']['url']
                snpname   = ljson['Picons']['latest'][latest]['snp']['name'] + ".tar.xz"
                url = "%s%s" % (urlpicons, snpname)
                picons_snp(url, url_latest)
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 2000, addonicon))
            else:
                return
    else:
        urlpicons = ljson['Picons']['url']
        snpname   = ljson['Picons']['latest'][latest]['snp']['name'] + ".tar.xz"
        url = "%s%s" % (urlpicons, snpname)
        picons_snp(url, url_latest)
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 2000, addonicon))

def compare_release_srp(path):
    ljson = json.loads(latest_json.read())
    for key in ljson['Picons']['latest'].keys():
        latest = key
    if os.path.exists(srp_json):
        with open(srp_json) as release_json:
            rjson = json.load(release_json)
        for key1 in rjson['Picons']['latest'].keys():
            release = key1
        if latest == release:
            if dialog.yesno('Picons Downloader Update', 'Already on latest version.', 'Do you want to download anyway?'):
                delete_file(path)
                urlpicons = ljson['Picons']['url']
                srpname   = ljson['Picons']['latest'][latest]['srp']['name'] + ".tar.xz"
                url = "%s%s" % (urlpicons, srpname)
                picons_srp(url, url_latest)
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 4000, addonicon))
            else:
                return
        else:
            if dialog.yesno('Picons Downloader Update', 'There is a newer version of the icons pack available.', 'Do you want to download anyway?'):
                delete_file(path)
                urlpicons = ljson['Picons']['url']
                srpname   = ljson['Picons']['latest'][latest]['srp']['name'] + ".tar.xz"
                url = "%s%s" % (urlpicons, srpname)
                picons_srp(url, url_latest)
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 4000, addonicon))
            else:
                return
    else:
        urlpicons = ljson['Picons']['url']
        srpname   = ljson['Picons']['latest'][latest]['srp']['name'] + ".tar.xz"
        url = "%s%s" % (urlpicons, srpname)
        picons_srp(url, url_latest)
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download finished"', 4000, addonicon))

def url_snp():
    ljson = json.loads(latest_json.read())
    for key in ljson['Picons']['latest'].keys():
        latest = key
    urlpicons = ljson['Picons']['url']
    snpname   = ljson['Picons']['latest'][latest]['snp']['name'] + ".tar.xz"
    url = "%s%s" % (urlpicons, snpname)
    picons_snp(url, url_latest)
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download the picons is finish"', 4000, addonicon))

def url_srp():
    ljson = json.loads(latest_json.read())
    for key in ljson['Picons']['latest'].keys():
        latest = key
    urlpicons = ljson['Picons']['url']
    srpname   = ljson['Picons']['latest'][latest]['srp']['name'] + ".tar.xz"
    url = "%s%s" % (urlpicons, srpname)
    picons_srp(url, url_latest)
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download the picons is finish"', 4000, addonicon))

def url_external():
    if addon.getSetting('pdest') == '':
        xbmcgui.Dialog().ok(addonname, "You need choose destination for picons", "", "")
        return
    elif addon.getSetting('purl') == '':
        xbmcgui.Dialog().ok(addonname, "You need choose the external url", "", "")
        return
    else:
        picons_ext(exturl)
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, '"Download the picons is finish"', 4000, addonicon))

def create_directories(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_log(file, path, date):
    log = open(file, 'a')
    log.write('Picons Downloader\n')
    log.write('%s %s%s' % ('The picons were successfully downloaded to the folder:', path,'\n'))
    log.write('%s %s' % ('Date:', date))

def delete_directories(path):
    shutil.rmtree(path)

def delete_tempfiles():
    shutil.rmtree(tempfolder)

def delete_file(path):
    if os.path.exists(path):
        os.remove(path)

def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print proc_stdout

def downloader(url,dest, header):

    dp.create(header,"Downloading","Please Wait...")
    urllib.urlretrieve(url,dest,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))

def _pbhook(numblocks, blocksize, filesize, url=None,dp=None):
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
        print percent
        dp.update(percent)
    except:
        percent = 100
        dp.update(percent)
    if dp.iscanceled():
        d = xbmcgui.Dialog()
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, "Download cancelled", 1000, addonicon))
        dp.close()
        sys.exit()

def extract_xz(_in):
    extract = '%s %s' % ('unxz', _in)
    subprocess_cmd(extract)

def extract_zstd(_in):
    extract = '%s%s %s %s' % (addonfolder, zstd,'-d', _in)
    subprocess_cmd(extract)

def extract_tar(picons, _out):
    dp.create('Picons Downloader', "Extracting","Please Wait...")
    extract = '%s %s%s %s %s %s' % ('tar xf', tempfolder, picons, '-C', _out, '--strip-components=1')
    dp.update(0)
    subprocess_cmd(extract)
    for i in range(1, 100) :
        dp.update(i)
        if dp.iscanceled() : break
        time.sleep(0.05)
    dp.close()

def extract_zip(_in, _out, dp, header):
    dp.create(header,"Extracting","Please Wait...")
    zin = zipfile.ZipFile(_in,  'r')
    nFiles = float(len(zin.infolist()))
    count  = 0
    try:
        for item in zin.infolist():
            count += 1
            update = count / nFiles * 100
            dp.update(int(update))
            zin.extract(item, _out)
    except Exception, e:
        print str(e)
        return False
    return True

def picons_snp(url, urljson):
    create_directories(tempfolder)
#    packageFile = os.path.join(tempfolder, 'picons-snp.tar.zst')
    packageFile = os.path.join(tempfolder, 'picons-snp.tar.xz')
    downloader(url,packageFile,header)
    create_directories(pdest)
#    extract_zstd(packageFile)
    extract_xz(packageFile)
    extract_tar('picons-snp.tar', pdest)
    delete_tempfiles()
    create_log
    create_directories(logfile)
    delete_file(logsnpjson)
    subprocess_cmd('%s %s %s' % ('wget -O', logsnpjson, urljson))

def picons_srp(url, urljson):
    create_directories(tempfolder)
#    packageFile = os.path.join(tempfolder, 'picons-srp.tar.zst')
    packageFile = os.path.join(tempfolder, 'picons-srp.tar.xz')
    downloader(url,packageFile,header)
    create_directories(pdest)
#    extract_zstd(packageFile)
    extract_xz(packageFile)
    extract_tar('picons-srp.tar', pdest)
    delete_tempfiles()
    create_log
    create_directories(logfile)
    delete_file(logsrpjson)
    subprocess_cmd('%s %s %s' % ('wget -O', logsrpjson, urljson))

def picons_ext(url):
    parsed = urlparse(exturl)
    root, ext = splitext(parsed.path)
    if root.endswith('.tar'):
        ext = 'tar' + ext
    if ext == '.zip' : # zip
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.zip')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_zip(packageFile,pathpicons,dp,header)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)

    elif ext == 'tar.gz' or ext == '.gz': # tar.gz and .gz
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.tar.gz')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_tar('picons-ext.tar.gz', pathpicons)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)

    elif ext == 'tar.xz' : # tar.xz
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.tar.xz')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_xz(packageFile)
        extract_tar('picons-ext.tar', pathpicons)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)

    elif ext == '.xz' : # .xz
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.xz')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_xz(packageFile, pathpicons)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)

    elif ext == 'tar.zst' : # tar.zst
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.tar.zst')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_zstd(packageFile)
        extract_tar('picons-ext.tar', pathpicons)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)

    elif ext == '.zst' : # .zst
        create_directories(tempfolder)
        packageFile = os.path.join(tempfolder, 'picons-ext.zst')
        downloader(exturl,packageFile,header)
        create_directories(pathpicons)
        extract_zstd(packageFile, pathpicons)
        delete_tempfiles()
        create_directories(logfile)
        delete_file(log3rdparty)
        create_log(log3rdparty, pathpicons, date)
