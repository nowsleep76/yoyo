from flask import Blueprint, request, jsonify
from models.database import get_all_spots, get_all_species

spots_bp = Blueprint('spots', __name__)

@spots_bp.route('/api/spots', methods=['GET'])
def list_spots():
    species = request.args.get('species', type=str)

    spots = get_all_spots(species)

    return jsonify(spots)

@spots_bp.route('/api/spots/species', methods=['GET'])
def list_species():
    species = get_all_species()

    return jsonify({'species': species})
