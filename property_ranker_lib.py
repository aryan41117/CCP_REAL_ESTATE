from flask import flash


def rank_by_price(properties):
   try:
        ranked_properties = sorted(properties, key=lambda x: x.get('price', float('inf')))
        return ranked_properties
    except Exception as e:
        print(f"Error while ranking properties: {e}")
        flash("There was an issue ranking the properties.", category='error')
        return []

def filter_by_location(properties, selected_location):
    try:
        if selected_location:
            return [p for p in properties if p.get('location') == selected_location]
        return properties
    except Exception as e:
        print(f"Error while filtering properties: {e}")
        flash("There was an issue filtering the properties.", category='error')
        return []
