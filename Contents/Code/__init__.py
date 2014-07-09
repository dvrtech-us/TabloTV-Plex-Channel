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
#loadLiveTVData   = tablohelpers.loadLiveTVData
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
VERSION			= "0.96"
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
		PlexLog('Main Menu','Early LoadTablo Fail')

	oc = ObjectContainer()
	
	if 'private_ip' not in Dict:
		Log('privateIPERROR')
		return ObjectContainer(header='Error', message=' Could Not Locate a tablo on your network')
		
	else:
		try:
			episodelistids = JSON.ObjectFromURL('http://' + Dict['private_ip'] + ':18080/plex/rec_ids', values=None, headers={}, cacheTime=60)
		except Exception as e:
			return ObjectContainer(header='Error', message='Could Not Connect to your tablo')
			
		oc.add(DirectoryObject(thumb=R('icon_livetv_hd.jpg'),key=Callback(livetvnew, title="Live TV"), title="Live TV"))
		oc.add(DirectoryObject(thumb=R('icon_recordings_hd.jpg'),key=Callback(Shows, title="Shows", url = Dict['private_ip'] ), title="Shows"))
		oc.add(DirectoryObject(thumb=R('icon_tvshows_hd.jpg'),key=Callback(allrecordings, title="All Recordings", url = Dict['private_ip'] ), title="Recent Recordings"))
		oc.add(DirectoryObject(thumb=R('icon_settings_hd.jpg'),key=Callback(Help, title="Help"), title="Help"))		

		
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
	ClearTabloData()
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
	
	loadLiveTVData(Dict)

	oc = ObjectContainer()
	oc.title1 = title

	if "LiveTV" in Dict:
		data =Dict["LiveTV"]


	#Loop through channels and create a Episode Object for each show
		for chid, airingData in data.iteritems():
			try:
				#All commented out are set in TabloLive.pys helpers
				oc.add(EpisodeObject(
					url = Encodeobj('channel' , airingData),
					show = airingData['channelNumber'] + ': ' + airingData['callSign'],
					title = airingData['title'],
					summary = airingData['description'],
					#originally_available_at = Datetime.ParseDate(airingData['originalAirDate']),
					#writers = ,
					#directors = ,
					#producers = ,
					#guest_stars = ,
					absolute_index = airingData['order'],
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
	oc.objects.sort(key = lambda obj: obj.absolute_index, reverse=False)
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
		#Dict.Reset();
		Log(LOG_PREFIX + "Starting LoadLiveTVData")

		ipaddress = str(Dict['private_ip'])

		channelids = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_ids', values=None, headers={}, cacheTime=600)
		
		Log(LOG_PREFIX+"channelids = %s",channelids)
		
		markforreload = True

		if "LiveTV" not in Dict:
			Dict["LiveTV"] = {}


		if markforreload :
			#Feed in new Data
			
			i = 0 #used for storing channels in correct order as reported by TabloTV ch_id
			
			for chid in channelids['ids']:
				i = i + 1
				if chid not in Dict["LiveTV"]:
					try:
						channelDict = getChannelDict(ipaddress,chid)
						#Log(LOG_PREFIX+' new channelDict = %s',channelDict)
						
						channelDict["order"] = i
						Dict["LiveTV"][chid] = channelDict
						
						#break  #Use this to debug livetv and grab 1 and only 1 channel
					except Exception as e:
						PlexLog("Parse Failed on jsonurl " , e)
				else:
					
					unixtimenow = Datetime.TimestampFromDatetime(Datetime.Now())
					unixtimestarted = Datetime.TimestampFromDatetime(Datetime.ParseDate(Dict["LiveTV"][chid]['airDate']))
					#set the duration to within a minute of it ending
					durationinseconds = int(Dict["LiveTV"][chid]['duration']/1000)-60
					unixtimeaproxend = unixtimestarted + durationinseconds
					if unixtimeaproxend > unixtimenow :
						channelDict = getChannelDict(ipaddress,chid)
						PlexLog('LiveTV time compare now', unixtimenow)
						PlexLog('LiveTV time compare start', unixtimestarted)
						PlexLog('LiveTV time compare dur', durationinseconds)
						PlexLog('LiveTV time compare end', unixtimeaproxend)
						
						channelDict["order"] = i
						Dict["LiveTV"][chid] = channelDict
					
						

'''#########################################
	Name: getChannelDict()
	
	Parameters: None
	
	Purpose:
	
	Returns:
	
	Notes: Moved to init for faster debugging
#########################################'''
def getChannelDict(ipaddress,chid):
	channelDict = {}
	#channelDict['url'] = 'http://' + ipaddress + ':18080/pvr/' + episodeID +'/'

	try:
		channelInfo = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_info?id='+str(chid), values=None, headers={}, cacheTime=60)
		
	except Exception as e:
		PlexLog('getChannelDict', "Call to CGI ch_info failed!")
		return e

	if 'meta' in channelInfo:
		chinfo = channelInfo['meta']
		
		#Set all defaults for min required EpisodeObject
		channelDict['private_ip'] = ipaddress
		channelDict['id'] = chid
		channelDict['title'] = ''
		channelDict['epTitle'] = ''
		channelDict['description'] = ''
		#channelDict[''] = ''
		channelDict['objectID'] = chinfo['objectID']
		channelDict['channelNumberMajor'] = 'N/A'
		channelDict['channelNumberMinor'] = 'N/A'
		channelDict['callSign'] = 'N/A'
		channelDict['duration'] = '0'
		channelDict['seasonNumber'] = 0 
		channelDict['episodeNumber'] = 0
		channelDict['airDate'] = str(Datetime.Now())
		channelDict['originalAirDate'] = str(Datetime.Now())
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
			channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])
			channelDict['art'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])
		else:
			channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['channelNumberMajor']+'-'+channelDict['channelNumberMinor'])
			channelDict['art'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])
		
		#set default channelNumber AFTER trying to get the number major and number minor
		channelDict['channelNumber'] = str(chinfo['channelNumberMajor']) + '-' + str(chinfo['channelNumberMinor'])

		if chinfo['dataAvailable'] == 1:
			
			try:
				channelEPGInfo = JSON.ObjectFromURL('http://' + ipaddress + ':18080/plex/ch_epg?id='+str(chid), values=None, headers={}, cacheTime=60)
			except Exception as e:

				return channelDict

			if 'meta' in channelEPGInfo:
				epgInfo = channelEPGInfo['meta']
				imageInfo = 0 #initialize to avoide reference before assignment
			else:

				channelDict['message'] = "No ch_epg info found. Using ch_info."
				return channelDict

			if 'guideSportEvent' in epgInfo:

				guideInfo = epgInfo['guideSportEvent']
				channelDict['type'] = 'Sport'
				if 'guideSportOrganization' in epgInfo:
					Log(LOG_PREFIX+'Guide Sport Organization')
					guideSportOrg = epgInfo['guideSportOrganization']
					if 'imageJson' in guideSportOrg:
						imageInfo = guideSportOrg['imageJson']['images']
			elif 'guideEpisode' in epgInfo:

				guideInfo = epgInfo['guideEpisode']
				channelDict['type'] = 'Episode'
				if 'guideSeries' in epgInfo:
					Log(LOG_PREFIX+'Series')
					guideDetailInfo = epgInfo['guideSeries']
					channelDict['type'] = 'Series'
					if 'imageJson' in guideDetailInfo:
						imageInfo = guideDetailInfo['imageJson']['images']
			elif 'guideMovieAiring' in epgInfo:
			
				guideInfo = epgInfo['guideMovieAiring']
				channelDict['type'] = 'Movie'
				if 'guideMovie' in epgInfo:
					Log(LOG_PREFIX+'guideMovie')
					guideDetailInfo = epgInfo['guideMovie']
					channelDict['type'] = 'guideMovie'
					if 'imageJson' in guideDetailInfo:
						imageInfo = guideDetailInfo['imageJson']['images']
			else:
				PlexLog(LOG_PREFIX, 'UNHANDLED TYPE!!! not sport or movie or episode')
				return channelDict

			#set images outside of series logic to ensure defaults are set
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
						channelDict['seriesThumb'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
						thumbFound = 1
					if seriesimage['imageStyle'] == 'cover' and thumbFound == 0:
						channelDict['seriesThumb'] = 'http://' + ipaddress + '/stream/thumb?id=' + str(seriesimage['imageID'])
						thumbFound = 1
			else:
				channelDict['seriesThumb'] = 'http://hostedfiles.netcommtx.com/Tablo/plex/makeposter.php?text=' + str(channelDict['callSign'])

			#Guide Series or Episode Info
			if channelDict['type'] != 'Sport':
				guideEpInfo = guideInfo['jsonForClient']

				if 'seasonNumber' in guideEpInfo:
					channelDict['seasonNumber'] = int(guideEpInfo['seasonNumber'])
				if 'episodeNumber' in guideEpInfo:
					channelDict['episodeNumber']= int(guideEpInfo['episodeNumber'])
				if 'airDate' in guideEpInfo:
					channelDict['airDate'] = guideEpInfo['airDate']
				if 'originalAirDate' in guideEpInfo:
					channelDict['originalAirDate'] = guideEpInfo['originalAirDate']
				if 'description' in guideEpInfo:
					channelDict['description'] = guideEpInfo['description']
				if 'duration' in guideEpInfo:
					channelDict['duration'] = int(guideEpInfo['duration']) *1000
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
					channelDict['duration'] = int(guideJsonInfo['duration']) *1000
				if 'originalAirDate' in guideJsonInfo:
					channelDict['originalAirDate'] = guideJsonInfo['originalAirDate']
				if 'cast' in guideJsonInfo:
					channelDict['cast']= [castMember for castMember in guideJsonInfo['cast']]
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
					channelDict['duration'] = int(guideJsonInfo['duration']) *1000


	#PlexLog(LOG_PREFIX + "Completed getChannelDict",chid)
	return channelDict




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
				# The commented out code was to try to bypass a tuncation issue with plex sync
				# Plex sync still did not work but this does resolve the truncation
				# and may be needed later
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
		
		shows = {}
		data =Dict["tablo"]
	
		for episodejson, value in data.iteritems():
		 
			episodeDict = value
			try:
				
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
				
	#if their is only 1 season, skip the unneeded screen
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
	lasttabloip = ''
	try:
		if 'public_ip' in Dict:
			lasttabloip = Dict['public_ip']
		Dict['tabloips'] = getTabloIP()
		for tablo in Dict['tabloips']:
			count = count + 1
			Dict['public_ip'] = str(tablo['public_ip'])
			Dict['private_ip'] = str(tablo['private_ip'])
		#detect if the IP address has changed (most likely due to dhcp)
		# if it did, clear the dicts because the stored IP's will be incorrect
		# @ToDo remove all references in the dicts to the tablo's IP and use the Tablos' ID
		# To find the IP in the tabloips Dict
		if Dict['public_ip'] != lasttabloip:
			ClearTabloData()
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
	Name: ClearTabloData()
	
	Parameters: None
	
	Handler: 
	
	Purpose: Central function to reset data
	
	Returns:
	
	Notes:
#########################################'''
def ClearTabloData():
	HTTP.ClearCookies()
	HTTP.ClearCache()
	Dict.Reset()
	if "tablo" not in Dict:
		PlexLog('ClearTabloData','Clear appears to have worked')

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
	if 'ver' in Dict:
		if Dict['ver'] != VERSION:
			ClearTabloData()
	else: 
		ClearTabloData()
	LoadTablos()
	loadData(Dict)
	loadLiveTVData(Dict)
	Dict['ver'] =VERSION
except Exception as e:
	PlexLog('At start',e)