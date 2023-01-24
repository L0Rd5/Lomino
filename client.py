from os import urandom
from requests import Session
from hmac import new
from hashlib import sha1
from json import dumps
from base64 import b64encode
from time import time as timestamp

class Client:
	def __init__(self, device : str = None,comId : str = None proxies : dict = None):
		self.api = 'https://service.narvii.com/api/v1'
		if device is None:
			self.device = self.device_generator()
		else:
			self.device = device
		self.proxies = proxies
		self.comId = comId
		self.userId = None
		self.sid = None
		self.req = Session()
		self.headers = {'NDCDEVICEID':self.device,
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
		'Accept-Language':'ar',
		'Content-Type':'application/x-www-form-urlencoded',
		'Host':'service.narvii.com',
		'Accept-Encoding':'gzip',
		'Connection':'keep_alive'}
		
	def sig(self, data : str):
		return b64encode(bytes.fromhex('19')+new(bytes.fromhex('DFA5ED192DDA6E88A12FE12130DC6206B1251E44'),data.encode(),sha1).digest()).decode()
		
	def device_generator(self, identifier : str = urandom(20)):
		return ("19" + identifier.hex() + new(bytes.fromhex("E7309ECC0953C6FA60005B2765F99DBBC965C8E9"), b"\x19" + identifier, sha1).hexdigest()).upper()
		
	def sign_in(self, email : str , password : str):
		data = dumps({'email':email,
		'secret':str(0,password),
		'deviceID':self.device,
		'v':2,
		'clientType':100,
		'action':'normal',
		'timestamp':int(timestamp()*1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/g/s/auth/login',data = data, headers = self.headers, proxies = self.proxies)
		respone = request.json()
		self.sid = respone['sid']
		self.userId = respone['account']['uid']
		self.headers['NDCAUTH'] = f'sid={self.aid}'
		return respone['api:message']
	
	def get_code(self, link : str):
		request = req.get(f'{self.api}/g/s/link-resolution?q={link}',headers = self.headers, proxies = self.proxies)
		respone = request.json()
		return respone
		
	def join_community(self):
		data = dumps({"timestamp": int(timestamp() * 1000)})
		self.headers['NDC-MSG-SIG'] = self.sig(data)
		request = req.post(f'{self.api}/x{self.comId}/s/community/join',data = data,headers = self.headers, proxies = proxies)
		respone = request.json()
		return respone['api:message']