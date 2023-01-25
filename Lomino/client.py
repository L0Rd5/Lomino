from os import urandom
from requests import Session
from binascii import hexlify
from uuid import UUID
from hmac import new
from hashlib import sha1
from json import dumps , loads
from base64 import b64encode, b64decode
from functools import reduce
from time import time as timestamp
from datetime import datetime
from websocket import WebSocket

req = Session()
web = WebSocket()

class Exceptions(Exception):
	def __init__(*args, **kwargs):
		Exception.__init__(*args, **kwargs)
	
class Client:
	def __init__(self, device : str = None,comId : str = None, proxies : dict = None):
		self.api = 'https://service.narvii.com/api/v1'
		if device:
			self.device = device
		else:
			self.device = self.device_generator()
		self.proxies = proxies
		self.comId = comId
		self.userId = None
		self.sid = None
		self.headers = {'NDCDEVICEID':self.device,
		'User-Agent':None,
		'Accept-Language':'ar',
		'Content-Type':'application/x-www-form-urlencoded',
		'Host':'service.narvii.com',
		'Accept-Encoding':'gzip',
		'Connection':'keep_alive'}
		
	def sig(self, data : str):
		return b64encode(bytes.fromhex('19')+new(bytes.fromhex('DFA5ED192DDA6E88A12FE12130DC6206B1251E44'),data.encode(),sha1).digest()).decode()
		
	def device_generator(self, identifier : str = urandom(20)):
		return ("19" + identifier.hex() + new(bytes.fromhex("E7309ECC0953C6FA60005B2765F99DBBC965C8E9"), b"\x19" + identifier, sha1).hexdigest()).upper()
	
	def get_time_zone(self):
		times = ["-60","-120 ","-180","-240","-300","-360","-420","-480","-540","-600","+780","+720","+660","+600","+540","+480","+420","+360","+300","+240","+180","+120","+60","+0"]
		return int(times[datetime.utcnow().hour])
	
	def get_code(self, link: str, proxies : dict = None):
		request = req.get(f'{self.api}/g/s/link-resolution?q={link}',headers = self.headers, proxies = proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def get_from_sid(self, sid : str):
		return loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())
	
	def sign_in_with_sid(self , sid : str):
		userId = self.get_from_sid(sid)['2']
		self.sid = sid
		self.headers['NDCAUTH'] = f'sid={sid}'
		
	def sign_in(self, email : str , password : str):
		data = dumps({'email':email,
		'secret':f'0 {password}',
		'deviceID':self.device,
		'v':2,
		'clientType':100,
		'action':'normal',
		'timestamp':int(timestamp()*1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/g/s/auth/login',data = data, headers = self.headers, proxies = self.proxies)
		respone = request.json()
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			self.sid = respone['sid']
			self.userId = respone['account']['uid']
			self.headers['NDCAUTH'] = f'sid={self.sid}'
			return respone
			
	def sign_out(self):
		data = dumps({'deviceID': self.device,
		'clientType': 100,
		'timestamp': int(timestamp()*1000
		)})
		self.headers['NDC-MSG-SIG'] = sig(data)
		request = req.post(f'{self.api}/g/s/auth/logout', data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
		
	def join_community(self):
		data = dumps({'timestamp': int(timestamp() * 1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/community/join',data = data,headers = self.headers, proxies = proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
		
	def join_chat(self, chatId : str):
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}'
		else:
			api = f'{self.api}/g/s/chat/thread/{chatId}/member/{self.userId}'
		request = req.post(api, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
		
	def check_lottery(self, tz : int = None):
		if tz:
			timezone = tz
		else:
			timezone = self.get_time_zone()
		data = dumps({'timezone':timezone,
		'timestamp':int(timestamp()*1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/check-in',data = data , headers = self.headers , proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def send_time_object(self, tz : int = None):
		if tz:
			timezone = tz
		else:
			timezone = self.get_time_zone()
		timetamp = int(timestamp())
		data = dumps({'userActiveTimeChunkList':[{'start':timetamp,
		'end':timetamp+300}
		for i in range(25)],
		'optInAdsFlags':2147483647,
		'timestamp': timetamp*1000,
		'timezone':timezone})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/community/stats/user-active-time',data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def leave_chat(self, chatId : str):
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}'
		else:
			api = f'{self.api}/g/s/chat/thread/{chatId}/member/{self.userId}'
		request = req.delete(api,headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def leave_community(self):
		request = req.post(f'{self.api}/x{self.comId}/s/community/leave',headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()

	def subscribe_vip(self, userId : str, Renew : bool = False):
		transactionId = UUID(hexlify(urandom(16)).decode('ascii'))
		data = dumps({'timestamp':int(timestamp()*1000),
		'paymentContext':{'isAutoRenew':
			Renew,
			'transactionId':transactionId}})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/influencer/{userId}/subscribe',data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def send_message(self, chatId: str, message: str = None, messageType: int = 0, file = None, fileType: str = None, replyTo: str = None, mentionUserIds: list = None, stickerId: str = None, embedId: str = None, embedType: int = None, embedLink: str = None, embedTitle: str = None, embedContent: str = None, embedImage = None):
		if message is not None and file is None:
			message = message.replace('<$', '')
			mentions = []
		if mentionUserIds:
			for mention_uid in mentionUserIds:
				mentions.append({'uid': mention_uid})
		time_tamp = int(timestamp())
		data = {'type': messageType,
		'content': message,
		'clientRefId':
			int(time_tamp / 10 % 1000000000),
		'attachedObject':
			{'objectId': embedId,
		'objectType': embedType,
		'link': embedLink,
		'title': embedTitle,
		'content': embedContent,
		'mediaList': embedImage},
		'extensions': {'mentionedArray': 
		mentions},
		'timestamp': int(time_tamp*1000)}
		if replyTo:
			data["replyMessageId"] = replyTo
		if stickerId:
			data['content'] = None
			data['stickerId'] = stickerId
			data['type'] = 3
		if file:
			data['content'] = None
			if fileType == 'audio':
				data['type'] = 2
				data['mediaType'] = 110
			elif fileType == 'image':
				data['mediaType'] = 100
				data['mediaUploadValueContentType'] = 'image/jpg'
				data['mediaUhqEnabled'] = True
			elif fileType == 'gif':
				data['mediaType'] = 100
				data['mediaUploadValueContentType'] = 'image/gif'
				data['mediaUhqEnabled'] = True
			else:
				raise TypeError("يا غبي حط مسار للملف")
			data["mediaUploadValue"] = b64encode(file.read()).decode()
		data = dumps(data)
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/message'
		else:
			request = '{self.api}/g/s/chat/thread/{chatId}/message'
		request = req.post(api, data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exception(request.text)
		else:
			return request.json()

	def send_verify_link(self, email : str):
		data = dumps({'type': 1,
		'deviceID': self.device,
		'identity': email})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/g/s/auth/request-security-validation',data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def claim_reputation(self, chatId : str):
		request = req.post(f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation',headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def verify(self, email : str, code : str):
		data = dumps({'identity': email,
		'data': {'code': code},
		'type': 1,
		'deviceID': self.device})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/g/s/auth/activate-email',data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def sign_up(self, nickname : str, email : str, password : str, code : str = None, address : str = None):
		data = dumps({
		'nickname': nickname,
		'email': email,
		'secret': f'0 {password}',
		'deviceID': self.device,
		'clientType': 100,
		'latitude': 0,
		'longitude': 0,
		'address': address,
		'clientCallbackURL': 'narviiapp://relogin',
		'validationContext': {'data':{'code': code},
		'type': 1,
		'identity': email,
		'timestamp': int(timestamp()*1000)}})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/g/s/auth/register',data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def get_about_wallet(self):
		request = req.get(f"{self.api}/g/s/wallet", headers=self.headers, proxies=self.proxies)
		if request.status_code != 200:
			return Exceptions(request.text)
		else:
			return request.json()
	
	def send_coins(self, coins : int, blogId : str = None, wikiId : str = None, chatId : str = None):
		transactionId = UUID(hexlify(urandom(16)).decode('ascii'))
		data = {'coins': int(coins),
		'tippingContext': 
		{'transactionId': transactionId},
		'timestamp': int(timestamp() *1000)}
		if blogId:
			api = f'{self.api}/x{self.comId}/s/blog/{blogId}/tipping'
		elif chatId:
			api = f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/tipping'
		elif wikiId:
			api = f'{self.api}/x{self.comId}/s/tipping'
			data['objectType'] = 2
			data['objectId'] = wikiId
		else:
			raise TypeError('يحمار حط ايدي')
		data = dumps(data)
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(url, data = data, headers = self.headers, proxies = self.proxies)
		if req.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()

	def get_about_user(self, userId : str):
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/user-profile/{userId}'
		else:
			api = f'{self.api}/g/s/user-profile/{userId}'
		request = req.get(api, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def follow(self, userId : str):
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/user-profile/{userId}/member'
		else:
			api = f'{self.api}/g/s/user-profile/{userId}/member'
		data = dumps({
		'timestamp': int(timestamp()*1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(api, data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def unfollow(self, userId : str):
		if self.comId:
			api = f'{self.api}/x{self.comId}/s/user-profile/{userId}/member/{self.userId}'
		else:
			api = f'{self.api}/g/s/user-profile/{userId}/member/{self.userId}'
		data = dumps({
		'timestamp': int(timestamp()*1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.delete(api, data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def comment(self, content : str = None, userId : str = None, replyTo : str = None, blogId : str = None, wikiId : str = None):
		data = {'content': content, 'timestamp': int(timestamp() *1000)}
		if replyTo:
			data["respondTo"] = replyTo
		elif userId:
			api = f'{self.api}/x{self.comId}/s/user-profile/{userId}/comment'
		elif blogId:
			api = f'{self.api}/x{self.comId}/s/blog/{blogId}/comment'
		elif wikiId:
			api = f'{self.api}/x{self.comId}/s/item/{wikiId}/comment'
		else:
			raise TypeError('يا غبي حط تايب')
		data = dumps(data)
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(api, data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def delete_comment(self, commentId : str, userId: str = None, blogId : str = None, wikiId : str = None):
		if userId:
			api = f'{self.api}/x{self.comId}/s/user-profile/{userId}/comment/{commentId}'
		elif blogId:
			api = f'{self.api}/x{self.comId}/s/blog/{blogId}/comment/{commentId}'
		elif wikiId:
			api = f'{self.api}/x{self.comId}/s/item/{wikiId}/comment/{commentId}'
		else:
			raise TypeError('حط تايب ولاك')
		request = req.delete(api, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
			
	def post(self, title : str ,content : str, fans : bool = False, blog : bool = False, wiki : bool = False, backgroundColor : str = None, keywords : list = None, icon : str = None):
		data = {'content': content,
		'latitude': 0,
		'longitude': 0,
		'extensions': {'props': [],'fansOnly': fans,
		'style': {
		'backgroundColor': backgroundColor}},
		'timestamp':int(timestamp() *1000)}
		if blog is True:
			data['type'] = 0
			data['contentLanguage'] = 'ar'
			data['title'] = title
			data['eventSource'] = 'GlobalComposeMenu'
			api = f'{self.api}/x{self.comId}/s/blog'
		elif wiki is True:
			data['icon'] = icon
			data['keywords'] = keywords,
			data['label'] = title
			data['eventSource'] = 'GlobalComposeMenu'
			api = f'{self.api}/x{self.comId}/s/item'
		else:
			raise TypeError('التايب غلط يباشا')
		data = dumps(data)
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(api, data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def vote(self, blogId : str, optionId : str):
		data = dumps({'value': 1,
		'eventSource': 'PostDetailView',
		'timestamp': int(timestamp() *1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote', data = data, headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()
	
	def stream(self, chatId : str, joinRole : int = None, channelType : int = None, joinId : str = '72446', type : int = 112):
		data = dumps({'o':{'ndcId': self.comId,
		'threadId': chatId, 'joinRole': joinRole,
		'channelType': channelType,
		'id': joinId}, 't': type})
		web_data = f'{self.device}|{int(timestamp()*1000)}'
		self.headers['NDC-MSG-SIG'] = self.sig(web_data)
		connect_video = web.connect(f'wss://ws1.narvii.com?signbody={web_data.replace("|", "%7C")}', header = self.headers,proxies = self.proxies)
		web.send(data)
	
	def get_my_communities(self, start : int = 0, size : int = 25):
		request = req.get(f'{self.api}/g/s/community/joined?v=1&start={start}&size={size}', headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()['communityList']
	
	def get_about_chat(self, chatId : str):
		request = req.get(f'{self.api}/g/s/chat/thread/{chatId}', headers = self.headers, proxies = self.proxies)
		if request.status_code!=200:
			raise Exceptions(request.text)
		else:
			return request.json()['thread']