import pickle
import time
import tensorflow as tf
from sklearn.model_selection import train_test_split
from alexnet import AlexNet
from sklearn.utils import shuffle

# Load traffic signs data.
with open('./train.p', 'rb') as f:
    data = pickle.load(f)

# Split data into training and validation sets.
X_train, X_val, y_train, y_val = train_test_split(data['features'], data['labels'], test_size=0.33, random_state=0)

# Cut in quarters for laptop training
X_train = X_train[:len(X_train)//4]
y_train = y_train[:len(y_train)//4]
X_val = X_val[:len(X_val)//4]
y_val = y_val[:len(y_val)//4]

# Define placeholders and resize operation.
features = tf.placeholder(tf.float32, (None, 32, 32, 3))
labels = tf.placeholder(tf.int64, None)
resized = tf.image.resize_images(features, (227, 227))

fc7 = AlexNet(resized, feature_extract=True)
# NOTE: `tf.stop_gradient` prevents the gradient from flowing backwards
# past this point, keeping the weights before and up to `fc7` frozen.
# This also makes training faster, less work to do!
fc7 = tf.stop_gradient(fc7)

nb_classes = 43

# Add the final layer for traffic sign classification.
shape = (fc7.get_shape().as_list()[-1], nb_classes)
fc8W = tf.Variable(tf.truncated_normal(shape, stddev=1e-2))
fc8b = tf.Variable(tf.zeros(nb_classes))
logits = tf.nn.xw_plus_b(fc7, fc8W, fc8b)

cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=labels)
loss_op = tf.reduce_mean(cross_entropy)
opt = tf.train.AdamOptimizer()
train_op = opt.minimize(loss_op, var_list=[fc8W, fc8b])
init_op = tf.global_variables_initializer()

preds = tf.arg_max(logits, 1)
accuracy_op = tf.reduce_mean(tf.cast(tf.equal(preds, labels), tf.float32))

epochs = 2
batch_size = 512


def eval_on_data(X, y, sess):
    print("Trying to eval data...")
    print("Total size: ", X.shape[0])
    total_acc = 0
    total_loss = 0
    for offset in range(0, X.shape[0], batch_size):
        end = offset + batch_size
        X_batch = X[offset:end]
        y_batch = y[offset:end]

        loss, acc = sess.run([loss_op, accuracy_op], feed_dict={features: X_batch, labels: y_batch})
        total_loss += (loss * X_batch.shape[0])
        total_acc += (acc * X_batch.shape[0])

    return total_loss / X.shape[0], total_acc / X.shape[0]


with tf.Session() as sess:
    sess.run(init_op)

    for i in range(epochs):
        print("Running for epoch ", i)
        X_train, y_train = shuffle(X_train, y_train)
        t0 = time.time()

        print("Total size: ", X_train.shape[0])
        for offset in range(0, X_train.shape[0], batch_size):
            print("Running a batch...")
            end = offset + batch_size
            sess.run(train_op, feed_dict={features: X_train[offset:end], labels: y_train[offset:end]})

        val_loss, val_acc = eval_on_data(X_val, y_val, sess)
        print("Epoch", i + 1)
        print("Time %.3f seconds" % (time.time() - t0))
        print("Validation Loss = ", val_loss)
        print("Validation Acc = ", val_acc)
        print("")
