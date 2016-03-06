# -*- coding: utf-8 -*-

import urllib2
import re, time
from HTMLParser import HTMLParser
from string import join
import configuration

#class to query yahoo, based on the one developed by T. Javier Robles Prado (http://users.servicios.retecal.es/tjavier/python/google.py.html)

URL          = 'http://search.yahoo.com'
COD_SEARCH   = '/search?fr=ylt&p='

class YahooQuery:
	def __init__(self, query):
		self.results = {}
		self.number = 0
		self.__yahoo(query)
			
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
		
	def __yahoo(self, query = None):
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
		
		parser = self.YahooParser(search)
		#parser
		self.results = parser.getResults()
		self.number = parser.getNumberOfResults() 		
		
	def __run(self, query):  
		try:          
			query = URL + COD_SEARCH + self.__formatQuery(query)

			request = urllib2.Request(query)
			request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
		
			stream = urllib2.urlopen(request)

			return stream.read()
		except:
			print time.ctime() +": Connection refused"
			return -1
            
	class YahooParser(HTMLParser):
		
		def __init__(self, html):
			HTMLParser.__init__(self) 
			self.yahooLinkFound = False
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
			try:
				result = self.data.partition("1 - 10 of ")[2]
				result = result.split(" ")[0]
				result = result.replace(",","")
	
				return int(result)
			except ValueError:
				try:
					result = self.data.partition("1 - ")[2]
					result = result.split(" ")[0]
					result = result.replace(",","")
					
					return int(result)
				except:
					return 0

			
		#Result of yahoo:
		#interests: the text	
		def handle_data(self,data):
			self.data += (data + self.appendingText)
			if self.yahooLinkFound:
				self.results[self.links] += (data + self.appendingText)
		
		def handle_starttag(self,tag,attrs):
			#it is a yahoo result
			if tag == "p" or tag == "br" or tag == "td" or tag == "h1" or tag == "h2" \
			or tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.appendingText = "\n"
			else:
				if tag == "sub" or tag =="sup":
					self.appendingText = " "
				else:
					self.appendingText = ""
				
			if tag == "div":
				for pair in attrs:
					if pair[0] == "id" and pair[1] =="pg" and self.yahooLinkFound == True:
						self.yahooLinkFound = False
					if pair[0] == "class" and pair[1] =="res":
						self.yahooLinkFound = True
						self.links += 1
						self.results[self.links]=""
	
		def handle_endtag(self,tag):
			if tag == "tr" or tag == "h1" or tag == "h2" or \
			tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.data += " "
				if self.yahooLinkFound:
					self.results[self.links] += " "		

		def handle_charref (self, name):
			if name == "39":
				self.data += "\'"
				if self.googleLinkFound:
					self.results[self.links] += "\'"				
