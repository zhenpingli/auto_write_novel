# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 16:00:39 2019

@author: lizhenping
this file is come from the tutorial from hanxiaoyang and the tensorflow tutorial
https://blog.csdn.net/han_xiaoyang/article/details/51253274
https://www.tensorflow.org/tutorials/text/text_generation
代码源自谷歌TensorFlow官方例子和寒小阳的例子改编，稍后将会给出完全使用numpy写的lstm的例子。非常推荐新手从新写一遍lstm

"""
import numpy as np
import itertools
import nltk 
import csv 
import jieba
from nltk.probability import FreqDist
import tensorflow as tf 
import os 
tf.enable_eager_execution()

tf.device('/device:GPU:0')
vocabulary_size = 9000
unknown_token = "UNKNOWN_TOKEN"
sentence_start_token = "START"
sentence_end_token = "END"

# 读取数据，添加SENTENCE_START和SENTENCE_END在开头和结尾
print("Reading CSV file...")
with open('four1.txt', 'r') as f:
    line = f.readlines()
   
    # 分句
    input_sentences = [nltk.sent_tokenize(x.lower()) for x in line]
    sentences = itertools.chain(*[nltk.sent_tokenize(x.lower()) for x in line])
    # 添加SENTENCE_START和SENTENCE_END
    sentences = ["%s %s %s" % (sentence_start_token, x, sentence_end_token) for x in sentences]
print ("Parsed %d sentences." % (len(sentences)))


input_sentences = [jieba.lcut("".join(sent)) for sent in input_sentences]

tokenized_sentences = [jieba.lcut("".join(sent)) for sent in sentences]

tokenized_sentences= itertools.chain(*tokenized_sentences)
tokenized_sentences= list(tokenized_sentences)

# 统计词频
word_freq = FreqDist(tokenized_sentences)
tops=word_freq.most_common(50)
print ("Found %d unique words tokens." % len(word_freq.items()))



# 取出高频词构建词到位置，和位置到词的索引
vocab = word_freq.most_common(vocabulary_size)
index_to_word = [x[0] for x in vocab]
index_to_word.append(unknown_token)
word_to_index = dict([(w,i) for i,w in enumerate(index_to_word)])





print ("Using vocabulary size %d." % vocabulary_size)
print ("The least frequent word in our vocabulary is '%s' and appeared %d times." % (vocab[-1][0], vocab[-1][1]))




# 把所有词表外的词都标记为unknown_token
for i, sent in enumerate(input_sentences):
    print(sent)
    print(i)

    
    input_sentences[i] = [w if w in word_to_index else unknown_token for w in sent]
    print(input_sentences[i])

print ("\nExample sentence: '%s'" % sentences[0])
print ("\nExample sentence after Pre-processing: '%s'" % input_sentences[0])


# 构建完整训练集
X_train = np.asarray([[word_to_index[w] for w in sent[:-1]] for sent in input_sentences])

y_train = np.asarray([[word_to_index[w] for w in sent[1:]] for sent in input_sentences])

max_len = max((len(l) for l in X_train))

X_train = list(map(lambda l:l + [0]*(max_len - len(l)), X_train))

x_train=[]
for line in X_train:
    for number in line:
        x_train.append(number)
examples_per_epoch = len(x_train)//max_len    
x_train = np.array(x_train)  


char_dataset = tf.data.Dataset.from_tensor_slices(x_train)


  
sequences = char_dataset.batch(max_len, drop_remainder=True)

for item in sequences.take(3):
  print(repr(item.numpy()))
'''  
index_to_word
a = [index_to_word[x] for x in x_train]  
 '''
    
def split_input_target(chunk):
    input_text = chunk[:-1]
    print("++++++++++++++++++++++++")
    print(input_text)
    print(repr(input_text))
    print("++++++++++++++++++++++++")
    target_text = chunk[1:]
    return input_text, target_text

dataset = sequences.map(split_input_target)
'''
iterator = dataset.make_one_shot_iterator()
one_element = iterator.get_next()
'''   
BATCH_SIZE = 2
steps_per_epoch = examples_per_epoch//BATCH_SIZE

# Buffer size to shuffle the dataset
# (TF data is designed to work with possibly infinite sequences,
# so it doesn't attempt to shuffle the entire sequence in memory. Instead,
# it maintains a buffer in which it shuffles elements).
#BUFFER_SIZE = 10000

dataset = dataset.batch(BATCH_SIZE, drop_remainder=True)
'''
iterator = dataset.make_one_shot_iterator()
one_element = iterator.get_next()
'''

vocab_size = len(vocab)+1

# The embedding dimension
embedding_dim = 256

# Number of RNN units
rnn_units = 1024
    

if tf.test.is_gpu_available():
  rnn = tf.keras.layers.CuDNNGRU
else:
  import functools
  rnn = functools.partial(
    tf.keras.layers.GRU, recurrent_activation='sigmoid')
  
    
def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
  model = tf.keras.Sequential([
    tf.keras.layers.Embedding(vocab_size, embedding_dim,
                              batch_input_shape=[batch_size, None]),
    rnn(rnn_units,
        return_sequences=True,
        recurrent_initializer='glorot_uniform',
        stateful=True),
    tf.keras.layers.Dense(vocab_size)
  ])
  return model

model = build_model(
  vocab_size = len(vocab)+1,
  embedding_dim=embedding_dim,
  rnn_units=rnn_units,
  batch_size=BATCH_SIZE) 
model.summary()


iterator = dataset.make_one_shot_iterator()
one_element = iterator.get_next()
######################################
for input_example_batch,target_example_batch in dataset.take(3):
   
    print("ssssssssss")
    
    example_batch_predictions = model(input_example_batch)
    print(example_batch_predictions.shape,"#(batch_size,sequence_length,vocab_size)")


sampled_indices = tf.random.categorical(example_batch_predictions[0],num_samples=1)
sampled_indices = tf.squeeze(sampled_indices,axis = -1).numpy()




######################
def loss(labels, logits):
    return tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)

example_batch_loss  = loss(target_example_batch, example_batch_predictions)
print("prediction shape :" , example_batch_predictions.shape,"#(batch_size,sequence_length,vocab_size")
print("scalar_loss:      ", example_batch_loss.numpy().mean())


##################################

model.compile(
        optimizer = tf.train.AdamOptimizer(),
        loss = loss)


##########################



# Directory where the checkpoints will be saved
checkpoint_dir = './training_checkpoints'
# Name of the checkpoint files
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

checkpoint_callback=tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_prefix,
    save_weights_only=True)
########################


#################################
EPOCHS=20
history = model.fit(dataset.repeat(), epochs=EPOCHS, steps_per_epoch=steps_per_epoch, callbacks=[checkpoint_callback])
################################# 

tf.train.latest_checkpoint(checkpoint_dir)

model = build_model(vocab_size, embedding_dim, rnn_units, batch_size=1)

model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))

model.build(tf.TensorShape([1, None]))

model.summary()


def generate_text(model, start_string):
  # Evaluation step (generating text using the learned model)

  # Number of characters to generate
  num_generate = 10

  # Converting our start string to numbers (vectorizing)
  input_eval = [word_to_index[start_string]]
  print(input_eval)
  input_eval = tf.expand_dims(input_eval, 0)

  # Empty string to store our results
  text_generated = []

  # Low temperatures results in more predictable text.
  # Higher temperatures results in more surprising text.
  # Experiment to find the best setting.
  temperature = 1.0

  # Here batch size == 1
  model.reset_states()
  for i in range(num_generate):
      print(input_eval)
      predictions = model(input_eval)
      # remove the batch dimension
      predictions = tf.squeeze(predictions, 0)

      # using a multinomial distribution to predict the word returned by the model
      predictions = predictions / temperature
      predicted_id = tf.multinomial(predictions, num_samples=1)[-1,0].numpy()

      # We pass the predicted word as the next input to the model
      # along with the previous hidden state
      input_eval = tf.expand_dims([predicted_id], 0)

      text_generated.append([index_to_word[predicted_id]])
      

  return (start_string + ''.join('%s' %id for id in text_generated))

print(generate_text(model, start_string=u"郭敬明"))