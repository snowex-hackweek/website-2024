# Data Access and Formats

There is a host of different ways to access NASA Earth observing data.  This section provides a map to a selection of data access methods and user resources. At the hackweek, the focus is on accessing data from a cloud compute instance in AWS us-west-2.  However, some of the access methods and tools can be used from a local machine as well.

The tutorials are organized as follows:

- [Overview](overview.md) provides an introduction to data access tools and offers some guidance on the capabilities and applicability of the different tools.
- [NSIDC DAAC and NASA Resources](NSIDC_resources.md) explores various resources for learning about and accessing ICESat-2, SnowEx, and other NASA Earthdata.  
- [Using NASA EarthData Search to Discover Cloud-Hosted Data](earthdata_search.md) describes how to use the Earthdata Search GUI search interface for NASA data.  This is probably the simplest way to search for ICESat-2, SnowEx and other NASA data.
- [Using `earthaccess` to Search for, Access and Download SnowEx Data in the Cloud](earthaccess_snowex.ipynb) presents a Python package to search for NASA datasets and granules, and to download those granules.
- [Using `earthaccess` to Search for, Access and Open ICESat-2 Data in the Cloud](earthaccess_icesat2.ipynb) presents a Python package to search for NASA datasets and granules, and to download those granules, or, if you are in  AWS `us-west-2` cloud compute instance, open data files directly from cloud storage.
