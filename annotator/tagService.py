# -*- coding: utf-8 -*-

import nltk, re, pprint, live, configuration, time
from SimpleXMLRPCServer import SimpleXMLRPCServer

# Create server
server = SimpleXMLRPCServer((configuration.TAG_SERVICE_URL, configuration.TAG_SERVICE_PORT))
server.register_introspection_functions()

# Register an instance; all the methods of the instance are 
# published as XML-RPC methods.
class TextAnalyzer:
	def __init__(self):
		self.tagger = self.trainTagger()


	def getTextNounStatements(self, taggedTokens):
		#grammar to detect chuncks in text
		grammar = r"""
			NOUNP: {<NNP|NN|NNS>+}
			UNINP: {<DT|DTI|DTS|DTX|PP\$>?<JJ|JJ-TL|JJR|JJT|JJS>?<NOUNP>}
			NP : {<UNINP>?<UNINP><UNINP>?}
			"""
		taggedWords = []
		for tag in taggedTokens:
			taggedWords.append(nltk.tag.str2tuple(tag))
			
		cp = nltk.RegexpParser(grammar)
		textChunks = str(cp.parse(taggedWords))

		#Now extract the NP from the whole text
		pattern = re.compile("\(NP.*\)")
		iterator = pattern.finditer (textChunks)
		
		eventually = []
		#clean the ones without NNPs
		for result in iterator:
			temp = textChunks[result.start():result.end()].split()
			phrase = textChunks[result.start():result.end()].replace("(NOUNP ","").replace("(UNINP ","").strip()
			phrase = phrase.replace("(NP ", " ")
			phrase = phrase.replace(")", "")
			phrase = phrase.replace("(", "")
			phrase = phrase.replace("\"","")	
			try:
				eventually.index(phrase)
			except:
				eventually.append(phrase)
				
		self.__log("Retrieving "+ str(len(eventually)) + " Noun Statements without querying any web search engine")
		
		return eventually
		
	def getTextNounPhrases(self, taggedTokens):
		#grammar to detect chuncks in text
		grammar = r"""
			NOUNP: {<NN|NNS>*<NNP>+<NN|NNS>*}
			UNINP: {<DT|DTI|DTS|DTX|PP\$>?<JJ|JJ-TL|JJR|JJT|JJS>?<NOUNP>}
			NP : {<UNINP>?<UNINP><UNINP>?}
			"""
		taggedWords = []
		for tag in taggedTokens:
			taggedWords.append(nltk.tag.str2tuple(tag))
			
		cp = nltk.RegexpParser(grammar)
		textChunks = str(cp.parse(taggedWords))
		
		#Now extract the NP from the whole text
		pattern = re.compile("\(NP.*\)")
		iterator = pattern.finditer (textChunks)
		
		eventually = []
		#clean the ones without NNPs
		for result in iterator:
			temp = textChunks[result.start():result.end()].split()
			for temp2 in temp:
				if temp2.find("/NNP") == -1 and temp2.find("/NN") == -1:
					Named = False
				else:
					Named = True
			
			if Named:
				phrase = textChunks[result.start():result.end()].replace("(NOUNP ","").replace("(UNINP ","").strip()
				try:
					eventually.index(phrase)
				except:
					eventually.append(phrase)
		
		#using WordNet, the non-relevant phrases are discarded
		candidates = self.__discardNonRelevantNPs(eventually)
		#evaluate with google the ones which are NounPhrases
		self.__log("Detected " + str(len(candidates)) + " possible Noun-Phrases from " + str(len(eventually)) + " candidates")
		
		NPs = self.__searchReliableNounPhrases(candidates)
		return NPs

	def trainTagger(self):
		self.__log( "Training the Tagger")
		patterns = 	[ 
			(r'[A-Z].*$','NNP'), # proper noun
			(r'.*ing$', 'VBG'), # gerunds 
			(r'.*ed$', 'VBD'), # simple past 
			(r'.*es$', 'VBZ'), # 3rd singular present 
			(r'.*ould$', 'MD'), # modals 
			(r'.*\'s$', 'NN$'), # possessive nouns 
			(r'.*s$', 'NNS'), # plural nouns 
			(r'.*al$', 'JJ'), # gerunds 
			(r'^-?[0-9]+(.[0-9]+)?$', 'CD'), # cardinal numbers 
			(r'[0-9]*((\.|,)[0-9]*)*$', 'CD'), # cardinal numbers 
			(r'\(', '('),
			(r'\)', ')'),
			(r'\]', ']'),
			(r'\[', '['),
			(r',', ','),
			(r'--', '--'),
			(r'-', '-'),
			(r'\.|\||\?|!|;|:|¬∑|‚Ä¢', '.'),
			(r':', ':'),
			(r'.*', 'NN') # nouns (default) 
			]

		brown = nltk.corpus.brown.tagged_sents()
	
		regexp_tagger = nltk.RegexpTagger(patterns)
		unigram_tagger = nltk.UnigramTagger(brown, backoff=regexp_tagger)
		bigram_tagger = nltk.BigramTagger(brown, backoff=unigram_tagger)
		
		print "Tagger trained"
		#self.__log("Calculating precision")
		#self.__log("Tagger precision: " + str(nltk.tag.accuracy(bigram_tagger, brown)*100))
		
		return bigram_tagger
		
	def tagText(self, text):
		tokens = text.split()
		taggedTokens = self.tagger.tag(tokens)
		result = []
		for tagged in taggedTokens:
			result.append(tagged[0]+"/"+tagged[1])
			
		return result

	def __discardNonRelevantNPs(self, candidates):
		goodCandidates = []
		stemmer = nltk.WordnetStemmer()
		discarded = 0
		self.__log( "Discarding non-relevant NPs")
		
		for candidate in candidates:
			candidate = candidate.replace("(NP ", " ")
			candidate = candidate.replace(")", "")
			candidate = candidate.replace("(", "")
			candidate = candidate.replace("\"","")	

			temp = candidate.split()
			tokens = candidate.split()
			text=""
			nnp=""
			
			#get the text with only Nouns
			for token in tokens:
				parts = token.partition("/")
				if parts[2]=="NN" or parts[2]=="NNP":
					if parts[0] != "." and parts[0] != ",":
						text+=parts[0] + " "
			
				if parts[2] == "NNP":
					if parts[0] != "." and parts[0] != ",":
						nnp+=parts[0] + " "
				
			#get the last name
			text = text.strip()
			nnp = nnp.strip()
			
			#Try to find the Proper Nouns in WordNet
			
			if self.__searchInWN(text) == False:
				tokens = nnp.partition(" ")
				for token in tokens:
					if self.__searchInWN(token) == False:
						goodCandidates.append(candidate)
						self.__log("appending: " + candidate)
						break
					else:
						discarded += 1
		self.__log(str(discarded) + " elements have been discarded")
		
		return goodCandidates
	
	#searches a chain of text into WN, if it's not there, returns false, else returns true
	def __searchInWN(self, chain):
		try:
			#look for the token in wordnet, if we found it, we should discard it except if it is an instance
			result = nltk.wordnet.N[chain]
			for synset in result.synsets(): 
				for relation in synset.relations():		
					if relation.find("instance") != -1:
						return False
		except KeyError, k:
			try:
				nltk.wordnet.ADJ[chain]
				return True
			except KeyError, j:
				try:
					nltk.wordnet.ADV[chain]
					return True
				except KeyError, l:
					try:
						nltk.wordnet.V[chain]
						return True
					except KeyError, m:
						return False
		except:
			return True
			
	def __searchReliableNounPhrases(self, candidates):
		candidatesEvaluated = []

		for candidate in candidates:
			#get the text from the candidates
			text = ""
			nounPhrase = []

			candidate = candidate.replace("(NP ", " ")
			candidate = candidate.replace(")", "")
			candidate = candidate.replace("(", "")
			candidate = candidate.replace("\"","")	

			temp = candidate.split()

			for temp2 in temp:
				nounPhrase.append(temp2)

			for element in nounPhrase:
				chunck = ""
				chuncks = element.split("/")
				
				if len(chuncks) > 2:
					for i in range(len(chuncks)-1):
						chunck += chuncks[i] + "/"
				else:
					chunck = chuncks[0]
					
				text += (chunck + " ")
			
			text = text.strip().partition(",")[0].partition(".")[0]
			#ask google about what we have
			#print "		: %s" % text

			query = live.LiveQuery("\""+text+"\"")
			self.__log(text + " has " + str (query.getNumberResults()) + " results")
			
			dictionary = {	'textTagged' : candidate, \
				      	'text' : text, \
				      	'matchings' : float(query.getMatchingResults(text)) , \
				      	'matchingPercentage' : query.getMatchingPercentage(text), \
				      	'results' : float(query.getNumberResults()), \
				      	'candidates' : [], \
					'is_a' : ""}
					
			candidatesEvaluated.append(dictionary)
			
		return candidatesEvaluated
	
	def __log (self, chain):
		print time.ctime() + ": " + chain
		
server.register_instance(TextAnalyzer())
print time.ctime() + ": Tagging service - Ready"
# Run the server's main loop
server.serve_forever()