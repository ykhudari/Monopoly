using DataFrames
using Random

# Data loading and preprocessing functions
function load_and_preprocess_hotel_data(filepath)
    hotels_df = CSV.File(filepath) |> DataFrame
    
    # Convert Month column to Date type
    hotels_df.Month .= Date.(hotels_df.Month, "d-u")
    
    # Sort DataFrame by Month
    hotels_df = sort(hotels_df, :Month)
    
    return hotels_df
end

function load_and_preprocess_airbnb_data(filepath)
    airbnbs_df = DataFrame(CSV.File(filepath))
    airbnbs_df.price = parse.(Float64, replace.(airbnbs_df.price, r"[\$,]" => ""))
    airbnbs_df.airbnb_type = cut(airbnbs_df.price, edges=[0, 100, 200, Inf], labels=["Budget", "Standard", "Premium"])
    return airbnbs_df
end

function load_and_preprocess_airbnb_data(filepath)
    airbnbs_df = CSV.File(filepath) |> DataFrame
    
    # Convert price column to Float64
    airbnbs_df.price .= parse.(Float64, replace.(string.(airbnbs_df.price), r"[\$,]" => ""))
    
    # Create airbnb_type column based on price bins
    airbnb_bins = [0, 100, 200, Inf]
    airbnb_labels = ["Budget", "Standard", "Premium"]
    airbnbs_df[!, :airbnb_type] .= cut(airbnbs_df[!, :price], bins=airbnb_bins, labels=airbnb_labels)
    
    return airbnbs_df
end

function load_and_preprocess_visitor_data(filepath)
    visitors_df = CSV.File(filepath) |> DataFrame
    
    # Calculate total_visitors column
    visitors_df[!, :total_visitors] .= visitors_df[:, :`JFK visitors (2023)`] .+ visitors_df[:, :`LaGuardia visitors (2023)`]
    
    # Convert Month column to Date type
    visitors_df.Month .= Dates.Date.(string.(visitors_df.Month), "yyyy-mm-dd")
    
    # Select only the desired columns
    visitors_df = select(visitors_df, [:Month, :total_visitors])
    
    return visitors_df
end
# Agent abstracts
abstract type AccommodationAgent end

mutable struct HotelAgent <: AccommodationAgent
    id::String
    base_price::Float64
    amenities::Vector{String}
    location::String
    occupancy_rate::Float64
    hotel_type::String
end

mutable struct AirbnbAgent <: AccommodationAgent
    id::Int
    base_price::Float64
    amenities::Vector{String}
    location::String
    occupancy_rate::Float64
    airbnb_type::String
end
function adjust_pricing(agent::AccommodationAgent, demand_factor::Float64)
    price_change = (demand_factor - 1) * 0.1  # Sensitivity to demand
    new_price = agent.base_price * (1 + price_change)
    dampening_factor = 0.05  # This dampens the change to prevent extreme prices
    agent.base_price = min(max(new_price, 10.0), agent.base_price * (1 + dampening_factor))
end

mutable struct TouristAgent
    budget_level::Float64
    preferences::Dict{String, Any}
    chosen_accommodation::Union{HotelAgent, AirbnbAgent}
end
function calculate_utility(tourist::TouristAgent, accommodation::AccommodationAgent, weights::Dict{String, Float64})
    if accommodation.base_price > 0
        price_score = 1 / accommodation.base_price <= tourist.budget_level ? 1 / accommodation.base_price : 0
    else
        price_score = 0  # Assign a score of 0 if base_price is not positive
    end

    location_score = tourist.preferences["location"] == accommodation.location ? 1 : 0
    amenity_score = sum(amenity in accommodation.amenities for amenity in tourist.preferences["amenities"]) / length(tourist.preferences["amenities"])
    total_score = weights["price"] * price_score + weights["location"] * location_score + weights["amenity"] * amenity_score

    return total_score
end

function choose_accommodation(tourist::TouristAgent, accommodations::Vector{AccommodationAgent}, weights::Dict{String, Float64})
    best_score = 0
    for accommodation in accommodations
        utility_score = calculate_utility(tourist, accommodation, weights)
        if utility_score > best_score
            best_score = utility_score
            tourist.chosen_accommodation = accommodation
        end
    end
end
manhattan_locations = Dict(
    "Upper Manhattan" => ["Harlem", "Inwood", "Washington Heights", "Upper East Side", "Upper West Side"],
    "Mid Manhattan" => ["Midtown", "Murray Hill", "Hell's Kitchen", "Chelsea", "Gramercy"],
    "Lower Manhattan" => ["Lower East Side", "East Village", "West Village", "Soho", "Chinatown", "Financial District"]
)

# Reverse the mapping to assign each neighborhood to a Manhattan location
neighborhood_to_location = Dict(neigh => loc for (loc, neighs) in manhattan_locations for neigh in neighs)

# Function to preprocess Airbnb data updated to assign standardized Manhattan locations
function load_and_preprocess_airbnb_data(filepath)
    airbnbs_df = DataFrame(CSV.File(filepath))
    airbnbs_df.price = parse.(Float64, replace.(airbnbs_df.price, r"[\$,]" => ""))
    airbnbs_df.airbnb_type = cut(airbnbs_df.price, edges=[0, 100, 200, Inf], labels=["Budget", "Standard", "Premium"])
    # Map the neighborhoods to the standardized locations
    airbnbs_df.manhattan_location = map(x -> get(neighborhood_to_location, x, ""), airbnbs_df.neighbourhood_cleansed)
    return airbnbs_df
end
hotel_amenities = Dict(
    "Luxury" => ["Spa", "Fine Dining", "Concierge Service"],
    "Upper Upscale" => ["Fitness Center", "Business Center", "Room Service"],
    "Upscale" => ["Free Wi-Fi", "Parking", "Restaurant"],
    "Upper Midscale" => ["Complimentary Breakfast", "Free Wi-Fi", "Pool"],
    "Upper Manhattan" => ["Unique Experience", "Prime Location", "Exclusive Services"]
)

hotel_types_to_manhattan = Dict(
    "Luxury" => "Mid Manhattan",
    "Upper Upscale" => "Mid Manhattan",
    "Upscale" => "Mid Manhattan",
    "Upper Midscale" => "Lower Manhattan",
    "Upper Manhattan" => "Upper Manhattan"
)
