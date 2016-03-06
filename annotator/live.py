# -*- coding: utf-8 -*-

import urllib2
import re, time
from HTMLParser import HTMLParser
from string import join
import unicodedata
import configuration 
#class to query MSN Live, based on the one developed by T. Javier Robles Prado (http://users.servicios.retecal.es/tjavier/python/google.py.html)

URL          = 'http://search.msn.com'
COD_SEARCH   = '/results.aspx?setlang=en-US&form=LTRE&q='
COUNT        = '&count=100'

class LiveQuery:
	def __init__(self, query):
		self.results = {}
		self.number = 0
		self.__live(query)
		f = open(configuration.QUERY_LOG, 'a')
		f.write(query + " " + str(self.number)+"\n")
		f.close()
		
	
	def getResults(self):
		return self.results
	
	def getNumberResults(self):
		return self.number
	

	def getMatchingPercentage(self, text):
		resultText = ""
		numberOfGoodMatchings = 0
		numberOfMatchings = 0
		
		text = text.replace("+","\+")
		text = text.replace (".","\.")
		text = text.replace ("|","\|")
		text = text.replace ("$","\$")
		text = text.replace ("?","\?")
		text = text.replace ("^","\^")
		text = text.replace ("*","\*")
		text = text.replace ("(","\(")
		text = text.replace (")","\)")
		text = text.replace ("{","\{")
		text = text.replace ("}","\}")
		
		#create a new string with the text of all the results
		for result in self.results.values():
			resultText += result
		
		#search good matchings
		pattern = re.compile(text)
		iterator = pattern.finditer (resultText)
		numberOfGoodMatchings = sum(1 for _ in iterator)
		
		#search number of total matchings
		pattern = re.compile(text,re.I)
		iterator = pattern.finditer (resultText)
		numberOfMatchings = sum(1 for _ in iterator)

		#return the percentage
		if numberOfMatchings < 1:
			return -1.0
		else:
			return float(float(numberOfGoodMatchings) / float(numberOfMatchings))

	def getMatchingResults(self, text):
		resultText = ""
		numberOfGoodMatchings = 0

		text = text.replace("+","\+")
		text = text.replace (".","\.")
		text = text.replace ("|","\|")
		text = text.replace ("$","\$")
		text = text.replace ("?","\?")
		text = text.replace ("^","\^")
		text = text.replace ("*","\*")
		text = text.replace ("(","\(")
		text = text.replace (")","\)")
		text = text.replace ("{","\{")
		text = text.replace ("}","\}")
		
		#create a new string with the text of all the results
		for result in self.results.values():
			resultText += result
		
		#search good matchings
		pattern = re.compile(text)
		iterator = pattern.finditer (resultText)
		numberOfGoodMatchings = sum(1 for _ in iterator)	
	
		return numberOfGoodMatchings

	def __formatQuery(self, query):
		query.replace("\"","%22")
		a = query.split()
		return join(a, '+')

	def __live(self, query = None):
		if query is None:
			print time.ctime() +": no query given"
			return -1
		
		search = self.__run (query)
		
		if search == -2:
			print time.ctime() +": No results for the query"
			return 
		if search == -1:
			print time.ctime() +": Impossible to connect"
			return
		
		#to clean the shit-tags into the page retrieved
		search = search.replace("<scr\"+'ipt", "\"<script>")
		search = search.replace("</scr\'+\"ipt>", "\'</script>")
		search = search.replace("a<c","a < c")
		
		parser = self.LiveParser(search)
		
		#parser
		self.results = parser.getResults()
		self.number = parser.getNumberOfResults() 		

	def __run(self, query):  
		try:
			query = URL + COD_SEARCH + self.__formatQuery(query) + COUNT

			request = urllib2.Request(query)
			request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
		
			stream = urllib2.urlopen(request)
			
			return stream.read()
		except:
			print time.ctime() +": Connection refused"
			return -1

	class LiveParser(HTMLParser):
		
		def __init__(self, html):
			HTMLParser.__init__(self) 
			self.liveResultsSection = False
			self.liveLink = False
			self.links = 0
			self.appendingText = ""
			self.results={}
			self.data = ""
			self.feed(html)
			
			
		def reset(self):
			# extend (called by SGMLParser.__init__)
			self.pieces = []
			HTMLParser.reset(self)
	
		def getResults(self):
			return self.results
	
		def getTextContent(self):
			return self.data
		
		def getNumberOfResults(self):
			result = self.__getShortVersion()
			if result == -1:
				result = self.__getLongVersion()
			
			if result == -1:
				return 0
			else:
				return result
		
		def __getShortVersion(self):
			try:
				result = self.data.partition("1-99 of ")[2]
				result = result.split(" ")[0]
				result = result.split("\n")[0]
				result = result.replace(",","")

				return long(result)
			except ValueError:
				try:
					result = self.data.partition("1-100 of ")[2]
					result = result.split(" ")[0]
					result = result.split("\n")[0]
					result = result.replace(",","")
					
					return long(result)
				except ValueError:
					try:
						result = self.data.partition("Web\n\n1-")[2]
						result = result.split(" ")[0]
						result = result.replace(",","")
					
						return int(result)
					except ValueError:
						return -1
			except:
				return -1
		
		
		def __getLongVersion(self):
			try:
				result = self.data.partition("Web results \n\n1-99 of ")[2]
				result = result.split(" ")[0]
				result = result.split("\n")[0]
				result = result.replace(",","")

				return long(result)
			except ValueError:
				try:
					result = self.data.partition("Web results \n\n1-100 of ")[2]
					result = result.split(" ")[0]
					result = result.split("\n")[0]
					result = result.replace(",","")
					
					return long(result)
				except ValueError:
					try:
						result = self.data.partition("Web results \n\n1-")[2]
						result = result.split(" ")[0]
						result = result.replace(",","")
					
						return int(result)
					except ValueError:
						return -1
			except:
				return -1
		
		#Result of google:
		#interests: the text	
		def handle_data(self,data):
			self.data += (data + self.appendingText)	
			if self.liveLink:
				try:
					self.results[self.links] += unicodedata.normalize('NFKD', (data + self.appendingText).decode('utf-8')).encode('ascii','ignore')
				except UnicodeDecodeError:
					self.results[self.links] += (data + self.appendingText)
		
		def handle_starttag(self,tag,attrs):
			if tag == "p" or tag == "br" or tag == "td" or tag == "h1" or tag == "h2" \
			or tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.appendingText = "\n"
			else:
				if tag == "sub" or tag =="sup" or tag =="span":
					self.appendingText = " "
				else:
					self.appendingText = ""
					
			#it is a google result
			if tag == "div":
				for pair in attrs:
					if pair[0] == "id" and pair[1] =="results":
						self.liveResultsSection = True
					if pair[0] == "id" and pair[1] !="results":
						self.liveResultsSection = False
						
			if self.liveResultsSection:
				if tag == "li":
					if len(attrs) == 0:
						self.liveLink = True
						self.links += 1
						self.results[self.links]=""
											
					for pair in attrs:
						if pair[0] == "class" and pair[1] =="firstResult": 
							self.liveLink = True
							self.links += 1
							self.results[self.links]=""
					
					
		def handle_endtag(self,tag):	
			if tag == "li" and self.liveLink:
				self.liveLink = False
			if tag == "tr" or tag == "h1" or tag == "h2" or \
			tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.data += "\n"
				if self.liveLink:
					self.results[self.links] += "\n"

		def handle_charref (self, name):
			if name == "39":
				self.data += "\'"
				if self.googleLinkFound:
					self.results[self.links] += "\'"
