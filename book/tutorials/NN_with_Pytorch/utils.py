import numpy as np
import matplotlib.pyplot as plt

def Sigmoid(z):
    """
    A function that performs the sigmoid transformation
    
    Arguments:
    ---------
        -* z: array/list of numbers to activate
    
    Returns:
    --------
        -* logistic: the transformed/activated version of the array
    """
    logistic = 1 / (1 + np.exp(-z))
    return logistic
    

def Tanh(z):
    """
    A function that performs the hyperbolic tangent transformation
    
    Arguments:
    ---------
        -* z: array/list of numbers to activate
    
    Returns:
    --------
        -* hyp: the transformed/activated version of the array
    """
    hyp = np.tanh(z)
    return hyp


def ReLu(z):
    """
    A function that performs the rectified linear unit transformation
    
    Arguments:
    ---------
        -* z: array/list of numbers to activate
    
    Returns:
    --------
        -* points: the transformed/activated version of the array
    """
    points = np.where(z < 0, 0, z)
    return points

def plot_activations():
    """
    A function to plot the Sigmoid, Tanh, and ReLU activation functions.
    """
    z = np.linspace(-10, 10, 100)
    fa = plt.figure(figsize=(16, 5))

    # Plot Sigmoid
    plt.subplot(1, 3, 1)
    plt.plot(z, Sigmoid(z), color="red", label=r'$\frac{1}{1 + e^{-z}}$')
    plt.grid(True, which='both')
    plt.xlabel('z')
    plt.ylabel('g(z)', fontsize=15)
    plt.title("Sigmoid Activation Function")
    plt.legend(loc='best', fontsize=22)

    # Plot Tanh
    plt.subplot(1, 3, 2)
    plt.plot(z, Tanh(z), color="red", label=r'$\tanh (z)$')
    plt.grid(True, which='both')
    plt.xlabel('z')
    plt.ylabel('g(z)', fontsize=15)
    plt.title("Hyperbolic Tangent Activation Function")
    plt.legend(loc='best', fontsize=18)

    # Plot ReLU
    plt.subplot(1, 3, 3)
    plt.plot(z, ReLu(z), color="red", label=r'$\max(0,z)$')
    plt.grid(True, which='both')
    plt.xlabel('z')
    plt.ylabel('g(z)', fontsize=15)
    plt.title("Rectified Linear Unit Activation Function")
    plt.legend(loc='best', fontsize=18)

    plt.tight_layout()

    plt.show()

