# VisdomObserver
A sacred `RunObserver` which uses `visdom` to plot logged metrics and image artifacts. Supports creation
of dynamically updating plots with different sets of metrics easily.


# Installation
Install using pip:  
`pip install visdom-observer`

OR

First, clone this repository using  
`git clone https://github.com/rajatvd/VisdomObserver/`

Then, `cd` into the `package` directory and run the following command:  
`pip install .`

# Usage
Simply add an instance of this observer to a `sacred` Experiment object. Make sure to have a visdom server running while the experiment is running. Open up visdom in the browser and view the environment created for the particular run. All scalars logged using `ex.log_scalar` will be recorded. Create dynamic metric plots easily using the GUI pane in visdom.

A detailed example is shown in the `example_experiment.ipynb` notebook. Run this script to see the observer in action:  
`python rendevous_control.py -b 0.1`

# Todo

- [ ] Allow the create plot GUI to work after a run completes, and for previously completed runs.
- [ ] Create plots vs timestamp and not just vs step.
