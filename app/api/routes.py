from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Node, User, Alert
from app import db
import requests
from requests.exceptions import RequestException
import subprocess
import json

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
def get_node_metrics(node_id):
    try:
        node = Node.query.get_or_404(node_id)
        
        # Check Node Exporter status
        nodeExporter_status = 'Inactive'
        try:
            response = requests.get(
                f'http://{node.ipAddress}:{node.portNodeExporter}/metrics', 
                timeout=2,
                verify=False
            )
            if response.ok:
                nodeExporter_status = 'Active'
        except:
            pass

        # Check Promtail status
        promtail_status = 'Inactive'
        try:
            response = requests.get(
                f'http://{node.ipAddress}:{node.portPromtail}/ready', 
                timeout=2,
                verify=False
            )
            if response.ok:
                promtail_status = 'Active'
        except:
            pass

        # Update node status based on either service being active
        if nodeExporter_status == 'Active' or promtail_status == 'Active':
            node.status = 'active'
        else:
            node.status = 'inactive'
        
        db.session.commit()

        return jsonify({
            'nodeExporter': nodeExporter_status,
            'promtail': promtail_status,
            'status': node.status
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

@api.route('/nodes/connect-node-exporter', methods=['POST'])
@jwt_required()
def connect_node_exporter():
    try:
        data = request.get_json()
        ip = data.get('ip')
        port = data.get('port')
        
        if not ip or not port:
            return jsonify({'error': 'Missing IP or port'}), 400

        target = f"{ip}:{port}"
        file_path = "/root/prometheus-config/tg_prometheus.json"
        
        # Construct the jq command
        command = f"""
        NEW_TARGET="{target}"
        FILE_PATH="{file_path}"
        jq --arg new_target "$NEW_TARGET" '.[] .targets += [$new_target]' "$FILE_PATH" > "$FILE_PATH.tmp" && mv "$FILE_PATH.tmp" "$FILE_PATH"
        """
        
        # Execute the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")

        return jsonify({'status': 'success', 'message': 'Node Exporter connected successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500