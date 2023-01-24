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

req = Session()

class Exceptions(Exception):
	def __init__(*args, **kwargs):
		Exception.__init__(*args, **kwargs)


def get_code(link: str, proxies : dict = None):
	request = req.get(f'https://service.narvii.com/api/v1/g/s/link-resolution?q={link}',headers = {'NDCDEVICEID':Client().device_generator()}, proxies = proxies)
	if request.status_code!=200:
		raise Exceptions(request.text)
	return request.json()
	
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
			request = req.post(f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}',headers = self.headers, proxies = self.proxies)
		else:
			request = req.post(f'{self.api}/g/s/chat/thread/{chatId}/member/{self.userId}',headers = self.headers, proxies = self.proxies)
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
			request = req.delete(f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}',headers = self.headers, proxies = self.proxies)
		else:
			request = req.delete(f'{self.api}/g/s/chat/thread/{chatId}/member/{self.userId}',headers = self.headers, proxies = self.proxies)
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

	def subscribe_vip(self, userId : str, Renew : bool = False,transactionId : str = None):
		if transactionId:
			transactionId = transactionId
		else:
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
				raise TypeError("spicify file type")
			data["mediaUploadValue"] = b64encode(file.read()).decode()
		data = dumps(data)
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		if self.comId:
			request = req.post(f'{self.api}/x{self.comId}/s/chat/thread/{chatId}/message',data = data, headers = self.headers, proxies = self.proxies)
		else:
			request = req.post(f'{self.api}/g/s/chat/thread/{chatId}/message',data = data, headers = self.headers, proxies = self.proxies)
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