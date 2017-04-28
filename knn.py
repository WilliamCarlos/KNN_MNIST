# MNIST handwritten digit recognition - data file loading demo
# Written by William Lee, April 2017 -- Code HEAVILY inspired/taken from Matt Zucker

import numpy as np
import gzip
import struct
import cv2
import pdb

IMAGE_SIZE = 28


######################################################################
# Read a 32-bit int from a file or a stream

def read_int(f):
    buf = f.read(4)
    data = struct.unpack('>i', buf)
    return data[0]


######################################################################
# Open a regular file or a gzipped file to decompress on-the-fly

def open_maybe_gz(filename, mode='rb'):
    if filename.endswith('.gz'):
        return gzip.open(filename, mode)
    else:
        return open(filename, mode)


######################################################################
# Read the MNIST data from an images file or a labels file. The file
# formats are documented at http://yann.lecun.com/exdb/mnist/

def read_mnist(images_file, labels_file):
    images = open_maybe_gz(images_file)

    imagic = read_int(images)
    assert (imagic == 2051)
    icount = read_int(images)
    rows = read_int(images)
    cols = read_int(images)
    assert (rows == IMAGE_SIZE and cols == IMAGE_SIZE)

    print(
    'reading', icount, 'images of', rows, 'rows by', cols, 'cols.')

    labels = open_maybe_gz(labels_file)

    lmagic = read_int(labels)
    assert (lmagic == 2049)
    lcount = read_int(labels)

    print(
    'reading', lcount, 'labels.')

    assert (icount == lcount)

    image_array = np.fromstring(images.read(icount * rows * cols),
                                dtype=np.uint8).reshape((icount, rows, cols))

    label_array = np.fromstring(labels.read(lcount),
                                dtype=np.uint8).reshape((icount))

    return image_array, label_array




# OpenCV has fast matching code, but the Python interface to it
# changes significantly from version to version. This is a reasonably
# fast pure numpy k-nearest-neighbor function that you might find
# helpful for your own code.

#points = search space
#p = center, point to search around
#k = number of neighbors to return
def bruteforce_knn(points, p, k):

    assert(len(p) == points.shape[1])

    diff = points - p
    d = (diff**2).sum(axis=1)
    idx = np.argpartition(d, k)

    idx = idx[:k]
    d = d[idx]

    idx2 = np.argsort(d)
    return idx[idx2], np.sqrt(d[idx2])



######################################################################
# Show use of the MNIST data set:

def main():
    # Read images and labels. This is reading the 10k-element test set
    # (you can also use the other pair of filenames to get the
    # 60k-element training set).
    images, labels = read_mnist('MNIST_data/t10k-images-idx3-ubyte.gz',
                                'MNIST_data/t10k-labels-idx1-ubyte.gz')
    imagesTraining, labelsTraining = read_mnist('MNIST_data/train-images-idx3-ubyte.gz',
                                          'MNIST_data/train-labels-idx1-ubyte.gz')



    # This is a nice way to reshape and rescale the MNIST data
    # (e.g. to feed to PCA, Neural Net, etc.) It converts the data to
    # 32-bit floating point, and then recenters it to be in the [-1,
    # 1] range.
    classifier_input = images.reshape(-1, IMAGE_SIZE * IMAGE_SIZE).astype(np.float32)
    classifier_input = classifier_input * (2.0 / 255.0) - 1.0

    classifier_input_training = imagesTraining.reshape(-1, IMAGE_SIZE * IMAGE_SIZE).astype(np.float32)
    classifier_input_training = classifier_input_training * (2.0 / 255.0) - 1.0

    ##################################################
    # Now just display some stuff:

    print(
    'test images has datatype {}, shape {}, and ranges from {} to {}'.format(
        images.dtype, images.shape, images.min(), images.max()))

    print(
    'test input has datatype {}, shape {}, and ranges from {} to {}'.format(
        classifier_input.dtype, classifier_input.shape,
        classifier_input.min(), classifier_input.max()))

    print(
    'test images has datatype {}, shape {}, and ranges from {} to {}'.format(
        imagesTraining.dtype, imagesTraining.shape, imagesTraining.min(), imagesTraining.max()))

    print(
    'test input has datatype {}, shape {}, and ranges from {} to {}'.format(
        classifier_input_training.dtype, classifier_input_training.shape,
        classifier_input_training.min(), classifier_input_training.max()))



    #print('shape', imagesTraining.shape)

    #will hold 60k images in R^784 format
    points = np.zeros((60000, IMAGE_SIZE*IMAGE_SIZE))
    for i in range(1, 60000):
        #convert 28x28 image to vector in R^784 and add to points
        points[i,:] = imagesTraining[i,:,:].flatten('F') #flatten col order

    #TODO: sphereize our data

    #define A (points), and mean shift them
    avgPoint = points.sum(axis=0)
    avgPoint = avgPoint/60000

    #(meanshifting via matrix tranpose)
    A = np.transpose(points)
    #A = A - np.matlib.repmap(avgPoint, 1, 60000)
    #A = A - np.transpose(np.tile(avgPoint, (60000, 1)))

    for a in range(A.shape[1]):
        A[:,a] = A[:,a] - avgPoint
    A = np.transpose(A)

    # pdb.set_trace()
    #Break up A using SVD
    u, s, v = np.linalg.svd(A, full_matrices=False)
    s = np.diag(s)
    #pdb.set_trace()

    #calculate P as sqrt(m) * V * sigma^-1  * V^T
    P = np.sqrt(60000) * v * np.linalg.inv(s) * np.transpose(v)

    #A' = AP, use A' as our new dataset
    points = np.matmul(A,P)


    #Now, for every point in the test set, conduct knn search and classify as that
    k = 3 #set k for knn
    numCorrect = 0 #used to calculate accuracy
    for i, image in enumerate(images):
        p = images[i,:,:].flatten() #change this so p = flatten(image) #change to test data
        matches, dist = bruteforce_knn(points, p, k)
        #pdb.set_trace()

        #create a voting histogram, which holds the # of votes for each class
        voting = np.zeros(10)
        for j in range(k):
            voting[labelsTraining[matches[j]]] = voting[labelsTraining[matches[j]]] + 1

        #find the classification with the most votes (if tie, take the first appearance)
        max = 0
        for j in range(10):
            if max < voting[j]:
                max = i
        classification = max

        #need to find the max occuring
        # print('the point {} was classified as {}'.format(labels[i], labelsTraining[matches[0]]))
        print('the point {} was classified as {}'.format(labels[i], classification))
        if labels[i]==labelsTraining[matches[0]]:
            numCorrect = numCorrect+1
        print('classification accuracy: {}'.format(float(numCorrect)/(i+1)))

    for i, image in enumerate(imagesTraining):
        displayTraining = cv2.resize(image, (8 * IMAGE_SIZE, 8 * IMAGE_SIZE),
                                     interpolation=cv2.INTER_NEAREST)
        print(
        'image training {} has label {}'.format(i, labelsTraining[i]))
        cv2.imshow('training data', displayTraining)

        while np.uint8(cv2.waitKey(5)).view(np.int8) <0: pass


    for i, image in enumerate(images):
        display = cv2.resize(image, (8 * IMAGE_SIZE, 8 * IMAGE_SIZE),
                             interpolation=cv2.INTER_NEAREST)
        print(
        'image test {} has label {}'.format(i, labels[i]))
        cv2.imshow('test data', display)

        while np.uint8(cv2.waitKey(5)).view(np.int8) < 0: pass




######################################################################

if __name__ == '__main__':
    main()
