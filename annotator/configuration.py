#tagging service configuration
ANNOTATION_SERVICE_PORT=8081
ANNOTATION_SERVICE_URL="localhost"

#annotation service configuration
TAG_SERVICE_PORT=8082
TAG_SERVICE_URL="localhost"

#Detection of Noun Phrases parameters
MATCHING_PERCENTAGE = 0.7
NUMBER_OF_RESULTS_FOR_RELEVANCE = 50
NUMBER_OF_MATCHINGS = 5
SIMILARITY_THRESHOLD = 0.3

#Ontology service configuration
ONTOLOGY_SERVICE_URL = "http://localhost:8080/semantic_services"
ONTOLOGY_NAME = "film_reduced.owl"

#logging files
QUERY_LOG = "./query.log"