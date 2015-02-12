'''#########################################
        Author: @DavidVR - Van Ronk, David
                        @PiX64  - Reid, Michael

    Source:

    Purpose:

    Legal:
#########################################'''
import pprint

'''#### Define Global Vars ####'''
TITLE = 'Tablo'
ART = 'channel_splash_hd.png'
ICON = 'icon.png'
NOTV_ICON = 'no_tv_110x150.jpg'
ICON_PREFS = 'icon_settings_hd.jpg'
SHOW_THUMB = 'no_tv_110x150.jpg'
PREFIX = '/video/tablo'
LOG_PREFIX = "***TabloTV2: "
ASSOCSERVER = 'https://api.tablotv.com/assocserver/getipinfo/'
VERSION = "2.0"
FOLDERS_COUNT_IN_TITLE = True  # Global VAR used to enable counts on titles
DEBUG_IT = True
ONE_DAY_IN_SECONDS = 86400
UseMeta = True

''' LOGGING FUNCTION '''
def tplog(location, message):
    if DEBUG_IT:
        Log(LOG_PREFIX + str(location) + ': ' + pprint.pformat(message))

############################################
###########  "Database" FUNCTIONS   ###########
############################################
def build_tablos():
    # build a list of Tablos from the Association Server
    count = 0
    tplog("Start Build_Tablos" ,'')
    try:
        if 'OVERRIDE_IP' in Prefs:
            if Prefs['OVERRIDE_IP'] != '' and Prefs['OVERRIDE_IP'] is not None:
                tablos = {}
                tablos[0]['PRIVATE_IP'] = Prefs['OVERRIDE_IP']
                tablos[0]['PRIVATE_PORT'] = Prefs['OVERRIDE_PORT']
                tablos[0]['PUBLIC_IP'] = Prefs['OVERRIDE_IP']
                tablos[0]['PUBLIC_PORT'] = Prefs['OVERRIDE_PORT']
                Dict['tablos'] = tablos
                return True
    except Exception as e:
        tplog("Error Checking Override" ,e)

    try:
        cpes = JSON.ObjectFromURL(ASSOCSERVER)

        if 'success' in cpes:
            tablos = {}
            for cpe in cpes['cpes']:
                count += 1
                datetime = Datetime.Now()
                last_seen_with_tz = Datetime.ParseDate(cpe['last_seen'])
                tablo_server_id = cpe['serverid']
                last_seen_no_tz = last_seen_with_tz.replace(tzinfo=None)
                seconds_since_last_seen = int(( datetime.utcnow() - last_seen_no_tz).total_seconds())

                if DEBUG_IT:
                    tplog('Processing Tablo',cpe)
                    tplog('--Last Seen', seconds_since_last_seen)
                if seconds_since_last_seen < 86400:
                    tablos[tablo_server_id] = {}

                    #Reload the already saved recordings if we already have this tablo
                    #First See if we already have a CPES array
                    if 'CPES' in Dict:
                        #now see if we have this tablo
                        tplog('Found CPES','here')
                        if tablo_server_id in Dict['CPES']:
                            tplog('Found CPE ',tablo_server_id)
                            if 'CHANNELS' not in Dict['CPES'][tablo_server_id]:
                                tplog('No CHANNELS key Found for CPE ',tablo_server_id)
                                tablos[tablo_server_id]['CHANNELS'] = {}
                            else:
                                tplog('CHANNELS key Found for CPE ',tablo_server_id)
                                tablos[tablo_server_id]['CHANNELS'] = Dict['CPES'][tablo_server_id]['CHANNELS']
                            if 'RECORDINGS' not in Dict['CPES'][tablo_server_id]:
                                tplog('No RECORDINGS key Found for CPE ',tablo_server_id)
                                tablos[tablo_server_id]['RECORDINGS'] = {}
                            else:
                                tplog('RECORDINGS key Found for CPE ',tablo_server_id)
                                tablos[tablo_server_id]['RECORDINGS'] = Dict['CPES'][tablo_server_id]['RECORDINGS']
                        else:
                            tplog('Not Found for CPE ',tablo_server_id)
                            tablos[tablo_server_id]['CHANNELS'] = {}
                            tablos[tablo_server_id]['RECORDINGS'] = {}
                    tablos[tablo_server_id]['NAME'] = cpe['host']
                    tablos[tablo_server_id]['PUBLIC_IP'] = str(cpe['public_ip'])
                    tablos[tablo_server_id]['PRIVATE_IP'] = str(cpe['private_ip'])
                    tablos[tablo_server_id]['PRIVATE_PORT'] = '18080'
                    tablos[tablo_server_id]['SERVER_ID'] = tablo_server_id
            Dict['CPES'] = tablos

            if DEBUG_IT:
                tplog('created cpes for',tablos)
            return True
        else:
            return False
    except Exception as e:
        tplog("Error Contacting Association Server" ,e)
        if 'tablos' in Dict:
            return True
        else:
            return False




def sync_database_recordings(LoadLimit = 50):
    if DEBUG_IT:
            tplog('Start sync_database  ',LoadLimit)
    #Loop through Each Tablo
    count = 0
    if DEBUG_IT:
        tplog('-- sync_database CPES ','')
       # tplog('-- sync_database CPES ',Dict['CPES'])
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        if DEBUG_IT:
            tplog('sync_database cpe found ',cpe['NAME'])
        #Get the list of recordings
        try:
            cpe_recording_list = JSON.ObjectFromURL('http://' + cpe['PRIVATE_IP'] + ':'+ cpe['PRIVATE_PORT'] +'/plex/rec_ids', values=None, headers={}, cacheTime=60)
        except Exception as e:
            tplog("Error Reading CPE" ,e)
        if DEBUG_IT:
            tplog('sync_database Recordings found ','')
            #tplog('sync_database Recordings found ',cpe_recording_list)

        #Loop Through and add recording information to the database
        cpe_recording_list['ids'].sort();
        for recordingIDint in cpe_recording_list['ids']:
            recordingID = str(recordingIDint)
            if count < LoadLimit:
                a = True
                #tplog('sync_database Recording ID ',recordingID)
            else:
                tplog('sync_database Recording ID ignored due to load limit',recordingID)
                return recordingID
            if not recordingID in Dict['CPES'][tablo_server_id]['RECORDINGS'] and count < LoadLimit:

                if count < LoadLimit:
                    count += 1
                    try:
                        cpe_recording = JSON.ObjectFromURL('http://' + cpe['PRIVATE_IP'] + ':'+ cpe['PRIVATE_PORT'] +'/pvr/' + recordingID +'/meta.txt', values=None, headers={}, cacheTime=60)
                        Dict['CPES'][tablo_server_id]['RECORDINGS'][recordingID] = getEpisodeDict(cpe_recording,recordingID)
                        if DEBUG_IT:
                            tplog('sync_database Recording first load ',recordingID)
                            #tplog('sync_database Recording found ',Dict['CPES'][tablo_server_id]['RECORDINGS'][recordingID])
                    except Exception as e:
                        tplog("sync_database Error Loading Meta" ,e)
                else:
                    tplog('sync_database hit load limit ',count)

        #Remove Recordings that have been Deleted from the Tablo
        tplog("sync_database Checking for Deletions" ,"")
        Temp = Dict['CPES'][tablo_server_id]['RECORDINGS'].copy()
        try:
            #tplog('sync_database delete checking against' , cpe_recording_list['ids'])
            for existing_recording_id in Temp:
                int_existing_recording_id = int(existing_recording_id)
                #tplog('sync_database delete checking' , int_existing_recording_id)
                if not int(existing_recording_id) in cpe_recording_list['ids']:
                    del Dict['CPES'][tablo_server_id]['RECORDINGS'][existing_recording_id]
                    tplog('sync_database Deleting' , int_existing_recording_id)
        except Exception as e:
            tplog("sync_database Error Deleting" ,e)
    return 1

def sync_database_channels(LoadLimit = 200):
    if DEBUG_IT:
            tplog('Start sync_database_channels  ',LoadLimit)
    #Loop through Each Tablo
    count = 0

    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        #Load Channel Information
        try:
            tplog("sync_database_channels CPE " ,tablo_server_id)
            i = 0  # used for storing channels in correct order as reported by TabloTV ch_id
            url = 'http://' + cpe['PRIVATE_IP'] + ':'+ cpe['PRIVATE_PORT'] + '/plex/ch_ids'
            cpe_channel_list = JSON.ObjectFromURL(url, values=None, headers={}, cacheTime=60)

            for chid in cpe_channel_list['ids']:
                loadchannel = False
                if chid not in Dict['CPES'][tablo_server_id]['CHANNELS']:
                    tplog('sync_database_channels - First Load: ', chid)
                    loadchannel = True
                else:
                    datetime = Datetime.Now()
                    startdatetimetz = Datetime.ParseDate(Dict['CPES'][tablo_server_id]['CHANNELS'][chid]['airDate'])
                    startdatetime = startdatetimetz.replace(tzinfo=None)
                    secondsintoprogram = int(( datetime.utcnow() - startdatetime).total_seconds())
                    # set the duration to within a minute of it ending
                    durationinseconds = int(Dict['CPES'][tablo_server_id]['CHANNELS'][chid]['duration'] / 1000)
                    tplog('Comparing ','secondsintoprogram' + str(secondsintoprogram)+ 'durationinseconds' + str(durationinseconds)  )
                    #if the program is ending or has ended reload
                    if secondsintoprogram > (durationinseconds- 60):
                        tplog('sync_database_channels - ReLoad: ', chid)
                        loadchannel = True
                if loadchannel:
                    channelDict = get_channel_dict(tablo_server_id, chid)
                    channelDict['order'] = i
                    Dict['CPES'][tablo_server_id]['CHANNELS'][chid] = channelDict

        except Exception as e:
            tplog("Error Reading CPE Channels" ,e)

def get_channel_dict(tablo_server_id, intchid):
    chid = str(intchid)
    channelDict = {}

    tplog('get_channel_dict', 'Requesting chid' + chid)
    try:
        channelInfo = JSON.ObjectFromURL('http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+  Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/plex/ch_info?id=' + str(chid), values=None,
                                          headers={}, cacheTime=60)

    except Exception as e:
        tplog('getChannelDict', "Call to CGI ch_info failed!")
        return e

    if 'meta' in channelInfo:
        chinfo = channelInfo['meta']

        # Set all defaults for min required EpisodeObject
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
                channelEPGInfo = JSON.ObjectFromURL('http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+  Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/plex/ch_epg?id=' + str(chid),
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
                        channelDict['art'] = seriesimage['imageID']
                        artFound = 1
                    if seriesimage['imageStyle'] == 'snapshot' and artFound == 0:
                        channelDict['art'] = seriesimage['imageID']
                        artFound = 1
                    if seriesimage['imageStyle'] == 'thumbnail' and thumbFound == 0:
                        channelDict['seriesThumb'] = seriesimage['imageID']
                        thumbFound = 1
                    if seriesimage['imageStyle'] == 'cover' and thumbFound == 0:
                        channelDict['seriesThumb'] = seriesimage['imageID']
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


'''#########################################
    Name: getEpisodeDict()

    Parameters: None

    Purpose:

    Returns:

    Notes:
#########################################'''
def getEpisodeDict(recordingobj,recordingID):
    recordingDict = {}
    recordingtype = 'Unknown'
    recordinginfo = recordingobj
    if 'meta' in recordingobj or UseMeta:

        recordingDict['recordingID'] = recordingID
        #use image url to retrieve show images.  Snap.jpg isn't always available
        recordingDict['seriesthumb'] = recordingID + 'snap.jpg'
        recordingDict['backgroundart'] = recordingID + 'snap.jpg'
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
                        recordingDict['backgroundart'] = str(seriesimage['imageID'])
                    if seriesimage['imageType'] == 'series_3x4_small':
                        recordingDict['seriesthumb'] =  str(seriesimage['imageID'])
            if 'totalEpisodes' in recordinginfo['recSeries']['jsonFromTribune']:
                recordingDict['showtotalepisodes'] = int(recordinginfo['recSeries']['jsonFromTribune']['totalEpisodes'])
            if 'title' in recordinginfo[root]['jsonFromTribune']['program']:
                recordingDict['showname'] = recordinginfo[root]['jsonFromTribune']['program']['title']
            if 'seriesId' in recordinginfo['recSeries']['jsonFromTribune']:
                recordingDict['showid'] = recordinginfo['recSeries']['jsonFromTribune']['seriesId']
            if 'seasonNumber' in recordinginfo[root]['jsonForClient']:
                recordingDict['seasonnum'] = int(recordinginfo[root]['jsonForClient']['seasonNumber'])
            if 'episodeNumber' in recordinginfo[root]['jsonForClient']:
                recordingDict['episodenum'] = int(recordinginfo[root]['jsonForClient']['episodeNumber'])

        '''#### CAPTURE Movie ONLY INFO ####### '''
        if 'recMovieAiring' in recordinginfo:
            recordingtype = 'Movie'
            root = 'recMovieAiring'
            if 'plot' in recordinginfo['recMovie']['jsonForClient']:
                recordingDict['summary'] = recordinginfo['recMovie']['jsonForClient']['plot']
        '''#### CAPTURE Sports ONLY INFO ####### '''
        if 'recSportEvent' in recordinginfo:
            recordingtype = 'Sports'
            root = 'recSportEvent'


        if 'episodeTitle' in recordinginfo[root]['jsonFromTribune']['program']:
            recordingDict['title']  = recordinginfo[root]['jsonFromTribune']['program']['episodeTitle']
        elif 'title' in recordinginfo[root]['jsonFromTribune']['program']:
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


############################################
###########  Menu FUNCTIONS   ###########
############################################
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
    build_tablos()
    sync_database_recordings(100)
    sync_database_channels(200)

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

    build_tablos()
    nomoretosync = sync_database_recordings(50)

    if nomoretosync > 1:
        oc = ObjectContainer()
        oc.no_cache = True
        oc.add(DirectoryObject(thumb=R('icon_settings_hd.png'), key=Callback(stillsyncing), title="Recordings are still syncing please continue to click here until sync finishes Last Recording was "+ nomoretosync))
        return oc

    oc = ObjectContainer()
    oc.no_cache = True
    oc.add(DirectoryObject(thumb=R('icon_livetv_hd.png'), key=Callback(livetv), title="Live TV"))
    oc.add(DirectoryObject(thumb=R('icon-Movies.png'),key=Callback(movies), title="Movies"))
    oc.add(DirectoryObject(thumb=R('icon-TVShow.png'),key=Callback(shows), title="TV Shows"))
    oc.add(DirectoryObject(thumb=R('icon_sports_hd.png'),key=Callback(sports), title="Sports"))
    oc.add(DirectoryObject(thumb=R('icon-Recordings.png'),key=Callback(recentrecordings), title="Recent Recordings"))
    oc.add(DirectoryObject(thumb=R('icon_scheduled_hd.png'),
                               key=Callback(scheduled, title="Scheduled Recordings"),
                               title="Scheduled Recordings"))
    oc.add(DirectoryObject(thumb=R('icon_settings_hd.png'), key=Callback(Help, title="Help"), title="Help"))
    return oc
def stillsyncing():
    nomoretosync = sync_database_recordings(50)

    if nomoretosync > 1:
        oc = ObjectContainer()
        oc.no_cache = True
        oc.add(DirectoryObject(thumb=R('icon_settings_hd.png'), key=Callback(MainMenu), title="Recordings are still syncing please continue to click here until sync finishes Last Recording was "+ nomoretosync))
        return oc
    return MainMenu()
'''#########################################
        Name: livetv()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/livetv', allow_sync=True)
def livetv():
    sync_database_channels()

    oc = ObjectContainer()
    oc.no_cache = True
    oc.title1 = 'Live TV'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,channelDict in cpe['CHANNELS'].iteritems():
            #tplog('recordingDict',recordingDict)
            tplog('id',channelDict)
            oc.add(getlivetvepisode(channelDict,tablo_server_id))



    return oc

'''#########################################
        Name: getlivetvepisode()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''
@route(PREFIX + '/getlivetvepisode')
def getlivetvepisode(channelDict, tablo_server_id, ocflag = False):
    tplog('getliveepisode',channelDict)
    eptitle = ''
    epsummary = ''
    epshow = ''
    eporder = ''
    epobjectID = 0
    if ocflag:
        get_channel_dict(tablo_server_id,channelDict)
    try:
        eptitle = channelDict['title'] + '-' + channelDict['epTitle']
        epsummary = channelDict['description']
        epshow = channelDict['channelNumber'] + ': ' + channelDict['callSign']
        eporder = channelDict['order']
        epobjectID = int(channelDict['objectID'])
    except Exception as e:
        tplog('841',e)
    episode = EpisodeObject(

                    key=Callback(playlive, objectID=epobjectID,tablo_server_id=tablo_server_id,),
                    rating_key=epobjectID,
                    show=epshow,
                    title=eptitle,
                    summary=epsummary,
                    absolute_index=eporder,  # season = airingData['seasonNumber'],
                    thumb=Resource.ContentsOfURLWithFallback(url=getAssetImageURL(channelDict['seriesThumb'],tablo_server_id), fallback=NOTV_ICON),
                    source_title='TabloTV',

                )

    return episode
'''#########################################
        Name: playlive()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''

@route(PREFIX + '/playlive')
def playlive(objectID,tablo_server_id, pregenurl = ''):
    if pregenurl != '':
        tplog(' --> playlive ocflagged: ', pregenurl)
        episode = EpisodeObject(
                                key=Callback(playlive,objectID=objectID,tablo_server_id=tablo_server_id, pregenurl = pregenurl),
                                rating_key=objectID,

                                title='Start Live TV',

                                items=[
                                        MediaObject(
                                            parts = [
                                                PartObject(
                                                    key=HTTPLiveStreamURL(ocflag)
                                                )
                                            ],

                                            optimized_for_streaming = True,
                                        )
                                    ]
                        )
        return ObjectContainer(objects=[episode])

    cmd = "/player/watchLive"
    parms = {"channelid": int(objectID)}
    result = TabloAPI(tablo_server_id,cmd,parms)
    tplog(' --> playlive result: ', result)
    if 'relativePlaylistURL' in result['result']:
        video_url = "http://" + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + '/' + result['result']['relativePlaylistURL']
        tplog(' --> playlive video_url: ', video_url)
        #return HTTPLiveStreamURL(video_url)
        episode = EpisodeObject(
                            key=Callback(playlive,objectID=objectID,tablo_server_id=tablo_server_id, pregenurl = video_url),
                            rating_key=objectID,

                            title='Start Live TV',

                            items=[
                                    MediaObject(
                                        parts = [
                                            PartObject(
                                                key=HTTPLiveStreamURL(video_url)
                                            )
                                        ],

                                        optimized_for_streaming = True,
                                    )
                                ]
                    )

        return episode

    else:
        return MessageContainer(
            "Error",
            result['result']['error']['errorDesc']
        )
    #return HTTPLiveStreamURL(url)


'''#########################################
        Name: recentrecordings()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/recentrecordings', allow_sync=True)
def recentrecordings():
    sync_database_recordings()

    oc = ObjectContainer()
    oc2 = ObjectContainer()
    oc.title1 = 'Recent Recordings'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            #tplog('recordingDict',recordingDict)
            tplog('id',id)
            if recordingDict['recordingtype'] == 'TvShow':
                oc2.add(getepisodeasmovie(recordingDict,tablo_server_id))
            if recordingDict['recordingtype'] == 'Sports':
                oc2.add(getmovie(recordingDict,tablo_server_id))
            if recordingDict['recordingtype'] == 'Movie':
                oc2.add(getmovie(recordingDict,tablo_server_id))

    # Re-sort the records so that the latest recorded episodes are at the top of the list
    oc2.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)
    count = 0
    for obj in oc2.objects:
        count += 1
        if count <201:
            oc.add(obj)

    return oc


'''#########################################
        Name: Shows()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Shows', allow_sync=True)
def shows():
    sync_database_recordings(100)
    shows = {}
    oc = ObjectContainer()
    oc.title1 = 'Shows'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            #tplog('recordingDict',recordingDict)

            if recordingDict['recordingtype'] == 'TvShow':
                seriesId = recordingDict['seriesId']
                if not seriesId in shows:
                    tplog('---Shows', recordingDict['seriesthumb'])
                    shows[seriesId] = 'true'
                    oc.add(TVShowObject(
                        rating_key=seriesId,
                        art=recordingDict['backgroundart'],
                        key=Callback(seasons, title=recordingDict['showname'],  seriesid=seriesId),
                        title=recordingDict['showname'],
                        summary=recordingDict['seriesdesc'],
                        duration=recordingDict['duration'],
                        thumb=Resource.ContentsOfURLWithFallback(url=getAssetImageURL(recordingDict['seriesthumb'],tablo_server_id), fallback=NOTV_ICON),

                        originally_available_at=Datetime.ParseDate(recordingDict['airdate'])
                    ))

    # Re-sort the records so that they are Alphabetical
    oc.objects.sort(key=lambda obj: obj.title, reverse=False)

    return oc
'''#########################################
        Name: Seasons()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Seasons', allow_sync=True)
def seasons(title, seriesid):
    sync_database_recordings(100)
    seasons = {}
    lastseason = ''
    countseason = 0
    oc = ObjectContainer()
    oc.title1 = 'Seasons'

    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            if recordingDict['seriesId'] == seriesid:
                season = recordingDict['seasonnum']
                if not season in seasons:
                    seasons[season] = 'true'
                    countseason += 1
                    lastseason = season
                    oc.add(SeasonObject(
                            art=recordingDict['backgroundart'],
                            index=recordingDict['seasonnum'],
                            rating_key=str(seriesid) + 'S' + str(recordingDict['seasonnum']),
                            key=Callback(episodes, title=recordingDict['showname'], seriesid=seriesid, seasonnum=recordingDict['seasonnum']),
                            title='Season ' + str(recordingDict['seasonnum']),
                            thumb=Resource.ContentsOfURLWithFallback(url=getAssetImageURL(recordingDict['seriesthumb'],tablo_server_id),fallback=NOTV_ICON))
                    )

    # Re-sort the records so that they are ordered by Season number
    oc.objects.sort(key=lambda obj: obj.index, reverse=True)

    return oc

'''#########################################
        Name: Episodes()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Episodes', allow_sync=True)
def episodes(title, seriesid,seasonnum):
    tplog('====checking seriesid', seriesid)
    tplog('====checking seasonnum', seasonnum)
    oc = ObjectContainer()
    oc.title1 = 'Episodes'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            tplog('====checking ', recordingDict['seriesId'])

            if str(recordingDict['seriesId']) == str(seriesid) and str(recordingDict['seasonnum']) == str(seasonnum):
                tplog('====added ', seriesid)
                oc.add(getepisode(recordingDict,tablo_server_id))

    # Re-sort the records so that the latest recorded episodes are at the top of the list
    oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)

    return oc

'''#########################################
        Name: movies()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/Movies', allow_sync=True)
def movies():
    sync_database_recordings(100)

    oc = ObjectContainer()
    oc.title1 = 'Movies'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            #tplog('recordingDict',recordingDict)

            if recordingDict['recordingtype'] == 'Movie':
                oc.add(getmovie(recordingDict,tablo_server_id))

    # Re-sort the records so that the latest recorded episodes are at the top of the list
    oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)

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
def sports():
    sync_database_recordings(100)

    oc = ObjectContainer()
    oc.title1 = 'Sports'
    recordings = {}
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        for id,recordingDict in cpe['RECORDINGS'].iteritems():
            #tplog('recordingDict',recordingDict)
            if recordingDict['recordingtype'] == 'Sports':
                oc.add(getmovie(recordingDict,tablo_server_id))


    # Re-sort the records so that the latest recorded episodes are at the top of the list
    oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)

    return oc









'''#########################################
        Name: getepisode()

        Parameters: None

        Handler: @route

        Purpose: Returns a episode object for a recorded episode

        Returns:

        Notes:
#########################################'''
def getepisode(episodeDict,tablo_server_id, ocflag = False):
    #set values outside of function for better debugging
    epbackground_art = episodeDict['backgroundart']
    eptitle =episodeDict['title']
    epseason=episodeDict['seasonnum']
    epindex=episodeDict['episodenum']
    epsummary=episodeDict['summary']
    epduration=episodeDict['duration']
    epthumb=Resource.ContentsOfURLWithFallback(url=getSnapImageURL(episodeDict,tablo_server_id), fallback=episodeDict['seriesthumb'])
    eporiginally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    url = 'http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+ Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/pvr/' + episodeDict['recordingID'] + '/pl/playlist.m3u8'
    episode =  EpisodeObject(
                            key=Callback(getmovie,episodeDict=episodeDict,tablo_server_id=tablo_server_id, ocflag = True),
                            rating_key=episodeDict['recordingID'],
                            art=epbackground_art,
                            title=eptitle,
                            season=epseason,
                            index=epindex,
                            summary=epsummary,
                            duration=epduration,
                            thumb=epthumb,
                            originally_available_at=eporiginally_available_at,
                            items=[
                                    MediaObject(
                                        parts = [
                                            PartObject(
                                                key=HTTPLiveStreamURL(url),
                                                duration=epduration,
                                            ),
                                        ],
                                        duration=epduration,
                                        optimized_for_streaming = True,
                                    )
                                ]
                    )
    if ocflag:
        return ObjectContainer(objects=[episode])
    return episode

'''#########################################
        Name: getmovie()

        Parameters: None

        Handler: @route

        Purpose: Returns a episode object for a recorded episode

        Returns:

        Notes:
#########################################'''
def getmovie(episodeDict,tablo_server_id, ocflag = False):
    #set values outside of function for better debugging
    epbackground_art = episodeDict['backgroundart']
    eptitle =episodeDict['title']
    epsummary=episodeDict['summary']
    epduration=episodeDict['duration']
    epthumb=Resource.ContentsOfURLWithFallback(url=getSnapImageURL(episodeDict,tablo_server_id), fallback=episodeDict['seriesthumb'])
    eporiginally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    url = 'http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+ Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/pvr/' + episodeDict['recordingID'] + '/pl/playlist.m3u8'
    movie =   MovieObject(
                            key=Callback(getmovie,episodeDict=episodeDict,tablo_server_id=tablo_server_id, ocflag = True),
                            rating_key=episodeDict['recordingID'],
                            art=epbackground_art,
                            title=eptitle,
                            summary=epsummary,
                            duration=epduration,
                            thumb=epthumb,
                            originally_available_at=eporiginally_available_at,
                            items=[
                                    MediaObject(
                                        parts = [
                                            PartObject(
                                                key=HTTPLiveStreamURL(url),
                                                duration=epduration,
                                            ),
                                        ],
                                        duration=epduration,
                                        optimized_for_streaming = True,
                                    )
                                ]
    )
    if ocflag:
        return ObjectContainer(objects=[movie])
    return movie

'''#########################################
        Name: getepisode()

        Parameters: None

        Handler: @route

        Purpose: Returns a episode object for a recorded episode

        Returns:

        Notes:
#########################################'''
def getepisodeasmovie(episodeDict,tablo_server_id, ocflag = False):
    #set these first for easier debugging
    epart=episodeDict['backgroundart']
    eptitle=episodeDict['showname'] + ' - ' + episodeDict['title']
    epsummary=episodeDict['summary']
    epduration=episodeDict['duration']
    epthumb=Resource.ContentsOfURLWithFallback(url=getSnapImageURL(episodeDict,tablo_server_id), fallback=episodeDict['seriesthumb'])
    eporiginally_available_at=Datetime.ParseDate(episodeDict['airdate'])
    url = 'http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+ Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/pvr/' + episodeDict['recordingID'] + '/pl/playlist.m3u8'
    if DEBUG_IT:
        tplog('URL Found', url)

    movie =  MovieObject(
                            key=Callback(getepisodeasmovie,episodeDict=episodeDict,tablo_server_id=tablo_server_id, ocflag = True),
                            rating_key=episodeDict['recordingID'],
                            art=epart,
                            title=eptitle,
                            summary=epsummary,
                            duration=epduration,
                            thumb=epthumb,
                            originally_available_at=eporiginally_available_at,
                            items=[
                                    MediaObject(
                                        parts = [
                                            PartObject(
                                                key=HTTPLiveStreamURL(url),
                                                duration=epduration,
                                            ),
                                        ],
                                        duration=epduration,
                                        optimized_for_streaming = True,
                                    )
                                ]

    )

    if ocflag:
        return ObjectContainer(objects=[movie])
    return movie



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
    oc = ObjectContainer()
    oc.title1 = title
    mymessage = ""
    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        cmd = "/info/guideSeries/get"
        parms = {"filter":{"orderby":"startdate","schedulestate":"scheduled"}}
        result = TabloAPI(tablo_server_id,cmd,parms)

        recordings = result['result']['series']

        datetime = Datetime.Now()
        timezoneoffset = int((datetime - datetime.utcnow()).total_seconds())

        # Loop through channels and create a Episode Object for each show
        for airingData in recordings:
                    unixtimestarted = Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime']))
                    displayeddate = str(Datetime.FromTimestamp(Datetime.TimestampFromDatetime(Datetime.ParseDate(airingData['startTime'])) + timezoneoffset))
                    recordingtype = 'Unknown'
                    if 'scheduleType' in airingData['schedule']:
                        recordingtype = airingData['schedule']['scheduleType']
                    imagedid = ''
                    if 'images' in airingData:
                        imagedid = airingData['images'][0]['imageID']
                    tplog('scheduled airingdata loop',airingData)
                    # All commented out are set in TabloLive.pys helpers
                    oc.add(
                        #TVShowObject(
                    PopupDirectoryObject(
                        title= displayeddate + ' - ' + airingData['title'],
                        summary='Recording on : ' + cpe['NAME'] + ' Scheduled to Record: '+ recordingtype ,
                        key=Callback(nothing, title=title) , # season = airingData['seasonNumber'],
                        thumb=Resource.ContentsOfURLWithFallback(url=getAssetImageURL(imagedid,tablo_server_id) ,fallback=NOTV_ICON),
                        tagline=unixtimestarted
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
    oc = ObjectContainer()
    return oc





############################################
###########  Help FUNCTIONS   ###########
############################################


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
    #oc.add(DirectoryObject(thumb=R('icon-prefs.png'), key=Callback(DeleteDups, title="Delete Dups"),
   #                        title="Delete Dups "))
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



    for tablo_server_id,cpe in Dict['CPES'].iteritems():
        cmd = "/server/status"
        parms = {}
        result = TabloAPI(tablo_server_id,cmd,parms)
        tplog('detect',result)
        tablo = result['result']
        mymessage = mymessage + " Tablo Reported Name: " + tablo['name'] + '\r\n' + '    Reported IP: ' + tablo['localAddress'] + ' Running Version: ' + tablo['serverVersion']
    return ObjectContainer(header=title, message=mymessage)

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
        Name: Reset Plugin()

        Parameters: None

        Handler: @route

        Purpose:

        Returns:

        Notes:
#########################################'''


@route(PREFIX + '/ResetPlugin')
def ResetPlugin(title):

    try:
        # Pass full Tablo info to here for better parsing and future multiple tablo support
        del Dict['CPES']
        build_tablos()
        sync_database_recordings(999)
        sync_database_channels(200)
    except:
        Log('Could not fetch tablo IP, Will use cached IP if available')

    return ObjectContainer(header=title, message='Plugin Reset Complete, Please go back to Main Menu Now')

############################################
###########  UTILITY FUNCTIONS   ###########
############################################

def getSnapImageURL(episodeDict,tablo_server_id):
    recordingID = episodeDict['recordingID']
    return 'http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+ Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/pvr/' + recordingID +'/snap.jpg'

def getAssetImageURL(assetID,tablo_server_id):
    return 'http://' + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] + ':'+ Dict['CPES'][tablo_server_id]['PRIVATE_PORT'] +'/stream/thumb?id=' + str(assetID)
'''#########################################
    Name: TabloAPI()

    Parameters: None

    Purpose:

    Returns:

    Notes:
        Returns result so that test for error can be handled in calling function
#########################################'''
def TabloAPI(tablo_server_id,cmd,parms):
    url = "http://" + Dict['CPES'][tablo_server_id]['PRIVATE_IP'] +":8886"
    tplog('TabloAPI', "Starting TabloAPI Call")
    if DEBUG_IT:
        tplog(LOG_PREFIX + "cmd", cmd)
    request = {"jsonrpc":2.0,"id":"1","method": str(cmd),"params": parms}

    if DEBUG_IT:
        tplog('TabloAPI Request: ',  request)
    try:
        values = JSON.StringFromObject(request)
        result = JSON.ObjectFromString(str(HTTP.Request(url ,values=None, headers={}, cacheTime=60, encoding=None, errors=None, timeout=30, immediate=False, sleep=0, data=values)))
    except Exception as e:
        tplog("Error when calling TabloAPI. Exception = ",e)
        return e
    if DEBUG_IT:
        tplog('TabloAPI', result)
        tplog('TabloAPI',  "End TabloAPI Call")
    return result


