'''#########################################   
	Author: @DavidVR - Van Ronk, David 
			@PiX64  - Reid, Michael
 
    Source: 

    Purpose:  
    
    Legal:
#########################################'''
import pprint

#Load SharedServiceCode helper functions
tablohelpers 	= SharedCodeService.tablohelpers
Decodeobj 		= tablohelpers.Decodeobj
Encodeobj 		= tablohelpers.Encodeobj
TabloAPI 		= tablohelpers.TabloAPI
getEpisodeDict 	= tablohelpers.getEpisodeDict
loadData 		= tablohelpers.loadData
getTabloIP		= tablohelpers.getTabloIP
loadLiveTVData   = tablohelpers.loadLiveTVData
#PlexLog = SharedCodeService.TabloHelpers.PlexLog

'''#### Define Global Vars ####'''
TITLE = 'Tablo'
ART			 	= 'TabloProduct_FrontRight-default.jpg'
ICON		 	= 'tablo_icon_focus_hd.png'
NOTV_ICON		= 'no_tv_110x150.jpg'
ICON_PREFS 		= 'icon_settings_hd.jpg'
SHOW_THUMB      = 'no_tv_110x150.jpg'
PREFIX 			= '/video/Tablo'
LOG_PREFIX 		= "***TabloTV: "
VERSION			= "0.95"
FOLDERS_COUNT_IN_TITLE = True #Global VAR used to enable counts on titles
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
		
		count = LoadTablos()
		if count == 0:
			 return ObjectContainer(header='Error', message='API Could Not Locate a tablo on your network')
	except:
		Log('Early LoadTablo Fail in MainMenu')

	oc = ObjectContainer()
	
	if 'private_ip' not in Dict:
		Log('privateIPERROR')
		return ObjectContainer(header='Error', message=' Could Not Locate a tablo on your network')
		
	else:
		try:
			episodelistids = JSON.ObjectFromURL('http://' + Dict['private_ip'] + ':18080/plex/rec_ids', values=None, headers={}, cacheTime=60)
		except Exception as e:
			return ObjectContainer(header='Error', message='Could Not Connect to your tablo')
			
		#oc.add(DirectoryObject(thumb=R('icon_livetv_hd.jpg'),key=Callback(livetv, title="Live TV", url = Dict['private_ip'] ), title="Live TV"))
		oc.add(DirectoryObject(thumb=R('icon_livetv_hd.jpg'),key=Callback(livetvnew, title="Live TV NEW"), title="Live TV NEW"))
		oc.add(DirectoryObject(thumb=R('icon_recordings_hd.jpg'),key=Callback(Shows, title="Shows", url = Dict['private_ip'] ), title="Shows"))
		oc.add(DirectoryObject(thumb=R('icon_tvshows_hd.jpg'),key=Callback(allrecordings, title="All Recordings", url = Dict['private_ip'] ), title="Recent Recordings"))
		oc.add(DirectoryObject(thumb=R('icon_settings_hd.jpg'),key=Callback(Help, title="Help"), title="Help"))		
		#Uncomment the line below to try JSON loading the data
		#oc.add(DirectoryObject(thumb=R('icon_tvshows_hd.jpg'),key=Callback(testdata), title="testjsondata"))
		
		#oc.add(PrefsObject(title='Change your IP Address', thumb=R(ICON_PREFS)))
		
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
	oc.add(DirectoryObject(thumb=R('info.png'),key=Callback(About, title="About TabloTV Plex"), title="About"))	
	oc.add(DirectoryObject(thumb=R('icon-prefs.png'),key=Callback(ResetPlugin, title="Reset Plugin"), title="Reset Plugin "))	
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
	HTTP.ClearCookies()
	HTTP.ClearCache()
	Dict["tablo"] = {}
	Dict["LiveTV"] = {}
	try:
		#Pass full Tablo info to here for better parsing and future multiple tablo support
		count = 0
		Dict['tabloips'] = getTabloIP()
		for tablo in tabloips:
			count = count + 1
			Dict['public_ip'] = str(tablo['public_ip'])
			Dict['private_ip'] = str(tablo['private_ip'])

		if count == 0:
			 return ObjectContainer(header='Error', message='API Could Not Locate a tablo on your network')
	except:
		Log('Could not fetch tablo IP, Will use cached IP if avalible')
	#loadData(Dict) move to functions where it is needed rather than loading upfront.. IF we go to livetv only no need to load recordings.. unecessary

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
	PlexLog('test', JSON.ObjectFromString('{"cpes": [{"http": 21280, "public_ip": "99.224.78.110", "ssl": 21243, "host": "quad_2665", "private_ip": "192.168.1.142", "slip": 21207, "serverid": "SID_5087B8002665", "inserted": "2014-04-15 20:46:56.152096+00:00", "board_type": "quad", "server_version": "2.1.11", "name": "GH Quad Tablo", "modified": "2014-06-10 01:26:09.003166+00:00", "roku": 1, "last_seen": "2014-06-10 01:26:08.999852+00:00"}], "success": true}'))
	return ObjectContainer(header=title, message='TabloTV Plex Plugin Version ' + VERSION)

'''#########################################
	Name: livetv()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/livetv',allow_sync=True)
def livetv(title, url):
	
	url = "http://" + Dict['private_ip'] +":8886"
	
	result = TabloAPI(url,"/info/channel/get",{})

	oc = ObjectContainer()
	oc.title1 = "Live TV"
	myDict = {}
	#Log(pprint.pformat(result))
	if 'result' in result:
		channellist = result['result']['channels']
		for channel in channellist:
			#Log(pprint.pformat(channel))
			try:
				channelDict = {}
				channelDict['private_ip'] = Dict['private_ip']
				 
				channelDict['title'] = channel['title'] 
				channelDict['callSign'] = channel['callSign']
				channelDict['channelNumber'] = str(channel['channelNumberMajor']) + '-' + str(channel['channelNumberMinor'])
				channelDict['objectID'] = channel['objectID'] 
				Log(LOG_PREFIX + ' series thumb = %s',str(channel['imageID']))
				
				if channel['imageID'] == 0:
					#channelDict['seriesthumb'] = GetDefaultFanart(channel['title'])
					channelDict['seriesthumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])
					#channelDict['seriesthumb'] = GetGoogleImage(channelDict['callSign'] + ' stations.fcc.gov'+ ' Logo')
					#channelDict['seriesthumb'] = GetGoogleImage(channelDict['callSign'] + ' ' + str(channel['channelNumberMajor']) + '-' + str(channel['channelNumberMinor']))
				else:
					channelDict['seriesthumb'] = 'http://' + Dict['private_ip'] + '/stream/thumb?id=' + str(channel['imageID'])
				#oc.add(TVShowObject(
				Log(LOG_PREFIX+'channelDict = %s',channelDict)
				oc.add(EpisodeObject(
						url = Encodeobj('channel' , channelDict),
						#show = channelDict['title'],
						#show = str(channel['channelNumberMajor']) + '-' + str(channel['channelNumberMinor']) + ':     ' + channel['callSign'],
						#key=Callback(livetv, title=title, url=url),
						title = str(channel['channelNumberMajor']) + '-' + str(channel['channelNumberMinor']) + ' ' + channel['callSign'] + ': ' + str(channelDict['title']),
						summary = channelDict['title'],
						thumb = Resource.ContentsOfURLWithFallback(url=channelDict['seriesthumb'], fallback=NOTV_ICON)
						)
					)
			except Exception as e:
				Log("Parse Failed on channel " + str(e))
	else:
		Log(pprint.pformat(result))
		return MessageContainer(
            "Error",
            result['result']['error']['errorDesc']
        )

	return oc

'''#########################################
	Name: livetvnew()
	
	Parameters: title
				url
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/livetvnew',allow_sync=True)
def livetvnew(title):
	
	#if "LiveTV" not in Dict:
	loadLiveTVData(Dict)
	#Log(LOG_PREFIX+'LiveTVData loaded as: %s',Dict["LiveTV"])
	#else:
	#	Log(LOG_PREFIX+'LiveTVData ALREADY! loaded as: %s',Dict["LiveTV"])

	oc = ObjectContainer()
	oc.title1 = title

	if "LiveTV" in Dict:
		data =Dict["LiveTV"]

		#Log(LOG_PREFIX+'livetvdata = %s',data)

		for chid, airingData in data.iteritems():
			#Log(LOG_PREFIX+' airingdata =%s value=%s',airingData,chid)
			try:
				#All commented out are set in TabloLive.pys helpers
				oc.add(EpisodeObject(
				#oc.add(TVShowObject(
					url = Encodeobj('channel' , airingData),
					show = airingData['channelNumber'] + ': ' + airingData['callSign'],
					title = airingData['title'],
					summary = airingData['description'],
					#originally_available_at = Datetime.ParseDate(airingData['originalAirDate']),
					#writers = ,
					#directors = ,
					#producers = ,
					#guest_stars = ,
					#absolute_index = airingData['episodeNumber'],
					#season = airingData['seasonNumber'],
					thumb = Resource.ContentsOfURLWithFallback(url=airingData['seriesThumb'], fallback=NOTV_ICON),
					#art= Resource.ContentsOfURLWithFallback(url=airingData['art'], fallback=ART),
					source_title = 'TabloTV'
					#duration = airingData['duration']
					#description = airingData['description']
					)
				)
			except Exception as e:
				Log("Parse Failed on channel " + str(e))

	return oc

'''#########################################
	Name: allrecordings()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/allrecordings',allow_sync=True)
def allrecordings(title, url):
	loadData(Dict)

	oc = ObjectContainer()
	oc.title1 = "All Recordings"
	#Check for cached data, if we do not have any, run load data
	if "tablo" not in Dict:
		loadData(Dict)
	#if we do have data, create episode objects for each episode
	if "tablo" in Dict:
	
	
		for episodejson, value in Dict["tablo"].iteritems():
			try:
				episodeDict = value
				#altdict = {}
				#altdict['alt'] = 'Yes'
				#altdict['private_ip'] = Dict['private_ip']
				#altdict['episodeID'] = episodeDict['episodeID'] 
				#myurl = Encodeobj('TabloRecording' , altdict)
				myurl = Encodeobj('TabloRecording' , episodeDict)
				oc.add(EpisodeObject(
					url = myurl,
					show = episodeDict['showname'] ,
					title = episodeDict['title'],
					summary = episodeDict['summary'],
					thumb = Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg', fallback=SHOW_THUMB),
					duration = episodeDict['duration'],
					season = episodeDict['seasonnum'],
					originally_available_at = Datetime.ParseDate(episodeDict['airdate'])
				))
			except Exception as e:
				Log(" Failed on episode " + str(e))
	#Resort the records so that the latest recorded episodes are at the top of the list
	oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)
	oc.add(PrefsObject(title='Change your IP Address', thumb=R(ICON_PREFS)))
	return oc

'''#########################################
	Name: Shows()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/shows',allow_sync=True)
def Shows(title, url):
	
	oc = ObjectContainer()
	oc.title1 = "Shows"
	#Update the data on every call since we intelligently load the actual metadata
	loadData(Dict)
	
	if "tablo" in Dict:
		#Log(Dict["tablo"])
		shows = {}
		data =Dict["tablo"]
		#Log(pprint.pformat(data))
		for episodejson, value in data.iteritems():
		 	#Log(pprint.pformat(value))
			episodeDict = value
			try:
				
				#Log(repr(episodeinfo))
				seriesId = episodeDict['seriesId']
				if not seriesId in shows:
					shows[seriesId] = 'true'
					
					url = Encodeobj('TabloRecording' , episodeDict),
					oc.add(TVShowObject(
						rating_key = seriesId,
						art=episodeDict['backgroundart'] , 
						key=Callback(Seasons, title=episodeDict['showname'], url = url, seriesid = seriesId ),
						title = episodeDict['showname'],
						summary = episodeDict['seriesdesc'],
						duration = episodeDict['duration'],
						thumb = Resource.ContentsOfURLWithFallback(url=episodeDict['seriesthumb'], fallback=ICON),
						episode_count = episodeDict['showtotalepisodes'],
						originally_available_at = Datetime.ParseDate(episodeDict['airdate'])
					))
			except Exception as e:
				Log(" Failed on show " + str(e))
	oc.objects.sort(key = lambda obj: obj.title)
	#oc.add(PrefsObject(title='Change your IP Address', thumb=R(ICON_PREFS)))
	return oc

'''#########################################
	Name: Seasons()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/seasons',allow_sync=True)
def Seasons(title, url, seriesid):

	oc = ObjectContainer()
	#Update the data on every call since we intelligently load the actual metadata
	loadData(Dict)
	
	if "tablo" in Dict:

		seasons = {}
		data =Dict["tablo"]
		seasoncount = 0
		lastseason = ''

		for episodejson, value in data.iteritems():
		 	
			episodeDict = value
			try:	
				
				myseriesId = episodeDict['seriesId']
				
				if myseriesId == seriesid:
					if not episodeDict['seasonnum'] in seasons:
						seasoncount = seasoncount + 1
						lastseason = episodeDict['seasonnum']
						seasons[episodeDict['seasonnum']] = 'true'
						oc.art = Resource.ContentsOfURLWithFallback(url=episodeDict['backgroundart'], fallback=ART)
						oc.add(SeasonObject(
							art=episodeDict['backgroundart'],
							index = episodeDict['seasonnum'],
							rating_key = str(seriesid) + 'S' + str(episodeDict['seasonnum']),
							key=Callback(Episodes, title=episodeDict['showname'], seriesid = seriesid, seasonnum = episodeDict['seasonnum']   ),
							title = 'Season ' + str(episodeDict['seasonnum']),
							thumb = Resource.ContentsOfURLWithFallback(url=episodeDict['seriesthumb'], fallback=NOTV_ICON),
						))
			except Exception as e:
				PlexLog('Seasons'," Failed on show " + str(e))
	if seasoncount == 1:
		return Episodes(title, seriesid, lastseason)
	else:
		oc.objects.sort(key = lambda obj: obj.index)
		return oc

'''#########################################
	Name: Episodes()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/episodes',allow_sync=True)
def Episodes(title, seriesid, seasonnum):
	
	oc = ObjectContainer()
	if seasonnum != 0: 
		oc.title1 = title + " Season " + str(seasonnum) + " Episodes"
	else: 
		oc.title1 = title + " Episodes"
	#Update the data on every call since we intelligently load the actual metadata
	loadData(Dict)
	
	if "tablo" in Dict:
		#Log(Dict["tablo"])
		
		seasons = {}
		data =Dict["tablo"]
		for episodejson, value in data.iteritems():
			episodeDict = value
			try:
				#Log('here' + episodeDict['seriesId'] + ' sent ' + seriesid)
				if episodeDict['seriesId'] == seriesid:
					#Log('Season check_' + str(episodeDict['seasonnum']) + ' sent ' + str(seasonnum))
					if str(episodeDict['title']) == '0':
						PlexLog('Episode Title Check',episodeDict['title'])
					if str(episodeDict['summary']) == '0':
						PlexLog('Episode summary Check',episodeDict['summary'])
					if str(episodeDict['seasonnum']) == str(seasonnum):
						seasons[seriesid] = 'true'
						oc.art = Resource.ContentsOfURLWithFallback(url=episodeDict['backgroundart'], fallback=ART)
						oc.add(EpisodeObject(
							art=episodeDict['backgroundart'] , 
							url = Encodeobj('TabloRecording' , episodeDict),
							title = episodeDict['title'],
							season = episodeDict['seasonnum'],
							index = episodeDict['episodenum'],
							summary = episodeDict['summary'],
							duration = episodeDict['duration'],
							thumb = Resource.ContentsOfURLWithFallback(url=episodeDict['url'] + 'snap.jpg', fallback=episodeDict['seriesthumb']),
							originally_available_at = Datetime.ParseDate(episodeDict['airdate'])
						))
			except Exception as e:
				Log(" Failed on episode " + str(e))
	oc.objects.sort(key = lambda obj: obj.index)
	return oc

'''#########################################
	Name: reload()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
@route(PREFIX + '/reload',allow_sync=True)
def reload(title, url):
	Dict["hash"] = ""
	oc = MainMenu()
	oc.title1 = "Refresh Complete"
	return oc

'''#########################################
	Name: GetGoogleImage()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
def GetGoogleImage(searchterm):
	imageurl = ''
	searchterm = searchterm.replace(" ","+")
	searchurl = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=' + searchterm + '&start=0'
	data = JSON.ObjectFromURL(searchurl)
	#PlexLog('Google',data)
	for image_info in data['responseData']['results']:
		imageurl = image_info['unescapedUrl']
		PlexLog('Google Image' ,image_info)
	return imageurl
'''#########################################
	Name: LoabTablos()
	
	Parameters: None
	
	Handler: @route
	
	Purpose:
	
	Returns:
	
	Notes:
#########################################'''
def LoadTablos():
	#Pass full Tablo info to here for better parsing and future multiple tablo support
	count = 0
	try:
		Dict['tabloips'] = getTabloIP()
		for tablo in Dict['tabloips']:
			count = count + 1
			Dict['public_ip'] = str(tablo['public_ip'])
			Dict['private_ip'] = str(tablo['private_ip'])
	except Exception as e:
		PlexLog('LoadTablos Failure',e)
	return count
'''#########################################
	Name: PlexLog()
	
	Parameters: None
	
	Handler: 
	
	Purpose: Central Control of logging
	
	Returns:
	
	Notes:
#########################################'''
def PlexLog(location, message):
	if debugit:
		Log(LOG_PREFIX + str(location) + ': ' + pprint.pformat(message))

'''#########################################
	Name: None
	
	Parameters: None
	
	Handler: None
	
	Purpose: Placing fcn calls outside of a function will cause plex to preload data before running chanel.
	This allows us to load most data upfront and cut down on loading/execution time
	
	Returns: None
	
	Notes:
#########################################'''
try:
	LoadTablos()
	loadData(Dict)
	#loadLiveTVData(Dict) #Pre-Load channel data
except Exception as e:
	Log('LoadTablos Failure at start')