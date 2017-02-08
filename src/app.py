from __future__ import print_function
import tensorflow as tf
from flask import Flask, render_template, request, send_file
from tensorflow.examples.tutorials.mnist import input_data
import random
import numpy as np
import json
import network_json
import test_vars
import sys

mnist = input_data.read_data_sets('resource/MNIST_data', one_hot=True)

def get_image_brightness(image):
    total_brightness = 0
    for i in range(len(image)):
        total_brightness += image[i]
    return total_brightness / len(image)

def get_feature_json(features): # takes in contents of different layers in CNN e.g. conv1 or pool2
    feature_list = []
    feature_brightness = []
    for i in range(len(features)):
        feature_data = {}
        feature_data['feature_' + str(i)] = to_rgba(features[i].tolist())
        feature_brightness.append(get_image_brightness(features[i].flatten()))
        feature_list.append(feature_data)
    feature_list.append(feature_brightness)
    return feature_list

def to_rgba(images): # takes in the images contained inside a feature
    image_list = []
    for i in range(len(images)):
        for j in range(len(images[i])):
            for k in range(3):
                image_list.append(images[i][j])
            image_list.append(255)
    return image_list

def get_feature_map(layer, image_size, channels):
    temp_image = layer.reshape((image_size, image_size, channels))
    temp_image = temp_image.transpose((2, 0, 1))
    return temp_image.reshape((-1, image_size, image_size, 1))

#features = [x_image, h_conv1, h_pool1, h_conv2, h_pool2, h_pool2_flat, h_fc1, h_fc1_drop, fc_decision_data]\
#               0        1        2         3       4           5         6         7               8

def get_conv_data(feature_list):
    features = {}
    features['1'] = get_feature_json(np.array(np.round(np.multiply(feature_list[0], 255), decimals=0).tolist()))
    features['2'] = get_feature_json(np.round(np.multiply(get_feature_map(feature_list[1], 28, 32), 255), decimals=0))
    features['3'] = get_feature_json(np.round(np.multiply(get_feature_map(feature_list[2], 14, 32), 255), decimals=0))
    features['4'] = get_feature_json(np.round(np.multiply(get_feature_map(feature_list[3], 14, 64), 255), decimals=0))
    features['5'] = get_feature_json(np.round(np.multiply(get_feature_map(feature_list[4], 7, 64), 255), decimals=0))
    features['6'] = get_feature_json(np.array(np.round(np.multiply(feature_list[6], 255), decimals=0).tolist()))

    data = {}
    data['features'] = features
    data['prediction'] = np.argmax(feature_list[8])
    data['certainty'] = np.round(np.multiply(feature_list[8],100.0).squeeze(),decimals=8).tolist()
    return data

x = tf.placeholder("float", [784])

sess = tf.Session()

with tf.variable_scope("conv"):
    graph_variables, features = test_vars.conv(x)
saver = tf.train.Saver(graph_variables)
saver.restore(sess, "pre-trained/mnist/graph/mnist.ckpt")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/conv", methods=['POST'])
def conv():
    index = int(request.form['val'])
    struct = json.loads(request.form['struct'])
    image = mnist.test.images[index]
    label = mnist.test.labels[index]
    data = {}
    data['label'] = np.argmax(label)
    data['convdata'] = get_conv_data(sess.run(features, feed_dict={x:image}))
    data['struct'], data['no_nodes'] = network_json.get_json(struct)
    return json.dumps(data)

if __name__ == "__main__":
    app.run()
