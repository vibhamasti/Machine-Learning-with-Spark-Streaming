'''
MLSS: Machine Learning with Spark Streaming
Dataset: Tweet Sentiment Analysis
Submission by: Team BD_078_460_474_565
Course: Big Data, Fall 2021
'''

'''
 ---------------------------- Import definitions ------------------------------------
'''
import pickle
import json
import importlib

from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.sql import SQLContext, Row, SparkSession
from pyspark.sql.types import *

from sklearn.feature_extraction.text import CountVectorizer, HashingVectorizer
from sklearn.cluster import MiniBatchKMeans
from sklearn.linear_model import SGDClassifier, PassiveAggressiveClassifier
from sklearn.naive_bayes import MultinomialNB

from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import IncrementalPCA

from preprocessing.preprocess import *
from classification_models.logistic_regression import *
from classification_models.multinomial_nb import *
from classification_models.passive_aggressive import *
from clustering_models.kmeans_clustering import *

'''
 ---------------------------- Constant definitions ----------------------------------
'''
# Set constant for the TCP port to send from/listen to
TCP_IP = "localhost"
TCP_PORT = 6100

# Create schema
schema = StructType([
	StructField("sentiment", StringType(), False),
	StructField("tweet", StringType(), False),
])

'''
 ---------------------------- Spark definitions -------------------------------------
'''
# Create a local StreamingContext with two execution threads
sc = SparkContext("local[2]", "Sentiment")
sc.setLogLevel("WARN")
sql_context = SQLContext(sc)
	
spark = SparkSession \
.builder \
.config(conf=SparkConf()) \
.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Batch interval of 5 seconds - TODO: Change according to necessity
ssc = StreamingContext(sc, 5)

'''
 ---------------------------- Model definitions -------------------------------------
'''
# Define the Incremental PCA
pca = IncrementalPCA(n_components=2)

# Define MinMax Scaler
minmaxscaler = MinMaxScaler()

# Define CountVectorizer
CountVectorizer.cv_partial_fit = cv_partial_fit
cv = CountVectorizer(lowercase=True, analyzer = 'word', stop_words='english', ngram_range=(1,2))

# Define HashVectorizer 
hv = HashingVectorizer(n_features=2**16, alternate_sign=False, lowercase=True, analyzer = 'word', stop_words='english', ngram_range=(1,2))

# Define, initialize BatchKMeans Model
num_clusters = 2
kmeans_model = MiniBatchKMeans(n_clusters=num_clusters, init='k-means++', n_init=1, 
							   init_size=1000, batch_size=1000, verbose=False, max_iter=1000)

# Define LR Model
lr_model = SGDClassifier(loss='log')

# Define NB Model
multi_nb_model = MultinomialNB(alpha=1.0, class_prior=None, fit_prior=True)

# Define PA Model
pac_model = PassiveAggressiveClassifier(C = 0.5, random_state = 5)

'''
 ---------------------------- Processing -------------------------------------------
'''
# Process each stream - needs to run ML models
def process(rdd):
	
	global schema, spark, pca, minmaxscaler, cv, hv, \
		   lr_model, multi_nb_model, pac_model, kmeans_model
	
	# ==================Dataframe Creation=======================
	
	# Collect all records
	records = rdd.collect()
	
	# List of dicts
	dicts = [i for j in records 
					 for i in list(json.loads(j).values())]
	
	if len(dicts) == 0:
		return
	
	# Create a DataFrame with each stream	
	df = spark.createDataFrame((Row(**d) for d in dicts), 
								schema)
	# ============================================================
	
	# ==================Data Cleaning + Test======================
	df = df_preprocessing(df)
	print('\nAfter cleaning:\n')
	df.show()
	# ============================================================
	
	# ==================Preprocessing + Test======================
	df = transformers_pipeline(df, spark, pca, minmaxscaler, hv)
	print("\nAfter Preprocessing:\n")
	df.show()
	# ============================================================
	
	# ==================Logistic Regression=======================
	lr_model = LRLearning(df, spark, lr_model)
	
	with open('./trained_models/lr_model.pkl', 'wb') as f:
		pickle.dump(lr_model, f)
	
	# ============================================================
	
	# ==================Multinomial Naive Bayes===================
	multi_nb_model = \
			  MultiNBLearning(df, spark, multi_nb_model)
			  
	with open('./trained_models/multi_nb_model.pkl', 'wb') as f:
		pickle.dump(multi_nb_model, f)		  
	
	# ============================================================

	# =================Passive Aggressive Model===================
	pac_model = PALearning(df, spark, pac_model)
	
	with open('./trained_models/pac_model.pkl', 'wb') as f:
		pickle.dump(pac_model, f)
	
	# ============================================================

	# ===============KMeans Clustering + Test=====================
	with open('./num_iters', "r") as ni:
		num_iters = int(ni.read())
	
	num_iters += 1

	kmeans_model = \
			clustering(df, spark, kmeans_model, num_iters)
	
	with open('./num_iters', "w") as ni:
		ni.write(str(num_iters))
		
	with open('./trained_models/kmeans_model.pkl', 'wb') as f:
		pickle.dump(kmeans_model, f)
	# ============================================================


# Main entry point for all streaming functionality
if __name__ == '__main__':

	if not os.path.isdir('./trained_models'):
		os.mkdir('./trained_models')
		
	# Create a DStream - represents the stream of data received from TCP source/data server
	# Each record in 'lines' is a line of text
	lines = ssc.socketTextStream(TCP_IP, TCP_PORT)

	# TODO: check if split is necessary
	json_str = lines.flatMap(lambda x: x.split('\n'))
	
	file=open("./num_iters","w")
	file.write("0")
	file.close()
	
	# Process each RDD
	lines.foreachRDD(process)

	# Start processing after all the transformations have been setup
	ssc.start()             # Start the computation
	ssc.awaitTermination()  # Wait for the computation to terminate


