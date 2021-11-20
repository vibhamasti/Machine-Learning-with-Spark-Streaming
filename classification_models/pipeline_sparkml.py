from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from pyspark.ml.feature import NGram, VectorAssembler
from pyspark.ml.feature import StringIndexer, ChiSqSelector

from sklearn import linear_model
from sklearn.feature_extraction.text import CountVectorizer

# Custom function for partial fitting of C
def partial_fit(self, batch_data):
    if(hasattr(vectorizer , 'vocabulary_')):
        new_vocab = self.vocabulary_
    else:
        new_vocab = {}
    self.fit(batch_data)
    new_vocab = list(set(new_vocab.keys()).union(set(self.vocabulary_ )))
    self.vocabulary_ = {new_vocab[i] : i for i in range(len(new_vocab))}

# Apply custom function for class
CountVectorizer.partial_fit = partial_fit


def custom_model_pipeline(df, inputCols = ["tweet", "sentiment"], n=3):
    
    # Feature transformers: Tokenizer, NGrams, CountVectorizer, IDF, VectorAssembler
    
    # Converts the input string to lowercase, splits by white spaces
    tokenizer = Tokenizer(inputCol="tweet", outputCol="words")
    df = tokenizer.transform(df)								# Needs no saving
    df.head()
    
    # Create three cols for each transformer
    for i in range(1, n+1):
		
		# Converts the input string to an array of n-grams (space-separated string of words)
		ngrams = NGram(n=n, inputCol="words", outputCol="{0}_grams".format(i))
		df = ngrams.transform(df)								# Needs no saving

		# Extracts the vocab from the set of tweets in batch - uses saved transformer
		# Requires saving
		cv = CountVectorizer()
		input_to_cv = df.select("{0}_grams".format(i))
		cv.partial_fit(input_to_cv)
		output_col = cv.transform(input_to_cv)
		df = df.withColumn("{0}_cv".format(i), output_col)
		
	# ------------------------------- Pipeline worked on till CV (to be tested) ----------------------------------------------
		
		# Compute the IDF score given a set of tweets
	    #idf = IDF(inputCol="{0}_cv".format(i), outputCol="{0}_tfidf".format(i), minDocFreq=5)
		#df = cv.transform(idf)

	# Merges multiple columns into a vector column
	#assembler = VectorAssembler(inputCols=["{0}_tfidf".format(i) for i in range(1, n + 1)], outputCol="rawFeatures")
    
    #label_stringIdx = StringIndexer(inputCol = "Sentiment", outputCol = "label")
    
    #selector = ChiSqSelector(numTopFeatures=2**14,featuresCol='rawFeatures', outputCol="features")
    
    
    
def ml_algorithm():
	lr= linear_model.SGDClassifier()
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
