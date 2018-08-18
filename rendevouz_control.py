
# check if in an interactive environment
IPY = True
try:
    get_ipython()
except:
    IPY = False

from sacred import Experiment
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import ode
from sacred.observers import FileStorageObserver
from visdom_observer import VisdomObserver
import time
import os

ex = Experiment('rendevouz_control', interactive=IPY)
fobs = FileStorageObserver.create('my_runs')
ex.observers.append(fobs)
ex.observers.append(VisdomObserver())

@ex.config
def system_config():
    """System parameters"""
    # 'spring' constants
    K1 = 1
    K2 = 1
    
    # damping constants
    nu1 = -1
    nu2 = -1
    dim = 2

@ex.config
def solver_config():
    """Config for solver"""
    steps = 1000 # steps to solve
    dt = 0.01 # time resolution
    delay = 0.01 # added delay in loop to simulate work
    
    save_fig = True # whether to save a figure showing locations of the bodies
    
    # the configs below only matter is save_fig is True
    save_fig_steps=100 # steps between which to save figure of the bodies
    dpi=50 # dpi of saved figure

@ex.config
def init_value_config():
    """Initial values"""
    v1_init = [-1,0]
    v2_init = [1,0]
    r1_init = [0,1]
    r2_init = [0,-1]

    y_init = np.array([v1_init, 
                    v2_init, 
                    r1_init, 
                    r2_init]).reshape(-1)

@ex.capture
def f(t, y, K1=1, K2=1, nu1=-1, nu2=-1, dim=2):
    """Returns derivative of vector of vars.
    dim*4 variable vector: v1, v2, r1, r2"""
    
    v1, v2, r1, r2 = y.reshape(4,dim)
        
    v1_prime = nu1*v1 + K1*(r2-r1)
    v2_prime = nu2*v2 + K2*(r1-r2)
    r1_prime = v1
    r2_prime = v2
    
    return np.concatenate([v1_prime, 
                        v2_prime, 
                        r1_prime, 
                        r2_prime])

@ex.capture
def run_expt(y_init, dt, steps, dim, delay, save_fig, save_fig_steps, dpi):
    r = ode(f).set_initial_value(y_init)

    fig, ax = plt.subplots(1,1)
    
    plt.close(fig)
    
    t = dt
    y = [y_init]
    for i in range(steps):
        step = r.integrate(t)
        y.append(step)
        t+=dt
        
        v1, v2, r1, r2 = step.reshape(4,dim)
        
        # log metrics
        ex.log_scalar('rel_distance', np.linalg.norm(r1-r2))
        ex.log_scalar('rel_velocity', np.linalg.norm(v1-v2))
        
        arry = np.array(y)
        ax.axis('off')
        ax.scatter(arry[:,dim*2::dim], arry[:,dim*2+1::dim], c=['red', 'blue'])
        
        # save figure
        if save_fig and i%save_fig_steps==0:
            d = fobs.dir or 'figures'
            path = os.path.join(d,'fig.png')
            fig.savefig(path, bbox_inches='tight',dpi=dpi)
            ex.add_artifact(path)
            
        # extra delay to simulate work
        time.sleep(delay)
        
    y = np.array(y)
    
    return y

@ex.automain
def main():
    return run_expt()