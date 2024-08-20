import numpy as np
import matplotlib.pyplot as plt

def cosd(a):
    return np.cos( a * np.pi/180 )
def sind(a):
    return np.sin( a * np.pi/180 )
def tand(a):
    return np.tan( a * np.pi/180 )

def get_out_dir():
    '''
    choose an output directory based on operating system.

    for remote linux servers, the /tmp directory may use SSDs for faster read/write speeds.
    when running on windows, simply store in the local directory
    '''
    import platform, shutil, glob, os
    
    # git repo should include a small CSV of data by default. this will either be the
    # output directory or be copied to /tmp/ if linux
    output_dir = os.getcwd() + '/data/'
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        print('output directory prepared!')

    # linux operations
    cur_sys = platform.system()
    if cur_sys.lower() == 'linux':
        tmp_dir = '/tmp/'

        # copy any files that may exist 
        cur_files = glob.glob(output_dir + '*')
        for file in cur_files:
            shutil.copy2(file, tmp_dir)
        # change output directory to /tmp/
        output_dir = tmp_dir
    
    return output_dir
        
        

def gdal_corners(filename):
    '''
    a function  that can be used to determine the boundary of a raster / tif file.
    '''
    #http://stackoverflow.com/questions/2922532/obtain-latitude-and-longitude-from-a-geotiff-file
    from osgeo import gdal            # https://www.lfd.uci.edu/~gohlke/pythonlibs/
    ds = gdal.Open(filename)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5]
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3]
    return (minx,miny,maxx,maxy)
                
def join_files(file_list):
    
    '''
        a method for merging raster/tif data along the band dimension using 
        rioxarray. this method does not save data to storage.
    '''
    
    import rioxarray as rxr
    import xarray as xr
    
    # initialize band names
    var_names = []
    
    # loop over bands, append to a rasterio xarray
    for file in file_list:
        
        xmin,ymin,xmax,ymax=tuple(gdal_corners(file))
        cda=rxr.open_rasterio(file,chunks=(1,1200,1200))
        cda=cda.sel(x=slice(xmin,xmax),y=slice(ymax,ymin))
        
        if file == file_list[0]:
            da = cda
        else:
            da = xr.concat([da, cda], "band")
            
        # extract frequency / polarization band
        var_name = file.split('_')[5]
        var_name = var_name[0:2] + var_name[5:]
        var_names.append(var_name)

    # change band names for reading
    da = da.assign_coords({'band' : var_names})
    return da


def join_sar_radiom(da, radiom):
    ''' 
    
    input
        da - rioxarray containing SWESARR SAR data. 6 channels expected.
        radiom - pandas array containing radiometer data. 3 channels expected.
        
    output
        data_p - pandas data series intended for plotting with hvplot's "groupby" feature. 
                sadly, all measurement data is crammed into a single column, making this 
                difficult to use outside of hvplot functionality.
        out_data - pandas data series that is readable. intended for use in student exercise.
        
    TO-DO / IMPROVEMENTS :
        implementing this with xarray would be much more RAM efficient. 
        however, i find pandas arrays to be easier to conceptualize than xarrays.
        i feel its best to go with pandas arrays for the tutorial.
            ( with great shame, i admit i find it harder to visualize
              N-dimensional data rather than 2-dimensional data )
            
    '''
    import numpy as np
    import pandas as pd
    import datetime
    
    # first, convert the data from the SAR's meter-based, 
    # universal transverse mercator (UTM) coordinate system
    # to the radiometer's old-fashioned 
    # latitude/longitude coordinate system
    sar_geo = da.rio.reproject("EPSG:4326")
    
    # get latidue and longitude from SAR data
    lat_sar = sar_geo.y.data
    lon_sar = sar_geo.x.data

    # radiometer latitude/longitude values as numpy arrays
    lat_rad = radiom['Latitude (deg)'].to_numpy()
    lon_rad = radiom['Longitude (deg)'].to_numpy()

    # loop over latitude and longitude
    frames = []
    k = -1
    for lat, lon in zip(lat_rad, lon_rad):
        k+=1

        # get the difference between latitude and longitude pairs
        # for SAR and radiometer data
        lat_m = np.abs(lat_sar - lat).tolist()
        lon_m = np.abs(lon_sar - lon).tolist()

        # use python's built-in functions to find minimum index
        ind_lat = lat_m.index(min(lat_m))
        ind_lon = lon_m.index(min(lon_m))

        # write sar lat and lon
        s_lat = lat_sar[ind_lat]
        s_lon = lon_sar[ind_lon]

        # get distance between the estimated sar and radiometer center positions
        # using vincenty's formula from the geopy library
        dis = distance( (lat, lon), (s_lat, s_lon) ).m

        # construct data dictionary
        data_d = {'sar_lat': s_lat, 'sar_lon' : s_lon, 
                  'rad_lat' : lat, 'rad_lon' : lon, 
                  'ind_lat' : ind_lat, 'ind_lon' : ind_lon,
                  'dist_m' : dis}

        # make a pandas dataframe based on the above data!
        df = pd.DataFrame(data_d, index = [k])
        
        # throw it in an array for good measure
        frames.append(df)

    # use "list comprehension" syntax to merge the pandas dataframes together
    location_data = pd.concat( data for data in frames )
    del frames, df, data_d
    
    # now lets store our SAR data based on our filtered results
    sar_data = []

    for in1, in2 in zip( location_data['sar_lon'].tolist(), location_data['sar_lat'].tolist()):
        # access the dask array storing our results
        d = sar_geo.sel( x=in1, y=in2 ).compute().data.tolist()
        # append to our list
        sar_data.append(d)

    # convert both arrays array to a numpy array for easy merging
    data = np.array(sar_data)
    radiom_d = radiom.iloc[:,4:7].to_numpy()

    # insert the radiometer data to the SAR data as a column vector
    for i in range(np.size(radiom_d,1)):
        data = np.insert( data, np.size(data,1), radiom_d[:,i], axis=1 )
    del radiom_d

    # the following section is for plotting with hvplot while including a label only.
    #
    # use list operations paired with pandas series to repeat the lat/lon data
    lon_ser = pd.Series( location_data['sar_lon'].to_list() * (6)\
                        + location_data['rad_lon'].to_list() * (3) )
    lat_ser = pd.Series( location_data['sar_lat'].to_list() * (6)\
                        + location_data['rad_lat'].to_list() * (3) )
    
    # flatten MATLAB/*F*ortran style. (Default flattens as row vectors)
    data_ser = data.flatten(order='F')

    # get series length, create IDs for plotting
    # all series have the same length, so this shouldn't matter.
    sl = len(radiom['TB X (K)'])
    id_ser = pd.Series(
        ['09VV SAR']*sl + ['09VH SAR']*sl + ['13VV SAR']*sl + ['13VH SAR']*sl + \
            ['17VV SAR']*sl + ['17VH SAR']*sl + \
        ['X-band Rad']*sl + ['K-band Rad']*sl + ['Ka-band Rad']*sl, name="ID"
         )
    
    # the final frame used only for plotting by groups with hvplot
    frame = {'Longitude (deg)' : lon_ser, 'Latitude (deg)' : lat_ser,
             'Measurements' : data_ser, 'ID' : id_ser}
    data_p = pd.DataFrame(frame)
    
    # convert swesarr numpy data to dataframe
    swesarr_df = pd.DataFrame(data = data, 
                        columns = ["09VV SAR", "09VH SAR", 
                                   "13VV SAR", "13VH SAR",
                                   "17VV SAR", "17VH SAR",
                                   'X-band Rad', 'Ku-band Rad', 
                                   'Ka-band Rad'])
    
    # Convert UTC string to date time array
    times = radiom.UTC.to_frame()
    times = times['UTC'].to_list()

    # convert to datetime
    times = [datetime.datetime.strptime(time_str, '%Y%m%d-%H:%M:%S.%f') for time_str in times]

    radiom.UTC = times

    
    # combine time data with swesarr measurements
    out_data = pd.concat( [radiom.UTC.to_frame(), swesarr_df], axis=1)

    # return the variable used for plotting and its more user-friendly variant.
    return data_p, out_data

def filt_pit_to_sar(snow_pits, sar_data, box_size):
    
    '''
    input 
        snow_pits -- DataFrame created from snowexsql LayerMeasurements. (UTM CRS)
        sar_data  -- xarray.DataArray containing [6,y,x] SWESARR data (UTM CRS)
        box_size  -- length of the square about each snow pit used for averaging 
                     obtaining an average swesarr backscatter (numeric)
    
    output
        point_swe_filt -- GeoPandas GeoDataFrame of filtered snow pit data
        swesarr_mean   -- numpy array of mean SWESARR backscatter values for each filtered snowpit
    
    '''
    
    # the filtering box will be centered about the swesarr data
    box_size /= 2
    
    import numpy as np
    import geopandas as gpd
    
    to_nl = lambda a: 10**(a/10)
    to_db = lambda a: 10*np.log10(a)
    

    snow_pits['value'] = snow_pits['value'].astype(float)

    # Calculate SWE
    swe_lambda = lambda row: row['value'] * (row['depth'] - row['bottom_depth']) / 100
    snow_pits['swe'] = snow_pits.apply(swe_lambda, axis=1)

    # Prepare the data to be a single point by summing the SWE by site and date
    point_swe = gpd.GeoDataFrame(columns=['date', 'swe', 'geometry', 'site_id'])

    sites = snow_pits['site_id'].unique().tolist()

    my_sites = []
    # Loop over data by site and date
    for site in sites:
        if len(site.split()) == 1:
            ind1 = snow_pits['site_id'] == site
            dates = snow_pits['date'][ind1].unique().tolist()
            
            for date in dates:
                # Grab all density at this site and date
                ind2= snow_pits['date'] == date
                
                profile = snow_pits[ind1 & ind2]
            
                # sum the swe column and assign data to a dictionary
                data = gpd.pd.DataFrame ({'swe': profile['swe'].sum(), 'geometry': profile['geom'].iloc[0], 'date': date}, index=[0])
            
                # Add the data to a dataframe
                point_swe = gpd.pd.concat([point_swe, data], ignore_index=True)
                my_sites.append(site)
    point_swe['site_id'] = my_sites    

    # x and y coordinates as numpy arrays
    lat_pit = point_swe['geometry'].y.to_numpy()
    lon_pit = point_swe['geometry'].x.to_numpy()


    # get subelements of the primary xarray
    swesarr_subs = []
    for cur_lat, cur_lon in zip(lat_pit, lon_pit):
        # get bounding box about lat / lon
        lat_box = np.array([cur_lat]) + np.array([-box_size, box_size])
        lon_box = np.array([cur_lon]) + np.array([-box_size, box_size])
        
        # extract points
        tmp = sar_data.sel(y=slice(lat_box[1], lat_box[0]), x=slice(lon_box[0], lon_box[1]))
        # add to that thing
        swesarr_subs.append( tmp )
        
    # obtain the mean SAR value for each subelement
    swesarr_mean = np.zeros([6, len(my_sites)]) * np.nan
    for sub, ii in zip(swesarr_subs, range(len(my_sites))):
        for sub_band, jj in zip( sub['band'].values, range(6)):
            if not any( x == 0 for x in swesarr_subs[ii].shape ) :
                cur_data = swesarr_subs[ii].sel({'band':sub_band})
                swesarr_mean[jj,ii] = to_db(np.mean(to_nl(cur_data.values)))

    # filter out any data with nans
    nan_mask = ~np.isnan(swesarr_mean)
    nan_mask = np.logical_and.reduce(nan_mask,axis=0)
    swesarr_mean = swesarr_mean[:,nan_mask]
    my_sites = [a for a,b in zip(my_sites, nan_mask) if b]
    lat_pit = lat_pit[nan_mask]
    lon_pit = lon_pit[nan_mask]
    point_swe_filt = point_swe[nan_mask]
    point_swe_filt = point_swe_filt.reset_index(drop=True)
    point_swe_filt['lat'] = lat_pit
    point_swe_filt['lon'] = lon_pit
    
    return point_swe_filt, swesarr_mean

def filt_radiom_points( fp_10m, fp_18m, fp_37m, radiom, point_swe_filt ):
    '''

    Parameters
    ----------
    fp_10m : int / float (scalar)
        Semi-major axis of 10 GHz footprint [meter]
    fp_18m : int / float (scalar)
        Semi-major axis of 18 GHz footprint [meter]
    fp_37m : int / float (scalar)
        Semi-major axis of 37 GHz footprint [meter]
    radiom : pandas dataframe
        radiometer data from SWESARR CSV
    point_swe_filt : geopandas GeoDataFrame
        filtered SWE data from call to filt_pit_to_sar()

    Returns
    -------
    rad_swe : geopandas GeoDataFrame
        Dataframe of SWE snow pit data with nearest brightness temperature value available
    '''
    from pyproj import Transformer
    rad_lat = np.array( radiom['Latitude (deg)'])
    rad_lon = np.array( radiom['Longitude (deg)'])

    # Convert latitude and longitude to UTM
    wgs84_crs = "EPSG:4326"
    utm_crs   = "EPSG:32612"
    trnsfmr             = Transformer.from_crs(wgs84_crs, utm_crs)
    rad_east, rad_north = trnsfmr.transform(rad_lat, rad_lon)
    
    lat_pit = np.array( point_swe_filt['lat'] )
    lon_pit = np.array( point_swe_filt['lon'] )

    rad_pit10 = np.zeros( [ np.shape( lat_pit )[0]]) * np.nan
    rad_pit18 = np.zeros( [ np.shape( lat_pit )[0]]) * np.nan
    rad_pit37 = np.zeros( [ np.shape( lat_pit )[0]]) * np.nan
    for p_lat, p_lon, i in zip(lat_pit, lon_pit, range(len(radiom))): 
        dif_arr = np.sqrt( (rad_north - p_lat)**2 + (rad_east - p_lon)**2 )
        dif_val = np.min(dif_arr)
        dif_ind = np.argmin(dif_arr)
        if dif_val <= fp_10m:
            rad_pit10[i] = radiom['TB X (K)'][dif_ind]
        if dif_val <= fp_18m:
            rad_pit18[i] = radiom['TB K (K)'][dif_ind]
        if dif_val <= fp_37m:
            rad_pit37[i] = radiom['TB Ka (K)'][dif_ind]
            
    nan_mask_rad = ~np.isnan(rad_pit10) # filter about the widest footprint
    rad_swe = point_swe_filt[nan_mask_rad]
    rad_swe['TB_X'] = rad_pit10[nan_mask_rad]
    rad_swe['TB_K'] = rad_pit18[nan_mask_rad]
    rad_swe['TB_Ka'] = rad_pit37[nan_mask_rad]
    rad_swe = rad_swe.reset_index(drop=True)
    
    return rad_swe

def sar_swe_plot(point_swe_filt, swesarr_mean):
    s_i = np.argsort(point_swe_filt.swe.to_list())
    
    # color palette # https://zenodo.org/records/3381072
    okabe_ito = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
    sar_labs  = ['09VH', '09VV', '13VH', '13VV', '17VH', '17VV']
    ## plot avg swe and avg backscatter per site
    fig, ax1 = plt.subplots()
    plt.xticks(rotation=70)
    ax1.plot( point_swe_filt.site_id[s_i], point_swe_filt.swe[s_i], 'd', linewidth=2, label='SWE', color=okabe_ito[-1] )
    ax1.set_ylabel('SWE [mm]', color=okabe_ito[-1])
    ax1.set_xlabel('SnowEx20 Pit ID')
    ax2 = ax1.twinx()
    for each, lab, pal in zip(swesarr_mean[1:6:2,s_i], sar_labs[1:6:2], okabe_ito):
        sub_data = each
        bl1 = (sub_data > -20) & (sub_data < 0)
        sub_data[~bl1] = np.nan
        xlab = point_swe_filt.site_id[s_i]
        ax2.plot( xlab, sub_data, '-o', label=lab, color=pal )
    plt.legend()
    ax1.tick_params(axis='y', colors=okabe_ito[-1])
    ax2.set_ylabel('Backscatter [dB]')
    return fig

def radiom_swe_plot(rad_swe):
    '''
    plot SWE and brightness temperature together

    Parameters
    ----------
    rad_swe : geopandas dataframe
        combined radiometer and swe data

    Returns
    -------
    fig : matplotlib.pyplot.figure
        figure handle for generated image
    '''
    # color palette # https://zenodo.org/records/3381072
    okabe_ito = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
    TB_ids = ['TB_X', 'TB_K', 'TB_Ka']
    TB_leg = ['X (10)', 'K (18)', 'Ka (37)']
    
    s_i = np.argsort(rad_swe.swe.to_list())
    fig, ax1 = plt.subplots()
    plt.xticks(rotation=70)
    ax1.plot( rad_swe.site_id[s_i], rad_swe.swe[s_i], 'd', linewidth=2, label='SWE', color=okabe_ito[-1] )
    ax1.set_ylabel('SWE [mm]', color=okabe_ito[-1])
    ax1.set_xlabel('SnowEx20 Pit ID')
    ax2 = ax1.twinx()
    for lab, pal, leg in zip(TB_ids, okabe_ito, TB_leg):
        ax2.plot( rad_swe.site_id[s_i], rad_swe[lab][s_i], '-o', label=leg, color=pal )
    plt.legend()
    ax1.tick_params(axis='y', colors=okabe_ito[-1])
    ax2.set_ylabel('Brightness Temperature [K]')
    return fig


def rough_radiom_area(radiom, rad_swe, fp_10m, fp_18m, fp_37m):
    from pyproj import Transformer
    import holoviews as hv
    import pandas as pd
    import cartopy.crs as ccrs
    
    crs = ccrs.UTM(zone='12') #12n
    transparent_tile = hv.Tiles('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer/tile/{Z}/{Y}/{X}', name="EsriReference").opts(alpha=0.0)
    
    beg_i = radiom['UTC'].argmin()
    end_i = radiom['UTC'].argmax()

    end_lats = radiom['Latitude (deg)'][[beg_i, end_i]].to_list()
    end_lons = radiom['Longitude (deg)'][[beg_i, end_i]].to_list()

    wgs84_crs = "EPSG:4326"
    utm_crs   = "EPSG:32612"
    trnsfmr             = Transformer.from_crs(wgs84_crs, utm_crs)
    end_east, end_north = trnsfmr.transform(end_lats, end_lons)

    xd = {}
    for a, b in zip( [fp_10m, fp_18m, fp_37m], ['10', '18', '37']):
        xd['x_' + b] = np.array( [ end_east[0] - a, end_east[1] - a, end_east[1] + a, end_east[0] + a, end_east[0] - a] )
        xd['y_' + b] = np.array( [ end_north[0] + a, end_north[1] - a, end_north[1] - a, end_north[0] + a, end_north[0] + a] )


    # Overlay the plot with tiles and rectangle
    xd_pd = pd.DataFrame(xd)

    rect_data = []
    for a, b, c in zip( ['blue', 'orange', 'purple'], ['10', '18', '37'], ['EsriImagery', transparent_tile, transparent_tile]):
        rect_data.append(
            xd_pd.hvplot.polygons(
                x='x_' + b, 
                y='y_' + b, 
                color=a, 
                alpha=0.25, 
                line_width=0,
                geo=True,
                crs=utm_crs,
                tiles=c
            )
            )


    snow_pit_img = rad_swe.hvplot.points('lon', 'lat',  geo=True, color='swe', alpha=1,
                            tiles=transparent_tile, height=500, width=800, crs=utm_crs, hover_cols=['site_id'],
                            cmap='Reds')
    
    final_img = rect_data[0]*rect_data[1]*rect_data[2]*snow_pit_img
    return final_img

    
if __name__ == '__main__':
    print('name is main!')