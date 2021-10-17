import re, fitparse, json, argparse
from datetime import datetime, timezone
from matplotlib import pyplot as plt

# timestamp, altitude, heart_rate, speed, cadence, position_lat, position_long, temperature 

def process(files_name):
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
                elif _data.name == 'position_lat' and _data.units == 'semicircles':
                    data[_data.name].append(_data.value*180/2**31)
                elif _data.name == 'position_long' and _data.units == 'semicircles':
                    data[_data.name].append(_data.value*180/2**31)
                elif _data.name == 'timestamp':
                    data[_data.name].append(_data.value.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%Y-%m-%dT%H:%M:%S'))
                else:
                    data[_data.name].append(_data.value)
    
    # plot figures
    dt = [datetime.strptime(t, '%Y-%m-%dT%H:%M:%S') for t in data['timestamp']]
    fig, axes = plt.subplots(4, 1, figsize=(24, 12))
    axes[0].plot(dt, data['altitude'], '*')
    axes[0].set_title('Altitude (m)')
    axes[0].get_xaxis().set_ticks([])
    axes[1].plot(dt, data['heart_rate'], '*')
    axes[1].set_title('Heart Rate (bpm)')
    axes[1].get_xaxis().set_ticks([])
    axes[2].plot(dt, data['speed'], '*')
    axes[2].set_title('Speed (km/hr)')
    axes[2].get_xaxis().set_ticks([])
    axes[3].plot(dt, data['cadence'], '*')
    axes[3].set_title('Cadence (rpm)')
    fig.savefig('summary.png')
    
    # save CSV
    with open('summary.json', 'w') as f:
        json.dump(data, f, indent = 4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=str, help='File to parse', nargs='+')
    args, _ = parser.parse_known_args()
    
    process(args.files)