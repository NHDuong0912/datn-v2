from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum
import json
from flask_login import UserMixin, logout_user
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

auth = Blueprint('auth', __name__)

class TypeScript(Enum):
    NODE_EXPORTER = "node_exporter"
    PROMTAIL = "promtail"
    LOKI = "loki"

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    
    # Relationships
    nodes = db.relationship('Node', backref='owner', lazy='dynamic')
    access_logs = db.relationship('AccessLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def register(self):
        db.session.add(self)
        db.session.commit()
    
    def login(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    def updateProfile(self, username=None, email=None):
        if username:
            self.username = username
        if email:
            self.email = email
        db.session.commit()
    
    def deleteAccount(self, id):
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ipAddress = db.Column(db.String(100))
    status = db.Column(db.String(50))
    portNodeExporter = db.Column(db.Integer)
    portPromtail = db.Column(db.Integer)
    ownerId = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def get_nodes_by_user(cls, user_id, search=None, status=None):
        """Get all nodes for a user with optional filters."""
        query = cls.query.filter_by(ownerId=user_id)
        
        if search:
            query = query.filter(cls.name.ilike(f'%{search}%'))
        if status and status != 'all':
            query = query.filter_by(status=status)
            
        return query.all()

    def to_dict(self):
        """Convert node to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'ipAddress': self.ipAddress,
            'status': self.status,
            'portNodeExporter': self.portNodeExporter,
            'portPromtail': self.portPromtail
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(100))

    @classmethod
    def log_access(cls, user_id, action):
        """Log a user action."""
        try:
            print(f"Logging access: user_id={user_id}, action={action}")  # Debug statement
            log = cls(userId=user_id, action=action)
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to log access: {str(e)}")  # Debug statement
            raise Exception(f"Failed to log access: {str(e)}")

class DataCollectionConfig(db.Model):
    __tablename__ = 'data_collection_configs'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    dataSources = db.Column(db.String(500))  # JSON string representing Map<String, Map<String, boolean>>
    
    def configureCollection(self, id, source):
        pass
    
    def getCollectionConfig(self, id):
        return {}  # Map<String, Map<String, boolean>>

class OnchainData(db.Model):
    __tablename__ = 'onchain_data'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    blockHeight = db.Column(db.Integer)
    transactionCount = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def queryOnchainData(self, nodeId):
        return OnchainData
    
    def storeOnchainData(self):
        pass

class PerformanceData(db.Model):
    __tablename__ = 'performance_data'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpuUsage = db.Column(db.Float)
    memoryUsage = db.Column(db.Float)
    diskUsage = db.Column(db.Float)
    networkUpUsage = db.Column(db.Float)
    networkDownUsage = db.Column(db.Float)
    uptime = db.Column(db.Float)
    
    def fetchPerformanceData(self, nodeId):
        return PerformanceData
    
    def storePerformanceData(self):
        pass

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    # Add relationship to Node
    node = db.relationship('Node', backref=db.backref('alerts', lazy=True))

    @classmethod
    def create_alert(cls, node_id, message, destination):
        """Create a new alert for a node."""
        try:
            print(f"Creating alert for node {node_id}")  # Debug log
            alert = cls(
                nodeId=node_id,
                message=message,
                destination=destination
            )
            db.session.add(alert)
            db.session.commit()
            return alert
        except Exception as e:
            db.session.rollback()
            print(f"Error creating alert: {str(e)}")  # Debug log
            raise Exception(f"Failed to create alert: {str(e)}")

    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'nodeId': self.nodeId,
            'message': self.message,
            'destination': self.destination
        }

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    startDate = db.Column(db.DateTime)
    endDate = db.Column(db.DateTime)
    content = db.Column(db.Text)
    
    def generateReport(self, id, startDate, endDate):
        return Report
    
    def exportReport(self, reportId):
        pass

class WebDisplay(db.Model):
    __tablename__ = 'web_displays'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    frameUrlLogs = db.Column(db.String(500))
    frameUrlPerformance = db.Column(db.String(500))
    
    def generateIframeUrl(self, id, type):
        return ""
    
    def displayData(self, nodeId):
        pass

class ScriptGenerator(db.Model):
    __tablename__ = 'script_generators'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    typeScript = db.Column(db.Enum(TypeScript))
    scriptContent = db.Column(db.Text)
    
    def generateScript(self, id, port, ip, type):
        return ""
    
    def saveScript(self):
        pass

class ExternalSystem(db.Model):
    __tablename__ = 'external_systems'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    apiKey = db.Column(db.String(200))
    
    def fetchIframeUrlFromGrafana(self, nodeId, id, type):
        return ""
    
    def fetchLogFromLoki(self, id, query, startTime=None, endTime=None):
        return []
    
    def sendTelegramMessage(self, message):
        pass
    
    def addTargetToGrafana(self, nodeId, ipAddress, port):
        return False

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    
    # Log the logout action
    try:
        AccessLog.log_access(current_user_id, "User logged out")
        print("Logout action logged successfully")  # Debug statement
    except Exception as e:
        print(f"Failed to log access: {str(e)}")
    
    logout_user()
    return jsonify({'msg': 'User logged out successfully'}), 200