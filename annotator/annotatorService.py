# -*- coding: utf-8 -*-

import nltk, re, pprint, live, configuration, annotator
from SimpleXMLRPCServer import SimpleXMLRPCServer

# Create server
server = SimpleXMLRPCServer((configuration.ANNOTATION_SERVICE_URL, configuration.ANNOTATION_SERVICE_PORT))
server.register_introspection_functions()

# Register an instance; all the methods of the instance are 
# published as XML-RPC methods.
server.register_instance(annotator.Annotator())
print "Annotation service - Ready"
# Run the server's main loop
server.serve_forever()