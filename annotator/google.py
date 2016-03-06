# -*- coding: utf-8 -*-

import urllib2
import re, time
from HTMLParser import HTMLParser
from string import join
import configuration

#module to query google, based on the one developed by T. Javier Robles Prado (http://users.servicios.retecal.es/tjavier/python/google.py.html)

NUM	     = '100'
URL          = 'http://www.google.com'
COD_SEARCH   = '/search?num='+NUM+'&q='

"""
Main class of this module. Represents a query to the google search engine. It has several methods related to the query asked
"""
class GoogleQuery:
	def __init__(self, query):
		self.results = {}
		self.number = 0
		self.__google(query)
	
		f = open(configuration.QUERY_LOG, 'a')
		f.write(query + " " + str(self.number)+"\n")
		f.close()
		
	#Returns the results obtained from the query
	def getResults(self):
		return self.results
	
	#Returns the number of results of the query
	def getNumberResults(self):
		return self.number
	
	#Returns the matching percentage of the passed text into the results obtained
	def getMatchingPercentage(self, text):
		resultText = ""

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
		
		numberOfGoodMatchings = 0
		numberOfMatchings = 0
		
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
		
	#Private method to format the query as it can be sent and understood by Google
	def __formatQuery(self, query):
		a = query.replace("\"","%22")
		a = a.replace("'","%27")
		a = a.split()
		
		return join(a, '+')
		
	#Method to do the query to Google
	def __google(self, query = None):
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
		
		parser = self.GoogleParser(search)

		#parser
		self.results = parser.getResults()
		self.number = parser.getNumberOfResults()	

	#Private method which opens a connection via HTTP to Google search engine and queries the
	#arguments passed
	def __run(self, query):
		try:
			query = URL + COD_SEARCH + self.__formatQuery(query)

			#print time.ctime() +": Query to Google: " + query
			
			request = urllib2.Request(query)
			request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
		
			stream = urllib2.urlopen(request)

			return stream.read()
		except:
			print time.ctime() +": Connection refused"
			return -1
	
	"""
	Class used to parse the text from a query to Google
	"""
	class GoogleParser(HTMLParser):
		def __init__(self, html):
			HTMLParser.__init__(self) 
			self.googleLinkFound = False
			self.links = 0
			self.results={}
			self.appendingText = ""
			self.suffixingText = ""
			self.data = ""
			self.feed(html)
			
		def reset(self):
			# extend (called by SGMLParser.__init__)
			self.pieces = []
			HTMLParser.reset(self)
			
		#Method which returns a dictionary with the results from the query in <format dict[position]=result> 
		def getResults(self):
			return self.results
	
		#Method which returns the text of the query
		def getTextContent(self):
			return self.data
		
		#Method which extracts from the text of the HTML document the number of results of the query by Google
		def getNumberOfResults(self):
			try:
				result = self.data.partition("Results 1 - "+NUM+" of about ")[2]
				result = result.split(" ")[0]
				result = result.replace(",","")
					
				return int(result)
			except ValueError:
				try:
					result = self.data.partition("Results 1 - ")[2]
					result = result.split(" ")[0]
					result = result.replace(",","")
					
					return int(result)
				except:
					return 0

		#Inherited method from the Python HTMLParser to parse the data in the HTML documents
		def handle_data(self,data):
			self.data += (data + self.appendingText)
			if self.googleLinkFound:
				self.results[self.links] += (data + self.appendingText)
		
		#Inherited method from the Python HTMLParser to parse the starting tags in the HTML documents
		def handle_starttag(self,tag,attrs):
			if tag == "p" or tag == "br" or tag == "td" or tag == "h1" or tag == "h2" or \
			tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.appendingText = "\n"
			else:
				if tag == "sub" or tag =="sup":
					self.appendingText = " "
				else:
					self.appendingText = ""
				
			#it is a google result
			if tag == "div":
				for pair in attrs:
					if pair[0] == "class" and pair[1] =="g":
						self.googleLinkFound = True
						self.links += 1
						self.results[self.links]=""
					if pair[0] == "class" and pair[1] !="g":
						self.googleLinkFound = False
					
		def handle_endtag(self,tag):
			if tag == "tr" or tag == "h1" or tag == "h2" or \
			tag == "h3" or tag == "h4" or tag == "h5" or tag == "h6" or \
			tag == "title" or tag == "body" or tag == "div" or tag == "frame" or tag == "li":
				self.data += " "
				if self.googleLinkFound:
					self.results[self.links] += " "

		def handle_charref (self, name):
			if name == "39":
				self.data += "\'"
				if self.googleLinkFound:
					self.results[self.links] += "\'"				

			    
