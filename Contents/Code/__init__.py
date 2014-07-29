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
VERSION = "0.98"
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
        if count == 0:
            return ObjectContainer(header='Error', message='API Could Not Locate a tablo on your network')
    except:
        plexlog('Main Menu', 'Early LoadTablo Fail')

    oc = ObjectContainer()

    if 'private_ip' not in Dict:
        Log('privateIPERROR')
        return ObjectContainer(header='Error', message=' Could Not Locate a tablo on your network')

    else:
        try:
            episodelistids = JSON.ObjectFromURL('http://' + Dict['private_ip'] + ':18080/plex/rec_ids', values=None,
                                                headers={}, cacheTime=60)
        except Exception as e:
            return ObjectContainer(header='Error', message='Could Not Connect to your tablo')

        oc.add(
            DirectoryObject(thumb=R('icon_livetv_hd.jpg'), key=Callback(livetvnew, title="Live TV"), title="Live TV"))
        oc.add(DirectoryObject(thumb=R('icon_recordings_hd.jpg'),
                               key=Callback(Shows, title="Shows", url=Dict['private_ip']), title="Shows"))
        oc.add(DirectoryObject(thumb=R('icon_movies_hd.jpg'),
                               key=Callback(Movies, title="Movies"), title="Movies"))
        oc.add(DirectoryObject(thumb=R('icon_tvshows_hd.jpg'),
                               key=Callback(allrecordings, title="All Recordings", url=Dict['private_ip']),
                               title="Recent Recordings"))
        oc.add(DirectoryObject(thumb=R('icon_scheduled_hd.jpg'),
                               key=Callback(scheduled, title="Scheduled Recordings"),
                               title="Scheduled Recordings"))
        oc.add(DirectoryObject(thumb=R('icon_settings_hd.jpg'), key=Callback(Help, title="Help"), title="Help"))

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
    oc.add(DirectoryObject(thumb=R('info.png'), key=Callback(detected, title="About Your Tablo"), title="About Your Tablo"))
    oc.add(DirectoryObject(thumb=R('icon-prefs.png'), key=Callback(ResetPlugin, title="Reset Plugin"),
                           title="Reset Plugin "))
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
    myurl = "http://" + Dict['private_ip'] +":8886"
    cmd = "/info/guideSeries/get"
    parms = {"filter":{"orderby":"startdate","schedulestate":"scheduled"}}
    result = TabloAPI(myurl,cmd,parms)
   # plexlog('detect',result)
    recordings = result['result']['series']
    oc = ObjectContainer()
    oc.title1 = title
    ipaddress = Dict['private_ip']
    datetime = Datetime.Now()
    timezoneoffset = int((datetime - datetime.utcnow()).total_seconds())
    plexlog('secondsbetween',timezoneoffset)
    plexlog('date.now',datetime)
    plexlog('date.utcnow',datetime.utcnow())

    # Loop through channels and create a Episode Object for each show
    for airingData in recordings:
                unixtimestarted = Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime']))
                displayeddate = str(Datetime.FromTimestamp(Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime'])) + timezoneoffset))
                recordingtype = 'Unknown'
                if 'scheduleType' in airingData['schedule']:
                    recordingtype = airingData['schedule']['scheduleType']

                plexlog('airingdata loop',airingData)
                # All commented out are set in TabloLive.pys helpers
                oc.add(
                    #TVShowObject(
PopupDirectoryObject(
                    #rating_key=airingData['objectID'],
                    #show=airingData['title'],
                    title= displayeddate + ' - ' + airingData['title'],
                    summary='Original Air Date: ' + airingData['originalAirDate'] + ' Scheduled to Record: '+ recordingtype ,
                    # originally_available_at = Datetime.ParseDate(airingData['originalAirDate']),  #writers = ,
                    # directors = ,  #producers = ,  #guest_stars = ,
                    key=Callback(nothing, title=title) , # season = airingData['seasonNumber'],
                    thumb=Resource.ContentsOfURLWithFallback(url='http://' + ipaddress + '/stream/thumb?id=' + str(airingData['images'][0]['imageID']), fallback=NOTV_ICON),
                    # art= Resource.ContentsOfURLWithFallback(url=airingData['art'], fallback=ART),
                    #source_title='TabloTV'
                    # duration = airingData['duration']  #description = airingData['description']
                )
                )

    oc.objects.sort(key=lambda obj: obj.key, reverse=False)
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
    oc.header='No More Information Available'
    oc.message='No More Information Available'

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
    myurl = "http://" + Dict['private_ip'] +":8886"
    cmd = "/server/status"
    parms = {}
    result = TabloAPI(myurl,cmd,parms)
    plexlog('detect',result)
    tablo = result['result']
    mymessage = mymessage + " Tablo Reported Name: " + tablo['name'] + '   _______  Reported IP: ' + tablo['localAddress'] + '___________ Running Version: ' + tablo['serverVersion']
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
                    title=airingData['title'],
                    summary=airingData['description'],
                    # originally_available_at = Datetime.ParseDate(airingData['originalAirDate']),  #writers = ,
                    # directors = ,  #producers = ,  #guest_stars = ,
                    absolute_index=airingData['order'],  # season = airingData['seasonNumber'],
                    thumb=Resource.ContentsOfURLWithFallback(url=airingData['seriesThumb'], fallback=NOTV_ICON),
                    # art= Resource.ContentsOfURLWithFallback(url=airingData['art'], fallback=ART),
                    source_title='TabloTV'
                    # duration = airingData['duration']  #description = airingData['description']
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

    channelids = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_ids', values=None, headers={},
                                    cacheTime=600)

    plexlog( 'LoadliveTVData channelids',channelids)

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
                secondsintoprogram = int(( datetime.utcnow() - startdatetime).total_seconds())
                # set the duration to within a minute of it ending
                durationinseconds = int(Dict["LiveTV"][chid]['duration'] / 1000)
                plexlog('secondsintoprogram',secondsintoprogram)
                plexlog('durationinseconds',durationinseconds)
                if secondsintoprogram > (durationinseconds- 60):
                    plexlog('LiveTV','The Program is reloading')
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
        channelInfo = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_info?id=' + str(chid), values=None,
                                         headers={}, cacheTime=60)

    except Exception as e:
        plexlog('getChannelDict', "Call to CGI ch_info failed!")
        return e

    if 'meta' in channelInfo:
        chinfo = channelInfo['meta']

        # Set all defaults for min required EpisodeObject
        channelDict['private_ip'] = ipaddress
        channelDict['id'] = chid
        channelDict['title'] = ''
        channelDict['epTitle'] = ''
        channelDict['description'] = ''
        # channelDict[''] = ''
        channelDict['objectID'] = chinfo['objectID']
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

        if 'channelNumberMajor' in chinfo:
            channelDict['channelNumberMajor'] = chinfo['channelNumberMajor']
        if 'channelNumberMinor' in chinfo:
            channelDict['channelNumberMinor'] = chinfo['channelNumberMinor']
        if 'callSign' in chinfo:
            channelDict['callSign'] = chinfo['callSign']
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
        channelDict['channelNumber'] = str(chinfo['channelNumberMajor']) + '-' + str(chinfo['channelNumberMinor'])

        if chinfo['dataAvailable'] == 1:

            try:
                channelEPGInfo = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_epg?id=' + str(chid),
                                                    values=None, headers={}, cacheTime=60)
            except Exception as e:

                return channelDict

            if 'meta' in channelEPGInfo:
                epgInfo = channelEPGInfo['meta']
                imageInfo = 0  # initialize to avoide reference before assignment
            else:

                channelDict['message'] = "No ch_epg info found. Using ch_info."
                return channelDict

            if 'guideSportEvent' in epgInfo:

                guideInfo = epgInfo['guideSportEvent']
                channelDict['type'] = 'Sport'
                if 'guideSportOrganization' in epgInfo:
                    Log(LOG_PREFIX + 'Guide Sport Organization')
                    guideSportOrg = epgInfo['guideSportOrganization']
                    if 'imageJson' in guideSportOrg:
                        imageInfo = guideSportOrg['imageJson']['images']
            elif 'guideEpisode' in epgInfo:

                guideInfo = epgInfo['guideEpisode']
                channelDict['type'] = 'Episode'
                if 'guideSeries' in epgInfo:
                    Log(LOG_PREFIX + 'Series')
                    guideDetailInfo = epgInfo['guideSeries']
                    channelDict['type'] = 'Series'
                    if 'imageJson' in guideDetailInfo:
                        imageInfo = guideDetailInfo['imageJson']['images']
            elif 'guideMovieAiring' in epgInfo:

                guideInfo = epgInfo['guideMovieAiring']
                channelDict['type'] = 'Movie'
                if 'guideMovie' in epgInfo:
                    Log(LOG_PREFIX + 'guideMovie')
                    guideDetailInfo = epgInfo['guideMovie']
                    channelDict['type'] = 'guideMovie'
                    if 'imageJson' in guideDetailInfo:
                        imageInfo = guideDetailInfo['imageJson']['images']
            else:
                plexlog(LOG_PREFIX, 'UNHANDLED TYPE!!! not sport or movie or episode')
                return channelDict

            # set images outside of series logic to ensure defaults are set
            if imageInfo:
                artFound = 0
                thumbFound = 0
                for seriesimage in imageInfo:
                    if seriesimage['imageStyle'] == 'background' and artFound == 0:
                        channelDict['art'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
                        artFound = 1
                    if seriesimage['imageStyle'] == 'snapshot' and artFound == 0:
                        channelDict['art'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
                        artFound = 1
                    if seriesimage['imageStyle'] == 'thumbnail' and thumbFound == 0:
                        channelDict['seriesThumb'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(
                            seriesimage['imageID'])
                        thumbFound = 1
                    if seriesimage['imageStyle'] == 'cover' and thumbFound == 0:
                        channelDict['seriesThumb'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(
                            seriesimage['imageID'])
                        thumbFound = 1
            else:
                channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(
                    channelDict['callSign'])

            # Guide Series or Episode Info
            if channelDict['type'] != 'Sport':
                guideEpInfo = guideInfo['jsonForClient']

                if 'seasonNumber' in guideEpInfo:
                    channelDict['seasonNumber'] = int(guideEpInfo['seasonNumber'])
                if 'episodeNumber' in guideEpInfo:
                    channelDict['episodeNumber'] = int(guideEpInfo['episodeNumber'])
                if 'airDate' in guideEpInfo:
                    channelDict['airDate'] = guideEpInfo['airDate']
                if 'originalAirDate' in guideEpInfo:
                    channelDict['originalAirDate'] = guideEpInfo['originalAirDate']
                if 'description' in guideEpInfo:
                    channelDict['description'] = guideEpInfo['description']
                if 'duration' in guideEpInfo:
                    channelDict['duration'] = int(guideEpInfo['duration']) * 1000
                if 'schedule' in guideEpInfo:
                    channelDict['schedule'] = guideEpInfo['schedule']
                if 'title' in guideEpInfo:
                    channelDict['epTitle'] = guideEpInfo['title']

            if channelDict['type'] == 'Series' or channelDict['type'] == 'guideMovie':
                guideJsonInfo = guideDetailInfo['jsonForClient']
                if 'description' in guideJsonInfo and channelDict['description'] == '':
                    channelDict['description'] = guideJsonInfo['description']
                elif 'plot' in guideJsonInfo:
                    channelDict['description'] = guideJsonInfo['plot']
                if 'title' in guideJsonInfo:
                    channelDict['title'] = guideJsonInfo['title']
                if 'duration' in guideJsonInfo:
                    channelDict['duration'] = int(guideJsonInfo['duration']) * 1000
                if 'originalAirDate' in guideJsonInfo:
                    channelDict['originalAirDate'] = guideJsonInfo['originalAirDate']
                if 'cast' in guideJsonInfo:
                    channelDict['cast'] = [castMember for castMember in guideJsonInfo['cast']]
                if 'runtime' in guideJsonInfo:
                    channelDict['runtime'] = guideJsonInfo['runtime']
                if 'releaseYear' in guideJsonInfo:
                    channelDict['releaseYear'] = guideJsonInfo['releaseYear']
                if 'directors' in guideJsonInfo:
                    channelDict['directors'] = [director for director in guideJsonInfo['directors']]
                if 'schedule' in guideJsonInfo:
                    channelDict['schedule'] = guideJsonInfo['schedule']
                if 'airDate' in guideJsonInfo:
                    channelDict['airDate'] = guideJsonInfo['airDate']

            if channelDict['type'] == 'Sport':
                guideJsonInfo = guideInfo['jsonForClient']

                if 'eventTitle' in guideJsonInfo:
                    channelDict['title'] = guideJsonInfo['eventTitle']
                    channelDict['epTitle'] = guideJsonInfo['eventTitle']
                if 'airDate' in guideJsonInfo:
                    channelDict['airDate'] = guideJsonInfo['airDate']
                if 'duration' in guideJsonInfo:
                    channelDict['duration'] = int(guideJsonInfo['duration']) * 1000

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

        for recnum, value in Dict["RecordedTV"].iteritems():
            try:
                episodeDict = value
                # The commented out code was to try to bypass a tuncation issue with plex sync
                # Plex sync still did not work but this does resolve the truncation
                # and may be needed later
                # altdict = {}
                # altdict['alt'] = 'Yes'
                # altdict['private_ip'] = Dict['private_ip']
                # altdict['episodeID'] = episodeDict['episodeID']
                # myurl = Encodeobj('TabloRecording' , altdict)

                oc.add(getepisodeasmovie(episodeDict))
            except Exception as e:
                Log(" Failed on episode " + str(e))
    # if we do have data, create episode objects for each episode
    if "Movies" in Dict:

        for recnum, value in Dict["Movies"].iteritems():
            try:
                recordingDict = value
                # The commented out code was to try to bypass a tuncation issue with plex sync
                # Plex sync still did not work but this does resolve the truncation
                # and may be needed later
                # altdict = {}
                # altdict['alt'] = 'Yes'
                # altdict['private_ip'] = Dict['private_ip']
                # altdict['episodeID'] = episodeDict['episodeID']
                # myurl = Encodeobj('TabloRecording' , altdict)

                oc.add(getmovie(recordingDict))
            except Exception as e:
                Log(" Failed on movie " + str(e))
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
                Log(" Failed on movie " + str(e))
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

                    #url = Encodeobj('TabloRecording', episodeDict),
                    oc.add(TVShowObject(
                        rating_key=seriesId,
                        art=episodeDict['backgroundart'],
                        key=Callback(Seasons, title=episodeDict['showname'],  seriesid=seriesId),
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

    if "RecordedTV" in Dict:

        seasons = {}
        data = Dict["RecordedTV"]
        seasoncount = 0
        lastseason = ''

        for episodejson, value in data.iteritems():

            episodeDict = value
            try:

                myseriesId = episodeDict['seriesId']

                if myseriesId == seriesid:
                    if not episodeDict['seasonnum'] in seasons:
                        seasoncount += 1
                        lastseason = episodeDict['seasonnum']
                        seasons[episodeDict['seasonnum']] = 'true'
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

                if episodeDict['seriesId'] == seriesid:

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

        Purpose: Returns a episode object for a recorded episode

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


        episodelistids = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/rec_ids', values=None, headers={}, cacheTime=60)


        #hash = Hash.MD5(JSON.StringFromObject(episodelistids))
        markforreload = True
        if "RecordedTV" not in Dict:
            Dict["RecordedTV"] = {}
        if "Movies" not in Dict:
            Dict["Movies"] = {}
        reccount = 0


        if markforreload :
            Log('Feeding')
            #Feed in new Data
            for recnum in episodelistids['ids']:

                recnum = str(recnum)
                if recnum not in Dict["RecordedTV"] and recnum not in Dict["Movies"]  and reccount < 999:
                    try:

                        recordingDict = getEpisodeDict(ipaddress,recnum,True)
                        if recordingDict['recordingtype'] == 'TvShow':
                            Dict["RecordedTV"][recnum]= recordingDict
                        if recordingDict['recordingtype'] == 'Movie':
                            Dict["Movies"][recnum]= recordingDict
                        reccount = reccount + 1
                    except Exception as e:
                        plexlog("loaddata - Parse Failed on jsonurl ",e)
            plexlog('loaddata','Cleaning')
            #Feed in new Data
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



        #Log(myDict)

'''#########################################
    Name: getEpisodeDict()

    Parameters: None

    Purpose:

    Returns:

    Notes:
#########################################'''
def getEpisodeDict(ipaddress,episodeID,UseMeta):
    recordingDict = {}
    recordingDict['url'] = 'http://' + ipaddress + ':18080/pvr/' + episodeID +'/'
    recordingobj = {}
    recordingtype = 'Unknown'
    if UseMeta:
        meta_url = recordingDict['url'] + 'meta.txt'

        # Request the URL
        try:
            recordinginfo = JSON.ObjectFromURL(meta_url, cacheTime=7200)
        except Exception as e:
            Log(LOG_PREFIX+'call to meta.txt failed. File not found')
            return e
    else:
        recordingobj = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/rec_info?id=' + episodeID, values=None, headers={}, cacheTime=60)

    if 'meta' in recordingobj or UseMeta:
        if UseMeta == False:
            recordinginfo = recordingobj['meta']
        recordingDict['private_ip'] = ipaddress
        recordingDict['episodeID'] = episodeID
        #use image url to retrieve show images.  Snap.jpg isn't always available
        recordingDict['seriesthumb'] = recordingDict['url'] + 'snap.jpg'
        recordingDict['backgroundart'] = recordingDict['url'] + 'snap.jpg'
        recordingDict['summary'] = 'No Summary'
        root= 'other'
        '''#### CAPTURE EPISODE ONLY INFO ####### '''
        if 'recEpisode' in recordinginfo:
            recordingtype = 'TvShow'
            root= 'recEpisode'
            recordingDict['seriesId'] = recordinginfo['recSeries']['jsonFromTribune']['seriesId']
            recordingDict['seriesdesc'] = ''
            if 'shortDescription' in recordinginfo['recSeries']['jsonFromTribune']:
                recordingDict['seriesdesc'] = recordinginfo['recSeries']['jsonFromTribune']['shortDescription']
            if 'imageJson' in recordinginfo['recSeries']:
                for seriesimage in recordinginfo['recSeries']['imageJson']['images']:
                    #Log(LOG_PREFIX + 'imageType = %s', seriesimage['imageType'])
                    if seriesimage['imageType'] == 'iconic_4x3_large':
                        recordingDict['backgroundart'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
                    if seriesimage['imageType'] == 'series_3x4_small':
                        recordingDict['seriesthumb'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
            recordingDict['showtotalepisodes'] = int(recordinginfo['recSeries']['jsonFromTribune']['totalEpisodes'])
            recordingDict['showname'] = recordinginfo[root]['jsonFromTribune']['program']['title']
            recordingDict['showid'] = recordinginfo['recSeries']['jsonFromTribune']['seriesId']
            recordingDict['seasonnum'] = int(recordinginfo[root]['jsonForClient']['seasonNumber'])
            recordingDict['episodenum'] = int(recordinginfo[root]['jsonForClient']['episodeNumber'])

        '''#### CAPTURE Movie ONLY INFO ####### '''
        if 'recMovieAiring' in recordinginfo:
            recordingtype = 'Movie'
            root = 'recMovieAiring'
            if 'plot' in recordinginfo['recMovie']['jsonForClient']:
                recordingDict['summary'] = recordinginfo['recMovie']['jsonForClient']['plot']

        if 'episodeTitle' in recordinginfo[root]['jsonFromTribune']['program']:
            recordingDict['title']  = recordinginfo[root]['jsonFromTribune']['program']['episodeTitle']
        else:
            recordingDict['title'] = recordinginfo[root]['jsonFromTribune']['program']['title']
        #Description is not always in the JSON, so test first
        if 'description' in recordinginfo[root]['jsonForClient']:
            recordingDict['summary'] = recordinginfo[root]['jsonForClient']['description']
        elif 'longDescription' in recordinginfo[root]['jsonFromTribune']['program']:
            recordingDict['summary'] = recordinginfo[root]['jsonFromTribune']['program']['longDescription']
        elif 'longDescription' in recordinginfo[root]['jsonFromTribune']:
            recordingDict['summary'] = recordinginfo[root]['jsonFromTribune']['longDescription']


        #convert to seconds
        if 'duration' in recordinginfo[root]['jsonForClient']['video']:
            #convert to seconds
            recordingDict['duration']  = int(recordinginfo[root]['jsonForClient']['video']['duration']) *1000
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
    plexlog(LOG_PREFIX , "Starting getTabloIP Call")

    url = 'https://api.tablotv.com/assocserver/getipinfo/'
    try:
        if Prefs['ipoveride'] != '' and Prefs['ipoveride'] is not None:
            plexlog('pref','using overidge')
            plexlog('pref found',Prefs['ipoveride'])
            tablo = {}
            tablo['public_ip'] = Prefs['ipoveride']
            tablo['private_ip'] = Prefs['ipoveride']
            return tablo
    except Exception as e:
        plexlog("Error when calling getTabloIPPrefs" ,e)
    try:
        result = JSON.ObjectFromURL(url)

    except Exception as e:
        plexlog("Error when calling getipinfo" ,e)
        return e

    plexlog('GetTabloIP',result)
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
