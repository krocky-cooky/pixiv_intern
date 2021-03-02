import tensorflow as tf
from tensorflow.keras import layers as kl
from tensorflow.keras import Model
import numpy as np
import matplotlib.pyplot as plt
from sklearn.utils import shuffle
from PIL import Image
from tqdm import tqdm

import os,sys
sys.path.append(os.path.dirname(__file__))

from models import ResNet



class MnistTrainer(object):
    def __init__(
        self,
        input_shape,
        output_dim,
        patience = 4,
    ):
        self.model = ResNet(
            input_shape = input_shape,
            output_dim = output_dim
        )
        self.criterion = tf.keras.losses.CategoricalCrossentropy()
        self.optimizer = tf.keras.optimizers.SGD(learning_rate = 0.1)
        self.train_loss = tf.keras.metrics.Mean()
        self.train_acc = tf.keras.metrics.CategoricalAccuracy()
        self.val_loss = tf.keras.metrics.Mean()
        self.val_acc = tf.keras.metrics.CategoricalAccuracy()
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
        self.es = {
            'loss': float('inf'),
            'patience': patience,
            'step': 0
        }
        self.save_dir = './logs'
        if not os.path.exists(self.save_dir):
            os.mkdir('logs')

    def train(
        self,
        x_train,
        t_train,
        x_val,
        t_val,
        epochs,
        batch_size,
        early_stopping = False
    ):
        n_batches_train = x_train.shape[0] // batch_size
        n_batches_val = x_val.shape[0] // batch_size

        for epoch in range(epochs):
            x_,t_ = shuffle(x_train,t_train)
            self.train_loss.reset_states()
            self.val_loss.reset_states()
            self.train_acc.reset_states()
            self.val_acc.reset_states()
            
            for batch in tqdm(range(n_batches_train)):
                start = batch * batch_size
                end = start + batch_size
                x_batch = x_[start:end]
                t_batch = t_[start:end]
                self.train_step(x_batch,t_batch)

            for batch in tqdm(range(n_batches_val)):
                start = batch * batch_size
                end = start + batch_size
                x_batch = x_val[start:end]
                t_batch = t_val[start:end]
                self.val_step(x_batch,t_batch)
            
            self.history['train_loss'].append(self.train_loss.result())
            self.history['val_loss'].append(self.val_loss.result())
            self.history['train_acc'].append(self.train_acc.result())
            self.history['val_acc'].append(self.val_acc.result())
            print('epoch {} => train_loss: {},  train_acc: {}, val_loss: {}, val_acc: {}'.format(
                epoch + 1,
                self.train_loss.result(),
                self.train_acc.result(),
                self.val_loss.result(),
                self.val_acc.result()
            ))

            if early_stopping:
                if self.early_stopping(self.val_loss.result()):
                    break

        fig = plt.figure(figsize = (20,20))
        ax1 = fig.add_subplot(2,2,1)
        ax2 = fig.add_subplot(2,2,2)
        ax3 = fig.add_subplot(2,2,3)
        ax4 = fig.add_subplot(2,2,4)
        ax1.plot(self.history['train_loss'])
        ax2.plot(self.history['train_acc'])
        ax3.plot(self.history['val_loss'])
        ax4.plot(self.history['val_acc'])
        ax1.set_title('train_loss')
        ax2.set_title('train_acc')
        ax3.set_title('val_loss')
        ax4.set_title('val_acc')
        plt.show()

    def train_step(self,x,t):
        with tf.GradientTape() as tape:
            preds = self.model(x)
            loss = self.criterion(t,preds)
        grads = tape.gradient(loss,self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(grads,self.model.trainable_variables))
        self.train_loss(loss)
        self.train_acc(t,preds)

    def val_step(self,x,t):
        preds = self.model(x)
        loss = self.criterion(t,preds)
        self.val_loss(loss)
        self.val_acc(t,preds)

    def evaluate(self,x_test,t_test):
        accuracy = tf.metrics.CategoricalAccuracy()
        preds = self.model(x_test)
        loss = self.criterion(preds,t_test)
        accuracy(t_test,preds)
        print('accuracy: {}, loss: {}'.format(
            accuracy.result(),
            loss
        ))
        return (accuracy.result().numpy(),loss.numpy())

    def save(self,name):
        path = self.save_dir +'/' + name
        self.model.save_weights(path)
    
    def load(self,name):
        path = self.save_dir +'/' + name
        self.model.load_weights(path)

    def early_stopping(self,loss):
        if loss > self.es['loss']:
            self.es['step'] += 1
            if self.es['step'] > self.es['patience']:
                print('early stopping')
                self.load('early_stopping_saving')
                return True
        else:
            self.es['loss'] = loss
            self.es['step'] = 0
            self.save('early_stopping_saving')

        return False

    

class Trainer(object):
    def __init__(self):
        self.model = ResNet(
            input_shape = (128,128,3),
            output_dim = 1
        )
        self.criterion = tf.keras.losses.MSE()
        self.optimizer = tf.keras.optimizers.SGD(learning_rate = 0.1)
        self.train_loss = tf.keras.metrics.Mean()
        self.val_loss = tf.keras.metrics.Mean()
        self.history = {
            'train_loss': [],
            'val_loss': []
        }
    

    def train(
        self,
        x_train,
        t_train,
        x_val,
        t_val,
        epochs,
        batch_size,
        image_path
    ):
        n_batches_train = x_train.shape[0] // batch_size
        n_batches_val = x_val.shape[0] // batch_size

        for epoch in range(epochs):
            x_,t_ = shuffle(x_train,t_train)
            self.train_loss.reset_states()
            self.val_loss.reset_states()
            
            for batch in tqdm(range(n_batches_train)):
                start = batch * batch_size
                end = start + batch_size
                x_batch = x_[start:end]
                t_batch = t_[start:end]
                img_batch = self.get_image(image_path,x_batch)
                self.train_step(img_batch,t_batch)

            for batch in tqdm(range(n_batches_val)):
                start = batch * batch_size
                end = start + batch_size
                x_batch = x_val[start:end]
                t_batch = t_val[start:end]
                img_batch = self.get_image(image_path,x_batch)
                self.val_step(img_batch,t_batch)
            
            self.history['train_loss'].append(self.train_loss.result())
            self.history['val_loss'].append(self.val_loss.result())

            print('epoch {} => train_loss: {},  test_loss: {}'.format(
                epoch + 1,
                self.train_loss.result(),
                self.val_loss.result()
            ))

        fig = plt.figure(figsize = (20,10))
        ax1 = fig.add_subplot(1,2,1)
        ax2 = fig.add_subplot(1,2,2)
        ax1.plot(self.history['train_loss'])
        ax2.plot(self.history['val_loss'])
        ax1.set_title('train_loss')
        ax2.set_title('val_loss')
        plt.show()



    def get_image(
        image_pah,
        x_batch,
        extension = 'jpg'
    ):
        img_batch = list()
        for id in x_batch:
            image = np.load('./img_npy/' + str(id) + '.npy')
            img_batch.append(image)
            
        return np.array(img_batch)

    def train_step(self,x,t):
        with tf.GradientTape() as tape:
            preds = self.model(x)
            loss = self.criterion(t,preds)
        grads = tape.gradient(loss,model.trainable_variables)
        optimizer.apply_gradient(zip(grads,model.trainable_variables))
        self.train_loss(loss)

    def val_step(self,x,t):
        preds = self.model(x)
        loss = self.criterion(t,preds)
        self.val_loss(loss)

    def evaluate(self,x_test,t_test,batch_size = 1000):
        loss = tf.metrics.Mean()
        n_batches = x_test.shape[0] // batch_size
        for batch in range(n_batches):
            start = batch_size * batch
            end = start + batch_size
            x_batch = x_test[start:end]
            t_batch = t_test[start:end]
            img_batch = self.get_image(x_batch)
            loss(self.criterion(t_batch,self.model(img_batch)))

        start = batch_size * n_batches
        end = x_test.shape[0]
        x_batch = x_test[start:end]
        t_batch = t_test[start:end]
        img_batch = self.get_image(x_batch)
        loss(self.criterion(t_batch,self.model(img_batch)))
        print(loss.result().numpy())
        return loss.result().numpy()




