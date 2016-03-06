import xmlrpclib
import os.path
import re
import time

# Class which asks via XML-RPC to the Java OWL server which classes it has in the specified OWL file. 
# It stores the classes in a dictionary in the following format: classes[local_name] = full_name
#
# author: Jose Miguel Millan Rosa - iTAKA-URV
# date  : 14-01-08

class OntologyReader:

	def __init__(self, server):
		self.server = xmlrpclib.ServerProxy(server)
		self.classes={}
		
	#Private Method: sets the ontology URL
	def __setOntologyURL(self, param1):
		self.OntologyURL = param1
		self.URLSet=True

		return self.OntologyURL

	#Private Method: sets the ontology file path
	def __setOntologyFilePath(self, param1):
		if os.path.isfile(param1):
			if os.path.isabs(param1):
				self.OntologyPath=param1
			else:
				self.OntologyPath=os.path.abspath(param1)

			self.pathSet=True;
		else:
			raise IOError, "The path is not a file"
			
		return self.OntologyPath

	#sets the set of ontology names using a file path			
	def getOntologyClassesByPath(self,Path):
		self.__setOntologyFilePath(Path)
		if self.pathSet:
			self.classes={}
			classes = self.server.SemanticServiceProvider.getClassesFromPath(self.OntologyPath)
			
			pattern = re.split(" ",classes)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				self.classes[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]
	
		else:
			raise IOError, "URL is not properly written"

	#sets the set of ontology names using an URL	
	def getOntologyClassesByURL(self,URL):
		self.__setOntologyURL(URL)
		if self.URLSet:
			self.classes={}
			classes = self.server.SemanticServiceProvider.getClassesFromURL(self.OntologyURL)
			#Here I should separate the result using regular expressions. The URL are separated by blank spaces
			pattern = re.split(" ",classes)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				self.classes[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]

		else:
			raise IOError, "Path not defined properly"

	def getOntologyClassDescendantsByURL(self,URL,className):
		superclasses={}
		tempClasses={}
		
		self.__setOntologyURL(URL)
		if self.URLSet:
			print time.ctime() +": " + self.OntologyURL + " " + className
			tempClasses = self.server.SemanticServiceProvider.getClassDescendantsFromURL(self.OntologyURL, className)
			#Here I should separate the result using regular expressions. The URL are separated by blank spaces
			pattern = re.split(" ",tempClasses)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				superclasses[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]
			return superclasses
		else:
			raise IOError, "URL not defined properly"

	def getOntologyClassDescendantsByPath(self,path,className):
		superclasses={}
		tempClasses={}
			
		self.__setOntologyFilePath(Path)
		
		if self.PathSet:
			tempClasses = self.server.SemanticServiceProvider.getClassDescendantsFromPath(self.OntologyPath, className)
			#Here I should separate the result using regular expressions. The URL are separated by blank spaces
			pattern = re.split(" ",	tempClasses)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				superclasses[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]
			return superclasses
		else:
			raise IOError, "URL not defined properly"

	

	def getOntologyClassAncestorsByURL(self,URL,className):
		superclasses={}
		tempClasses={}
		
		self.__setOntologyURL(URL)
		if self.URLSet:
			print time.ctime() +": "+  self.OntologyURL + " " + className
			tempClasses = self.server.SemanticServiceProvider.getClassAncestorsFromURL(self.OntologyURL, className)
			#Here I should separate the result using regular expressions. The URL are separated by blank spaces
			pattern = re.split(" ",tempClasses)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				superclasses[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]
			return superclasses
		else:
			raise IOError, "URL not defined properly"

	def getOntologyClassAncestorsByPath(self,path,className):
		superclasses={}
		tempClasses={}
			
		self.__setOntologyFilePath(Path)
		
		if self.PathSet:
			tempClasses = self.server.SemanticServiceProvider.getClassAncestorsFromPath(self.OntologyPath, className)
			#Here I should separate the result using regular expressions. The URL are separated by blank spaces
			pattern = re.split(" ",	tempClasses)
			for i in range(len(pattern)-2): #Control the range
				secondPattern = re.split('(\W+)', pattern[i]) 
				localName = secondPattern[len(secondPattern)-3] #get the class localname
				superclasses[localName] = pattern[i] 
			#Using a dictionary, put the different elements ordered by {localname, fullname}
			#for className in self.classes.keys():
			#	print "Class name: " + className +  " complete class name:" + self.classes[className]
			return superclasses
		else:
			raise IOError, "URL not defined properly"

	
	#returns the set of ontology names		
	def getOntologyNames(self):
		if len(self.classes) > 0:
			return self.classes
		else:
			raise StandardError, "No classes stored"	
			

