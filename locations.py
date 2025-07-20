import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

# List of locations from user (parsed and cleaned)
locations = [
    "Albury", "Badgerys Creek", "Cobar", "Coffs Harbour", "Moree", "Newcastle", "Norah Head", "Norfolk Island", 
    "Penrith", "Richmond", "Sydney", "Wagga Wagga", "Williamtown", "Wollongong", "Canberra", "Tuggeranong", 
    "Mount Ginini", "Ballarat", "Bendigo", "Sale", "Melbourne", "Mildura", "Nhil", "Portland", "Dartmoor", 
    "Brisbane", "Cairns", "Gold Coast", "Townsville", "Adelaide", "Mount Gambier", "Nuriootpa", "Woomera", 
    "Albany", "Witchcliffe", "Pearce RAAF", "Perth Airport", "Perth", "Salmon Gums", "Walpole", "Hobart", 
    "Launceston", "Alice Springs", "Katherine", "Uluru"
]

# Initialize geolocator
geolocator = Nominatim(user_agent="climate_app_locator")
data = []

# Geocode each location
for loc in locations:
    try:
        location = geolocator.geocode(loc + ", Australia")
        if location:
            data.append({"Location": loc, "Latitude": location.latitude, "Longitude": location.longitude})
        else:
            data.append({"Location": loc, "Latitude": None, "Longitude": None})
    except:
        data.append({"Location": loc, "Latitude": None, "Longitude": None})
    sleep(1)  # To avoid hitting the geocoding API rate limit

# Create and save dataframe
coords_df = pd.DataFrame(data)
coords_df = coords_df.dropna()  # Drop any invalid locations not geocoded successfully
coords_df.to_excel("/mnt/data/location_coordinates.xlsx", index=False)
coords_df.head()
