# -*- coding: utf-8 -*-

import urllib2
import live
import nltk, re, pprint
import time
from HTMLParser import HTMLParser
import unicodedata


# Class to get and split a web content to analyze it later.
#
#
# author: Jose Miguel Millan Rosa
# date  : 14-01-08

class WebText():
	def __init__(self, url, tagger):	
		parser = self.WebParser(url)
		self.data = parser.getTextContent()
		
		#these are used to know which word in ASCII corresponds to each word in UTF-8
		self.rawData = parser.getContent()
		try:
			self.asciiRawData = unicodedata.normalize('NFKD', self.rawData.decode('utf-8')).encode('ascii','ignore')
		except:
			self.asciiRawData = self.rawData
		#this is used to work properly with the content
		try:
			self.data = unicodedata.normalize('NFKD', self.data.decode('utf-8')).encode('ascii','ignore')
		except:
			self.data = self.data
			
		self.tagger = tagger
		self.taggedTokens = self.tagger.tagText(self.data)
		
	def getTextContent(self):
		return self.data

	def getTextRawContent(self):
		return self.rawData

	def getRawWord(self,word):
		if self.asciiRawData.find(word) == -1:
			return None
		else:
			cleanTemp = self.asciiRawData.replace(".","").replace(",","").replace(";","").replace(":","")
			cleanRawTemp = self.rawData.replace(".","").replace(",","").replace(";","").replace(":","")
			
			temp = cleanTemp.split(" ")
			rawTemp = cleanRawTemp.split(" ")
			try:
				place = temp.index(word)
			except ValueError:
				print time.ctime() + ":--ERROR-- WebText:getRawWord ==> \""+word+"\" has not been found in the raw text, it may be written in a longer way."
				return word
			
			return rawTemp[place]
		
	def TaggedText(self):
		return self.taggedTokens
				
	def getTextNounPhrases(self):
		return self.tagger.getTextNounPhrases(self.taggedTokens)

	class WebParser(HTMLParser):
		
		def __init__(self, url):
			HTMLParser.__init__(self)

			request = urllib2.Request(url)
			request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
			
			self.readText = True
			self.content = urllib2.urlopen(request)
			self.appendingText = " "
			self.contentSGML = self.content.read()
			self.feed(self.contentSGML)
			
		def reset(self):
			# extend (called by SGMLParser.__init__)
			self.data = ""
			self.pieces = []
			HTMLParser.reset(self)
			
		# gets the content from the specified web page 
		def getContent(self):
			return self.contentSGML
			
		def getTextContent(self):
			return self.data
		
		def handle_data(self,data):
			if self.readText == True:
				string = data
				string.replace
				self.data += (data + self.appendingText)
			
		def handle_starttag(self,tag,attrs):
			#it is a yahoo result
			if tag == "script":
				self.readText = False
			else:
				if tag == "style":
					self.readText = False
				else:
					self.readText = True
				
			if tag == "br":
				self.appendingText = "\n"
			else:
				if tag == "td":
					self.appendingText = "."
				else:
					self.appendingText = " "
				

		def handle_charref (self, name):
			if name == "160":
				self.data += " "
			if name == "34":
				self.data += "\'"
			if name == "19":
				self.data += "\""
