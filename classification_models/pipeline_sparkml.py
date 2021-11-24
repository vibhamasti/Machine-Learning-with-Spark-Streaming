'''
MLSS: Machine Learning with Spark Streaming
Dataset: Tweet Sentiment Analysis
Submission by: Team BD_078_460_474_565
Course: Big Data, Fall 2021
'''

from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import NGram, VectorAssembler
from pyspark.ml.feature import StringIndexer, ChiSqSelector

from pyspark.sql.types import *
from pyspark.ml.linalg import Vectors, DenseVector

from sklearn import linear_model
from sklearn.feature_extraction.text import CountVectorizer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator



# Custom function for partial fitting of CV
def partial_fit(self, batch_data):

	if(hasattr(self, 'vocabulary_')):
		old_vocab = self.vocabulary_
	else:
		old_vocab = {}

	self.fit(batch_data)

	new_vocab = list(set(old_vocab.keys()).union(set(self.vocabulary_ )))
	self.vocabulary_ = {new_vocab[i] : i for i in range(len(new_vocab))}
	
	return self

CountVectorizer.partial_fit = partial_fit


def custom_model_pipeline(df, spark, inputCols = ["tweet", "sentiment"], n=3):
	
	input_str = 'tokens_noStop'
	
	input_col = df.select(input_str).collect()
	input_str_arr = [row[input_str] for row in input_col]
	input_arr = [str(a) for a in input_str_arr]
	
	vectorizer = CountVectorizer(lowercase=True, analyzer = 'word', stop_words='english', ngram_range=(1,2))
	vectorizer.partial_fit(input_arr)
	output_arr = vectorizer.transform(input_arr)
	output_arr = output_arr.toarray()
	
	#return output_arr
	#df.printSchema()
	
	output_col = list(map(lambda x: [x[0], x[1].tolist()], zip(input_str_arr, output_arr)))
	
	
	schema = StructType([
		StructField('tokens_noStop_copy', ArrayType(StringType())),
		StructField('count_vectors', ArrayType(IntegerType()))
	])
	
	dff = spark.createDataFrame(data=output_col, schema=schema)
	#dff.printSchema()
	#dff.show()
	

	df = df.join(dff, dff.tokens_noStop_copy == df.tokens_noStop, 'inner')
	df = df.drop('tokens_noStop_copy')
	

	#df.show()
	return df

	'''
	# Create three cols for each transformer
	for i in range(1, n+1):
		
		
		# Converts the input string to an array of n-grams (space-separated string of words)
		ngrams = NGram(n=i, inputCol="words", outputCol="{0}_grams".format(i))
		df = ngrams.transform(df)								# Needs no saving
		df.show()
		
		# Extracts the vocab from the set of tweets in batch - uses saved transformer
		# Requires saving
		vectorizer = CountVectorizer()
		input_str = "{0}_grams".format(i)
		output_str = "{0}_cv".format(i)
		
		input_arr = df.select(input_str).collect()
		cv_in_arr = [str(row[input_str]) for row in input_arr]
		vectorizer.partial_fit(cv_in_arr)
		output_col = vectorizer.transform(cv_in_arr)
#		print(*list(zip(vectorizer.get_feature_names(), output_col.sum(0).getA1())))
		output_col = DenseVector(output_col.toarray())
		print(output_col)
		#schema = StructType([StructField(output_str, DenseVector(), False)])
		output_df = spark.createDataFrame(data=output_col)
		output_df.show()
		#df = df.withColumn(output_str, output_df)
		#df.show()
		
	'''
	# ------------------------------ Pipeline worked on till CV (to be tested) ----------------------------------------------
		
		# Compute the IDF score given a set of tweets
		#idf = IDF(inputCol="{0}_cv".format(i), outputCol="{0}_tfidf".format(i), minDocFreq=5)
		#df = cv.transform(idf)

	# Merges multiple columns into a vector column
	#assembler = VectorAssembler(inputCols=["{0}_tfidf".format(i) for i in range(1, n + 1)], outputCol="rawFeatures")
	
	#label_stringIdx = StringIndexer(inputCol = "Sentiment", outputCol = "label")
	
	#selector = ChiSqSelector(numTopFeatures=2**14,featuresCol='rawFeatures', outputCol="features")
	
	
	
def get_model():
	lr = linear_model.SGDClassifier()
	return lr

	
	
#To run (?)
'''
pipeline = model_pipeline()
model = pipeline.fit(train_set)
predictions = model.transform(val_set)
accuracy = predictions.filter(predictions.label == predictions.prediction).count() / float(val_set.count())

evaluator = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction")

roc_auc = evaluator.evaluate(predictions)
# print accuracy, roc_auc
print ("Accuracy Score: {0:.4f}".format(accuracy))
print ("ROC-AUC: {0:.4f}".format(roc_auc))
'''

#To save and load
'''
pipeline.write().overwrite().save("./path")
pipeline = Pipeline.load("./path")
'''
