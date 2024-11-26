from flask import flash
from models import get_db

def rank_by_price(properties):
    """
    Ranks properties in ascending order based on price.

    :param properties: List of properties, each represented as a dictionary.
    :return: List of properties sorted by price (low to high).
    """
    try:
        # Ensure all properties have a 'price' key and sort them by price
        ranked_properties = sorted(properties, key=lambda x: x.get('price', float('inf')))
        return ranked_properties
    except Exception as e:
        print(f"Error while ranking properties: {e}")
        flash("There was an issue ranking the properties.", category='error')
        return []

def filter_by_location(properties, selected_location):
    """
    Filters properties by the selected location.

    :param properties: List of properties, each represented as a dictionary.
    :param selected_location: Location to filter properties by.
    :return: Filtered list of properties.
    """
    try:
        if selected_location:
            return [p for p in properties if p.get('location') == selected_location]
        return properties
    except Exception as e:
        print(f"Error while filtering properties: {e}")
        flash("There was an issue filtering the properties.", category='error')
        return []
