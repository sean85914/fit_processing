import re, fitparse, json, argparse, os
import numpy as np
from datetime import datetime, timezone
from matplotlib import pyplot as plt

# timestamp, altitude, heart_rate, speed, cadence, position_lat, position_long, temperature 

def annotate_extremum(x, y, ax, _min=False):
    '''Annotate extremum values.'''
    xmax = x[np.nanargmax(y)]
    ymax = np.nanmax(y)
    text= "y={:.0f}".format(ymax)
    kw = {'color': 'r', 'size': 'large'}
    ax.annotate(text, xy=(xmax, ymax), xytext=(xmax, ymax), **kw)
    ax.scatter(xmax, ymax, c='r', s=5)
    if _min:
        xmin = x[np.nanargmin(y)]
        ymin = np.nanmin(y)
        text= "y={:.0f}".format(ymin)
        kw['color'] = 'b'
        ax.annotate(text, xy=(xmin, ymin), xytext=(xmin, ymin), **kw)
        ax.scatter(xmin, ymin, c='r', s=5)
        
def plot_mean(x, y, ax, remove_zero=False):
    '''Plot horizontal line at average.'''
    if remove_zero:
        y_ = np.copy(y).astype(float)
        y_[y_==0] = np.nan
        mean = np.nanmean(y_)
    else:
        mean = np.nanmean(y)
    ax.hlines(mean, x[0], x[-1], 'k', 'dashed')
    ax.text(x[-1], mean, 'Average: {:.0f}'.format(mean))

def process(files_name, outDir):
    '''Process given FIT file and plot figures.
    
    Parameters:
        files_name (str): files' name to process
    '''
    data = {
        'timestamp': [], 
        'altitude': [], # m
        'heart_rate': [], # bpm
        'speed': [], # km/hr
        'cadence': [], # rpm
        'position_lat': [], # degree
        'position_long': [], # degree
        'temperature': [] # C
    }
    
    for file_name in files_name:
        fitfile = fitparse.FitFile(file_name)
        msgs = fitfile.messages
    
        for msg in msgs:
            data_types = set()
            for _data in msg.as_dict()['fields']:
                data_types.add(_data['name'])
            if len(set(data.keys()) - set(data_types)) != 0:
                continue
            for _data in msg:
                if _data.name not in list(data.keys()):
                    continue
                # convert unit
                if _data.name == 'speed' and _data.units == 'm/s':
                    data[_data.name].append(_data.value*3.6 if _data.value else 0)
                # ref: https://www.gps-forums.com/threads/explanation-sought-concerning-gps-semicircles.1072/
                elif _data.name in ['position_lat', 'position_long'] and _data.units == 'semicircles':
                    data[_data.name].append(_data.value*180/2**31)
                elif _data.name == 'timestamp':
                    data[_data.name].append(_data.value.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%Y-%m-%dT%H:%M:%S'))
                else:
                    data[_data.name].append(_data.value if _data.value is not None else float('nan'))
    
    # plot figures
    dt = [datetime.strptime(t, '%Y-%m-%dT%H:%M:%S') for t in data['timestamp']]
    fig, axes = plt.subplots(5, 1, figsize=(24, 12))
    # altitude
    axes[0].plot(dt, data['altitude'])
    axes[0].set_title('Altitude (m)')
    axes[0].get_xaxis().set_ticks([])
    # heart rate
    axes[1].plot(dt, data['heart_rate'])
    axes[1].set_title('Heart Rate (bpm)')
    axes[1].get_xaxis().set_ticks([])
    annotate_extremum(dt, data['heart_rate'], axes[1])
    plot_mean(dt, data['heart_rate'], axes[1])
    # speed
    axes[2].plot(dt, data['speed'])
    axes[2].set_title('Speed (km/hr)')
    axes[2].get_xaxis().set_ticks([])
    annotate_extremum(dt, data['speed'], axes[2])
    plot_mean(dt, data['speed'], axes[2])
    # cadence
    axes[3].plot(dt, data['cadence'])
    axes[3].set_title('Cadence (rpm)')
    axes[3].get_xaxis().set_ticks([])
    annotate_extremum(dt, data['cadence'], axes[3])
    plot_mean(dt, data['cadence'], axes[3], remove_zero=True)
    # temperature
    axes[4].plot(dt, data['temperature'])
    axes[4].set_title('Temperature (C)')
    annotate_extremum(dt, data['temperature'], axes[4], _min=True)
    plot_mean(dt, data['temperature'], axes[4])
    fig.savefig(os.path.join(outDir, 'summary.png'))
    
    # Map plot
    fig, ax = plt.subplots()
    ax.plot(data['position_long'], data['position_lat'])
    ax.set_title('GPS Trajectory')
    fig.savefig(os.path.join(outDir, 'map.png'))
    
    data['meta'] = files_name
    # save JSON
    with open(os.path.join(outDir, 'summary.json'), 'w') as f:
        json.dump(data, f, indent = 4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=str, help='Files to process', nargs='+')
    parser.add_argument('--outDir', type=str, default='', help='Output directory')
    args, _ = parser.parse_known_args()
    
    process(args.files, args.outDir)