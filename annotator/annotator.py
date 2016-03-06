# -*- coding: utf-8 -*-

import configuration
import os
import sys
import ontology
import google
import yahoo
import live
import web
import nltk
import annotation
import time
from nltk import wordnet
import re
from xmlrpclib import Server

"""
Main class of the auto Annotator system. It works as follows:
	1.- Obtains the text to annotate
	2.- Searches into the text the Named Entities
	3.- Using text patterns and the ontology classes tries to find relations between these classes and the Named Entities 
	4.- Annotates the Named Entities
"""

class Annotator:
	def __init__(self):
		self.nounPhrases = []
		self.ontoURL =  configuration.ONTOLOGY_SERVICE_URL + "/" + configuration.ONTOLOGY_NAME
		self.tagger = Server("http://" + configuration.TAG_SERVICE_URL + ":" + str(configuration.TAG_SERVICE_PORT), verbose=0)
	
	def startProcess(self, url):
		self.__log("Starting process")
		self.__log("Preparing the Tagger")
		self.__log("Reading ontology")
		
		ontologia = ontology.OntologyReader(configuration.ONTOLOGY_SERVICE_URL)
		ontologia.getOntologyClassesByURL(self.ontoURL)
		
		#read the web page
		webPage = web.WebText(url,self.tagger)
		self.__log("Analysing web contents")
		
		# parse, analyse and identify things in the web page
		taggedText = webPage.TaggedText()
	
		# detect into the text the possible entities - text patterns
		self.__log("Discarding non-relevant ones")
		
		NounPhrases = webPage.getTextNounPhrases()
		goodResults = []
		#filter good results
		for phrase in NounPhrases:
			self.__log(phrase['text'] + " " + str(phrase['results']) + " " + str(phrase['matchingPercentage']))
			
			if phrase['results'] > configuration.NUMBER_OF_RESULTS_FOR_RELEVANCE \
			and ( phrase['matchings'] > configuration.NUMBER_OF_MATCHINGS \
			and phrase['matchingPercentage'] > configuration.MATCHING_PERCENTAGE ):
				found = False
				for result in goodResults:
					if result['text'] == phrase["text"]:
						found = True
				
				if not found:
					goodResults.append(phrase)
					
		self.__log("Discarded: " + str(len(NounPhrases) - len(goodResults)) + " Noun-Phrases")
		
		self.__log("Extracting class candidates for the definitive " + str(len(goodResults)) + " Noun-Phrases")
		
		self.nounPhrases = goodResults	
		# search for class candidates
		self.getClassCandidates()
		
		self.__log("Class candidates extracted")

		# relate the entities with the ontology
		self.annotate(self.ontoURL,ontologia)
		
		#Once the NounPhrases are detected mark them with its rellevance
		for phrase in self.getNounPhrases():
			self.__log(phrase['text'] + " is a " + str(phrase['is_a']))
		
		annotatedPage = self.microFormat(self.getNounPhrases(), webPage)

		return annotatedPage
	
	def getNounPhrases (self):
		return self.nounPhrases
	
	def getClassCandidates(self):
		temp = []
		for phrase in self.nounPhrases:
			self.__log("Looking for " + phrase['text'] + " class candidates.")
		
			p = {}
			p = self.__patternIsA(phrase)
			p = self.__patternAndOther(p)
			p = self.__patternOrOther(p)
			p = self.__patternLikeOther(p)
			p = self.__patternSuchAs(p)
			p = self.__patternEspecially(p)
			p = self.__patternIncluding(p)
			temp.append(p)

		self.nounPhrases = temp
		
	def microFormat(self, NounPhrases, webPage):
		annotatedPage = webPage.getTextRawContent()
		
		for phrase in NounPhrases:
			rawText = ""
			words = phrase['text'].split(" ")
			for word in words:
				rawText += webPage.getRawWord(word)
			
			rawText = rawText.strip()
			if phrase['is_a'] != "":
				replacement = "<a href=\"" + phrase['is_a'] + "\" class=\"" + phrase['is_a'] + "\">" + rawText + "</a>"
				
				self.__log( "<<" + rawText +">> <<" + str(phrase['text']) + ">>")
				self.__log( replacement)
				
				#create a new annotation machine and annotate the text
				annotateMachine = annotation.Annotation(rawText,replacement)
				annotateMachine.feed(annotatedPage)
				#string with the web page
				annotatedPage = annotateMachine.output()
			else:
				self.__log(phrase['text'] + " hasn't any class assigned, so it won't be annotated.")
				
		return annotatedPage
		
	def annotate(self, url ,onto):
		ontoNames = onto.getOntologyNames()
		temp = []
		# 2.- If not, use wordnet. Get the last word and compare with each one in Ontology
		for phrase in self.nounPhrases:
			#for each Noun Phrase
			#1.- search it directly into the ontology
			self.__log("Step 3: Ontology length: " + str(len(ontoNames)))
			self.__log("Step 3: candidates number: " + str(len(phrase['candidates'])))
			Similars = self.__searchInOntology(phrase['candidates'], ontoNames)
			
			#1.1.- if no ones are found search the most similar
			if len(Similars) == 0:
				#1.2.- If not found, search the most similar
				Similars = []
				self.__log("Searching candidates for NE: " + phrase['text'])
				Similars = self.__getMostSimilars(phrase['candidates'],ontoNames)
				
				
			#1.3.- If (similars.length > 1) use PMI-IR, else ...
			if len(Similars) == 0:
				self.__log("No candidates in ontology for " + phrase['text'])
			else:
				self.__log("Most appropiate candidates::")
				#calculate PMI-IR
				highestValue = 0.0
				finalOne = ["",-1.0,"",0.0]
			
				for similar in Similars:
					ontologyValue = similar[0].partition("[")[2].partition("]")[0].replace("_"," ")
					#PMI-IR calculus
					query1 = live.LiveQuery("\""+ phrase['text'] + "\"" + " AND " + "\"" + ontologyValue + "\"")
					query2 = live.LiveQuery("\""+ ontologyValue + "\"")
					
					if float(query2.getNumberResults()) <= 0.0:
						similar[3] = 0.0
					else:
						similar[3] = float(float(query1.getNumberResults()) / float(query2.getNumberResults()))
					
						#end PMI-IR calculus
						self.__log(phrase['text'] + "-" + ontologyValue + ". Values: " + str(float(query1.getNumberResults())) + "-" + str(float(query2.getNumberResults())))
						self.__log("		" + similar[0] + " " +str(similar[1]) + " " +similar[2] + " " +str(similar[3]))
	
						#take the one with highest value
						if similar[3] > highestValue:
							highestValue = similar[3]
							finalOne = similar
						
				self.__log("PMI-IR: Chosen one "+ finalOne[0] + " with value "+ str(finalOne[3]))
				phrase['is_a'] = finalOne[0]

	def __searchInOntology(self, candidates, ontologyNames):
		similars = []
		stemmer = nltk.WordnetStemmer()
		
		for candidate in candidates:
			#for each candidate of each Noun Phrase
			for key, value in ontologyNames.iteritems():
				#for each ontology class
				Key = self.__getKeyText(candidate)
				realValue = value.partition("[")[2].partition("]")[0].replace("_"," ")
				realValue = realValue.lower().split(" ")

				for word in realValue:
					if word == Key:
						similars.append([value, 1.0, candidate, 0.0])
		
		return similars

	def __getMostSimilars(self, candidates, ontologyNames):
		similarities=[]
		mostSimilars=[]
		stemmer = nltk.WordnetStemmer()

		for candidate in candidates:
			#for each candidate of each Noun Phrase
			self.__log("		Step 3: searching the similarities for " + candidate)
			for key, value in ontologyNames.iteritems():
				#for each ontology class
				Key = self.__getKeyText(candidate)
				realValue = value.partition("[")[2].partition("]")[0].replace("_"," ")
				realValue = realValue.lower().split(" ")
				
				try:
					similarity = wordnet.N[stemmer.stem(Key.lower())][0].wup_similarity(wordnet.N[realValue.strip()][0])
					similarities.append([value, similarity, candidate, 0.0])
				except:
					similarities.append([value, -1.0, candidate, 0.0])
	
		#search the ones with highest value of similarity and filter the repeated ones
		for similarity in similarities:
			if similarity[1] > configuration.SIMILARITY_THRESHOLD:
				found = False
				for s in mostSimilars:
					if s[0] == similarity[0]:
						found = True
				if not found:
					mostSimilars.append(similarity)
				else:
					found = False

		return mostSimilars
	
	def __getKeyText(self, key):
		text = key.split()
		cleanText = ""
		stemmer = nltk.WordnetStemmer()
		for word in text:
			type = word.partition("/")[2]
			word = word.partition("/")[0]
			word = word.replace(",","").replace(";","").replace(":","").replace(".","").lower()
			
			if type == "NN" or type == "NNP":
				cleanText = word
			if type == "NNS":
				cleanText = stemmer.stem(word)
				if cleanText == None:
					cleanText = word


		return cleanText	

	def __addCandidate(self, phrase, candidate):
		cleanText = candidate
		try:
			phrase['candidates'].index(cleanText)
		except:
			if candidate.find(phrase['textTagged']) == -1:
				phrase['candidates'].append(cleanText)

	def __patternIsA(self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
			      
		#put phrase into the corresponding pattern
		
		queryText = "\"" + phrase['text'] + " is a *\""
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition(phrase['text'] + " is a ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)
			#NOW IN LOWER CASE
			parts = value.partition(phrase['text'].lower() + " is a ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)
		return phrase
	
	def __patternAndOther(self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"" + phrase['text'] + " and other *\""
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition(phrase['text'] + " and other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)		
			#NOW IN LOWER CASE
			parts = value.partition(phrase['text'].lower() + " and other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)		
	
		return phrase

	def __patternOrOther(self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"" + phrase['text'] + " or other *\""
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition(phrase['text'] + " or other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)		
			#NOW IN LOWER CASE
			parts = value.partition(phrase['text'].lower() + " or other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)			
	
		return phrase

	def __patternLikeOther(self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"" + phrase['text'] + ", like other *\""
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition(phrase['text'] + ", like other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)

			#NOW IN LOWER CASE
			parts = value.partition(phrase['text'].lower() + ", like other ")
			#get the concept from the corresponding place
			candidate = self.__getFirstCandidate(parts[2])
			if candidate != None:
				self.__addCandidate(phrase, candidate)	
		return phrase

	def __patternSuchAs(self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"* such as " + phrase['text'] + "\""   
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition( "such as " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)
						
			#NOW IN LOWER CASE
			parts = value.partition( "such as " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)
		return phrase
	
	def __patternEspecially (self, phrase):
		#dictionary = {'textTagged' : candidate, \
			     #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"* especially " + phrase['text'] + "\""   
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition( "especially " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)

			#NOW IN LOWER CASE
			parts = value.partition( "especially " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)
		return phrase
		
	def __patternIncluding (self, phrase):
		#dictionary = {'textTagged' : candidate, \
			      #'text' : text, \
			      #'matchings' : query.getMatchingResults(text) , \
			      #'matchingPercentage' : query.getMatchingPercentage(text), \
			      #'results' : query.getNumberResults(), \
			      #'candidates' : [], \
			      #'is_a: ""}
		#put phrase into the corresponding pattern
		
		queryText = "\"* including " + phrase['text'] + "\""
		
		query = live.LiveQuery(queryText)
		results = query.getResults()
		
		for key,value in results.iteritems():
			#split the text from the pattern
			parts = value.partition( "including " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)
			#NOW IN LOWER CASE
			parts = value.partition( "including " + phrase['text'])
			#get the concept from the corresponding place
			if parts[0] != parts:
				candidate = self.__getLastCandidate(parts[0])
				if candidate != None:
					self.__addCandidate(phrase, candidate)

		return phrase

	
	def __getFirstCandidate(self, text):
		part = text.partition(".")
		part = part[0].partition(",")
		part = part[0].partition("?")
		part = part[0].partition("\n")
		part = part[0].partition(";")
		part = part[0].partition(":")
		part = part[0].partition("|")
		part = part[0].partition(" -")
		part = part[0].partition("- ")
			
		if len(part[0]) > 0:
			nounPhrases = self.tagger.getTextNounStatements(self.tagger.tagText(part[0]))
			if len(nounPhrases) > 0:
				return nounPhrases[0]
		else:
			return None
		
	def __getLastCandidate(self, text):
		if len(text) > 0:
			nounPhrases = self.tagger.getTextNounStatements(self.tagger.tagText(text))
			if len(nounPhrases)>0:
				return nounPhrases[len(nounPhrases)-1]
		
		return None
		
	def __log(self, chain):
		print time.ctime() + ": " + chain
		
if __name__ == "__main__":
	
	if len(sys.argv) < 2:
		print 'Too few parameters:'
		print '		python annotator.py [web_to_annotate]'
		print 'Ex.-	python annotator.py http://en.wikipedia.org/wiki/Shelbyville_%28The_Simpsons%29'

		sys.exit()

	annotator = Annotator()
	annotatedPage = annotator.startProcess(sys.argv[1])

	#fileName = sys.argv[1].split("/")
	#file = open("./annotated-" + fileName[len(fileName)-1].split(".")[0] + ".html","w")
	#file.write(annotatedPage)
	#file.close()
	
	
	sys.exit()

