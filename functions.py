# coding: utf-8

from packages import *
from data import *

#ACQUISITION FUNCTIONS

def get_listings():
    """Function scraping all links to listings.csv files available on insideairbnb.com
    website, and saving downloaded files in a /data/raw-data folder.
    The files are named after their collection date (YYYY-MM.csv)."""
    soup = bs(requests.get('http://insideairbnb.com/get-the-data.html').content,'lxml')
    link_lst = [i['href'] for i in soup.select("td:contains('Paris')+td>a[onclick*=listings_visualisation]")]
    subfolder_names = ['raw-data','cleaned-data']
    for subfolder_name in subfolder_names:
        os.makedirs(os.path.join('data',subfolder_name))
    for link in link_lst:
        file = pd.read_csv(link)
        date = re.findall(r'20\d{2}-\d{2}',link)[0]
        file.to_csv(f'data/raw-data/{date}.csv',index=False)
        
def clean_df(df):
    """Function cleaning listing.csv files (fill NaN values, drop inappropriate columns,
    replace Airbnb neighbourhoods by official district numbers). It is used in the get_hist function."""
    df.drop('neighbourhood_group',axis=1,inplace=True)
    df.neighbourhood = df.neighbourhood.map(district_dict)
    df.rename(columns={'neighbourhood':'district'},inplace=True)
    df.reviews_per_month[df.number_of_reviews==0] = df.reviews_per_month[df.number_of_reviews==0].fillna(0)
    df.last_review[df.number_of_reviews==0] = df.last_review[df.number_of_reviews==0].fillna('Never')
    df[['name','host_name']] = df[['name','host_name']].fillna('Unknown')
    return df

def get_hist_df():
    """Function concatenating downloaded listing.csv files into a hist_df DataFrame.
    A column 'date' (YYYY-MM) is added to hist_df, so that we can still
    access the time period on which the data was originally scraped."""
    hist_df = pd.DataFrame()
    for file in os.listdir('data/raw-data'):
        temp_df = pd.read_csv(f'data/raw-data/{file}')
        if not file.startswith('.'):
            temp_df['date'] = re.findall(r'20\d{2}-\d{2}',file)[0]
            hist_df = pd.concat([hist_df,temp_df],ignore_index=True)
    hist_df = clean_df(hist_df)
    hist_df.to_csv(f'data/cleaned-data/listings-hist.csv',index=False)
    return hist_df

def get_lastm_df(hist_df):
    """Function creating a DataFrame with the data of the most
    recent month only (lastm_df) from the global hist_df."""
    date_lst = sorted(list(hist_df.date.unique()),reverse=True)
    return hist_df[hist_df.date==date_lst[0]]

#MAP FUNCTIONS

def read_map_df():
    """Function reading the neighbourhoods.geojson file as a GeoPandas DataFrame.
    This file references the coordinates of each neighbourhood."""
    #Read the neighbourhoods.geojson file with GeoPandas, and drop unappropriate columns
    map_df = gpd.read_file('neighbourhoods.geojson')
    map_df.drop('neighbourhood_group',axis=1,inplace=True)
    #Replace Airbnb neighbourhoods by official district numbers
    map_df.neighbourhood = map_df.neighbourhood.map(district_dict)
    map_df.rename(columns={'neighbourhood':'district'},inplace=True)
    #Apply the ESPG:3395 projection (so that the map does not look distorted)
    map_df = map_df.to_crs({'init': 'epsg:3395'})
    return map_df

def create_map(merged,variable,title):
    """"Function creating a colored map based on 3 variables:
    - merged (GeoPandas DataFrame): DataFrame resulting of the merge of
    the original map_df (columns: district number, district coordinates)
    with a data_for_map DataFrame (columns: district number, data to plot)
    - variable (str): column of the merged DataFrame, that should be used to plot the data
    - title (str): title to be given to the output map
    The output map is then saved in a /graphs folder."""
    sns.set(style='white')
    fig, ax = plt.subplots(1,1,figsize=(15,8))
    #Set up legend
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right',size='5%',pad=0.1)
    #Create map
    merged.plot(column=variable,ax=ax,cmap='Blues',edgecolor='lightgrey',legend=True,cax=cax)
    #Adjust layout
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlim(245000,277250)
    ax.set_ylim(6210000,6228000)
    ax.axis('off')
    #Save map
    if not os.path.exists('graphs'):
        os.mkdir('graphs')
    fig.savefig(f"graphs/map-lastm-{'-'.join(title.lower().split(' '))}.png", dpi=500)
                
def create_gif_frame(period_df):
    """Function plotting Airbnb listings on a map of Paris from a period_df
    (hist_df filtered on a specific period of time). The output image is saved in a /graphs/gif-frames folder.
    Generated images will be later used as gif frames, so that we can visualize the evolution
    of the number of listings over time."""
    sns.set(style='white')
    #Create listings coordinates
    geometry = gpd.points_from_xy(period_df.longitude,period_df.latitude)
    geo_df = gpd.GeoDataFrame(period_df, geometry=geometry,crs={'init': 'epsg:4326'})
    geo_df = geo_df.to_crs({'init': 'epsg:3395'})
    #Create map
    sns.set(style='white')
    fig, ax = plt.subplots(1,1,figsize=(15,8))
    map_df.plot(ax=ax,edgecolor='white',color='lightgray')
    geo_df.plot(ax=ax, markersize=10, color='blue', alpha=0.05)  
    #Get period_df info
    year = re.findall(r'(20\d{2})-\d{2}',period_df.date.unique()[0])[0]
    month_nb = int(re.findall(r'20\d{2}-(\d{2})',period_df.date.unique()[0])[0])
    month = calendar.month_name[month_nb]
    #Adjust layout            
    ax.text(0.1, 0.9, 'YEAR:',transform=ax.transAxes)
    ax.text(0.1, 0.86, year,transform=ax.transAxes,fontweight='bold',fontsize=16)
    ax.text(0.17, 0.9, 'MONTH:',transform=ax.transAxes)
    ax.text(0.17, 0.86, month,transform=ax.transAxes,fontweight='bold',fontsize=16)
    ax.text(0.1, 0.81, 'LISTING COUNT:',transform=ax.transAxes)
    ax.text(0.1, 0.77, f'{geo_df.shape[0]:,}',transform=ax.transAxes,fontweight='bold',fontsize=16)
    ax.set_xlim(245000,277250)
    ax.set_ylim(6210000,6228000)       
    ax.axis('off')
    #Save map
    if not os.path.exists('graphs/gif-frames'):
        os.mkdir('graphs/gif-frames')
    fig.savefig(f"graphs/gif-frames/gif-frame-{period_df.date.unique()[0]}.png", dpi=300)

def create_gif():
    """Function creating a gif from a set of gif frames, saved in the /graphs/gif-frames folder."""
    path = 'graphs/gif-frames/'
    frame_files = [frame_file for frame_file in os.listdir(path) if frame_file.endswith('.png')]
    frames = [imageio.imread(os.path.join(path,frame_file)) for frame_file in sorted(frame_files)]
    imageio.mimsave('graphs/map-hist-listing-count.gif',frames,fps=4)
                
#GRAPH FUNCTIONS

sns.set()
                
def create_listing_types_per_district(lastm_df):
    """Function creating a bar plot:
    - Title: Listing Types per District
    - Time period: previous month"""
    #Prepare data
    graph_df = lastm_df\
                .pivot_table(values='id',index='district',columns='room_type',aggfunc='count')
    graph_df = graph_df.apply(lambda x: round(x/x.sum(),3)*100,axis=1)
    #Create graph
    graph_df.plot.bar(figsize=(20,8),width=1)
    plt.xlabel('District',fontsize=18)
    plt.ylabel('Percentage of Total District Listings',fontsize=18)
    plt.tick_params(axis='x', labelsize=15, rotation=45)
    plt.tick_params(axis='y', labelsize=15)
    plt.ylim(0,110)
    title = 'Listing Types per District'
    plt.title(title,fontsize=22,fontweight='bold',pad=20)
    #Save figure
    plt.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')

def create_reviews_evol(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Number of Reviews
    - Time period: overall period"""
    #Prepare data
    graph_df = hist_df.pivot_table(values='number_of_reviews',index='date',aggfunc='sum').reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig, ax = plt.subplots(figsize=(20,8))
    sns.scatterplot('datenum', 'number_of_reviews', data=graph_df, ax=ax, s=80)
    ax.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    title = 'Evolution of the Number of Reviews'
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlabel('Years',fontsize=18)
    ax.set_ylabel('Number of Reviews',fontsize=18)
    ax.tick_params(axis='x', labelsize=15)
    ax.tick_params(axis='y', labelsize=15)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')
                
def create_listing_evol(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Number of Listings
    - Time period: overall period"""
    #Prepare data
    graph_df = hist_df.pivot_table(values='id',index='date',aggfunc='count')\
                .rename(columns={'id':'number_of_listings'}).reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig, ax = plt.subplots(figsize=(20,8))
    sns.scatterplot('datenum', 'number_of_listings', data=graph_df, ax=ax, s=80)
    ax.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    title = 'Evolution of the Number of Listings'
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlabel('Years',fontsize=18)
    ax.set_ylabel('Number of Listings',fontsize=18)
    ax.tick_params(axis='x', labelsize=15)
    ax.tick_params(axis='y', labelsize=15)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')

def create_listing_evol_per_type(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Number of Listings per Type
    - Time period: overall period"""
    #Prepare data
    graph_df = hist_df.pivot_table(values='id',index=['date','room_type'],aggfunc='count')\
                .rename(columns={'id':'number_of_listings'}).reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig, ax = plt.subplots(figsize=(20,8))
    sns.scatterplot('datenum', 'number_of_listings', data=graph_df, hue = 'room_type', s=70)
    ax.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    title = 'Evolution of the Number of Listings per Type'
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlabel('Years',fontsize=18)
    ax.set_ylabel('Number of Listings',fontsize=18)
    ax.tick_params(axis='x', labelsize=15)
    ax.tick_params(axis='y', labelsize=15)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')
                
def create_price_evol(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Average Price per Night
    - Time period: overall period"""
    sns.set()
    #Prepare data
    graph_df = hist_df.pivot_table(values='price',index='date',aggfunc='mean').reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig, ax = plt.subplots(figsize=(20,8))
    sns.scatterplot('datenum', 'price', data=graph_df, ax=ax, s=70)
    ax.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    title = 'Evolution of the Average Price per Night'
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlabel('Years',fontsize=18)
    ax.set_ylabel('Price',fontsize=18)
    ax.tick_params(axis='x', labelsize=15)
    ax.tick_params(axis='y', labelsize=15)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')
                
def create_price_evol_per_type(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Average Price per Night per Listing Type
    - Time period: overall period"""
    #Prepare data
    graph_df = hist_df.pivot_table(values='price',index=['date','room_type'],aggfunc='mean').reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig, ax = plt.subplots(figsize=(20,8))
    sns.scatterplot('datenum', 'price', data=graph_df, hue = 'room_type',s=70)
    ax.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    title = 'Evolution of the Average Price per Night per Listing Type'
    ax.set_title(title,fontsize=22,fontweight='bold',pad=20)
    ax.set_xlabel('Years',fontsize=18)
    ax.set_ylabel('Price',fontsize=18)
    ax.tick_params(axis='x', labelsize=15)
    ax.tick_params(axis='y', labelsize=15)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')
                
def create_listing_review_evol(hist_df):
    """Function creating a scatter plot:
    - Title: Evolution of the Number of Listings vs Reviews
    - Time period: overall period""" 
    #Prepare data
    graph_df = hist_df.pivot_table(values=['id','number_of_reviews'],index='date',\
                aggfunc={'id':'count','number_of_reviews':'sum'})\
                .rename(columns={'id':'number_of_listings'}).reset_index()
    graph_df['datenum']=mdates.datestr2num(graph_df.apply(lambda x: str(x.date)+'-01', axis=1))
    #Create graph
    fig,ax1 = plt.subplots(figsize=(20,8))
    #Create 1st plot
    sns.scatterplot(x='datenum',y='number_of_listings', data=graph_df, ax=ax1, s=80, color='C0')
    ax1.set_xlim(mdates.datestr2num('2014-12-01'),mdates.datestr2num('2020-02-01'))
    ax1.set_xlabel('Years',fontsize=18)
    ax1.set_ylabel('Number of Listings',fontsize=18,color='C0')
    ax1.tick_params(axis='x', labelsize=15)
    ax1.tick_params(axis='y', labelsize=15)
    title = 'Evolution of the Number of Listings vs Reviews'
    ax1.set_title(title,fontsize=22,fontweight='bold',pad=20)
    #Convert date units back to their usual format
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    #Create 2nd plot
    ax2 = ax1.twinx()
    sns.scatterplot(x='datenum',y='number_of_reviews', data=graph_df, ax=ax2, s=80, color='C1')
    ax2.tick_params(axis='x', labelsize=15)
    ax2.tick_params(axis='y', labelsize=15)
    ax2.set_ylabel('Number of Reviews',fontsize=18,color='C1')
    ax2.grid(None)
    #Save graph
    fig.savefig(f"graphs/hist-graph-{'-'.join(title.lower().split(' '))}.png",dpi=300,bbox_inches='tight')