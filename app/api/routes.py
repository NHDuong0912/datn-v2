from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Node, User, Alert
from app import db
import requests
from requests.exceptions import RequestException

api = Blueprint('api', __name__)

@api.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    })

@api.route('/nodes', methods=['GET'])
@jwt_required()
def get_nodes():
    try:
        current_user_id = get_jwt_identity()
        search = request.args.get('search', '')
        status = request.args.get('status', 'all')
        
        nodes = Node.get_nodes_by_user(current_user_id, search, status)
        return jsonify([node.to_dict() for node in nodes])
    except Exception as e:
        print(f"Error in get_nodes: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

@api.route('/nodes', methods=['POST'])
@jwt_required()
def create_node():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        new_node = Node.create_node(current_user_id, data)
        return jsonify(new_node.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/nodes/<int:node_id>', methods=['PUT'])
@jwt_required()
def update_node(node_id):
    try:
        current_user_id = get_jwt_identity()
        node = Node.query.filter_by(id=node_id, ownerId=current_user_id).first()
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
            
        data = request.get_json()
        node.update_node(data)
        return jsonify(node.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/nodes/<int:node_id>', methods=['DELETE'])
@jwt_required()
def delete_node(node_id):
    try:
        current_user_id = get_jwt_identity()
        node = Node.query.filter_by(id=node_id, ownerId=current_user_id).first()
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
            
        node.delete_node()
        return jsonify({'message': 'Node deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/nodes/<int:node_id>/metrics', methods=['GET'])
@jwt_required()
def check_node_metrics(node_id):
    try:
        current_user_id = get_jwt_identity()
        node = Node.query.filter_by(id=node_id, ownerId=current_user_id).first()

        if not node:
            return jsonify({'error': 'Node not found'}), 404

        # Check Node Exporter
        node_exporter_url = f"http://{node.ipAddress}:{node.portNodeExporter}/metrics"
        try:
            response = requests.get(node_exporter_url, timeout=5)
            node_exporter_status = f"NodeExporter {node.portNodeExporter}" if response.status_code == 200 else "NodeExporter Null"
        except requests.exceptions.RequestException:
            node_exporter_status = "NodeExporter Null"

        # Check Promtail
        promtail_url = f"http://{node.ipAddress}:{node.portPromtail}/metrics"
        try:
            response = requests.get(promtail_url, timeout=5)
            promtail_status = f"Promtail {node.portPromtail}" if response.status_code == 200 else "Promtail Null"
        except requests.exceptions.RequestException:
            promtail_status = "Promtail Null"

        return jsonify({
            'nodeExporter': node_exporter_status,
            'promtail': promtail_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/nodes/<int:node_id>/alerts', methods=['GET', 'POST'])
@jwt_required()
def manage_alerts(node_id):
    try:
        current_user_id = get_jwt_identity()
        node = Node.query.filter_by(id=node_id, ownerId=current_user_id).first()

        if not node:
            return jsonify({'error': 'Node not found'}), 404

        if request.method == 'GET':
            alerts = Alert.query.filter_by(nodeId=node_id).all()
            return jsonify([alert.to_dict() for alert in alerts])

        # Handle POST request
        data = request.get_json()
        print("Received alert data:", data)  # Debug log
        
        if not data or 'message' not in data or 'destination' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        alert = Alert.create_alert(
            node_id=node_id,
            message=data['message'],
            destination=data['destination']
        )

        return jsonify(alert.to_dict()), 201

    except Exception as e:
        print(f"Error managing alerts: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@api.route('/nodes/<int:node_id>/check-service', methods=['POST'])
@jwt_required()
def check_service(node_id):
    try:
        data = request.get_json()
        service_type = data.get('type')
        ip = data.get('ip')
        port = data.get('port')

        # Set up request parameters
        url = f'http://{ip}:{port}/{"metrics" if service_type == "nodeExporter" else "ready"}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        timeout = 5

        try:
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            return jsonify({
                'status': 'success' if response.status_code == 200 else 'error',
                'message': ('Service is running' if response.status_code == 200 
                          else f'Service responded with status {response.status_code}')
            })
        except requests.exceptions.ConnectTimeout:
            return jsonify({
                'status': 'error',
                'message': f'Connection timed out after {timeout} seconds'
            }), 408
        except requests.exceptions.ConnectionError:
            return jsonify({
                'status': 'error',
                'message': 'Could not connect to service'
            }), 503
        except RequestException as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500