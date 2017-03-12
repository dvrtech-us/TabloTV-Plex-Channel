'''#########################################
        Author: @DavidVR - Van Ronk, David
                       @PiX64  - Reid, Michael

    Source:

    Purpose:

    Legal:
#########################################'''
import pprint

# Load SharedServiceCode helper functions
tablohelpers = SharedCodeService.tablohelpers
Decodeobj = tablohelpers.Decodeobj
Encodeobj = tablohelpers.Encodeobj
TabloAPI = tablohelpers.TabloAPI

# loadLiveTVData   = tablohelpers.loadLiveTVData
# plexlog = SharedCodeService.TabloHelpers.plexlog

'''#### Define Global Vars ####'''
TITLE = 'Tablo'
ART = 'TabloProduct_FrontRight-default.jpg'
ICON = 'tablo_icon_focus_hd.png'
NOTV_ICON = 'no_tv_110x150.jpg'
ICON_PREFS = 'icon_settings_hd.jpg'
SHOW_THUMB = 'no_tv_110x150.jpg'
PREFIX = '/video/Tablo'
LOG_PREFIX = "***TabloTV: "
VERSION = "0.992"
FOLDERS_COUNT_IN_TITLE = True  # Global VAR used to enable counts on titles
debugit = True

'''#########################################
        Name: Start()

        Parameters: None

        Purpose:

        Returns:

        Notes: see: http://dev.plexapp.com/docs/Functions.html#ValidatePrefs
#########################################'''


def Start():
    Log(LOG_PREFIX + "Starting TabloTV Plex Channel Plugin: " + VERSION)
    # Plugin setup
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    # Object / Directory / VideoClip setup
    ObjectContainer.title1 = TITLE
    ObjectContainer.view_group = 'InfoList'
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(NOTV_ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(NOTV_ICON)
    VideoClipObject.art = R(ART)

    # HTTP setup
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0'


'''#########################################
        Name: MainMenu()

        Parameters: None

        Handler: @handler -

        Purpose: Gather and display all top level items

        Returns:

        Notes:
#########################################'''


@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():
    try:

        count = loadtablos()
        if count == 0 and Prefs['ipoveride'] is None:
            Log('here')
            plexlog('Main Menu - API Fail', Prefs['ipoveride'])
            return ObjectContainer(header='Error', message='API Could Not Locate a tablo on your network')
        if Prefs['ipoveride'] != '' and Prefs['ipoveride'] is not None:
            plexlog('pref', 'using overidge')
            plexlog('pref found', Prefs['ipoveride'])
            Dict['public_ip'] = Prefs['ipoveride']
            Dict['private_ip'] = Prefs['ipoveride']
    except:
        plexlog('Main Menu', 'Early LoadTablo Fail')

    oc = ObjectContainer()

    if 'private_ip' not in Dict:
        Log('privateIPERROR')
        oc.add(PrefsObject(title='Could Not Locate a tablo on your network', thumb=R(ICON_PREFS)))
        return oc
    else:
        try:
            recs = JSON.ObjectFromURL('http://' + Dict['private_ip'] + ':8885/recordings/airings', values=None, headers={}, cacheTime=60)

            episodelistids = {
                'ids': [
                    rec.split('/')[-1]
                    for rec in recs
                ]
            }
        except Exception as e:
            return ObjectContainer(header='Error', message='Could Not Connect to your tablo')

        oc.add(DirectoryObject(thumb=R('icon_livetv_hd.jpg'), key=Callback(livetvnew, title="Live TV"),
                               title="Live TV"))
        oc.add(DirectoryObject(thumb=R('icon_recordings_hd.jpg'),
                               key=Callback(Shows, title="Shows", url=Dict['private_ip']), title="Shows"))
        oc.add(DirectoryObject(thumb=R('icon_movies_hd.jpg'),
                               key=Callback(Movies, title="Movies"), title="Movies"))
        oc.add(DirectoryObject(thumb=R('icon_sports_hd.jpg'),
                               key=Callback(Sports, title="Sports"), title="Sports"))
        oc.add(DirectoryObject(thumb=R('icon_tvshows_hd.jpg'),
                               key=Callback(allrecordings, title="All Recordings", url=Dict['private_ip']),
                               title="Recent Recordings"))
        # oc.add(DirectoryObject(thumb=R('icon_scheduled_hd.jpg'),
        #                        key=Callback(scheduled, title="Scheduled Recordings"),
        #                        title="Scheduled Recordings"))
        oc.add(DirectoryObject(thumb=R('icon_settings_hd.jpg'), key=Callback(Help, title="Help"), title="Help"))
        oc.add(PrefsObject(title='Change your IP Address', thumb=R(ICON_PREFS)))
    return oc


'''#########################################
        Name: Help()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/help')
def Help(title):
    oc = ObjectContainer()
    oc.add(DirectoryObject(thumb=R('info.png'), key=Callback(About, title="About TabloTV Plex"), title="About"))
    oc.add(DirectoryObject(thumb=R('info.png'), key=Callback(detected, title="About Your Tablo"),
                           title="About Your Tablo"))
    oc.add(DirectoryObject(thumb=R('icon-prefs.png'), key=Callback(ResetPlugin, title="Reset Plugin"),
                           title="Reset Plugin "))
    # oc.add(DirectoryObject(thumb=R('icon-prefs.png'), key=Callback(DeleteDups, title="Delete Dups"),
    #                        title="Delete Dups "))
    return oc


'''#########################################
        Name: Reset Plugin()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/ResetPlugin')
def ResetPlugin(title):
    cleartablodata()
    try:
        # Pass full Tablo info to here for better parsing and future multiple tablo support
        count = 0
        Dict['tabloips'] = getTabloIP()
        for tablo in tabloips:
            count += 1
            Dict['public_ip'] = str(tablo['public_ip'])
            Dict['private_ip'] = str(tablo['private_ip'])

        if count == 0:
            return ObjectContainer(header='Error', message='API Could Not Locate a tablo on your network')
    except:
        Log('Could not fetch tablo IP, Will use cached IP if avalible')

    return ObjectContainer(header=title, message='Plugin Reset Complete, Please go back to Main Menu Now')


'''#########################################
        Name: Delete Duplicates()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/DeleteDups')
def DeleteDups(title):
    try:
        myurl = "http://" + Dict['private_ip'] + ":8886"
        cmd = "/recordings/deleteRecordings"
        parms = {"recordingsType": "recEpisode", "recordings": [33810, 33813]}
        result = TabloAPI(myurl, cmd, parms)
        plexlog('DeDup', result)

        oc = ObjectContainer()
        oc.title1 = title
        ipaddress = Dict['private_ip']
    except:
        Log('Dup Failed')

    return ObjectContainer(header=title, message='Plugin Reset Complete, Please go back to Main Menu Now')


'''#########################################
        Name: About()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/about')
def About(title):
    return ObjectContainer(header=title, message='TabloTV Plex Plugin Version ' + VERSION)


'''#########################################
        Name: scheduled()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/scheduled')
def scheduled(title):
    mymessage = ""
    myurl = "http://" + Dict['private_ip'] + ":8886"
    cmd = "/info/guideSeries/get"
    parms = {"filter": {"orderby": "startdate", "schedulestate": "scheduled"}}
    result = TabloAPI(myurl, cmd, parms)
    # plexlog('detect',result)
    recordings = result['result']['series']
    oc = ObjectContainer()
    oc.title1 = title
    ipaddress = Dict['private_ip']
    datetime = Datetime.Now()
    timezoneoffset = int((datetime - datetime.utcnow()).total_seconds())
    plexlog('secondsbetween', timezoneoffset)
    plexlog('date.now', datetime)
    plexlog('date.utcnow', datetime.utcnow())

    # Loop through channels and create a Episode Object for each show
    for airingData in recordings:
        unixtimestarted = Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime']))
        displayeddate = str(Datetime.FromTimestamp(
            Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime'])) + timezoneoffset))
        recordingtype = 'Unknown'
        if 'scheduleType' in airingData['schedule']:
            recordingtype = airingData['schedule']['scheduleType']
        imagedid = ''
        if 'images' in airingData:
            imagedid = airingData['images'][0]['imageID']
        plexlog('airingdata loop', airingData)
        # All commented out are set in TabloLive.pys helpers
        oc.add(
                # TVShowObject(
                PopupDirectoryObject(
                        # rating_key=airingData['objectID'],
                        # show=airingData['title'],
                        title=displayeddate + ' - ' + airingData['title'],
                        summary='Original Air Date: ' + airingData[
                            'originalAirDate'] + ' Scheduled to Record: ' + recordingtype,
                        # originally_available_at = Datetime.ParseDate(airingData['originalAirDate']),  #writers = ,
                        # directors = ,  #producers = ,  #guest_stars = ,
                        key=Callback(nothing, title=title),  # season = airingData['seasonNumber'],
                        thumb=Resource.ContentsOfURLWithFallback(
                            url='http://' + ipaddress + ':18080/stream/thumb?id=' + str(imagedid), fallback=NOTV_ICON),
                        # art= Resource.ContentsOfURLWithFallback(url=airingData['art'], fallback=ART),
                        tagline=unixtimestarted
                        # duration = airingData['duration']  #description = airingData['description']
                )
        )

    oc.objects.sort(key=lambda obj: obj.tagline, reverse=False)
    return oc


'''#########################################
        Name: nothing()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


def nothing(title):
    oc = scheduled(title)
    oc.header = 'No More Information Available'
    oc.message = 'No More Information Available'

    return oc


'''#########################################
        Name: Detected()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/about/Detected')
def detected(title):
    mymessage = ""
    myurl = "http://" + Dict['private_ip'] + ":8886"
    cmd = "/server/status"
    parms = {}
    result = TabloAPI(myurl, cmd, parms)
    plexlog('detect', result)
    tablo = result['result']
    mymessage = mymessage + " Tablo Reported Name: " + tablo['name'] + '   _______  Reported IP: ' + tablo[
        'localAddress'] + '___________ Running Version: ' + tablo['serverVersion']
    return ObjectContainer(header=title, message=mymessage)


'********************************************************************************************'
'********************** Start OF LIVE TV CODE ***********************************************'
'********************************************************************************************'

'''#########################################
        Name: livetvnew()

        Parameters: title
                                url

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/livetvnew', allow_sync=False)
def livetvnew(title):
    loadLiveTVData(Dict)

    oc = ObjectContainer()
    oc.title1 = title
    oc.no_cache = True
    if "LiveTV" in Dict:
        data = Dict["LiveTV"]

        # Loop through channels and create a Episode Object for each show
        for chid, airingData in data.iteritems():
            try:
                # All commented out are set in TabloLive.pys helpers
                oc.add(EpisodeObject(
                        url=Encodeobj('channel', airingData),
                        show=airingData['channelNumber'] + ': ' + airingData['callSign'],
                        title=airingData.get('title', 'unknown'),
                        summary=airingData.get('summary', ''),
                        absolute_index=airingData['order'],
                        season = airingData.get('seasonNumber'),
                        thumb=Resource.ContentsOfURLWithFallback(url=airingData['seriesThumb'], fallback=NOTV_ICON),
                        art= Resource.ContentsOfURLWithFallback(url=airingData['art'], fallback=ART),
                        source_title='TabloTV',
                        duration = airingData.get('duration')
                )
                )
            except Exception as e:
                Log("Parse Failed on channel " + str(e))
    oc.objects.sort(key=lambda obj: obj.absolute_index, reverse=False)
    return oc


'''#########################################
        Name: loadLiveTVData()

        Parameters: Dict

        Handler: @route

        Purpose:

        Returns:

        Notes: Moved to init for faster debugging
#########################################'''


def loadLiveTVData(Dict):
    # Dict.Reset();
    Log(LOG_PREFIX + "Starting LoadLiveTVData")

    ipaddress = str(Dict['private_ip'])

    if Prefs['ipoveride'] != '' and Prefs['ipoveride'] is not None:
        plexlog('pref', 'using overidge')
        plexlog('pref found', Prefs['ipoveride'])
        ipaddress = Prefs['ipoveride']

    try:
        recs = JSON.ObjectFromURL('http://' + ipaddress + ':8885/guide/channels', values=None, headers={}, cacheTime=60)

        channelids = {
            'ids': [
                int(rec.split('/')[-1])
                for rec in recs
            ]
        }
    except Exception as e:
        ("Parse Failed on Channel IDS" + str(e))
        return 0

    plexlog('LoadliveTVData channelids', channelids)

    markforreload = True

    if "LiveTV" not in Dict:
        Dict["LiveTV"] = {}

    if markforreload:
        # Feed in new Data

        i = 0  # used for storing channels in correct order as reported by TabloTV ch_id

        for chid in channelids['ids']:
            i += 1
            if chid not in Dict["LiveTV"]:

                channelDict = getChannelDict(ipaddress, chid)
                # Log(LOG_PREFIX+' new channelDict = %s',channelDict)

                channelDict["order"] = i
                Dict["LiveTV"][chid] = channelDict

                # break  #Use this to debug livetv and grab 1 and only 1 channel

            else:
                datetime = Datetime.Now()
                startdatetimetz = Datetime.ParseDate(Dict["LiveTV"][chid]['airDate'])
                startdatetime = startdatetimetz.replace(tzinfo=None)
                secondsintoprogram = int((datetime.utcnow() - startdatetime).total_seconds())
                # set the duration to within a minute of it ending
                durationinseconds = int(Dict["LiveTV"][chid]['duration'] / 1000)
                plexlog('secondsintoprogram', secondsintoprogram)
                plexlog('durationinseconds', durationinseconds)
                if secondsintoprogram > (durationinseconds - 60):
                    plexlog('LiveTV', 'The Program is reloading')
                    channelDict = getChannelDict(ipaddress, chid)

                    channelDict["order"] = i
                    Dict["LiveTV"][chid] = channelDict


'''#########################################
        Name: getChannelDict()

        Parameters: None

        Purpose:

        Returns:

        Notes: Moved to init for faster debugging
#########################################'''


def getChannelDict(ipaddress, intchid):
    chid = str(intchid)
    channelDict = {}
    # channelDict['url'] = 'http://' + ipaddress + ':18080/pvr/' + episodeID +'/'
    plexlog('getChannelDict', 'Requesting chid' + chid)
    try:
        channelInfo = JSON.ObjectFromURL('http://' + ipaddress + ':8885/guide/channels/' + str(chid), values=None,
                                         headers={}, cacheTime=60)

    except Exception as e:
        plexlog('getChannelDict', "Call to CGI ch_info failed!")
        return e

    if 'channel' in channelInfo:
        chinfo = channelInfo['channel']

        # Set all defaults for min required EpisodeObject
        channelDict['private_ip'] = ipaddress
        channelDict['id'] = chid
        channelDict['title'] = ''
        channelDict['description'] = ''
        channelDict[''] = ''
        channelDict['objectID'] = channelInfo['object_id']
        channelDict['channelNumberMajor'] = 'N/A'
        channelDict['channelNumberMinor'] = 'N/A'
        channelDict['callSign'] = 'N/A'
        channelDict['duration'] = '0'
        channelDict['seasonNumber'] = 0
        channelDict['episodeNumber'] = 0
        channelDict['airDate'] = str('2014-01-01')
        channelDict['originalAirDate'] = str('2014-01-01')
        channelDict['schedule'] = ''
        channelDict['duration'] = 0
        channelDict['cast'] = []
        channelDict['releaseYear'] = 0
        channelDict['directors'] = []

        if 'major' in chinfo:
            channelDict['channelNumberMajor'] = chinfo['major']
        if 'minor' in chinfo:
            channelDict['channelNumberMinor'] = chinfo['minor']
        if 'call_sign' in chinfo:
            channelDict['callSign'] = chinfo['call_sign']
            channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(
                    channelDict['callSign'])
            channelDict['art'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(
                    channelDict['callSign'])
        else:
            channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(
                    channelDict['channelNumberMajor'] + '-' + channelDict['channelNumberMinor'])
            channelDict['art'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(
                    channelDict['callSign'])

        # set default channelNumber AFTER trying to get the number major and number minor
        channelDict['channelNumber'] = str(channelDict['channelNumberMajor']) + '-' + str(channelDict['channelNumberMinor'])
        try:
            epg_info = JSON.ObjectFromURL('http://{}:8885/views/livetv/channels/{}'.format(ipaddress, chid), cacheTime=60)[0]
            epg_info.update(JSON.ObjectFromURL('http://{}:8885{}'.format(ipaddress, epg_info['path'])))
            epg_info.update(epg_info.get('airing_details', {}))
        except Exception as e:
            return channelDict

        for key, chtype in (('series', 'Series'), ('movies', 'Movie'), ('sport', 'Sport'), ('programs', 'Program')):
            if key in epg_info:
                channelDict['type'] = chtype
                epg_info.update(epg_info[key])
                break

        try:
            channelDict['seriesThumb'] = 'http://{}/stream/thumb?id={}'.format(ipaddress, epg_info['thumbnail_image']['image_id'])
            channelDict['art'] = 'http://{}/stream/thumb?id={}'.format(ipaddress, epg_info['background_image']['image_id'])
        except:
            channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])
            channelDict['art'] = channelDict['seriesThumb']

        for tablo_key, plex_key in (
            ('season_number', 'seasonNumber'),
            ('episode_number', 'episodeNumber'),
            ('datetime', 'airDate',),
            ('orig_air_date', 'originalAirDate'),
            ('description', 'summary'),
            ('title', 'title'),
            ('plot', 'plot')
        ):
            channelDict[plex_key] = epg_info.get(tablo_key)

        if 'duration' in epg_info:
            channelDict['duration'] = int(epg_info['duration'])


    return channelDict


'********************************************************************************************'
'********************** END OF LIVE TV CODE *************************************************'
'********************************************************************************************'

'********************************************************************************************'
'********************** Start OF Recorded TV CODE ********************************************'
'********************************************************************************************'

'''#########################################
        Name: allrecordings()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/allrecordings', allow_sync=True)
def allrecordings(title, url):
    loadData()

    oc = ObjectContainer()
    oc.title1 = title
    # Check for cached data, if we do not have any, run load data
    if "RecordedTV" not in Dict:
        loadData()
    # if we do have data, create episode objects for each episode
    if "RecordedTV" in Dict:
        Log(Dict['RecordedTV'])
        for recnum, value in Dict["RecordedTV"].iteritems():
            try:
                episodeDict = value
                Log(episodeDict)

                oc.add(getepisodeasmovie(episodeDict))
            except Exception as e:
                Log(" Failed on episode " + str(e))
    # if we do have data, create episode objects for each episode
    if "Movies" in Dict:

        for recnum, value in Dict["Movies"].iteritems():
            try:
                recordingDict = value

                oc.add(getmovie(recordingDict))
            except Exception as e:
                Log(" Failed on movie " + str(e))
    if "Sports" in Dict:

        for recnum, value in Dict["Sports"].iteritems():
            try:
                recordingDict = value

                oc.add(getevent(recordingDict))
            except Exception as e:
                Log(" Failed on event " + str(e))
    # Resort the records so that the latest recorded episodes are at the top of the list
    oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)
    oc.add(PrefsObject(title='Change your IP Address', thumb=R(ICON_PREFS)))
    return oc


'''#########################################
        Name: Movies()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Movies', allow_sync=True)
def Movies(title):
    oc = ObjectContainer()
    oc.title1 = "Movies"
    # Update the data on every call since we intelligently load the actual metadata
    loadData()

    if "Movies" in Dict:

        shows = {}
        data = Dict["Movies"]
        for recnum, value in data.iteritems():
            episodeDict = value
            try:
                oc.add(getmovie(episodeDict))
            except Exception as e:
                Log(" Failed on event " + str(e))
    oc.objects.sort(key=lambda obj: obj.title)

    return oc


'''#########################################
        Name: Sports()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Sports', allow_sync=True)
def Sports(title):
    oc = ObjectContainer()
    oc.title1 = "Sports"
    # Update the data on every call since we intelligently load the actual metadata
    loadData()

    if "Sports" in Dict:

        shows = {}
        data = Dict["Sports"]
        for recnum, value in data.iteritems():
            episodeDict = value
            try:
                oc.add(getevent(episodeDict))
            except Exception as e:
                Log(" Failed on Sports " + str(e))
    oc.objects.sort(key=lambda obj: obj.title)

    return oc


'''#########################################
        Name: Shows()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/shows', allow_sync=True)
def Shows(title, url):
    oc = ObjectContainer()
    oc.title1 = "Shows"
    # Update the data on every call since we intelligently load the actual metadata
    loadData()

    if "RecordedTV" in Dict:

        shows = {}
        data = Dict["RecordedTV"]

        for episodejson, value in data.iteritems():

            episodeDict = value
            try:

                seriesId = episodeDict['seriesId']
                if not seriesId in shows:
                    shows[seriesId] = 'true'
                    if not 'showname' in episodeDict:
                        episodeDict['showname'] = ''
                    if not 'backgroundart' in episodeDict:
                        episodeDict['backgroundart'] = SHOW_THUMB
                    if not 'seriesdesc' in episodeDict:
                        episodeDict['seriesdesc'] = ''
                    if not 'duration' in episodeDict:
                        episodeDict['duration'] = 1800.0
                    if not 'seriesthumb' in episodeDict:
                        episodeDict['seriesthumb'] = ICON
                    if not 'showtotalepisodes' in episodeDict:
                        episodeDict['showtotalepisodes'] = 0
                    if not 'airdate' in episodeDict:
                        episodeDict['airdate'] = '1900-01-01'

                    # url = Encodeobj('TabloRecording', episodeDict),
                    oc.add(TVShowObject(
                            rating_key=seriesId,
                            art=episodeDict['backgroundart'],
                            key=Callback(Seasons, title=episodeDict['showname'], seriesid=seriesId),
                            title=episodeDict['showname'],
                            summary=episodeDict['seriesdesc'],
                            duration=episodeDict['duration'],
                            thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['seriesthumb'], fallback=ICON),
                            episode_count=episodeDict['showtotalepisodes'],
                            originally_available_at=Datetime.ParseDate(episodeDict['airdate'])
                    ))
            except Exception as e:
                Log(" Failed on show " + str(e))
    oc.objects.sort(key=lambda obj: obj.title)

    return oc


'''#########################################
        Name: Seasons()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/seasons', allow_sync=True)
def Seasons(title, seriesid):
    oc = ObjectContainer()
    # Update the data on every call since we intelligently load the actual metadata
    loadData()

    strseriesid = str(seriesid)
    if "RecordedTV" in Dict:

        seasons = {}
        data = Dict["RecordedTV"]
        seasoncount = 0
        lastseason = ''

        for episodejson, value in data.iteritems():

            episodeDict = value
            try:

                myseriesId = str(episodeDict['seriesId'])
                if myseriesId == strseriesid:
                    if not episodeDict['seasonnum'] in seasons:
                        seasoncount += 1
                        lastseason = episodeDict['seasonnum']
                        seasons[episodeDict['seasonnum']] = 'true'
                        if 'showname' in episodeDict:
                            oc.title1 = episodeDict['showname']
                        oc.art = Resource.ContentsOfURLWithFallback(url=episodeDict['backgroundart'], fallback=ART)
                        oc.add(SeasonObject(
                                art=episodeDict['backgroundart'],
                                index=episodeDict['seasonnum'],
                                rating_key=str(seriesid) + 'S' + str(episodeDict['seasonnum']),
                                key=Callback(episodes, title=episodeDict['showname'], seriesid=seriesid,
                                             seasonnum=episodeDict['seasonnum']),
                                title='Season ' + str(episodeDict['seasonnum']),
                                thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['seriesthumb'],
                                                                         fallback=NOTV_ICON),
                        ))
            except Exception as e:
                plexlog('Seasons', " Failed on show " + str(e))

    # if their is only 1 season, skip the unneeded screen
    if seasoncount == 1:
        return episodes(title, seriesid, lastseason)
    else:
        oc.objects.sort(key=lambda obj: obj.index)
        return oc


'''#########################################
        Name: episodes()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/episodes', allow_sync=True)
def episodes(title, seriesid, seasonnum):
    seriesid = str(seriesid)
    oc = ObjectContainer()
    if seasonnum != 0:
        oc.title1 = title + " Season " + str(seasonnum) + " Episodes"
    else:
        oc.title1 = title + " Episodes"
    # Update the data on every call since we intelligently load the actual metadata
    loadData()

    if "RecordedTV" in Dict:

        seasons = {}
        data = Dict["RecordedTV"]
        for episodejson, value in data.iteritems():
            episodeDict = value
            try:

                if str(episodeDict['seriesId']) == seriesid:

                    if str(episodeDict['seasonnum']) == str(seasonnum):
                        seasons[seriesid] = 'true'
                        oc.art = Resource.ContentsOfURLWithFallback(url=episodeDict['backgroundart'], fallback=ART)
                        oc.add(getepisode(episodeDict))

            except Exception as e:
                Log(" Failed on episode " + str(e))
    oc.objects.sort(key=lambda obj: obj.index)

    return oc


'''#########################################
        Name: getepisode()

        Parameters: None

        Handler: @route

        Purpose: Returns a episode object for a recorded episode

        Returns:

        Notes:
#########################################'''


def getepisode(episodeDict):
    return EpisodeObject(
            art=episodeDict['backgroundart'],
            url=Encodeobj('TabloRecording', episodeDict),
            title=episodeDict['title'],
            show=episodeDict.get('showname'),
            season=episodeDict['seasonnum'],
            index=episodeDict['episodenum'],
            summary=episodeDict['summary'],
            duration=episodeDict['duration'],
            thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg',
                                                     fallback=episodeDict['seriesthumb']),
            originally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    )


'''#########################################
        Name: getmovie()

        Parameters: None

        Handler: @route

        Purpose: Returns a object for a movie recording

        Returns:

        Notes:
#########################################'''


def getmovie(episodeDict):
    return MovieObject(
            art=episodeDict['backgroundart'],
            url=Encodeobj('TabloRecording', episodeDict),
            title=episodeDict['title'],
            summary=episodeDict['summary'],
            duration=episodeDict['duration'],
            thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg',
                                                     fallback=episodeDict['seriesthumb']),
            originally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    )


'''#########################################
        Name: getevent()

        Parameters: None

        Handler: @route

        Purpose: Returns a object for a single event recording e.g. sports

        Returns:

        Notes:
#########################################'''


def getevent(episodeDict):
    return MovieObject(
            art=episodeDict['backgroundart'],
            url=Encodeobj('TabloRecording', episodeDict),
            title=episodeDict['title'],
            summary=episodeDict['summary'],
            duration=episodeDict['duration'],
            thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg',
                                                     fallback=episodeDict['seriesthumb']),
            originally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    )


'''#########################################
        Name: getepisode()

        Parameters: None

        Handler: @route

        Purpose: Returns a episode object for a recorded episode

        Returns:

        Notes:
#########################################'''


def getepisodeasmovie(episodeDict):
    return MovieObject(
            art=episodeDict['backgroundart'],
            url=Encodeobj('TabloRecording', episodeDict),
            title=episodeDict['showname'] + ' - ' + episodeDict['title'],
            summary=episodeDict['summary'],
            duration=episodeDict['duration'],
            thumb=Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg',
                                                     fallback=episodeDict['seriesthumb']),
            originally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    )


'''#########################################
        Name: getgoogleimage()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


def getgoogleimage(searchterm):
    imageurl = ''
    searchterm = searchterm.replace(" ", "+")
    searchurl = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=' + searchterm + '&start=0'
    data = JSON.ObjectFromURL(searchurl)

    for image_info in data['responseData']['results']:
        imageurl = image_info['unescapedUrl']
        plexlog('Google Image', image_info)
    return imageurl


'''#########################################
        Name: LoabTablos()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


def loadtablos():
    # Pass full Tablo info to here for better parsing and future multiple tablo support
    count = 0
    lasttabloip = ''
    try:
        if 'public_ip' in Dict:
            lasttabloip = Dict['public_ip']
        Dict['tabloips'] = getTabloIP()
        for tablo in Dict['tabloips']:
            count += 1
            datetime = Datetime.Now()
            last_seen_with_tz = Datetime.ParseDate(tablo['last_seen'])
            last_seen_no_tz = last_seen_with_tz.replace(tzinfo=None)
            secondssincelastseen = int((datetime.utcnow() - last_seen_no_tz).total_seconds())
            plexlog('loadtablos', secondssincelastseen)
            if secondssincelastseen < (86400):
                Dict['public_ip'] = str(tablo['public_ip'])
                Dict['private_ip'] = str(tablo['private_ip'])
        # detect if the IP address has changed (most likely due to dhcp)
        # if it did, clear the dicts because the stored IP's will be incorrect
        # @ToDo remove all references in the dicts to the tablo's IP and use the Tablos' ID
        # To find the IP in the tabloips Dict
        if Dict['public_ip'] != lasttabloip:
            cleartablodata()
    except Exception as e:
        plexlog('loadtablos Failure', e)

    return count


'''#########################################
        Name: plexlog()

        Parameters: None

        Handler:

        Purpose: Central Control of logging

        Returns:

        Notes:
#########################################'''


def plexlog(location, message):
    Log(LOG_PREFIX + str(location) + ': ' + pprint.pformat(message))


'''#########################################
        Name: cleartablodata()

        Parameters: None

        Handler:

        Purpose: Central function to reset data

        Returns:

        Notes:
#########################################'''


def cleartablodata():
    HTTP.ClearCookies()
    HTTP.ClearCache()
    Dict.Reset()
    # bug in Dict.Reset() is not deleting keys so we do this explicitedly
    if "RecordedTV" in Dict:
        del Dict["RecordedTV"]
    if "Movies" in Dict:
        del Dict["Movies"]
    if "Sports" in Dict:
        del Dict["Sports"]
    if "RecordedTV" not in Dict:
        plexlog('cleartablodata', 'Clear appears to have worked')


'''#########################################
    Name: loadData()

    Parameters: None

    Handler: @route

    Purpose:

    Returns:

    Notes:
#########################################'''


def loadData():
    ipaddress = str(Dict['private_ip'])
    if Prefs['ipoveride'] != '' and Prefs['ipoveride'] is not None:
        plexlog('pref', 'using overidge')
        plexlog('pref found', Prefs['ipoveride'])
        ipaddress = Prefs['ipoveride']

    try:
        recs = JSON.ObjectFromURL('http://' + ipaddress + ':8885/recordings/airings', values=None, headers={}, cacheTime=60)

        episodelistids = {
            'ids': [
                int(rec.split('/')[-1])
                for rec in recs
            ]
        }

    except Exception as e:
        ("Parse Failed on episode IDS" + str(e))
        return 0
    # hash = Hash.MD5(JSON.StringFromObject(episodelistids))
    markforreload = True
    if "RecordedTV" not in Dict:
        Dict["RecordedTV"] = {}
    if "Movies" not in Dict:
        Dict["Movies"] = {}
    if "Sports" not in Dict:
        Dict["Sports"] = {}
    reccount = 0

    if markforreload:
        Log('Feeding')
        # Feed in new Data
        for recnum in episodelistids['ids']:

            recnum = str(recnum)
            if recnum not in Dict["RecordedTV"] and recnum not in Dict["Movies"] and recnum not in Dict["Sports"] and reccount < 999:
                try:

                    recordingDict = getEpisodeDict(ipaddress, recnum, True)
                    if recordingDict['recordingtype'] == 'TvShow':
                        Dict["RecordedTV"][recnum] = recordingDict
                    elif recordingDict['recordingtype'] == 'Sports':
                        Dict["Sports"][recnum] = recordingDict
                    elif recordingDict['recordingtype'] == 'Movie':
                        Dict["Movies"][recnum] = recordingDict
                    else:
                        # this should be an exception so lets ignore it
                        #plexlog('loaddata', 'Exception retrieving ' + recnum)
                        recordingDict['recordingtype'] = 'Exception'
                    reccount = reccount + 1
                except Exception as e:
                    plexlog("loaddata - Parse Failed on jsonurl ", e)


        plexlog('loaddata', "Cleaning up extra items ... ")
        # Feed in new Data
        Temp = Dict["RecordedTV"].copy()
        for episode in Temp:
            if not int(episode) in episodelistids['ids']:
                try:
                    Log('deleting ' + episode)
                    if episode in Dict["RecordedTV"]:
                        del Dict["RecordedTV"][episode]

                except Exception as e:
                    Log("Parse Failed on delete key " + str(e))
        Temp = Dict["Movies"].copy()
        for movie in Temp:
            if not int(movie) in episodelistids['ids']:
                try:
                    Log('deleting Movie ' + movie)
                    if movie in Dict["Movies"]:
                        del Dict["Movies"][movie]

                except Exception as e:
                    Log("Parse Failed on delete move key " + str(e))



                    # Log(myDict)


'''#########################################
    Name: getEpisodeDict()

    Parameters: None

    Purpose:

    Returns:

    Notes:
#########################################'''


def getEpisodeDict(ipaddress, episodeID, UseMeta):
    recordingDict = {}
    recordingDict['url'] = 'http://' + ipaddress + ':18080/pvr/' + episodeID + '/'
    recordingobj = {}
    recordingtype = 'Unknown'
    if UseMeta:
        meta_url = recordingDict['url'] + 'meta.txt'

        # Request the URL
        try:
            recordinginfo = JSON.ObjectFromURL(meta_url, cacheTime=7200, headers={'Accept': 'application/json'})
        except Exception as e:
            Log(LOG_PREFIX + 'call to meta.txt failed. File not found')
            return e
    else:
        recordingobj = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/rec_info?id=' + episodeID, values=None,
                                          headers={}, cacheTime=60)

    if 'meta' in recordingobj or UseMeta:
        if UseMeta == False:
            recordinginfo = recordingobj['meta']
        recordingDict['private_ip'] = ipaddress
        recordingDict['episodeID'] = episodeID
        recordingDict['title'] = ''
        # use image url to retrieve show images.  Snap.jpg isn't always available
        recordingDict['seriesthumb'] = recordingDict['url'] + 'snap.jpg'
        recordingDict['backgroundart'] = recordingDict['url'] + 'snap.jpg'
        recordingDict['summary'] = 'No Summary'
        root = 'other'

        '''#### CAPTURE EPISODE ONLY INFO ####### '''
        if 'recEpisode' in recordinginfo:
            recordingtype = 'TvShow'
            root = 'recEpisode'
            if 'jsonForClient' in recordinginfo['recSeries']:
                seriesinfo = recordinginfo['recSeries']['jsonForClient']
            else:
                # don't see any jsonFromTribune properties coming from Tablo. This may be legacy stuff
                seriesinfo = recordinginfo['recSeries']['jsonFromTribune']
            # showname is the tv show name e.g. 'Bewitched'
            # showid identifies the tv series (i.e. all episodes in all seasons)
            if 'seriesId' in seriesinfo:
                recordingDict['seriesId'] = seriesinfo['seriesId']
                recordingDict['showid'] = seriesinfo['seriesId']
            else:
                recordingDict['seriesId'] = seriesinfo['objectID']
                recordingDict['showid'] = seriesinfo['objectID']
            if 'title' in seriesinfo:
                recordingDict['showname'] = seriesinfo['title']
                recordingDict['title'] = seriesinfo['title']
            else:
                recordingDict['showname'] = ''
            recordingDict['seriesdesc'] = ''
            if 'shortDescription' in seriesinfo:
                recordingDict['seriesdesc'] = seriesinfo['shortDescription']
            elif 'description' in seriesinfo:
                recordingDict['seriesdesc'] = seriesinfo['description']
            if 'imageJson' in recordinginfo['recSeries']:
                for seriesimage in recordinginfo['recSeries']['imageJson']['images']:
                    # Log(LOG_PREFIX + 'imageType = %s', seriesimage['imageType'])
                    if seriesimage['imageType'] == 'iconic_4x3_large':
                        recordingDict['backgroundart'] = 'http://' + ipaddress + ':18080/stream/thumb?id=' + str(
                                seriesimage['imageID'])
                    if seriesimage['imageType'] == 'series_3x4_small':
                        recordingDict['seriesthumb'] = 'http://' + ipaddress + ':18080/stream/thumb?id=' + str(
                                seriesimage['imageID'])
            if 'totalEpisodes' in seriesinfo:
                recordingDict['showtotalepisodes'] = int(seriesinfo['totalEpisodes'])

            if 'jsonForClient' in recordinginfo[root]:
                episodeinfo = recordinginfo[root]['jsonForClient']
                # is this the id of the show or the series? what is it used for
                # seriesid=episodeinfo['relationships']['recSeries']
                # while the show's id is episodeinfo['objectID']
                # recordingDict['showid'] = episodeinfo['objectID']
                recordingDict['showid'] = episodeinfo['relationships']['recSeries']
                recordingDict['seasonnum'] = int(episodeinfo['seasonNumber'])
                recordingDict['episodenum'] = int(episodeinfo['episodeNumber'])
            else:
                # don't see any jsonFromTribune properties coming from Tablo. This may be legacy stuff
                episodeinfo = recordinginfo[root]['jsonFromTribune']
                recordingDict['showname'] = episodeinfo['program']['title']
                recordingDict['showid'] = episodeinfo['seriesId']
                recordingDict['seasonnum'] = int(episodeinfo['seasonNumber'])
                recordingDict['episodenum'] = int(episodeinfo['episodeNumber'])

        '''#### CAPTURE Movie ONLY INFO ####### '''
        if 'recMovieAiring' in recordinginfo:
            recordingtype = 'Movie'
            root = 'recMovieAiring'
            movieinfo = recordinginfo['recMovie']['jsonForClient']
            if 'plot' in movieinfo:
                recordingDict['summary'] = movieinfo['plot']
            else:
                recordingDict['summary'] = ''
            if 'title' in movieinfo:
                recordingDict['title'] = movieinfo['title']

        '''#### CAPTURE Events/Sports-Events ONLY INFO ####### '''
        if 'recSportEvent' in recordinginfo:
            recordingtype = 'Sports'
            root = 'recSportEvent'

        if 'jsonForClient' in recordinginfo[root]:
            episodeinfo = recordinginfo[root]['jsonForClient']
            if 'episodeTitle' in episodeinfo:
                recordingDict['title'] = episodeinfo['episodeTitle']
            elif 'eventTitle' in episodeinfo:
                recordingDict['title'] = episodeinfo['eventTitle']
            elif 'title' in episodeinfo:
                recordingDict['title'] = episodeinfo['title']
        else:
            episodeinfo = recordinginfo[root]['jsonFromTribune']
            if 'episodeTitle' in episodeinfo['program']:
                recordingDict['title'] = episodeinfo['program']['episodeTitle']
            elif 'title' in episodeinfo['program']:
                recordingDict['title'] = episodeinfo['program']['title']
            if 'longDescription' in episodeinfo['program']:
                recordingDict['summary'] = episodeinfo['program']['longDescription']
            elif 'longDescription' in episodeinfo:
                recordingDict['summary'] = episodeinfo['longDescription']

        # Description is not always in the JSON, so test first
        if 'description' in recordinginfo[root]['jsonForClient']:
            recordingDict['summary'] = recordinginfo[root]['jsonForClient']['description']

        # convert to seconds
        if 'duration' in recordinginfo[root]['jsonForClient']['video']:
            # convert to seconds
            recordingDict['duration'] = int(recordinginfo[root]['jsonForClient']['video']['duration']) * 1000
        else:
            recordingDict['duration'] = 0

        recordingDict['video'] = recordinginfo[root]['jsonForClient']['video']

        recordingDict['airdate'] = recordinginfo[root]['jsonForClient']['airDate']
        recordingDict['recordingtype'] = recordingtype

    return recordingDict


'''#########################################
    Name: GetTabloIP()

    Parameters: None

    Handler:

    Purpose: Central Control of logging

    Returns:

    Notes:
#########################################'''


def getTabloIP():
    plexlog(LOG_PREFIX, "Starting getTabloIP Call")

    url = 'https://api.tablotv.com/assocserver/getipinfo/'
    try:
        if Prefs['ipoveride'] != '' and Prefs['ipoveride'] is not None:
            plexlog('pref', 'using overidge')
            plexlog('pref found', Prefs['ipoveride'])
            tablo = {}
            tablo['public_ip'] = Prefs['ipoveride']
            tablo['private_ip'] = Prefs['ipoveride']
            return tablo
    except Exception as e:
        plexlog("Error when calling getTabloIPPrefs", e)
    try:
        result = JSON.ObjectFromURL(url)

    except Exception as e:
        plexlog("Error when calling getipinfo", e)
        return e

    plexlog('GetTabloIP', result)
    if 'success' in result:

        return result['cpes']

    else:
        return ''


'''#########################################
        Name: None

        Parameters: None

        Handler: None

        Purpose: Placing fcn calls outside of a function will cause plex to preload data before running chanel.
        This allows us to load most data upfront and cut down on loading/execution time

        Returns: None

        Notes:
#########################################'''

if 'ver' in Dict:
    if Dict['ver'] != VERSION:
        cleartablodata()
    loadData()
else:
    cleartablodata()
    loadtablos()
    loadData()
    loadLiveTVData(Dict)
    Dict['ver'] = VERSION
