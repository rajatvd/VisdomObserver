
import visdom
from sacred.observers import RunObserver
import numpy as np
import pprint
import os
import imageio
from torchvision.transforms import ToPILImage, ToTensor

IMAGE_EXTENSIONS = ['.png','.PNG','.svg','.bmp','.jpg','.jpeg']

def metric_dict_to_xy(metric_data_dict, metric_names):
    """Returns the values and steps numpy arrays of the given metric
    names for the metric data dict.
    
    Returns tuple (y, step)"""
    y=[]
    step=[]
    for metric_name in metric_names:
        metric = metric_data_dict[metric_name]
        y.append(metric['values'])
        step.append(metric['steps'])
        
    y = np.array(y).T
    step = np.array(step).T
    return y, step

class MetricWindow():
    """Wraps around a visdom window with line plots for displaying metrics."""
    def __init__(self, vis, metric_data_dict, metric_names_to_plot=None, title=None):
        """
        vis: visdom instance
        metric_data_dict: data for metrics in the following format:
        {
            'metric1':{
                'values':[list of values],
                'steps':[list of steps (x axis values)]
                'timestamps':[list of timestamps]
            }, 
            'metric2':{
                ...
            },
            ...
        }
        
        metric_names_to_plot: list of metric names to plot. 
            Only the names specified in this list are plotted from the data_dict.
            Will throw a key error if a metric in this list is not present in the 
            data_dict.
            
        title: Title of the plot
        
        """
        self.vis = vis
        self.metric_names = metric_names_to_plot or list(metric_data_dict.keys())
        self.title = title
        
#         print(metric_data_dict)
        
        self.opts = dict(
            legend=self.metric_names,
            xlabel='Steps',
            ylabel='Value',
            title=title or 'Metrics'
        )
        
        y, step = metric_dict_to_xy(metric_data_dict, self.metric_names)
        
        self.win = self.vis.line(y, X=step, 
                        opts=self.opts)
        
    def update(self,metric_data_dict):
        """Update the lines in this metric plot with the given data_dict. Appends
        the new data. Note that only the metric names for this window will be plotted,
        so the metric_data_dict can contain other metrics as well, which will be ignored."""
        
        y, step = metric_dict_to_xy(metric_data_dict, self.metric_names)
        
        if len(y)==0:
            return
        
        self.vis.line(y, X=step,
                     opts = self.opts,
                     win=self.win,
                     update='append')

def update_metric_dict(metric_data_dict, new_data):
    """Updates the metric_data_dict with the new_data which is also
    a dict of metrics by names. 
    Assumes new_data.keys is a subset of metric_data_dict.keys"""
     
    for metric_name, metric in new_data.items():
        data = metric_data_dict[metric_name]
        data['values'] += metric['values']
        data['steps'] += metric['steps']
        data['timestamps'] += metric['timestamps']

def plot_create_callback_generator(checkbox_dict, create_metric_plot, log=False):
    """Create a generator whose .send function acts as a callback. Since
    the function is a generator, it is basically a stateful callback. Make
    sure to call next on the generator once before registering the callback.
    
    checkbox_dict: The dictionary in which to maintain states of checkboxes.
        If an unseen checkbox fires this callback, assumes it has been set to true.
    
    Assumes that property id 1 is a text input. Uses this as the title for creating
    plots.
      
    create_metric_plot: The function to call when the element with property id 0 is called.
        Assumes that it is a button meant for creating plots. Passes in the value of the text
        field into this function, assumes that it is used as a title.
    """
    
    event = yield # first next call
    text_field = ''
    
    while True:
        prop_id = event['propertyId']
        item = event['pane_data']['content'][prop_id]
        
        if log:
            pprint.pprint(event)
        
        if prop_id == 1:
            text_field = event['value']
        
        elif prop_id == 0:
            create_metric_plot(text_field)
        
        elif item['type'] == 'checkbox':
            checkbox_dict[item['name']] = not checkbox_dict.get(item['name'], False)
            
       
        # wait for next event
        event = yield

class VisdomObserver(RunObserver):
    """Observes scalar log events and artifact events and dynamically updates metric 
    plots in visdom"""
    def __init__(self):
        
        self.artifact_wins = {}
        self.step_wins = []
            
       
    def started_event(self, ex_info, command, host_info, start_time, config,
                      meta_info, _id):
        
        self.env = ex_info['name']+str(_id)
        self.vis = visdom.Visdom(env=self.env)
        
        # display config
        cfg = pprint.pformat(config, indent=2)
        cfg = cfg.replace('\n','<br>')
        
        self.vis.text(cfg, opts={'title':'Config'})
        
    def completed_event(self, stop_time, result):
        
        self.vis.save([self.env])
        
    def create_metric_plot(self, title):
        """Create a new metric plot with the given title. Only 
        the metrics selected by the checkboxes will be plotted."""
        
        try:
            metric_names = []
            for key, value in self.checkbox_state.items():
                if value: 
                    metric_names.append(key)

    #         print(metric_names)

            if len(metric_names) == 0:
                return

            window = MetricWindow(self.vis, 
                                  self.metric_data_dict,
                                  metric_names_to_plot=metric_names,
                                  title=title)

            self.step_wins.append(window)
        except KeyError as e:
            print(e)
            print("Could not create plot, please try again")
    
    def make_properties_window(self):
        """Create a window which allows creation of metric plots.
        Has a text field for plot title, and checkboxes for each metric
        in the metric_data_dict.
        """
        
        mets = list(self.metric_data_dict.keys())
        checkboxes = [{'type':'checkbox', 'name':met} for met in mets]
        
        create = {
            'type': 'button', 
            'name': 'New metric plot', 
            'value': 'Create'
        }
        
        title_inp = {
            'type':'text',
            'name':'Plot Title'
        }
        
        win = self.vis.properties([create]+[title_inp]+checkboxes)
        
        self.checkbox_state = {}
        
        g = plot_create_callback_generator(self.checkbox_state, self.create_metric_plot)
        next(g)
        handler = g.send
        
        self.vis.clear_event_handlers(win)
        self.vis.register_event_handler(handler, win)
    
    
    
    def log_metrics(self, metrics_by_name, info):
        """
        Update stored metrics and all plots. If this is the first call,
        create a properties window with the metrics. Assumes no new metrics are
        sent in the middle of a run.
        """
        
        if len(metrics_by_name.keys())==0:return
    
        if hasattr(self, 'metric_data_dict'):
            update_metric_dict(self.metric_data_dict, metrics_by_name)
        else:
            self.metric_data_dict = metrics_by_name
            self.make_properties_window()
        
    
        for win in self.step_wins:
            if self.vis.win_exists(win.win):
                win.update(metrics_by_name)
            
        self.vis.save([self.env])
    
    def artifact_event(self, name, filename):
        """If added artifacts are images, plot them."""
        
        fname, ext = os.path.splitext(filename)
#         print(name,filename,fname,ext)
        win = self.artifact_wins.get(filename, None)
        
        if ext in IMAGE_EXTENSIONS:
            self.artifact_wins[filename] = self.vis.image(
                ToTensor()(imageio.imread(filename, pilmode='RGB')),
                opts={'title':name},
                win=win
            )