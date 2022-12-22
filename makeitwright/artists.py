__name__ = "artists"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
import WrightTools as wt
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from process.helpers import roi, parse_args
import styles

def plot(data, **kwargs):
    if type(data) is wt.Collection:
        data = [data[key] for key in data]
    if type(data) is not list:
        data = [data]
        
    #set parameters for plotting from kwargs
    params = {
        "plot_type" : "line",
        "xscale" : "linear",
        "xticks" : True,
        "yscale" : "linear",
        "yticks" : True,
        "axis" : 0,
        "channel" : -1,
        "ROI" : None,
        "xrange" : None,
        "vrange" : None,
        "offset" : 0,
        "reference_lines" : None,
        "title" : None
        }
    params.update(styles.spectra)
    params.update(**kwargs)
        
    signed=False
    
    colors = __parse_colors(data, params['colors'])
    
    #setup plot frame
    fig, ax = plt.subplots(figsize=(params['fig_width'], params['fig_height']))
    
    for i in range(len(data)):
        #convert axis/channel indices to natural names
        axis, = parse_args(data[i], params["axis"])
        
        if params['channel']=='prompt': #kill this if else if all your code suddenly stops working
            channel, = parse_args(data[i], input(f'select channel from {data[i].natural_name}: {[ch.natural_name  for ch in data[i].channels]} '),  dtype='Channel')
        else:    
            channel, = parse_args(data[i], params["channel"],  dtype='Channel')
        if data[i][channel].signed:
            signed=True
    
        #extract ROI
        if params["ROI"] is not None:
            out = roi(data[i], params["ROI"])
        else:
            out = data[i]
    
        #plot data
        if params["plot_type"] == "line":
            ax.plot(out[axis][:],out[channel][:]+i*params["offset"], 
                    linewidth=params["linewidth"], alpha=params["alpha"], color=colors[i])
        if params["plot_type"] == "scatter":
            ax.scatter(out[axis][:],out[channel][:]+i*params["offset"],
                    marker=params["marker"], alpha=params["alpha"], color=colors[i], s=params["marker_size"])
    
    if signed:
        ax.axhline(y=0, color='black', linewidth=1)
    
    if params["reference_lines"] is not None:
        if type(params["reference_lines"]) is not list:
            params["reference_lines"] = [params["reference_lines"]]
        for reference_line in params["reference_lines"]:
            ax.axvline(x=reference_line, zorder=0, linewidth=1, color='grey', linestyle='--', alpha=0.5)
    
    #adjust plot frame
    if params["xrange"] is not None:
        xrange = params["xrange"]
    else:
        xrange = __get_range(*data, reference_key=params["axis"], dtype='Axis')
    if params["xscale"] == 'log' and xrange[0]<=0:
        xrange[0] = 0.001
    ax.set_xlim(*xrange)
    ax.set_xscale(params["xscale"])
    if params["xlabel"] is None:
        try:
            params["xlabel"] = out[axis].attrs['label']
        except KeyError:
            params["xlabel"] = 'x'
    ax.set_xlabel(params["xlabel"])
    if not params["xticks"]:
        ax.set_xticks([])
    
    if params["vrange"] is not None:
        vrange = params["vrange"]
    else:
        vrange = __get_range(*data, reference_key=params["channel"], offset=params["offset"])
    if params["yscale"] == 'log' and vrange[0]<=0:
        vrange[0] = 0.001
    ax.set_ylim(*vrange)
    ax.set_yscale(params["yscale"])
    if params["ylabel"] is None:
        try:
            params["ylabel"] = out[channel].attrs['label']
        except KeyError:
            params["ylabel"] = 'y'
    ax.set_ylabel(params["ylabel"])
    if not params["yticks"]:
        ax.set_yticks([])
    
    if params["title"] is not None:
        ax.set_title(params["title"])

def plot2D(data, channel, **kwargs):
    
    #convert axis/channel indices to natural names
    channel, = parse_args(data, channel, dtype='Channel')

    #set parameters for plotting from kwargs
    params = {
        "ROI" : None,
        'ticks' : 'auto',
        "vrange" : None,
        "reference_lines" : None,
        "title" : None
        }
    params.update(styles.profile)
    
    if data[channel].signed:
        params["cmap"] = cm.RdBu_r   
    params.update(**kwargs)
    
    if params["ROI"] is not None:
        out = roi(data, params["ROI"])
    else:
        out = data
    
    #determine range to be plotted
    if params["vrange"] is None:
        vrange = __get_range(out, reference_key=channel)
    else:
        vrange = params["vrange"]
    
    #setup plot frame
    fig, ax = plt.subplots(figsize=(params['fig_width'], params['fig_height']))
    
    #plot data
    xgrid, ygrid = np.meshgrid(out.axes[0][:], out.axes[1][:])
    #array needs to be transposed before passing to pcolormesh because apparently no matplotlib devs thought about what arrays look like
    try:
        mesh = ax.pcolormesh(xgrid, ygrid, np.transpose(out[channel][:]), cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    except TypeError:
        mesh = ax.pcolormesh(xgrid, ygrid, out[channel][:], cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    ax.set_xlabel(params["xlabel"])
    ax.set_ylabel(params["ylabel"])
    if params["title"] is not None:
        ax.set_title(params["title"])
    
    if params["reference_lines"] is not None:
        if type(params["reference_lines"]) is not list:
            params["reference_lines"] = [params["reference_lines"]]
        for reference_line in params["reference_lines"]:
            ax.axvline(x=reference_line, linewidth=1, color='grey', linestyle='--', alpha=0.25)
    
    #set ticks
    if params['ticks'] == 'auto':
        ticks = np.linspace(vrange[0], vrange[1], num=11)
    elif params['ticks'] is None:
        ticks = []
    else:
        ticks = params['ticks']
    
    # plot colorbar
    cbar = plt.colorbar(mesh)
    cbar.set_ticks(ticks)
    cbar.set_label(params["cbar_label"])

def plot3D(data, profile_axis, channel, **kwargs):
    
    #convert axis/channel indices to natural names
    profile_axis, = parse_args(data, profile_axis)
    spectral_axis = data.axes[-1].natural_name
    channel, = parse_args(data, channel, dtype='Channel')
    non_profile_axis = [axis.natural_name for axis in data.axes[:-1] if axis.natural_name != profile_axis][0]

    #set parameters for plotting from kwargs
    params = {
        "ROI" : None,
        'ticks' : 'auto',
        "vrange" : None,
        "reference_lines" : None,
        "title" : None
        }
    params.update(styles.profile)
    if data[channel].signed:
        params["cmap"] = cm.RdBu_r
    params.update(**kwargs)
    
    #extract ROI
    if params["ROI"] is not None:
        out = roi(data, params["ROI"])
        if len(out.axes) != 2:
            out = roi(out, {non_profile_axis : 'sum'})
    else:
        out = roi(data, {non_profile_axis : 'sum'})
    out.transform(spectral_axis, profile_axis)

    #determine range to be plotted
    if params["vrange"] is None:
        vrange = __get_range(out, reference_key=channel)
    else:
        vrange = params["vrange"]
    
    #setup plot frame
    fig, ax = plt.subplots(figsize=(params['fig_width'], params['fig_height']))
    
    #plot data
    xgrid, ygrid = np.meshgrid(out.axes[1][:], out.axes[0][:])
    try:
        mesh = ax.pcolormesh(xgrid, ygrid, np.transpose(out[channel][:]), cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    except TypeError:
        mesh = ax.pcolormesh(xgrid, ygrid, out[channel][:], cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    ax.set_xlabel(params["xlabel"])
    ax.set_ylabel(params["ylabel"])
    
    if params["reference_lines"] is not None:
        if type(params["reference_lines"]) is not list:
            params["reference_lines"] = [params["reference_lines"]]
        for reference_line in params["reference_lines"]:
            ax.axvline(x=reference_line, linewidth=1, color='grey', linestyle='--', alpha=0.25)
    
    #set ticks
    if params['ticks'] == 'auto':
        ticks = np.linspace(vrange[0], vrange[1], num=11)
    elif params['ticks'] is None:
        ticks = []
    else:
        ticks = params['ticks']
    
    # plot colorbar
    cbar = plt.colorbar(mesh)
    cbar.set_ticks(ticks)
    cbar.set_label(params["cbar_label"])
    
    if params["title"] is not None:
        ax.set_title(params["title"])

def image(data, channel, **kwargs):
    #convert axis/channel indices to natural names
    channel, = parse_args(data, channel, dtype='Channel') 

    #set parameters for plotting from kwargs
    params = {
        "ROI" : None,
        "vrange" : None,
        "reference_lines" : None,
        "title" : None
        }
    params.update(styles.image)
    if data[channel].signed:
        params["cmap"] = cm.RdBu_r
    params.update(**kwargs)
    
    #extract ROI
    if params["ROI"] is not None:
        out = roi(data, params["ROI"])
    else:
        out = data
    
    #determine range to be plotted
    if params["vrange"] is None:
        vrange = __get_range(out, reference_key=channel)
    else:
        vrange = params["vrange"]
    
    #setup plot frame
    fig, ax = plt.subplots(figsize=(params['fig_width'], params['fig_height']))
    
    #plot data
    xgrid, ygrid = np.meshgrid(out.axes[0][:], out.axes[1][:])
    ax.pcolormesh(xgrid, ygrid, np.transpose(out[channel][:]), cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    
    if params["reference_lines"] is not None:
        if type(params["reference_lines"]) is not list:
            params["reference_lines"] = [params["reference_lines"]]
        for reference_line in params["reference_lines"]:
            ax.axvline(x=reference_line, linewidth=1, color='grey', linestyle='--', alpha=0.25)
    
    ax.set_xlabel(params["xlabel"])
    ax.set_ylabel(params["ylabel"])
    ax.set_aspect("equal")
    if params["title"] is not None:
        ax.set_title(params["title"])

def image3D(data, channel, **kwargs):
    
    #convert axis/channel indices to natural names
    channel, = parse_args(data, channel, dtype='Channel')
    non_spatial_axis = data.axes[-1].natural_name

    #set parameters for plotting from kwargs
    params = {                            
        "ROI" : None,
        'ticks' : 'auto',
        "vrange" : None,
        "title" : None
        }
    params.update(styles.image)
    if data[channel].signed:
        params["cmap"] = cm.RdBu_r
    params.update(**kwargs)
    
    #extract ROI
    if params["ROI"] is not None:
        out = roi(data, params["ROI"])
        if len(out.axes) != 2:
            out = roi(out, {non_spatial_axis : 'sum'})
    else:
        out = roi(data, {non_spatial_axis : 'sum'})
    
    #determine range to be plotted
    if params["vrange"] is None:
        vrange = __get_range(out, reference_key=channel)
    else:
        vrange = params["vrange"]
    
    #setup plot frame
    fig, ax = plt.subplots(figsize=(params['fig_width'], params['fig_height']))
    
    #plot data
    xgrid, ygrid = np.meshgrid(out.axes[0][:], out.axes[1][:])
    mesh = ax.pcolormesh(xgrid, ygrid, np.transpose(out[channel][:]), cmap=params["cmap"], vmin=vrange[0], vmax=vrange[1])
    ax.set_xlabel(params["xlabel"])
    ax.set_ylabel(params["ylabel"])
    ax.set_aspect("equal")
    if params["title"] is not None:
        ax.set_title(params["title"])
    
    #set ticks
    if params['ticks'] == 'auto':
        ticks = np.linspace(vrange[0], vrange[1], num=11)
    elif params['ticks'] is None:
        ticks = []
    else:
        ticks = params['ticks']
    
    # plot colorbar
    cbar = plt.colorbar(mesh)
    cbar.set_ticks(ticks)
    cbar.set_label(params["cbar_label"])
        
def plot_tandem(d1,d2, figsize=(2.6,1), axis=0, channels=(-1,-1), 
                xticks=True, yticks=[True,True], xlabel="wavelength (nm)", ylabels=["reflectance","absorbance"], 
                xrange=[400,650], vranges=[(0,1),(0,1)], colors=['coral','royalblue'], 
                linewidth=1, reference_lines=None):
    #setup plot frame
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()

    #convert axis/channel indices to natural names
    axis1, = parse_args(d1, axis)
    axis2, = parse_args(d2, axis)
    channel1, = parse_args(d1, channels[0],  dtype='Channel')
    channel2, = parse_args(d2, channels[1],  dtype='Channel')
    
    #plot data
    ax1.plot(d1[axis1][:],d1[channel1][:], linewidth=linewidth, color=colors[0])
    ax2.plot(d2[axis1][:],d2[channel2][:], linewidth=linewidth, color=colors[1])
    
    if reference_lines is not None:
        if type(reference_lines) is not list:
            reference_lines = [reference_lines]
        for line in reference_lines:
            ax1.axvline(x=line, zorder=0, linewidth=1, color='grey', linestyle='--', alpha=0.5)
    
    #adjust plot frame
    if xrange is None:
        xrange = __get_range(*[d1,d2], reference_key=axis, dtype='Axis')
    ax1.set_xlim(*xrange)
    ax1.set_xlabel(xlabel)
    if not xticks:
        ax1.set_xticks([])
    
    for i, v in enumerate(vranges):
        if v is None:
            if i==0:
                vranges[i] = __get_range(d1, reference_key=channel1, offset=0)
            if i==1:
                vranges[i] = __get_range(d2, reference_key=channel2, offset=0)
    ax1.set_ylim(*vranges[0])
    ax2.set_ylim(*vranges[1])
    ax1.set_ylabel(ylabels[0])
    ax2.set_ylabel(ylabels[1])
    if not yticks[0]:
        ax1.set_yticks([])
    if not yticks[1]:
        ax2.set_yticks([])

def __parse_colors(data, colors):
    if type(colors) is list:
        if len(colors) < len(data):
            q, r = divmod(len(data), len(colors))
            colors = q*colors+colors[:r]
    else: 
        try:
            colors = colors(np.linspace(0,1,len(data)))
        except:
            colors = [colors for i in range(len(data))]
    return colors

def __get_range(*data, reference_key=0, dtype='Channel', window='default', offset=0):
    ranges = []
    signed=False
    default_windows = {
        'Axis' : 1,
        'Channel' : 1.1
        }
    if window=='default':
        window = default_windows[dtype]
    
    for d in data:   
        key, = parse_args(d, reference_key, dtype=dtype)
        ranges.append([np.min(d[key][:]), np.max(d[key][:])])
        if dtype=='Channel':
            if d[key].signed:
                signed=True
    
    ranges_min, ranges_max = min([r[0] for r in ranges]), max([r[1] for r in ranges])
    if offset != 0:
        ranges_max = sum([r[0] for r in ranges]) + offset*(len(data)-1) + [r[1] for r in ranges][-1]
    
    rng = [(ranges_min+(ranges_max-ranges_min)/2)-(window*(ranges_max-ranges_min)/2), (ranges_min+(ranges_max-ranges_min)/2)+(window*(ranges_max-ranges_min)/2)]
    if signed and ranges_min*ranges_max < 0 and not offset: #make window symmetric about zero if min and max have opposite sign
        return [-window*max(rng),window*max(rng)]
    else:
        return rng

def __contrast(d, ch, contrast=[99,1]):
    return [np.percentile(d[ch][:],min(contrast)),np.percentile(d[ch][:],max(contrast))]