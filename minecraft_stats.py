#!/usr/bin/env python3
# coding: utf-8

# # Minecraft Stats
# 
# This notebook summarize minecraft stats files across all worlds saved on the local machine. PathLib is used - configure pathlib to work with your operating system.
# 
# The first code cell (immediately below) builds the 

# In[1]:


import pandas as pd
import re
from pathlib import Path
import gzip
import hvplot.pandas
from bokeh.resources import INLINE
import panel as pn
import holoviews as hv

pn.extension(sizing_mode = 'stretch_width')
hv.extension("bokeh")


local_user = 'culley'
# OSX path
path = Path('/Users/{user}/Library/Application Support/minecraft/saves/'.format(user=local_user))
stats_files = list(path.rglob("*/stats/*.json"))
nbtfiles = list(path.rglob("*/level.dat"))


def minecraft_key(key_name):
    return 'minecraft:{key}'.format(key=key_name)

def merge_data_frames(df, df2, df_name):
    return pd.merge(
        df,
        pd.DataFrame({'minecraft_key':df2.keys(), df_name: df2.values()}),
        how="left",
        left_on="minecraft_key",
        right_on="minecraft_key"
    )

def world_stats(path):
    df = pd.read_json(path)
    stats = df['stats']
    try:
        broken = stats[minecraft_key('broken')]
    except KeyError:
        broken = {}
    try:
        crafted = stats[minecraft_key('crafted')]
    except KeyError:
        crafted = {}
    try:
        custom = stats[minecraft_key('custom')]
    except KeyError:
        custom = {}       
    try:
        dropped = stats[minecraft_key('dropped')]
    except KeyError:
        dropped = {}
    try:
        killed = stats[minecraft_key('killed')]
    except KeyError:
        killed = {}
    try:
        mined = stats[minecraft_key('mined')]
    except KeyError:
        mined = {}
    try:
        picked_up = stats[minecraft_key('picked_up')]
    except KeyError:
        picked_up = {}
    try:
        used = stats[minecraft_key('used')]
    except KeyError:
        used = {}

    df = pd.DataFrame()
    # create unique list of keys from all dictionaries
    df['minecraft_key'] = list(set(broken.keys()) | 
                          set(crafted.keys()) | 
                          set(custom.keys()) | 
                          set(dropped.keys()) | 
                          set(killed.keys()) | 
                          set(mined.keys()) | 
                          set(picked_up.keys()) | 
                          set(used.keys()))
    df = merge_data_frames(df, broken, 'broken')
    df = merge_data_frames(df, crafted, 'crafted')
    df = merge_data_frames(df, custom, 'custom')
    df = merge_data_frames(df, dropped, 'dropped')
    df = merge_data_frames(df, killed, 'killed')
    df = merge_data_frames(df, mined, 'mined')
    df = merge_data_frames(df, picked_up, 'picked_up')
    df = merge_data_frames(df, used, 'used')
    # remove minecraft: prefix
    df['minecraft_key'] =  [re.sub(r'minecraft:','', str(x)) for x in df['minecraft_key']]
    df['world_name'] = path.parts[7]
    df['wood_type'] = df['minecraft_key'].str.extract(r'(dark_oak|birch|oak|acacia|spruce|jungle|mangrove)')
    #df.set_index('minecraft_key')
    df = df.fillna(0)
    df = df.astype({'broken': 'int','broken': 'int','crafted': 'int','custom': 'int','dropped': 'int','killed': 'int','mined': 'int','picked_up': 'int','used': 'int'})
    return df

minecraft_stats = pd.DataFrame()
for file_name in stats_files:
    try:
        minecraft_stats = pd.concat([minecraft_stats, world_stats(file_name)])
    except ValueError:
        print('Value Error:  ', file_name.as_uri())
    except KeyError:
        print('Key Error:  ', file_name.as_uri())



# In[2]:


pn.extension()


woods = minecraft_stats.groupby('wood_type').sum()
woods['id'] = woods.index
woods = woods.drop(woods.index[0])
woods_long_format = pd.melt(woods, id_vars=['id'], value_vars=['crafted', 'mined', 'picked_up', 'used'])
woods_long_format['variable'] = woods_long_format['variable'].replace('picked_up', 'picked up')
woods_long_format['id'] = woods_long_format['id'].replace('dark_oak', 'dark oak')
wood_type_plot = woods_long_format.hvplot.bar('id', 'value', 
                             by='variable', 
                             legend='top_left', 
                             height=500, 
                             width=1000,
                             ylabel='Total',
                             xlabel='Wood Type Statistics',
                             rot=60, 
                             cmap='Category20',
                             title='Wood Type Summary for {cnt} Saved Worlds'.format(cnt=minecraft_stats['world_name'].nunique()))


wood_type_plot_description = pn.pane.Markdown("""

This plot looks at all stat entries for the various minecraft wood types. For example, 
mining an oak trapdoor is included in the "mined" tally.

""", width=1000)

wood_type_plot



# In[3]:


#hvplot.help('bar', generic=False, docstring=False)
#hvplot.help('scatter', generic=False, style=False)

path = Path('/Users/{user}/Library/Application Support/minecraft/logs/'.format(user=local_user))
files = list(path.rglob("*.log.gz"))
minecraft_log = pd.DataFrame( columns=['log_date', 'log_source', 'log_entry'])
minecraft_log['log_date'] = pd.to_datetime(minecraft_log['log_date'])
for file in files: 
    log_file_parts = re.search(r".*(\d{4}-\d{2}-\d{2}).*", file.name)
    if log_file_parts is not None:
        log_date = log_file_parts.group(1)
        try:
            f = gzip.open('/Users/{}/Library/Application Support/minecraft/logs/{}-2.log.gz'.format(local_user, log_date),'rb')
            for line in f:
                if line.decode()[0] == '[':
                    log_parts = re.search(r"\[(\d\d:\d\d:\d\d)\] \[([^\[]*)\]: (.+)", line.decode())
                    #print(log_parts.group(3))
                    l = log_parts.group(3)
                    
                    try:
                        if re.match(r'.*joined the game$', log_parts.group(3)):
                            ts = pd.Timestamp("{} {}".format(log_date, log_parts.group(1)))
                            minecraft_log.loc[len(minecraft_log.index)] = [ts, log_parts.group(2), log_parts.group(3)]
                            f.close()
                    except:
                        f.close()
        except Exception as e: 
            pass

minecraft_log['user_name'] = [re.sub(r' joined the game$','', str(x)) for x in minecraft_log['log_entry']]
minecraft_log['user_name'] = minecraft_log['user_name'].replace('.*\[CHAT\] ', '', regex=True)
minecraft_log['user_name'] = minecraft_log['user_name'].replace(' \(.*', '', regex=True)
minecraft_log['dates'] = minecraft_log['log_date'].dt.date
minecraft_log['times'] = minecraft_log['log_date'].dt.time
minecraft_log = minecraft_log.rename(columns={"user_name": "User Name"})


# In[4]:


log_in_times_plot_description = pn.pane.Markdown("""

#### Session data is sourced from the Minecraft Java Edition log files.

""", width=1000)
log_in_times_plot_description


# In[5]:


log_in_times_plot = minecraft_log.hvplot.scatter(
    x='dates', 
    y='times', 
    title='Minecraft Sessions',
    hover_cols=['log_date'],
    by='User Name',
    xlabel='Log In Date',
    ylabel='Log In Time',
    legend='top',
    height=500, 
    width=800
)
log_in_times_plot


# ## Create Dashboard
# 

# In[6]:


#bootstrap = pn.template.BootstrapTemplate(title='Minecraft Summary Stats')
bootstrap = pn.template.BootstrapTemplate(title='Minecraft Summary Stats')


md = pn.pane.Markdown("""
This dashboard summarizes Minecraft Java Edition 
Stats across saved worlds on a local machine. 
Data for the current output serves as example output - download and 
execute the jupyter notebook to create a dashboard with your data.

Visit the [GitHub page](https://github.com/CulleyHarrelson/MinecraftStats) to learn more.
""")

bootstrap.sidebar.append(md)
bootstrap.main.append(log_in_times_plot_description)
bootstrap.main.append(log_in_times_plot)
bootstrap.main.append(wood_type_plot_description)
bootstrap.main.append(wood_type_plot)


bootstrap.servable();

bootstrap.save(filename='MinecraftStats.html')


# In[23]:


from datetime import datetime

# Get the current date
current_date = datetime.now()

# Format the date as yyyy-mm-dd
formatted_date = current_date.strftime('%Y-%m-%d')



template = pn.template.FastGridTemplate(
    site="MinecraftStats", title='XX world analysis: ' + formatted_date,
    sidebar=md,
)

#gspec[0:1, 3:4] = pn.Spacer(background='purple', margin=0)


template.main[0:3, 1:] = log_in_times_plot
template.main[3:6, 1:] = wood_type_plot

template.save(filename='MinecraftStats2.html')


#meta_description (str): A meta description to add to the document head for search engine optimization. For example ‘P.A. Nelson’.

#meta_keywords (str): Meta keywords to add to the document head for search engine optimization.

#meta_author (str): A meta author to add to the the document head for search engine optimization. For example ‘P.A. Nelson’.

#meta_refresh (str): A meta refresh rate to add to the document head. For example ‘30’ will instruct the browser to refresh every 30 seconds. Default is ‘’, i.e. no automatic refresh.

#meta_viewport (str): A meta viewport to add to the header.

#base_url (str): Specifies the base URL for all relative URLs in a page. Default is ‘’, i.e. not the domain.

#base_target (str): Specifies the base Target for all relative URLs in a page. Default is _self.



# ## Extract world name and hardcore byte flag from level.dat
# 
# work in progress

# In[8]:


from nbtlib import File

path = Path('/Users/{user}/Library/Application Support/minecraft/saves/'.format(user=local_user))
nbtfiles = list(path.rglob("*/level.dat"))
world_types = pd.DataFrame(columns = ['world_name', 'hardcore', 'play_time'])

for nbtfile_name in nbtfiles:
    level_data = File.load(nbtfile_name, gzipped=True)
    hardcore = level_data['Data']['hardcore']
    level_name = level_data['Data']['LevelName']
    play_time = level_data['Data']['Time']
    world_types.loc[len(world_types.index)] = [level_name, hardcore, play_time]

world_types.describe()


# In[9]:


#help(pn.GridSpec)
#help(File)


# In[20]:


ACCENT_COLOR = pn.template.FastGridTemplate.accent_base_color
XS = np.linspace(0, np.pi)

def sine(freq, phase):
    return hv.Curve((XS, np.sin(XS * freq + phase))).opts(
        responsive=True, min_height=400, title="Sine", color=ACCENT_COLOR
    ).opts(line_width=6)

def cosine(freq, phase):
    return hv.Curve((XS, np.cos(XS * freq + phase))).opts(
        responsive=True, min_height=400, title="Cosine", color=ACCENT_COLOR
    ).opts(line_width=6)

freq = pn.widgets.FloatSlider(name="Frequency", start=0, end=10, value=2)
phase = pn.widgets.FloatSlider(name="Phase", start=0, end=np.pi)

sine = pn.bind(sine, freq=freq, phase=phase)
cosine = pn.bind(cosine, freq=freq, phase=phase)

template = pn.template.FastGridTemplate(
    site="Panel", title="FastGridTemplate",
    sidebar=[pn.pane.Markdown("## Settings"), freq, phase],
)


template.main[:2, 1:] = pn.pane.HoloViews(hv.DynamicMap(sine), sizing_mode="stretch_both")
template.main[2:4, 1:] = pn.pane.HoloViews(hv.DynamicMap(cosine), sizing_mode="stretch_both")
template.main[4:5, 1:] = pn.pane.Markdown("# Hello World!")

template.save("my_plots.html")

