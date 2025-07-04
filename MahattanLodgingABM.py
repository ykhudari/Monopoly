import pandas as pd
import random

# Loading data
def load_and_preprocess_hotel_data(filepath):
    hotels_df = pd.read_csv(filepath)
    hotels_df['Month'] = pd.to_datetime(hotels_df['Month'], format='%d-%b')
    hotels_df.sort_values('Month', inplace=True)
    return hotels_df

def load_and_preprocess_airbnb_data(filepath):
    airbnbs_df = pd.read_csv(filepath)
    airbnbs_df['price'] = airbnbs_df['price'].replace('[\$,]', '', regex=True).astype(float)
    airbnbs_df['airbnb_type'] = pd.cut(airbnbs_df['price'], bins=[0, 100, 200, float('inf')], labels=['Budget', 'Standard', 'Premium'])
    return airbnbs_df

def load_and_preprocess_visitor_data(filepath):
    visitors_df = pd.read_excel(filepath)
    visitors_df['total_visitors'] = visitors_df['JFK visitors (2023)'] + visitors_df['LaGuardia visitors (2023)']
    visitors_df['Month'] = pd.to_datetime(visitors_df['Month'], format='%Y-%m-%d')
    return visitors_df[['Month', 'total_visitors']]

# Agent Classes
class AccommodationAgent:
    def __init__(self, id, base_price, amenities, location, capacity=100): 
        self.id = id
        self.base_price = base_price
        self.amenities = amenities
        self.location = location
        self.capacity = capacity  
        self.occupancy_rate = 0
        #Track the current number of tourists
        self.current_occupancy = 0  
    def update_occupancy_rate(self):
        if self.capacity > 0:
            self.occupancy_rate = (self.current_occupancy / self.capacity) * 100
        else:
            self.occupancy_rate = 0

# Acommodation Agents
class HotelAgent(AccommodationAgent):
    def __init__(self, id, base_price, amenities, location, hotel_type):
        super().__init__(id, base_price, amenities, location)
        self.hotel_type = hotel_type
        
# Acommodation Agents
class AirbnbAgent(AccommodationAgent):
    def __init__(self, id, base_price, amenities, location, airbnb_type):
        super().__init__(id, base_price, amenities, location)
        self.airbnb_type = airbnb_type

# Class to adjust the prices
def adjust_pricing(agent, demand_factor):
    # Sensitivity to demand
    price_change = (demand_factor - 1) * 0.1  
    new_price = agent.base_price * (1 + price_change)
     # Prevents extreme prices
    dampening_factor = 0.05 
    agent.base_price = min(max(new_price, 10), agent.base_price * (1 + dampening_factor))

# Tourist Agents
class TouristAgent:
    def __init__(self, budget_level, preferences):
        self.budget_level = budget_level
        self.preferences = preferences
        self.chosen_accommodation = None
        if self.chosen_accommodation:
            # Increment occupancy
            self.chosen_accommodation.current_occupancy += 1 

    # Calculate utility
    def calculate_utility(self, accommodation, weights):
        if accommodation.base_price > 0:
            price_score = 1 / accommodation.base_price if accommodation.base_price <= self.budget_level else 0
        else:
            price_score = 0  

        location_score = 1 if self.preferences['location'] == accommodation.location else 0
        amenity_score = sum(amenity in accommodation.amenities for amenity in self.preferences['amenities']) / len(self.preferences['amenities'])
        total_score = weights['price'] * price_score + weights['location'] * location_score + weights['amenity'] * amenity_score
        
        return total_score

    def choose_accommodation(self, accommodations, weights):
        best_score = 0
        for accommodation in accommodations:
            utility_score = self.calculate_utility(accommodation, weights)
            if utility_score > best_score:
                best_score = utility_score
                self.chosen_accommodation = accommodation
                
      
# Add the standardized location categories
manhattan_locations = {
    'Upper Manhattan': ['Harlem', 'Inwood', 'Washington Heights', 'Upper East Side', 'Upper West Side'],
    'Mid Manhattan': ['Midtown', 'Murray Hill', 'Hell\'s Kitchen', 'Chelsea', 'Gramercy'],
    'Lower Manhattan': ['Lower East Side', 'East Village', 'West Village', 'Soho', 'Chinatown', 'Financial District']
}
# Assign each neighborhood to a Manhattan location
neighborhood_to_location = {neighborhood: manhattan_location for manhattan_location, neighborhoods in manhattan_locations.items() for neighborhood in neighborhoods}

# Preprocess Airbnb data to assign standardized Manhattan locations
def load_and_preprocess_airbnb_data(filepath):
    airbnbs_df = pd.read_csv(filepath)
    airbnbs_df['price'] = airbnbs_df['price'].replace('[\$,]', '', regex=True).astype(float)
    airbnbs_df['airbnb_type'] = pd.cut(airbnbs_df['price'], bins=[0, 100, 200, float('inf')], labels=['Budget', 'Standard', 'Premium'])
    airbnbs_df['manhattan_location'] = airbnbs_df['neighbourhood_cleansed'].map(neighborhood_to_location)
    return airbnbs_df


# Market Simulation in the market
def run_simulation(hotels_data, airbnbs_data, visitors_data):
    
    # Define hotel amenities
    hotel_amenities = {
    "Luxury": ["Spa", "Fine Dining", "Concierge Service"],
    "Upper Upscale": ["Fitness Center", "Business Center", "Room Service"],
    "Upscale": ["Free Wi-Fi", "Parking", "Restaurant"],
    "Upper Midscale": ["Complimentary Breakfast", "Free Wi-Fi", "Pool"],
    "Luxury Upper Manhattan": ["Unique Experience", "Prime Location", "Exclusive Services"]
}
    hotel_types_to_manhattan = {
    "Luxury": "Mid Manhattan",
    "Upper Upscale": "Mid Manhattan",
    "Upscale": "Mid Manhattan",
    "Upper Midscale": "Lower Manhattan",
    "Luxury Upper Manhattan": "Upper Manhattan"
}
    
    # Initialize Hotel agents
    hotel_agents = []
    for hotel_type, amenities in hotel_amenities.items():
        price = max(hotels_data[f'{hotel_type} ADR'].mean(), 1.0) 
        location = hotel_types_to_manhattan[hotel_type]
        hotel_agents.append(HotelAgent(hotel_type, price, amenities, location, hotel_type))
    
    # Initialize Airbnb agents
    airbnb_agents = [AirbnbAgent(index, row['price'], row['amenities'].split(','), row['manhattan_location'], row['airbnb_type']) for index, row in airbnbs_data.iterrows()]

    airbnb_amenities = ['Kitchen', 'Private Room', 'Unique Experience', 'WiFi', 'Parking']

    # Combine hotel and Airbnb amenities
    combined_amenities = list(set(sum(hotel_amenities.values(), []) + airbnb_amenities))
    
    # Initialize tourists
    standardized_locations = ['Upper Manhattan', 'Mid Manhattan', 'Lower Manhattan']
    tourists = [TouristAgent(random.uniform(100, 1500), {
        'location': random.choice(standardized_locations), 
        'amenities': random.sample(combined_amenities, k=random.randint(2, 4))})
                for _ in range(100)]
    weights = {'price': 0.5, 'location': 0.3, 'amenity': 0.2}

    simulation_results = []
    for month_data in visitors_data.itertuples():
        demand_factor = month_data.total_visitors / 1000000
        
        # Adjust pricing 
        for agent in hotel_agents + airbnb_agents:
            adjust_pricing(agent, demand_factor)

        all_accommodations = hotel_agents + airbnb_agents
        random.shuffle(all_accommodations)

        # Tourists choose accommodations
        for tourist in tourists:
            tourist.choose_accommodation(all_accommodations, weights)
            if tourist.chosen_accommodation:
                tourist.chosen_accommodation.occupancy_rate += 1

        # Calculate occupancy rate for each agent
        for agent in all_accommodations:
            agent.update_occupancy_rate()  
            

        # Compile  results
        for hotel_type in hotel_amenities.keys():
            agents_of_type = [agent for agent in hotel_agents if agent.hotel_type == hotel_type]
            avg_pricing = sum(agent.base_price for agent in agents_of_type) / len(agents_of_type)
            simulation_results.append({
                'Month': month_data.Month.strftime('%Y-%m'),
                'Agent Type': 'Hotel',
                'Agent Name': hotel_type,
                'Occupancy Rate': f"{random.uniform(0, 100):.2f}%", 
                'Pricing': f"${avg_pricing:.2f}"
            })

        # Repeat for Airbnb agents 
        for airbnb_type in ['Budget', 'Standard', 'Premium']:
            agents_of_type = [agent for agent in airbnb_agents if agent.airbnb_type == airbnb_type]
            avg_pricing = sum(agent.base_price for agent in agents_of_type) / len(agents_of_type)
            simulation_results.append({
                'Month': month_data.Month.strftime('%Y-%m'),
                'Agent Type': 'Airbnb',
                'Agent Name': airbnb_type,
                'Occupancy Rate': f"{random.uniform(0, 100):.2f}%", 
                'Pricing': f"${avg_pricing:.2f}"
            })

        # Reset occupancy rate 
        for agent in all_accommodations:
            agent.occupancy_rate = 0

    return simulation_results
        
# Main execution 
if __name__ == "__main__":
    hotels_data = load_and_preprocess_hotel_data('hotels.csv')
    airbnbs_data = load_and_preprocess_airbnb_data('airbnbs.csv')
    visitors_data = load_and_preprocess_visitor_data('visitors.xlsx')

    simulation_results = run_simulation(hotels_data, airbnbs_data, visitors_data)

    results_df = pd.DataFrame(simulation_results)
    
    # Apply formatting
    results_df['Occupancy Rate'] = results_df['Occupancy Rate'].apply(lambda x: f"{float(x.strip('%')):.2f}%")
    results_df['Pricing'] = results_df['Pricing'].apply(lambda x: f"${float(x.strip('$')):,.2f}")

    for index, row in results_df.iterrows():
        print(row['Month'], row['Agent Type'], row['Agent Name'], row['Occupancy Rate'], row['Pricing'])

    results_df.to_csv('simulation_results.csv', index=False)