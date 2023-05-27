import numpy as np
import data_utils as du
from sklearn.utils import shuffle
import matplotlib.pyplot as plt

def calc_accuracy(labels, predicted):
    confronted = (labels == predicted)
    TP = 0
    
    for i in confronted:
        if(i == True):
            TP = TP + 1
    
    return TP/len(predicted)

def k_fold(learners,x,labels,k):
    error_rates = []
    for learner in learners:
        X, Y = shuffle(x.T, labels)
        X = np.array_split(X, k)
        y = np.array_split(Y, k)
        concat_predicted = []
        for i in range(k): #for each fold
            X_train = np.concatenate(np.delete(X, i, axis=0), axis=0).T
            y_train = np.concatenate(np.delete(y, i, axis=0), axis=0)
            X_val = X[i].T
            m,C = learner.fit(X_train, y_train)
            predicted = learner.trasform(X_val,m,C)
            concat_predicted.extend((predicted.tolist()))
        error_rates.append((1-calc_accuracy(Y, np.array(concat_predicted)))*100)
    return error_rates

class confusion_matrix:
    true_labels = []
    predicted_labels = []
    num_classes = 0
    FNR = 0
    FPR = 0
    
    def __init__(self, true_labels, predicted_labels):
        self.true_labels = true_labels
        self.predicted_labels = predicted_labels
        self.num_classes = len(np.unique(self.true_labels))
        self.confusion_matrix = np.zeros((self.num_classes, self.num_classes), dtype=int)

    def get_confusion_matrix(self):
        self.num_classes = len(np.unique(self.true_labels))
        joined_classes = np.array([self.true_labels, self.predicted_labels])
        for i in range(len(self.true_labels)):
            col = joined_classes[0][i]
            row = joined_classes[1][i]
            self.confusion_matrix[row][col] += 1
        return self.confusion_matrix
    
    def print_confusion_matrix(self, name):
        fig, ax = plt.subplots()
        
        ax.imshow(self.confusion_matrix, cmap='Blues')
    
        ax.set_xticks(np.arange(self.num_classes))
        ax.set_yticks(np.arange(self.num_classes))
        ax.set_xticklabels(np.arange(0, self.num_classes))
        ax.set_yticklabels(np.arange(0, self.num_classes))
        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')
        
        for i in range(self.num_classes):
            for j in range(self.num_classes):
                ax.text(j, i, self.confusion_matrix[i, j], ha='center', va='center', color='black')
        
        plt.savefig("Confusion Matrix - {}.png".format(name))
        plt.close()
        
    
    def FNR_FPR_binary(self):
        cm = self.confusion_matrix
        FNR = cm[0][1]/(cm[0][1]+cm[1][1])
        FPR = 1 - FNR
        return (FNR, FPR)
    
    def DCF_binary(self,pi, C):
        FNR, FPR = self.FNR_FPR_binary()
        Cfn = C[0][1]
        Cfp = C[1][0]
        return (pi*Cfn*FNR+(1-pi)*Cfp*FPR)

    def DCF_binary_norm(self,pi, C):
        FNR, FPR = self.FNR_FPR_binary()
        Cfn = C[0][1]
        Cfp = C[1][0]
        return (pi*Cfn*FNR+(1-pi)*Cfp*FPR)/np.min([pi*Cfn, (1-pi)*Cfp])

def FNR_FPR_binary_ind(confusion_matrix):
    cm = confusion_matrix
    FNR = cm[0][1]/(cm[0][1]+cm[1][1])
    FPR = cm[1][0]/(cm[0][0]+cm[1][0])
    return (FNR, FPR)

def DCF_binary_norm_ind(cm, pi,C):
    FNR = cm[0][1]/(cm[0][1]+cm[1][1])
    FPR = cm[1][0]/(cm[0][0]+cm[1][0])
    Cfn = C[0][1]
    Cfp = C[1][0]
    return (pi*Cfn*FNR+(1-pi)*Cfp*FPR)/np.min([pi*Cfn, (1-pi)*Cfp])
    
def min_DCF(scores, true_labels, pi, C):
    sorted_scores = sorted(scores)
    min_dcf = np.inf
    best_threshold = None
    for t in sorted_scores:
        predicted_labels = np.where(scores>t,1,0)
        cnf_mat = confusion_matrix(true_labels, predicted_labels, False)
        cm = cnf_mat.get_confusion_matrix()
        dcf = DCF_binary_norm_ind(cm,pi, C)
        if dcf < min_dcf:
            min_dcf = dcf
            best_threshold = t
    return min_dcf, best_threshold

def DCF(scores, true_labels, pi, C):
    Cfn = C[0][1]
    Cfp = C[1][0]
    t = - np.log((pi*Cfn)/(1-pi)*Cfp)
    predicted_labels = np.where(scores>t,1,0)
    cnf_mat = confusion_matrix(true_labels, predicted_labels, False)
    cm = cnf_mat.get_confusion_matrix()
    FNR, FPR = FNR_FPR_binary_ind(cm)
    return (pi*Cfn*FNR+(1-pi)*Cfp*FPR)/np.min([pi*Cfn, (1-pi)*Cfp]) 

def get_ROC(scores, true_labels, pi, C, name):
    sorted_scores = sorted(scores)
    FPR_list = []
    TPR_list = []
    for t in sorted_scores:
        predicted_labels = np.where(scores>t,1,0)
        cnf_mat = confusion_matrix(true_labels, predicted_labels, False)
        cm = cnf_mat.get_confusion_matrix()
        FNR, FPR = FNR_FPR_binary_ind(cm)
        TPR = 1 - FNR
        FPR_list.append(FPR)
        TPR_list.append(TPR)
    
    plt.plot(FPR_list, TPR_list, linestyle='-')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.grid(True)
    plt.savefig("ROC - {}.png".format(name))
    plt.close()
        
def get_error_plot(scores, true_labels, C,name):
    effPriorLogOdds = np.linspace(-3,3,21)
    pi = 1/(1+np.exp(-effPriorLogOdds))
    dcf = []
    min_dcf = []
    for p in pi:
        min_dcf.append(min_DCF(scores, true_labels, p, C))
        dcf.append(DCF(scores,true_labels, p, C))   
        
    plt.plot(effPriorLogOdds, dcf, label='min DCF', color='r')
    plt.plot(effPriorLogOdds, min_dcf, label='min DCF', color='b')
    plt.ylim([0, 1.1])
    plt.xlim([-3, 3])
    plt.ylabel('DCF value')
    plt.xlabel('prior log-odds')
    plt.savefig("error plot - {}.png".format(name))
    plt.close()
        

def binary_threshold(pi, C):
    Cfn = C[0][1]
    Cfp = C[1][0]
    t = - np.log((pi*Cfn)/(1-pi)*Cfp)
    return t