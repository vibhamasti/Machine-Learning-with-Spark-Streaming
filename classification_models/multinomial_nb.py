'''
MLSS: Machine Learning with Spark Streaming
Dataset: Tweet Sentiment Analysis
Submission by: Team BD_078_460_474_565
Course: Big Data, Fall 2021
'''
import numpy as np

from pyspark.mllib.linalg import Vectors

def MultiNBLearning(df, spark, classifier):
	"""
	Perform online learning of a Multinomial Naive Bayes model with batches of data
	"""
	
	trainingData = df.select("minmax_pca_vectors", "sentiment").collect()
	# OR 
	#trainingData = df.select("hashed_vectors", "sentiment").collect()
	
	X_train = np.array(list(map(lambda row: row.minmax_pca_vectors, trainingData)))
	# OR 
	#X_train = np.array(list(map(lambda row: row.hashed_vectors, trainingData)))
	
	#for y in X_train:
	#	for x in y:
	#		if x < 0:
	#			print(x)

	y_train = np.array(list(map(lambda row: row.sentiment, trainingData)), dtype='int64')

	# Fit the MNB classifier
	classifier.partial_fit(X_train, y_train, classes=np.unique(y_train))

	predictions = classifier.predict(X_train)
	
	accuracy = np.count_nonzero(np.array(predictions) == y_train) / y_train.shape[0]

	print("Accuracy of NB:", accuracy)
	
	return classifier
	
