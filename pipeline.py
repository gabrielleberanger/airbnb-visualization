# coding: utf-8

from packages import *
from data import *
from functions import *

if __name__=='__main__':

    #ACQUISITION

    get_listings()
    hist_df = get_hist_df()
    lastm_df = get_lastm_df(hist_df)

    #REPORTING - MAPS

    map_df = read_map_df()

    #Percentage of listings over total district accommodations
    data_for_map = lastm_df.pivot_table(values='id',index='district',aggfunc='count').rename(columns={'id':'number_of_listings'})
    acc_df = pd.DataFrame.from_dict(acc_dict,orient='index').reset_index().rename(columns={'index':'district',0:'number_of_acc'})
    data_for_map = data_for_map.merge(acc_df,on='district')
    data_for_map['listing_acc_per'] =                data_for_map.apply(lambda x: round(x.number_of_listings/x.number_of_acc*100,1),axis=1)
    merged = map_df.set_index('district').join(data_for_map)
    create_map(merged,variable='listing_acc_per',title='Percentage of Listings over Total District Accommodations')

    #Average number of reviews per listing
    map_df = read_map_df()
    data_for_map = lastm_df[['district','number_of_reviews','id']]                        .groupby('district').agg({'number_of_reviews':'sum','id':'count'})                        .rename(columns={'id':'number_of_listings'})
    data_for_map['reviews_per_listing'] =                data_for_map.apply(lambda x: round(x.number_of_reviews/x.number_of_listings,1),axis=1)
    data_for_map.drop(['number_of_reviews','number_of_listings'],axis=1,inplace=True)
    merged = map_df.set_index('district').join(data_for_map)
    create_map(merged,variable='reviews_per_listing',title='Average Number of Reviews per Listing')

    #Average price per night
    data_for_map = lastm_df[['district','price']].groupby('district').mean()
    merged = map_df.set_index('district').join(data_for_map)
    create_map(merged,variable='price',title='Average Price per Night')

    #Create gif               
    date_lst = sorted(list(hist_df.date.unique()))
    for date in date_lst:
        period_df = hist_df[hist_df.date==date]
        create_gif_frame(period_df)
    create_gif()

    #REPORTING - GRAPHS
    
    create_listing_types_per_district(lastm_df)
    create_reviews_evol(hist_df)
    create_listing_evol(hist_df)
    create_listing_evol_per_type(hist_df)
    create_price_evol(hist_df)
    create_price_evol_per_type(hist_df)
    create_listing_review_evol(hist_df)
