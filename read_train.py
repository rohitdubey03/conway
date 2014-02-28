import numpy as np
import csv
from sklearn import svm
from sklearn.linear_model import SGDClassifier
from sklearn import cross_validation
import time
from sklearn.externals import joblib
import pdb
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier

def generate_symmetry( data ):
    "generate the symmetry cell pattern"
    # data: n*400 array
    
    n,m = data.shape
    data_symm = np.zeros([5*n, m], dtype=int)

    for l in range(n):
    
        for k in range(400):
            i = k%20
            j = k/20

            k2 = (19-j) + 20*i
            k3 = (19-i) + 20*(19-j)
            k4 = j      + 20*(19-i)
            k5 = (19-i) + 20*j
            k6 = i      + 20*(19-j)

            data_symm[(l-1)*5,k2]   = data[l,k]
            data_symm[(l-1)*5+1,k3] = data[l,k]
            data_symm[(l-1)*5+2,k4] = data[l,k]
            data_symm[(l-1)*5+3,k5] = data[l,k]
            data_symm[(l-1)*5+4,k6] = data[l,k]

    return data_symm


def get_delta_neighbor( cell_num, delta ):
    "get the list of delta-neighboring cells"

    i_cell = cell_num%20
    j_cell = cell_num/20

    neighbor_indices = []

    nei_range = delta*2+1

    for i in range(nei_range):
        for j in range(nei_range):
            i_nei = i_cell-delta+i
            j_nei = j_cell-delta+j
            
            if (-1<i_nei<20) & (-1<j_nei<20):
                neighbor_indices.append(i_nei*20+j_nei)
    
    return neighbor_indices


def svm_vectors ( train, target, n_cells,delta ):
    "Get the SVM vectors for each cell"
    clfs = []
    start = time.time()
    for i in range(n_cells):
        print "%dth iteration" %i
        st_svc = time.time()
        clfs.append(SGDClassifier(loss="hinge", penalty="l2"))
        # clfs.append(svm.SVC())
        # clfs.append(KNeighborsClassifier())
        # clfs.append(AdaBoostClassifier(n_estimators=100))
        # clfs.append(RandomForestClassifier(n_estimators=40,n_jobs=4, criterion="entropy"))
        clfs[i].fit(train[:,get_delta_neighbor(i,delta)], target[:,i])
        # pdb.set_trace()
        ed_svc = time.time()
        print "done, time: %f" %(ed_svc-st_svc)        
    end = time.time()

    print "ellapsed time = ", end - start

    return clfs

def svm_predict (clfs, data_test, n_cells, delta ):
    "Predict the values for each cell"
    n_train, _ = data_test.shape
    data_predict = np.zeros([n_cells, n_train])

    for i in range(n_cells):
        print "%dth iteration" %i
        st_svc = time.time()
        data_predict[i] = np.array(clfs[i].predict( data_test[:,get_delta_neighbor(i,delta)]) )
        ed_svc = time.time()
        print "done, time: %f" %(ed_svc-st_svc)        

    return data_predict.T


nei_range = 20

# read in  data, parse into training and target sets
print "reading the dataset"
dataset = np.genfromtxt(open('Data/train.csv','r'), delimiter=',', dtype='f8')[1:]
n,m = dataset.shape

# clean up the datasets
print "cleaning up the dataset"
id = np.zeros(n, dtype=int)
delta = np.zeros(n, dtype=int)
data_st = [[] for i in range(5) ]
data_ed = [[] for i in range(5) ]
for i in range(n):
    id[i] = int(dataset[i,0])
    delta[i] = int(dataset[i,1])
    
    data_st[delta[i]-1].append(dataset[i,2:402])
    # data_2, data_3, data_4, data_5, data_6 = generate_symmetry( dataset[i,2:402] )
    # data_st[delta[i]-1].append(data_2)
    # data_st[delta[i]-1].append(data_3)
    # data_st[delta[i]-1].append(data_4)
    # data_st[delta[i]-1].append(data_5)
    # data_st[delta[i]-1].append(data_6)

    data_ed[delta[i]-1].append(dataset[i,402:802])
    # data_2, data_3, data_4, data_5, data_6 = generate_symmetry( dataset[i,402:802] )
    # data_ed[delta[i]-1].append(data_2)
    # data_ed[delta[i]-1].append(data_3)
    # data_ed[delta[i]-1].append(data_4)
    # data_ed[delta[i]-1].append(data_5)
    # data_ed[delta[i]-1].append(data_6)

max_delta = max(delta)
n_cells = 400
max_delta = 1

n_train = np.zeros(max_delta, dtype=int)
n_test = np.zeros(max_delta, dtype=int)
train_st = [[] for i in range(5) ]
train_ed = [[] for i in range(5) ]
test_st = [[] for i in range(5) ]
test_ed = [[] for i in range(5) ]

for i in range(max_delta):
    n_train[i] = int(len(data_st[i])*0.9)
    n_test[i] = int(len(data_st[i]) - n_train[i])

    train_st[i] = np.array(data_st[i][:n_train[i]], dtype=int)
    train_ed[i] = np.array(data_ed[i][:n_train[i]], dtype=int)
    test_st[i] = np.array(data_st[i][n_train[i]:], dtype=int)
    test_ed[i] = np.array(data_ed[i][n_train[i]:], dtype=int)

    # add 5 more symmetrical positions
    train_st[i] = np.concatenate((train_st[i], generate_symmetry(train_st[i])))
    train_ed[i] = np.concatenate((train_ed[i], generate_symmetry(train_ed[i])))

    n_train[i] = int(len(train_st[i]))



# classification functions for [delta][cell#]
clfs = [[] for i in range(max_delta)]
# solve the problem for different levels
for i in range(max_delta):

    # run the svm
    print "runnning the svm for delta = %i" %(i+1)
    clfs[i] =  svm_vectors( train_ed[i], train_st[i], n_cells, i+nei_range)

    # save the clfs
    # print "saving the clfs for delta = %i" %(i+1)
    # joblib.dump(clfs, 'conway_%i.pkl'%i) 

# predicted data for [delta]
data_predict = [[] for i in range(max_delta)]
# predict the values for different levels
for i in range(max_delta):
    print "predicting the values for delta = %i" %(i+1)
    data_predict[i] = svm_predict( clfs[i], test_ed[i], n_cells, i+nei_range)

er = np.zeros(max_delta)
for i in range(max_delta):
    er[i] = sum(sum(abs(test_st[i] - data_predict[i]).T)) / \
        (n_test[i]*n_cells)
    # er[i] = sum((abs(data_st[i][n_train:n_train*2+1,0:n_cells] - data_predict[i])).T)
    # print "error %% = %f" %(sum(er[i])/((n_train+1)*n_cells))

print er




# ## the data sample too big... try smaller sample size.
# cell_data = data_ed[:n_train]
# cell_target = data_st[:n_train,0]

# ## cross validation
# X_train, X_test, y_train, y_test = \
# cross_validation.train_test_split(cell_data, cell_target, \
#                                   test_size=0.4, random_state=0)

# clf = svm.SVC(kernel='linear', C=1)
# cv_scores = cross_validation.cross_val_score(clf, cell_data, cell_target, cv=5)

# print("Accuracy: %0.2f (+/- %0.2f)" % (cv_scores.mean(), cv_scores.std() * 2))


# import visualize_cells
# reload (visualize_cells)

# ds = data_st.reshape([20,20])
# visualize_cells.visualize_cells(ds)
